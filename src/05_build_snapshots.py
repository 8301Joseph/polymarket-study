"""
05_build_snapshots.py  --  works offline once the price files exist.

WHAT THIS DOES (in plain English)
---------------------------------
For each chosen market we want one question answered per time horizon:
   "What was the price 7 days (or 1 day, or 1 hour) before the market was
    effectively DECIDED, and did the first outcome end up winning?"
Each answer is a "snapshot": one row with a price and a win/lose result.

WHAT "DECIDED" MEANS HERE  (important, read this)
-------------------------------------------------
Polymarket's date fields are not usable as "the end":
  - 'endDate' is a deadline. Many markets carry a placeholder like 31 Dec
    that has nothing to do with when they really finished.
  - 'closedTime' is when the result was officially confirmed, which can be
    weeks AFTER the event happened. By then the price is already 0 or 1.

So we find the decision time from the price history itself:
    DECIDED TIME = the last moment the price was still between 2 and 98 cents.
After that the market has effectively been settled. We then look back 7 days,
1 day and 1 hour from that moment.

THE RULE THAT PREVENTS CHEATING (no look-ahead)
-----------------------------------------------
Having found the decision time, the price we record is the LAST price at or
before (decision time minus horizon). Nothing from after that moment is used
as the price. (The decision time itself is found using the future, but only to
decide WHERE to look, never what price to record.)

HOW TO RUN
    python src/05_build_snapshots.py
"""

import csv
import json
import os
from collections import Counter

SAMPLE_FILE = "data/clean/sample.csv"
PRICES_FOLDER = "data/raw/prices"
OUTPUT_FILE = "data/clean/snapshots.csv"

HORIZONS = {"7d": 7 * 24 * 3600, "1d": 24 * 3600, "1h": 3600}   # seconds

UNDECIDED_LOW = 0.02     # below this the market counts as "decided: No"
UNDECIDED_HIGH = 0.98    # above this the market counts as "decided: Yes"
EXTREME_LOW = 0.01       # snapshots at or below this price are skipped...
EXTREME_HIGH = 0.99      # ...and at or above this one
MAX_PRICE_AGE_HOURS = 48 # skip if the latest price we have is older than this

os.makedirs("data/clean", exist_ok=True)


def load_history(token):
    """Return the price history as a list of (time_in_seconds, price), oldest first."""
    path = os.path.join(PRICES_FOLDER, f"{token}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        points = json.load(f).get("history", [])
    out = []
    for point in points:
        t = float(point["t"])
        if t > 1e11:           # times in milliseconds -> seconds
            t = t / 1000
        out.append((t, float(point["p"])))
    out.sort()
    return out


def decided_time(history):
    """Time of the last price point that is still undecided (between 2c and 98c)."""
    last = None
    for t, p in history:
        if UNDECIDED_LOW < p < UNDECIDED_HIGH:
            last = t
    return last


def last_price_at_or_before(history, cutoff):
    """Return (time, price) of the last point at or before cutoff, else None."""
    best = None
    for t, p in history:
        if t <= cutoff:
            best = (t, p)
        else:
            break              # everything after this is the future: stop
    return best


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
with open(SAMPLE_FILE) as f:
    sample = list(csv.DictReader(f))

rows = []
skipped = Counter()            # why snapshots were skipped
skipped_by_outcome = Counter() # ...and whether the market's first outcome won

for m in sample:
    won = int(m["won"])
    history = load_history(m["token_id"])
    if not history:
        skipped[("no price file", "all")] += 1
        skipped_by_outcome[won] += 1
        continue

    t_decided = decided_time(history)
    if t_decided is None:
        skipped[("never undecided", "all")] += 1
        skipped_by_outcome[won] += 1
        continue

    for name, seconds in HORIZONS.items():
        found = last_price_at_or_before(history, t_decided - seconds)
        if found is None:
            reason = "no price that early"
        else:
            t_price, price = found
            age_hours = (t_decided - seconds - t_price) / 3600
            if age_hours > MAX_PRICE_AGE_HOURS:
                reason = "price too old"
            elif price <= EXTREME_LOW or price >= EXTREME_HIGH:
                reason = "price already extreme"
            else:
                reason = None
        if reason:
            skipped[(reason, name)] += 1
            skipped_by_outcome[won] += 1
            continue
        rows.append({
            "market_id": m["market_id"],
            "event_id": m["event_id"],
            "category": m["category"],
            "horizon": name,
            "price": price,
            "won": won,
            "volume": m["volume"],
            "closed_time": m["closed_time"],
        })

fields = ["market_id", "event_id", "category", "horizon", "price", "won", "volume", "closed_time"]
with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} snapshots to {OUTPUT_FILE}\n")
print("Snapshots skipped, and why:")
for (reason, horizon), n in sorted(skipped.items()):
    print(f"   {reason:>22} ({horizon}): {n}")

# A health check: if the skipped snapshots are mostly from markets that WON (or
# mostly from ones that LOST), our sample is lopsided and the results could be
# misleading. The two numbers below should be roughly balanced.
print("\nSkipped snapshots by outcome of the market:")
print(f"   first outcome won:  {skipped_by_outcome[1]}")
print(f"   first outcome lost: {skipped_by_outcome[0]}")
