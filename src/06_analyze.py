"""
06_analyze.py  --  works offline once data/clean/snapshots.csv exists.

WHAT THIS DOES (in plain English)
---------------------------------
Reads the snapshots and prints four things:
  1. The price-vs-reality table for each horizon (7d, 1d, 1h).
  2. A summary of long shots and favourites, by category and horizon.
  3. The same summary for politics vs sports, using ONLY the year both cover.
  4. A cost test: would betting against long shots / backing favourites have
     made money after trading costs?

TRY IT BEFORE YOU HAVE REAL DATA (fake data, works offline):
    python src/06_analyze.py --fake

HOW TO READ THE NUMBERS
-----------------------
  gap = actual win rate - average price
     gap < 0  ->  the outcome happened LESS often than the price said (overpriced)
     gap > 0  ->  it happened MORE often than the price said (underpriced)
  Favourite-longshot bias = negative gap for long shots AND positive gap for favourites.
"""

import csv
import math
import random
import sys
from datetime import datetime

SNAPSHOT_FILE = "data/clean/snapshots.csv"
NUM_BUCKETS = 10
HORIZONS = ["7d", "1d", "1h"]
CATEGORIES = ["politics", "sports"]
MIN_PER_GROUP = 30                 # groups smaller than this are flagged as unreliable
COSTS_CENTS = [0, 1, 2, 4]         # assumed trading costs per share

# Long shot / favourite cut-offs. "primary" is the main test; "strict" the check.
THRESHOLDS = {"primary": (0.30, 0.70), "strict": (0.10, 0.90)}

# The politics-vs-sports comparison only uses markets that closed on/after this
# date, because that is the year both categories cover.
COMPARISON_START = datetime.fromisoformat("2025-10-01T00:00:00+00:00").timestamp()


# ----------------------------------------------------------------------------
# LOADING DATA
# ----------------------------------------------------------------------------
def load_rows():
    rows = []
    with open(SNAPSHOT_FILE) as f:
        for r in csv.DictReader(f):
            rows.append({
                "event_id": r["event_id"], "category": r["category"],
                "horizon": r["horizon"], "price": float(r["price"]),
                "won": int(r["won"]), "closed_time": float(r["closed_time"]),
            })
    return rows


