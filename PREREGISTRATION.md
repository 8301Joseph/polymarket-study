# Pre-registration: Polymarket calibration study

## Question
Are Polymarket prices well calibrated, and are long shots overpriced?
In other words: if a market says an event has a 20% chance, does it happen about 20% of the time?

## Markets and sample periods
Resolved Polymarket markets in two categories, politics and sports. I chose the categories before looking at any data, and they will not change after I see results.

| Category | Polymarket tag | Sample period (by the market's closing time) |
| --- | --- | --- |
| Sports | Sports (tag 1) | 1 Oct 2023 to 30 Sep 2026 |
| Politics | Politics (tag 2) | 1 Oct 2025 to 30 Sep 2026 |

- A market's category is Polymarket's own tag. Markets carrying both tags are dropped.
- Sample size: up to 1,500 markets per category, picked at random with seed 42 from all eligible markets.
- Eligible: exactly two outcomes, a clear winner (no 50/50 or cancelled markets), and total volume of at least $10,000.
- The extra sports years give more data for the sports-only results. The politics-versus-sports comparison uses only markets that closed on or after 1 Oct 2025, because that is the year both cover and it avoids mixing in a time effect.
- Polymarket introduced trading fees in 2026 (sports on 18 Feb, most other categories on 30 Mar), so the most recent months are priced differently from earlier ones.

## The priced side
For every market I record the price of the first-listed outcome (for Yes/No markets, "Yes") and whether that outcome won.

## When a snapshot is taken
Polymarket's date fields are not reliable as "the end" of a market. The deadline can be a placeholder, and the official closing time can be weeks after the event. So:

- **Decided time:** the last moment the price was still between 0.02 and 0.98.
- **Snapshot:** the last recorded price at or before (decided time minus 7 days), (minus 1 day) and (minus 1 hour).
- Only prices at or before the snapshot time are ever recorded as the price (no look-ahead).

## Snapshots that are skipped
- Price at or below 0.01, or at or above 0.99
- No price exists that early, or the latest price is more than 48 hours old
- The market's price is never between 0.02 and 0.98

I will report how many snapshots were skipped for each reason, and split by whether the market's first outcome won. If the skips are lopsided, I will say so, because it could bias the results.

## Definitions
| Term | Definition |
| --- | --- |
| Horizon | 7 days, 1 day or 1 hour before the decided time |
| Price bucket | Ten buckets of 10 percentage points: 0-10%, 10-20%, and so on |
| Long shot | Price below 0.30 (primary test); below 0.10 (stricter check) |
| Favourite | Price above 0.70 (primary test); above 0.90 (stricter check) |
| Gap | Actual win rate minus average price, within a group |
| Brier score | Average of (price - outcome)^2; lower is better, and always guessing 50% scores 0.25 |

## Method
1. Download all finished markets in each category and keep the eligible ones.
2. Pick the random sample and download price histories.
3. Build the snapshots at the three horizons.
4. Group snapshots into 10% price buckets and compare the average price with the share that won.
5. Check long shots and favourites at both the primary and the stricter thresholds.
6. Compare politics with sports using only the shared year.
7. Test whether trading on any bias would be profitable after costs.

## What would count as a result
- **Bias exists:** long-shot groups have win rates clearly below their prices, AND favourite groups have win rates above their prices, consistently across all three horizons.
- **No bias:** gaps are small and their sign is inconsistent.
- I will not claim a bias from any group with fewer than 30 snapshots.

## Costs
I will test two bets: betting against long shots (buying the opposite side) and backing favourites. For each, I will report the average profit per share, with a 95% margin of error that treats markets from the same event as one cluster, at assumed trading costs of 0, 1, 2 and 4 cents per share. A bet counts as profitable only if its average profit is positive and larger than its margin of error. These costs are assumptions: the price history does not show the buy-sell spread.

## What I will NOT do
- Add or remove categories after seeing results
- Change the sample periods, sample size, seed, thresholds, horizons or exclusions after seeing results
- Keep testing variations until one shows a bias
- Edit the text above after I have looked at any results. Any later change goes in a new dated section.

## Revision note
The first draft used each market's "endDate" as the end of the market and Polymarket's "category" field to label markets. Looking at the real data format, I found that "endDate" is often a placeholder (for example 31 Dec for markets that finished months earlier) and that "category" is empty. I therefore switched to tags for categories and to the decided-time rule above. If the snapshots had used the deadline, markets that resolved early would have been dropped as "already decided" at short horizons, which could have created a false favourite-longshot pattern. The earlier plan of one shared two-year window for both categories was also replaced by the periods above. No results had been looked at when this revision was made.
