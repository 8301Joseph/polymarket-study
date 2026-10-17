"""
01_toy_calibration.py 

WHAT THIS DOES 
---------------------------------
Invent 2,000 fake prediction markets where WE know the true chance of each
event. Then we make the "market price" a slightly wrong version of the truth
(it squashes everything toward 50%). That is the favorite-longshot bias.

Then we do exactly what we will later do on real Polymarket data:
  1. Sort markets into price buckets (0-10%, 10-20%, ...).
  2. In each bucket, compare the AVERAGE PRICE to how often the event ACTUALLY
     happened.
  3. If they match, the market is "calibrated". If not, there is a bias.

HOW TO RUN
----------
    python 01_toy_calibration.py        (or python3 on Mac/Linux)

THINGS TO TRY (change a number, predict what happens, THEN run it)
------------------------------------------------------------------
  - Set DISTORTION = 1.0   -> no bias. Do the gaps shrink to roughly zero?
  - Set DISTORTION = 0.5   -> big bias. Do the gaps get bigger?
  - Set NUM_MARKETS = 50   -> few markets. Do the results get noisy? (Of course they will!)
"""

import random 
import math   

# ----------------------------------------------------------------------------
# SETTINGS 
# ----------------------------------------------------------------------------
NUM_MARKETS = 2000   # how many fake markets to create
DISTORTION = 0.8     # 1.0 = market is perfect. Lower = more favorite-longshot bias.
SEED = 17            # makes the random numbers repeatable (same result each run)

random.seed(SEED)

# ----------------------------------------------------------------------------
# STEP 1: make fake markets
# Each market is a small dictionary: the true chance, the market's price, and
# whether the event happened (1) or not (0).
# ----------------------------------------------------------------------------
markets = []
for _ in range(NUM_MARKETS):
    true_prob = random.random()                       # a random number between 0 and 1
    # The market price is the truth, pulled toward 50%. Example with
    # DISTORTION = 0.8: a true 10% becomes a market price of 18%.
    price = 0.5 + (true_prob - 0.5) * DISTORTION
    # The event happens with probability true_prob (like a weighted coin flip).
    happened = 1 if random.random() < true_prob else 0
    markets.append({"price": price, "outcome": happened})

# ----------------------------------------------------------------------------
# STEP 2: put markets into price buckets and compare price vs. reality
# ----------------------------------------------------------------------------
NUM_BUCKETS = 10    # buckets of width 0.1: 0-0.1, 0.1-0.2, ...

buckets = [[] for _ in range(NUM_BUCKETS)]   # a list of 10 empty lists
for m in markets:
    # int(price * 10) turns 0.37 into 3, meaning "bucket number 3" (30-40%)
    index = min(int(m["price"] * NUM_BUCKETS), NUM_BUCKETS - 1)
    buckets[index].append(m)

print(f"{'bucket':>10} {'markets':>8} {'avg price':>10} {'actual rate':>12} {'gap':>8}")
print("-" * 52)
for i, group in enumerate(buckets):
    if len(group) == 0:
        continue   # skip empty buckets (can happen with strong distortion)
    avg_price = sum(m["price"] for m in group) / len(group)
    actual_rate = sum(m["outcome"] for m in group) / len(group)
    gap = actual_rate - avg_price
    label = f"{i/NUM_BUCKETS:.0%}-{(i+1)/NUM_BUCKETS:.0%}"
    print(f"{label:>10} {len(group):>8} {avg_price:>10.3f} {actual_rate:>12.3f} {gap:>+8.3f}")

# ----------------------------------------------------------------------------
# STEP 3: one score for the whole market  (the "Brier score")
# For each market: (price - outcome) squared. Then average.
# Lower is better. Always guessing 50% scores 0.25.
# ----------------------------------------------------------------------------
brier = sum((m["price"] - m["outcome"]) ** 2 for m in markets) / len(markets)
print()
print(f"Brier score of the market prices: {brier:.4f}   (always guessing 50% = 0.2500)")

print()
print("HOW TO READ THE TABLE:")
print("  gap > 0 -> the event happened MORE often than the price said (underpriced)")
print("  gap < 0 -> the event happened LESS often than the price said (overpriced)")
print("  Favorite-longshot bias = negative gaps in LOW buckets, positive gaps in HIGH buckets.")
