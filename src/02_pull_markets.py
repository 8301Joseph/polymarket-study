"""
02_pull_markets.py  --  NEEDS WIFI.  Downloads a list of finished (resolved)
Polymarket markets and saves the raw answers to data/raw/markets/.

WHAT THIS DOES (in plain English)
---------------------------------
Polymarket has a public website-for-computers (an "API") where you can ask
"give me 100 closed markets" and it replies with a block of text in a format
called JSON. We ask over and over (page 1, page 2, ...) and save each reply as
its own file, untouched. We never edit these files. Later scripts read them.

IMPORTANT: I wrote the web address and the setting names below FROM MEMORY.
They may have changed. Everything you might need to fix is in the CONFIG block
right below. When you have wifi, check Polymarket's developer docs and fix
anything marked TODO. If you get an error, paste it to Claude.

HOW TO RUN (from the project folder, with wifi)
    pip install requests
    python src/02_pull_markets.py
"""

import json       # for saving the replies
import os         # for making folders
import time       # for pausing between requests
import requests   # for talking to the website  (install with: pip install requests)

# ----------------------------------------------------------------------------
# CONFIG  -- the only part you should need to edit
# ----------------------------------------------------------------------------
BASE_URL = "https://gamma-api.polymarket.com/markets"   # TODO: check this is still right
PAGE_SIZE = 100          # how many markets per request
MAX_PAGES = 5            # START SMALL. 5 pages = ~500 markets. Raise later.
PAUSE_SECONDS = 1.0      # wait between requests so we don't annoy the server
OUTPUT_FOLDER = "data/raw/markets"

# The "question" we ask the server. TODO: check these setting names in the docs.
BASE_PARAMS = {
    "closed": "true",    # only finished markets
    "limit": PAGE_SIZE,
}

# ----------------------------------------------------------------------------
# MAIN LOOP
# ----------------------------------------------------------------------------
os.makedirs(OUTPUT_FOLDER, exist_ok=True)   # make the folder if it isn't there

for page in range(MAX_PAGES):
    params = dict(BASE_PARAMS)               # copy the settings...
    params["offset"] = page * PAGE_SIZE      # ...and say which page we want (0, 100, 200, ...)

    response = requests.get(BASE_URL, params=params, timeout=30)

    # If the server says something went wrong, stop and show the problem.
    if response.status_code != 200:
        print(f"Problem on page {page}: status {response.status_code}")
        print(response.text[:500])           # show the first 500 characters of the error
        break

    data = response.json()                   # turn the reply into a Python list

    if len(data) == 0:                       # an empty page means we've reached the end
        print("No more markets. Done.")
        break

    # Save the reply exactly as received.
    filename = os.path.join(OUTPUT_FOLDER, f"page_{page:04d}.json")
    with open(filename, "w") as f:
        json.dump(data, f)

    print(f"Saved page {page}: {len(data)} markets -> {filename}")
    time.sleep(PAUSE_SECONDS)                # be polite

print("Finished pulling markets.")
