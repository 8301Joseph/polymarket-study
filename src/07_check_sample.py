"""
07_check_sample.py  --  a HEALTH CHECK, not a result. Works offline.

WHAT THIS DOES (in plain English)
---------------------------------
Before we look at whether prices were right, we check that the data is
usable. This script only COUNTS things. It never compares prices with
outcomes, so running it does not break the pre-registration.

It answers:
  1. How many snapshots do we have for each category and horizon?
  2. How many long shots and favourites are in each group? (We need at
     least 30 in a group to say anything about it.)
  3. Did the skipping rules remove one kind of market more than another?
     (Compare how often the first outcome wins among ALL sampled markets
      versus among the markets that made it into the snapshots.)

HOW TO RUN
    python3 src/07_check_sample.py
"""

import csv
from collections import defaultdict

HORIZONS = ["7d", "1d", "1h"]
CATEGORIES = ["politics", "sports"]

with open("data/clean/sample.csv") as f:
    sample = list(csv.DictReader(f))
with open("data/clean/snapshots.csv") as f:
    snaps = list(csv.DictReader(f))

# ---- 1 & 2: counts by category and horizon --------------------------------
print("SNAPSHOTS PER GROUP  (need at least 30 in a group to say anything about it)")
print(f"{'category':>9} {'horizon':>8} {'total':>7} {'<0.10':>7} {'<0.30':>7} {'>0.70':>7} {'>0.90':>7}")
for cat in CATEGORIES:
    for h in HORIZONS:
        prices = [float(r["price"]) for r in snaps if r["category"] == cat and r["horizon"] == h]
        print(f"{cat:>9} {h:>8} {len(prices):>7} "
              f"{sum(p < 0.10 for p in prices):>7} {sum(p < 0.30 for p in prices):>7} "
              f"{sum(p > 0.70 for p in prices):>7} {sum(p > 0.90 for p in prices):>7}")

# ---- 3: did skipping change the mix of markets? ----------------------------
print("\nHOW OFTEN THE FIRST OUTCOME WINS  (these two numbers should be close)")
print(f"{'category':>9} {'all sampled markets':>22} {'markets with a snapshot':>26}")
with_snapshot = defaultdict(set)
for r in snaps:
    with_snapshot[r["category"]].add(r["market_id"])
for cat in CATEGORIES:
    allm = [r for r in sample if r["category"] == cat]
    kept = [r for r in allm if r["market_id"] in with_snapshot[cat]]
    a = sum(int(r["won"]) for r in allm) / max(len(allm), 1)
    k = sum(int(r["won"]) for r in kept) / max(len(kept), 1)
    print(f"{cat:>9} {a:>16.1%} ({len(allm)}) {k:>20.1%} ({len(kept)})")

# ---- Markets per event: how clustered is the sample? ------------------------
print("\nCLUSTERING  (markets sharing an event are not independent)")
for cat in CATEGORIES:
    events = defaultdict(int)
    for r in sample:
        if r["category"] == cat:
            events[r["event_id"]] += 1
    n = sum(events.values())
    print(f"{cat:>9}: {n} markets from {len(events)} events; largest event has {max(events.values())} markets")