def fake_rows():
    """Invent snapshots with a built-in bias so you can test this script."""
    random.seed(1)
    rows = []
    for k in range(1500):
        true_prob = random.random()
        price = min(0.97, max(0.03, 0.5 + (true_prob - 0.5) * 0.8))
        rows.append({
            "event_id": str(k // 3),                      # 3 markets share an event
            "category": random.choice(CATEGORIES),
            "horizon": random.choice(HORIZONS),
            "price": price,
            "won": 1 if random.random() < true_prob else 0,
            "closed_time": random.choice([1.7e9, 1.77e9]),  # one old, one recent period
        })
    return rows


# ----------------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------------
def mean(values):
    return sum(values) / len(values)


def mean_and_error(values, clusters):
    """Average of 'values', plus a 95% margin of error.

    Markets from the same event move together, so they are NOT independent
    pieces of evidence. We handle that by adding up each event's deviations
    first (a 'cluster-robust' standard error). Plain-English version: the
    margin of error is wider when many results come from just a few events."""
    n = len(values)
    avg = mean(values)
    totals = {}
    for v, c in zip(values, clusters):
        totals[c] = totals.get(c, 0.0) + (v - avg)
    se = math.sqrt(sum(t * t for t in totals.values())) / n
    return avg, 1.96 * se


def calibration_table(rows, title):
    """Print the price-vs-reality table, one line per 10% price bucket."""
    print(f"\n=== {title}  ({len(rows)} snapshots) ===")
    if not rows:
        print("  (no data)")
        return
    buckets = [[] for _ in range(NUM_BUCKETS)]
    for r in rows:
        buckets[min(int(r["price"] * NUM_BUCKETS), NUM_BUCKETS - 1)].append(r)
    print(f"{'bucket':>10} {'n':>6} {'avg price':>10} {'actual':>8} {'gap':>8}")
    for i, g in enumerate(buckets):
        if not g:
            continue
        avg_p = mean([r["price"] for r in g])
        actual = mean([r["won"] for r in g])
        label = f"{i/NUM_BUCKETS:.0%}-{(i+1)/NUM_BUCKETS:.0%}"
        flag = "   <- fewer than 30, ignore" if len(g) < MIN_PER_GROUP else ""
        print(f"{label:>10} {len(g):>6} {avg_p:>10.3f} {actual:>8.3f} {actual-avg_p:>+8.3f}{flag}")
    brier = mean([(r["price"] - r["won"]) ** 2 for r in rows])
    print(f"  Brier score: {brier:.4f}   (always guessing 50% = 0.2500; lower is better)")


def group_summary(rows):
    """Return (n, avg price, actual rate, gap), or None if no rows."""
    if not rows:
        return None
    avg_p = mean([r["price"] for r in rows])
    actual = mean([r["won"] for r in rows])
    return len(rows), avg_p, actual, actual - avg_p


def summary_table(rows, title):
    """Long shots and favourites, at both thresholds, for each horizon."""
    print(f"\n=== {title} ===")
    print(f"{'horizon':>8} {'group':>22} {'n':>6} {'avg price':>10} {'actual':>8} {'gap':>8} {'+/- margin':>11}")
    for horizon in HORIZONS:
        subset = [r for r in rows if r["horizon"] == horizon]
        for label, (low, high) in THRESHOLDS.items():
            for group_name, group in (
                (f"long shots <{low:.2f}", [r for r in subset if r["price"] < low]),
                (f"favourites >{high:.2f}", [r for r in subset if r["price"] > high]),
            ):
                s = group_summary(group)
                if s is None:
                    print(f"{horizon:>8} {group_name:>22}      0  (no data)")
                    continue
                n, avg_p, actual, gap = s
                # 95% margin of error on the gap. Markets from the same event
                # are counted together (see mean_and_error), so it is not too optimistic.
                _, margin = mean_and_error([r["won"] - r["price"] for r in group],
                                           [r["event_id"] for r in group])
                if n < MIN_PER_GROUP:
                    flag = "  <- fewer than 30, too few to test"
                elif abs(gap) < margin:
                    flag = "  <- gap smaller than margin: could be luck"
                else:
                    flag = "  <- gap larger than margin"
                print(f"{horizon:>8} {group_name:>22} {n:>6} {avg_p:>10.3f} {actual:>8.3f} {gap:>+8.3f} {margin:>11.3f}{flag}")


def cost_test(rows, title):
    """Would these bets have made money after costs?

    Bet A: BET AGAINST long shots (buy the opposite side).  Profit per share = price - won - cost
    Bet B: BACK favourites.                                  Profit per share = won - price - cost
    Profits are in CENTS per share. 'cost' is an assumption (spread + fees)."""
    print(f"\n=== {title} ===")
    print("(primary thresholds: long shot < 0.30, favourite > 0.70; profit in cents per share, +/- 95% margin)")
    for horizon in HORIZONS:
        subset = [r for r in rows if r["horizon"] == horizon]
        for name, group, sign in (
            ("bet against long shots", [r for r in subset if r["price"] < 0.30], +1),
            ("back favourites", [r for r in subset if r["price"] > 0.70], -1),
        ):
            if len(group) < MIN_PER_GROUP:
                print(f"{horizon:>4} {name:>24}: only {len(group)} snapshots, too few")
                continue
            parts = []
            for cost in COSTS_CENTS:
                # sign=+1: price - won ; sign=-1: won - price   (then subtract the cost)
                profits = [100 * sign * (r["price"] - r["won"]) - cost for r in group]
                avg, margin = mean_and_error(profits, [r["event_id"] for r in group])
                parts.append(f"{cost}c cost: {avg:+.1f} (+/-{margin:.1f})")
            print(f"{horizon:>4} {name:>24}: " + " | ".join(parts))


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
rows = fake_rows() if "--fake" in sys.argv else load_rows()

# 1. Price-vs-reality tables, all categories together
for horizon in HORIZONS:
    calibration_table([r for r in rows if r["horizon"] == horizon], f"All markets, {horizon} before decided")

# 2. Long shots and favourites, per category (each category's own sample period)
for category in CATEGORIES:
    summary_table([r for r in rows if r["category"] == category],
                  f"{category.upper()} (full sample period): long shots and favourites")

# 3. Politics vs sports on the SAME year only (fair comparison)
recent = [r for r in rows if r["closed_time"] >= COMPARISON_START]
for category in CATEGORIES:
    summary_table([r for r in recent if r["category"] == category],
                  f"{category.upper()} (comparison year only, from 2025-10-01)")

# 4. Cost test
for category in CATEGORIES:
    cost_test([r for r in rows if r["category"] == category],
              f"COST TEST, {category.upper()} (full sample period)")

print("\nREMINDER: a gap can be luck. Never claim a bias from one group. Look for the")
print("same pattern across horizons, check the group sizes, and compare the gap with the")
print("margin of error. Costs are ASSUMED: the price history does not show the spread.")