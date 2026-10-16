"""
04_build_snapshots.py  --  works offline once the raw data exists.

WHAT THIS DOES (in plain English)
---------------------------------
For each finished market we want ONE question answered per time horizon:
   "What was the price 7 days, 1 day, and 1 hour before the market ended,
    and did the event end up happening?"
That pair (price, outcome) is a "snapshot". We write all snapshots to one
spreadsheet-like file (data/clean/snapshots.csv) that the analysis reads.

THE MOST IMPORTANT RULE (avoid "look-ahead bias")
-------------------------------------------------
When we pick the price at "1 day before the end", we may only use prices from
BEFORE that moment. Using a later price would be cheating, because it would
already contain information about the result. The code below always takes the
LAST price at or before the snapshot time.

NOTE: field names (endDate, outcomePrices, ...) are FROM MEMORY. Open one file
in data/raw/markets/ and check them. Lines marked TODO are the likely fixes.
"""

import csv
import glob
import json
import os
from datetime import datetime

MARKETS_FOLDER = "data/raw/markets"
PRICES_FOLDER = "data/raw/prices"
OUTPUT_FILE = "data/clean/snapshots.csv"

# The horizons, in seconds before the end. 7 days, 1 day, 1 hour.
HORIZONS = {"7d": 7 * 24 * 3600, "1d": 24 * 3600, "1h": 3600}

os.makedirs("data/clean", exist_ok=True)


def to_unix(text):
    """Turn a date string like '2026-03-01T12:00:00Z' into seconds since 1970."""
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def get_yes_token_id(market):
    raw = market.get("clobTokenIds")           # TODO: verify field name
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = json.loads(raw)
    return raw[0] if raw else None


def get_outcome(market):
    """Return 1 if YES won, 0 if NO won, None if unclear (we then skip it).

    TODO: I remember 'outcomePrices' being text like '["1", "0"]' after
    resolution (YES = 1 means YES won). Verify on a real file.
    """
    raw = market.get("outcomePrices")
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = json.loads(raw)
    yes_final = float(raw[0])
    if yes_final > 0.99:
        return 1
    if yes_final < 0.01:
        return 0
    return None   # 50/50 or cancelled markets: skip


def last_price_before(history, cutoff):
    """From a list of {'t': time, 'p': price}, return the last price at or
    before 'cutoff'. Returns None if there is no price that early."""
    best = None
    for point in history:                 # history is in time order
        if point["t"] <= cutoff:
            best = point["p"]
        else:
            break                         # stop: everything after is the future
    return best


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
rows = []
skipped = 0

for path in sorted(glob.glob(os.path.join(MARKETS_FOLDER, "*.json"))):
    with open(path) as f:
        markets = json.load(f)

    for m in markets:
        token = get_yes_token_id(m)
        if token is None:
            continue
        price_file = os.path.join(PRICES_FOLDER, f"{token}.json")
        if not os.path.exists(price_file):
            continue                       # we didn't download this one

        outcome = get_outcome(m)
        end_text = m.get("endDate")        # TODO: verify field name
        if outcome is None or end_text is None:
            skipped += 1
            continue
        end_time = to_unix(end_text)

        with open(price_file) as f:
            history = json.load(f).get("history", [])   # TODO: verify 'history'

        for name, seconds in HORIZONS.items():
            price = last_price_before(history, end_time - seconds)
            # Skip if no price exists that early, or if the market had
            # already decided (price at the extremes tells us nothing).
            if price is None or price <= 0.01 or price >= 0.99:
                skipped += 1
                continue
            rows.append({
                "market_id": m.get("id"),
                "category": m.get("category", "unknown"),   # TODO: may be missing; see README
                "horizon": name,
                "price": price,
                "outcome": outcome,
            })

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["market_id", "category", "horizon", "price", "outcome"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} snapshots to {OUTPUT_FILE}  (skipped {skipped})")
