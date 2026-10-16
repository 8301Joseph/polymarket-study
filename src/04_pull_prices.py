"""
04_pull_prices.py  --  NEEDS WIFI.  Downloads the price history for every
market in data/clean/sample.csv.

WHAT THIS DOES (in plain English)
---------------------------------
For each chosen market we ask Polymarket's price-history service: "what was the
price of this market's first outcome over time?" The reply is a list of points,
each with a time (t) and a price (p). We save each reply exactly as received to
data/raw/prices/<token id>.json.

Facts confirmed in Polymarket's docs:
  - address:  https://clob.polymarket.com/prices-history
  - settings: market (the token id), interval, fidelity (minutes between points)
  - reply:    {"history": [{"t": ..., "p": ...}, ...]}

NOT confirmed: how finely old, closed markets are stored. If a reply comes back
EMPTY at one fidelity, we retry with coarser ones. The log file records what
happened for each market, so we can see how many had to be coarser.

The script can be stopped and restarted: finished markets are skipped.

HOW TO RUN
    python src/04_pull_prices.py
"""

import csv
import json
import os
import time
import requests

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
PRICE_URL = "https://clob.polymarket.com/prices-history"   # confirmed in the docs
SAMPLE_FILE = "data/clean/sample.csv"
OUTPUT_FOLDER = "data/raw/prices"
LOG_FILE = "data/raw/prices_log.csv"
PAUSE_SECONDS = 0.3

# Try these in order. 60 = one price per hour. If that returns nothing, try
# every 4 hours, then every day.
FIDELITIES = [60, 240, 1440]

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

with open(SAMPLE_FILE) as f:
    sample = list(csv.DictReader(f))

log_rows = []
done = 0

for i, row in enumerate(sample, start=1):
    token = row["token_id"]
    outfile = os.path.join(OUTPUT_FOLDER, f"{token}.json")
    if os.path.exists(outfile):              # already downloaded: skip
        continue

    result = None
    used = None
    for fidelity in FIDELITIES:
        params = {"market": token, "interval": "max", "fidelity": fidelity}
        try:
            resp = requests.get(PRICE_URL, params=params, timeout=30)
        except requests.RequestException as error:
            print(f"[{i}] network problem for {token[:10]}...: {error}")
            break
        if resp.status_code == 429:          # "slow down" -- wait and try again
            time.sleep(5)
            continue
        if resp.status_code != 200:
            print(f"[{i}] status {resp.status_code} for {token[:10]}...")
            break
        data = resp.json()
        if data.get("history"):              # got real points: stop trying
            result = data
            used = fidelity
            break
        time.sleep(PAUSE_SECONDS)

    if result is None:
        log_rows.append({"market_id": row["market_id"], "token_id": token,
                         "result": "FAILED_OR_EMPTY", "fidelity": ""})
        print(f"[{i}/{len(sample)}] no price history for market {row['market_id']}")
    else:
        with open(outfile, "w") as f:
            json.dump(result, f)
        log_rows.append({"market_id": row["market_id"], "token_id": token,
                         "result": "ok", "fidelity": used})
        done += 1
        if done % 25 == 0:
            print(f"[{i}/{len(sample)}] saved {done} price histories so far")
    time.sleep(PAUSE_SECONDS)

# Append to the log (so restarts keep the history).
new_file = not os.path.exists(LOG_FILE)
with open(LOG_FILE, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["market_id", "token_id", "result", "fidelity"])
    if new_file:
        writer.writeheader()
    writer.writerows(log_rows)

print(f"Done. Downloaded {done} new price histories. Log: {LOG_FILE}")
