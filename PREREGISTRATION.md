# Pre-registration: Polymarket calibration study

## Question
Are Polymarket prices well calibrated, and are long shots overpriced?
In other words: if a market says an event has a 20% chance, does it happen about 20% of the time?

## Markets
Resolved Polymarket markets in two categories: politics/elections and sports.
I chose these before looking at any data because both have many finished markets, and they behave differently, so I can compare them. The categories will not change after I see results.

If the data has no usable category field, I will label markets with keyword rules written down before I look at any results.

## Exclusions
- Markets with total volume under $10,000 (prices in thin markets are mostly noise)
- Markets that resolved 50/50 or were cancelled
- Snapshots where the price is 0.01 or lower, or 0.99 or higher (the market has effectively decided)
- Snapshots where no price exists at or before the horizon time

## What I will measure
- The price 7 days, 1 day and 1 hour before the market closed
- Whether the event happened (1) or not (0)
- Only prices at or before the snapshot time are ever used (no look-ahead)

## Definitions
- Long shot: price below 0.30 (primary test). Stricter check: below 0.10.
- Favourite: price above 0.70 (primary test). Stricter check: above 0.90.
- Gap: actual rate of the event happening, minus the average price, within a bucket.
- Brier score: average of (price - outcome)^2. Lower is better. Always guessing 50% scores 0.25.

## Method
1. Group snapshots into 10 price buckets of 10 percentage points each.
2. In each bucket, compare the average price with the share of events that happened.
3. Compute the Brier score for each horizon and each category.
4. Check long shots and favourites at both the primary and the stricter thresholds.
5. Compare politics with sports.

## What would count as a result
- "Bias exists": long-shot buckets have actual rates clearly below their prices, AND favourite buckets have actual rates above their prices, consistently across all three horizons.
- "No bias": gaps are small and their sign is inconsistent.
- I will not claim a bias from any single bucket, or from a bucket with fewer than 30 markets.

## Costs
I will test whether any bias survives trading costs of 0, 1, 2 and 4 cents per share, and report all four. These costs are assumptions: the price history does not show the buy-sell spread, and Polymarket only introduced trading fees in 2026. A strategy counts as profitable only if its average return is positive after costs.

## What I will NOT do
- Add or remove categories after seeing results
- Change the thresholds, horizons or exclusions after seeing results
- Keep testing variations until one shows a bias
- Edit this file after I have looked at any results. Any later change goes in a new dated section, not over the original text.