# Polymarket Calibration Project

**Questions:** Are Polymarket prices well calibrated? Do long shots and favourites show the favourite-longshot bias? Does any bias survive trading costs?

If a prediction market says an event has a 20% chance, does it happen about 20% of the time? This project checks that on resolved Polymarket markets in two categories, politics and sports, at 7 days, 1 day and 1 hour before each market was decided. It then asks whether any bias is large enough to trade on after costs.

**Status:** analysis complete; write-up in progress. The design was pre-registered in [PREREGISTRATION.md](PREREGISTRATION.md) before any results were viewed.

## Main results
- **Prices were well calibrated.** Only 3 of the 28 price buckets with at least 30 snapshots have gaps larger than their 95% margin of error, which is about what chance alone would produce. Brier scores are 0.158 (7 days), 0.151 (1 day) and 0.153 (1 hour), against 0.250 for always guessing 50%.
- **No favourite-longshot bias** under the pre-registered definition, in either category or at any horizon.
- **One clear deviation:** politics at 7 days, where long shots (gap +0.036 ± 0.030) and favourites (+0.052 ± 0.043) both won more often than their prices implied. It is gone by 1 day.
- **No profitable strategy after costs.** Backing politics favourites at 7 days earned +5.2 ± 4.3 cents per share with no trading cost, the only case to pass the pre-registered rule, and it fails once a cost of 1 cent per share is assumed.

Full tables and figures are in [`results/`](results/).

## Data and sample
- Source: Polymarket's public APIs (Gamma API for market lists, CLOB API for price histories).
- Categories by Polymarket tag: Sports (tag 1) and Politics (tag 2).
- Sports markets closed 1 Oct 2023 to 30 Sep 2026; politics markets closed 1 Oct 2025 to 30 Sep 2026, a window chosen to exclude markets tied to the 2024 US election.
- Eligible markets have exactly two outcomes, a clear winner and at least $10,000 of trading volume. 1,500 per category are sampled at random (seed 42).
- Only the first-listed outcome of each market is analysed ("Yes" in Yes/No markets).
- 5,231 snapshots in total.

## Method in brief
1. Download resolved markets, apply the eligibility rules and draw the random sample.
2. Estimate each market's **decided time** from its price history: the last price between 0.02 and 0.98. (Polymarket's `endDate` is often a placeholder and `closedTime` can lag the event by weeks.)
3. Record the last price at or before 7 days, 1 day and 1 hour before the decided time, plus the outcome.
4. Group prices into ten 10% buckets and compare the average price with how often the outcome happened (gap = actual win rate minus average price). Also compute the Brier score.
5. Check long shots (price below 0.30; strict check below 0.10) and favourites (above 0.70; strict check above 0.90). Groups with fewer than 30 snapshots are not tested.
6. 95% margins of error treat markets from the same event as one cluster. A gap counts as clear only if it is larger than its margin.
7. Test whether betting against long shots or backing favourites makes money after assumed costs of 0, 1, 2 and 4 cents per share.

## Project layout
```
src/
  01_toy_calibration.py   Offline demo on fake data with a planted bias
  02_pull_markets.py      Download resolved markets by tag (needs internet)
  03_select_sample.py     Apply the eligibility rules and draw the random sample
  04_pull_prices.py       Download price histories for the sample (needs internet)
  05_build_snapshots.py   Estimate decided times and build data/clean/snapshots.csv
  06_analyze.py           Print the calibration, long-shot/favourite and cost-test tables
  07_check_sample.py      Health check: counts and skip-rule effects (no results)
  08_make_results.py      Write the results tables (CSV) and figures (PNG)
results/
  analysis_output.txt     Full printed output of 06_analyze.py
  table_*.csv             Results tables
  figure_*.png            Results figures
data/
  raw/                    Untouched API responses (not committed)
  clean/                  Tables built from raw (not committed)
PREREGISTRATION.md        The design, written before looking at results
```

## How to run
```
pip install -r requirements.txt
python src/01_toy_calibration.py     # works offline, good for understanding the idea
python src/02_pull_markets.py
python src/03_select_sample.py
python src/04_pull_prices.py
python src/05_build_snapshots.py
python src/07_check_sample.py        # optional health check
python src/06_analyze.py             # add --fake to test it on fake data
python src/08_make_results.py        # add --fake to test it on fake data
```

The data files are not committed, so running the scripts in order rebuilds them. The web addresses and field names in the pull scripts may need updating if Polymarket's API has changed.

## Related work
My AFL match forecasting model, which applies the same kind of calibration checks to betting markets.

## Limitations
Only resolved markets are included. Markets from the same event are not independent, so the effective sample is smaller than the market count. Only the first-listed outcome is analysed, and the politics sample covers one year. The 7-day snapshots cover fewer, and different, markets. Trading costs are assumed rather than measured, and Polymarket introduced fees part-way through the sample period. See the pre-registration for details.
