"""
03_pull_prices.py  --  NEEDS WIFI.  For each market we saved, download its
price history (what the price was at each moment) and save it.

WHAT THIS DOES (in plain English)
---------------------------------
Each market has a "YES" side and a "NO" side, and each side has a long ID
number called a "token ID". We only need the YES side's price history.
For every market in data/raw/markets/, we find that ID, ask the server for the
price history, and save the reply to data/raw/prices/<token id>.json.

IMPORTANT: web address, setting names, and the field names inside the market
data are FROM MEMORY. Check the TODO lines against the docs once you have wifi.
The script skips files it already downloaded, so you can stop and restart it.

HOW TO RUN
    python src/03_pull_prices.py
"""

import json
import os
import glob       # for listing all files in a folder
import time
import requests

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
PRICE_URL = "https://clob.polymarket.com/prices-history"   # TODO: check
MARKETS_FOLDER = "data/raw/markets"
OUTPUT_FOLDER = "data/raw/prices"
PAUSE_SECONDS = 0.5
MAX_MARKETS = 300        # START SMALL while testing
MIN_VOLUME = 10000       # skip markets with little trading (prices there are mostly noise)

# Setting names for the price request. TODO: check in the docs.
PRICE_PARAMS = {
    "interval": "max",   # ask for the whole history
    "fidelity": 60,      # one price per 60 minutes (TODO: check the unit)
}

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_yes_token_id(market):
    """Find the YES-side token ID inside one market's data.

    TODO: in the data I remember, 'clobTokenIds' is a piece of text that looks
    like a list, e.g. '["1234...", "5678..."]', and the first one is YES.
    Open one saved file in data/raw/markets/ and confirm this.
    """
    raw = market.get("clobTokenIds")
    if raw is None:
        return None
    if isinstance(raw, str):      # if it's text, turn it into a real list
        raw = json.loads(raw)
    if len(raw) == 0:
        return None
    return raw[0]                  # first entry = YES (TODO: verify with 'outcomes')


# ----------------------------------------------------------------------------
# MAIN LOOP
# ----------------------------------------------------------------------------
count = 0
for path in sorted(glob.glob(os.path.join(MARKETS_FOLDER, "*.json"))):
    with open(path) as f:
        markets = json.load(f)

    for market in markets:
        if count >= MAX_MARKETS:
            break

        # Skip thin markets. 'volume' may be text, so float() converts it. TODO: check field name.
        try:
            volume = float(market.get("volume", 0))
        except (TypeError, ValueError):
            volume = 0
        if volume < MIN_VOLUME:
            continue

        token = get_yes_token_id(market)
        if token is None:
            continue

        outfile = os.path.join(OUTPUT_FOLDER, f"{token}.json")
        if os.path.exists(outfile):       # already downloaded, skip
            continue

        params = dict(PRICE_PARAMS)
        params["market"] = token          # TODO: check the setting name
        resp = requests.get(PRICE_URL, params=params, timeout=30)

        if resp.status_code != 200:
            print(f"FAILED {token}: status {resp.status_code}")
            continue

        with open(outfile, "w") as f:
            json.dump(resp.json(), f)

        count += 1
        print(f"[{count}] saved {token[:12]}...")
        time.sleep(PAUSE_SECONDS)

print(f"Done. Downloaded {count} price histories.")
