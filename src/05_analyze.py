"""
05_analyze.py  --  works offline once data/clean/snapshots.csv exists.

WHAT THIS DOES (in plain English)
---------------------------------
Reads the snapshots and prints the same "price vs. reality" table as the toy
script, once for each time horizon (7d, 1d, 1h). That's the core result.

It can also run on the toy data so you can test it before real data exists:
    python src/05_analyze.py --fake
"""

import csv
import random
import sys

SNAPSHOT_FILE = "data/clean/snapshots.csv"
NUM_BUCKETS = 10


def load_rows():
    """Read the snapshot file into a list of dictionaries."""
    rows = []
    with open(SNAPSHOT_FILE) as f:
        for r in csv.DictReader(f):
            rows.append({
                "category": r["category"],
                "horizon": r["horizon"],
                "price": float(r["price"]),
                "outcome": int(r["outcome"]),
            })
    return rows


def fake_rows():
    """Make fake data (same idea as the toy script) so you can test this file."""
    random.seed(1)
    rows = []
    for _ in range(3000):
        true_prob = random.random()
        rows.append({
            "category": random.choice(["politics", "sports"]),
            "horizon": random.choice(["7d", "1d", "1h"]),
            "price": 0.5 + (true_prob - 0.5) * 0.8,
            "outcome": 1 if random.random() < true_prob else 0,
        })
    return rows


def calibration_table(rows, title):
    """Print the price-vs-reality table for a group of rows."""
    print()
    print(f"=== {title}  ({len(rows)} snapshots) ===")
    if len(rows) == 0:
        print("  (no data)")
        return

    buckets = [[] for _ in range(NUM_BUCKETS)]
    for r in rows:
        i = min(int(r["price"] * NUM_BUCKETS), NUM_BUCKETS - 1)
        buckets[i].append(r)

    print(f"{'bucket':>10} {'n':>6} {'avg price':>10} {'actual':>8} {'gap':>8}")
    for i, g in enumerate(buckets):
        if not g:
            continue
        avg_p = sum(r["price"] for r in g) / len(g)
        actual = sum(r["outcome"] for r in g) / len(g)
        label = f"{i/NUM_BUCKETS:.0%}-{(i+1)/NUM_BUCKETS:.0%}"
        # Warn when a bucket has very few markets: the gap is mostly luck.
        flag = "  <- few markets, ignore" if len(g) < 30 else ""
        print(f"{label:>10} {len(g):>6} {avg_p:>10.3f} {actual:>8.3f} {actual-avg_p:>+8.3f}{flag}")

    brier = sum((r["price"] - r["outcome"]) ** 2 for r in rows) / len(rows)
    print(f"  Brier score: {brier:.4f}  (always guessing 50% = 0.2500; lower is better)")


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
rows = fake_rows() if "--fake" in sys.argv else load_rows()

# 1. Overall, by horizon
for horizon in ["7d", "1d", "1h"]:
    calibration_table([r for r in rows if r["horizon"] == horizon], f"All markets, {horizon} before end")

# 2. By category (e.g. politics vs sports) at one horizon
for category in sorted(set(r["category"] for r in rows)):
    subset = [r for r in rows if r["category"] == category and r["horizon"] == "1d"]
    calibration_table(subset, f"{category}, 1d before end")

print()
print("REMINDER: a gap can be luck, especially with few markets. Never claim a")
print("bias from one bucket. Look for a consistent pattern across buckets.")
