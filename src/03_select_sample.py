"""
03_select_sample.py

WHAT THIS DOES (in plain English)
---------------------------------
02 downloaded EVERY finished market for each category. This script:
  1. Throws away markets we can't use (see the rules below).
  2. Keeps only markets that closed inside each category's sample period.
  3. Picks a RANDOM sample of SAMPLE_SIZE markets per category.
  4. Saves the chosen markets to data/clean/sample.csv.

WHY RANDOM? If we just took the first 500 markets the server gave us, we could
end up with a strange slice (for example only one month, or only one type of
market). A random pick, with the random seed written down in advance, means
nobody can say we hand-picked markets that suited us.

THE RULES (these are written in PREREGISTRATION.md too)
-------------------------------------------------------
  - Exactly two outcomes (Yes/No, or two teams).
  - The market must have a clear winner (no 50/50 or cancelled markets).
  - Total volume of at least $10,000.
  - Closed inside the sample period for its category.
  - The "priced side" is always the FIRST outcome listed (for Yes/No markets
    that is "Yes"). We record its price and whether it won.

HOW TO RUN
    python src/03_select_sample.py
"""

import csv
import glob
import json
import os
import random
from datetime import datetime

# ----------------------------------------------------------------------------
# SETTINGS  (match PREREGISTRATION.md -- do not change after seeing results)
# ----------------------------------------------------------------------------
SEED = 42                 # makes the "random" pick repeatable
SAMPLE_SIZE = 1500        # markets per category
MIN_VOLUME = 10000

# Sample period for each category, by the market's real closing time (UTC).
PERIODS = {
    "sports":   ("2023-10-01", "2026-09-30"),   # 3 years
    "politics": ("2025-10-01", "2026-09-30"),   # 1 year
}

RAW_FOLDER = "data/raw/markets"
OUTPUT_FILE = "data/clean/sample.csv"
os.makedirs("data/clean", exist_ok=True)


def parse_time(text):
    """Turn a time string into seconds since 1970. Handles the formats Polymarket
    uses, like '2025-03-14 14:36:55+00' and '2025-03-14T14:36:55Z'."""
    if not text:
        return None
    t = text.strip().replace(" ", "T").replace("Z", "+00:00")
    if len(t) > 3 and t[-3] in "+-" and t[-2:].isdigit():   # '+00' -> '+00:00'
        t = t + ":00"
    try:
        return datetime.fromisoformat(t).timestamp()
    except ValueError:
        return None


def as_list(value):
    """Some fields arrive as text that LOOKS like a list, e.g. '["a", "b"]'.
    Turn that into a real Python list. Real lists are left alone."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def date_to_unix(day):
    return datetime.fromisoformat(day + "T00:00:00+00:00").timestamp()


rng = random.Random(SEED)
rows = []
summary = []

for category, (start_day, end_day) in PERIODS.items():
    start = date_to_unix(start_day)
    end = date_to_unix(end_day) + 24 * 3600     # include the whole last day
    kept = {}
    counts = {"seen": 0, "not two outcomes": 0, "no clear winner": 0,
              "low volume": 0, "outside period": 0}

    for path in sorted(glob.glob(os.path.join(RAW_FOLDER, category, "*.json"))):
        with open(path) as f:
            markets = json.load(f)

        for m in markets:
            counts["seen"] += 1
            outcomes = as_list(m.get("outcomes"))
            tokens = as_list(m.get("clobTokenIds"))
            final = as_list(m.get("outcomePrices"))

            if not (outcomes and tokens and final) or len(outcomes) != 2 or len(tokens) != 2:
                counts["not two outcomes"] += 1
                continue

            first_final = float(final[0])        # final price of the first outcome
            if first_final >= 0.99:
                won = 1
            elif first_final <= 0.01:
                won = 0
            else:
                counts["no clear winner"] += 1   # 50/50 or cancelled
                continue

            try:
                volume = float(m.get("volume") or 0)
            except ValueError:
                volume = 0
            if volume < MIN_VOLUME:
                counts["low volume"] += 1
                continue

            closed = parse_time(m.get("closedTime"))
            if closed is None or not (start <= closed < end):
                counts["outside period"] += 1
                continue

            # Markets that belong to the same event (for example every team in
            # one tournament) are NOT independent. We record the event id so the
            # analysis can account for that.
            events = m.get("events") or []
            event_id = str(events[0].get("id")) if events and isinstance(events[0], dict) else str(m["id"])

            kept[str(m["id"])] = {           # a dict also removes duplicates
                "market_id": str(m["id"]),
                "event_id": event_id,
                "category": category,
                "question": (m.get("question") or "").strip().replace("\n", " "),
                "token_id": tokens[0],       # the FIRST outcome is the priced side
                "priced_outcome": outcomes[0],
                "won": won,
                "volume": volume,
                "closed_time": closed,
            }

    eligible = list(kept.values())
    chosen = rng.sample(eligible, min(SAMPLE_SIZE, len(eligible)))
    rows.extend(chosen)
    summary.append((category, counts, len(eligible), len(chosen)))

# Safety check: a market tagged BOTH politics and sports is ambiguous. Drop it.
ids = [r["market_id"] for r in rows]
duplicates = {i for i in ids if ids.count(i) > 1}
rows = [r for r in rows if r["market_id"] not in duplicates]

fields = ["market_id", "event_id", "category", "question", "token_id",
          "priced_outcome", "won", "volume", "closed_time"]
with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("SELECTION SUMMARY")
for category, counts, eligible, chosen in summary:
    print(f"\n{category}:")
    for reason, n in counts.items():
        print(f"   {reason:>18}: {n}")
    print(f"   {'eligible':>18}: {eligible}")
    print(f"   {'chosen at random':>18}: {chosen}")
print(f"\nDropped {len(duplicates)} markets tagged in both categories.")
print(f"Wrote {len(rows)} markets to {OUTPUT_FILE}")
