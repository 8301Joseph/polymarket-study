"""
02_pull_markets.py  --  NEEDS WIFI.  Downloads the list of finished (closed)
Polymarket markets for each category and saves the raw replies.

WHAT THIS DOES (in plain English)
---------------------------------
Polymarket's website-for-computers (the "API") can hand us a list of markets.
Every market on Polymarket carries "tags" (labels such as Politics or Sports).
Each tag has an ID number. The IDs below were looked up in Polymarket's own
tag list:  Politics = 2,  Sports = 1.

We ask for ONE category at a time, so we always know which category a market
belongs to (the "category" field inside each market turned out to be empty).
We save every reply exactly as received, in its own file. Later scripts read
those files. We never edit them.

Note: we do NOT filter by date here. Polymarket's date filter works on a
market's "deadline" date, which is often a placeholder (for example 31 Dec for
markets that actually finished months earlier). We filter by the real closing
time later, in 03_select_sample.py.

The script can be stopped and restarted: pages already saved are skipped.

HOW TO RUN
    pip install -r requirements.txt
    python src/02_pull_markets.py
"""

import json
import os
import time
import requests

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
BASE_URL = "https://gamma-api.polymarket.com/markets"   # confirmed in Polymarket's docs
PAGE_SIZE = 100          # markets per request
MAX_PAGES = 400          # safety limit per category (400 pages = up to 40,000 markets)
PAUSE_SECONDS = 0.5      # wait between requests so we don't annoy the server
MIN_VOLUME = 10000       # only markets with at least $10,000 traded (server-side filter)

# One entry per category.  name -> tag ID from Polymarket's tag list.
CATEGORIES = {
    "sports": 1,
    "politics": 2,
}

RAW_FOLDER = "data/raw/markets"

# ----------------------------------------------------------------------------
# MAIN LOOP
# ----------------------------------------------------------------------------
for name, tag_id in CATEGORIES.items():
    folder = os.path.join(RAW_FOLDER, name)
    os.makedirs(folder, exist_ok=True)
    print(f"=== {name} (tag {tag_id}) ===")

    for page in range(MAX_PAGES):
        filename = os.path.join(folder, f"page_{page:04d}.json")
        if os.path.exists(filename):          # already downloaded: skip
            continue

        params = {
            "closed": "true",                 # finished markets only
            "tag_id": tag_id,                 # this category only
            "volume_num_min": MIN_VOLUME,
            "limit": PAGE_SIZE,
            "offset": page * PAGE_SIZE,       # which page: 0, 100, 200, ...
        }
        response = requests.get(BASE_URL, params=params, timeout=30)

        if response.status_code != 200:
            print(f"Problem on page {page}: status {response.status_code}")
            print(response.text[:500])
            break

        data = response.json()                # a Python list of markets
        if len(data) == 0:                    # empty page = we reached the end
            print(f"No more {name} markets after page {page - 1}.")
            break

        with open(filename, "w") as f:
            json.dump(data, f)
        print(f"Saved {name} page {page}: {len(data)} markets")
        time.sleep(PAUSE_SECONDS)

print("Finished pulling markets.")
