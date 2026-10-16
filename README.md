# Polymarket Calibration Project

**Question:** Are Polymarket prices well calibrated, and are long shots overpriced?

If a prediction market says an event has a 20% chance, does it happen about 20% of the time? This project checks that on finished Polymarket markets in two categories, politics/elections and sports, and then asks whether any bias is large enough to trade on after costs.

**Status:** work in progress. Pre-registered design is in [PREREGISTRATION.md](PREREGISTRATION.md). Results are not in yet.

## Method in brief
1. Download finished (resolved) markets and their price histories.
2. Record the price 7 days, 1 day and 1 hour before each market closed, and the outcome.
3. Group into 10% price buckets and compare average price with how often the event happened.
4. Check whether long shots (price below 0.30) are overpriced and favourites (above 0.70) underpriced.
5. Test whether the bias survives trading costs of 0 to 4 cents per share.

## Project layout
```
src/
  01_toy_calibration.py   Offline demo on fake data with a planted bias
  02_pull_markets.py      Download resolved markets (needs internet)
  03_pull_prices.py       Download price histories (needs internet)
  04_build_snapshots.py   Build data/clean/snapshots.csv
  05_analyze.py           Print the price-vs-reality tables
data/
  raw/                    Untouched API responses (not committed)
  clean/                  Tables built from raw (not committed)
PREREGISTRATION.md        The design, written before looking at data
```

## How to run
```
pip install -r requirements.txt
python src/01_toy_calibration.py     # works offline, good for understanding the idea
python src/02_pull_markets.py
python src/03_pull_prices.py
python src/04_build_snapshots.py
python src/05_analyze.py             # add --fake to test it on fake data
```

The data files are not committed, so running the scripts in order rebuilds them. The web addresses and field names in the pull scripts may need updating if Polymarket's API has changed; those lines are marked `TODO`.

## Related work
My AFL match forecasting model, which applies the same kind of calibration checks to betting markets.

## Limitations
Only resolved markets are included; related markets are not independent; thin markets are noisy; trading costs are assumed rather than measured. See the pre-registration for details.