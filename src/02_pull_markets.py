"""
02_pull_markets.py  --  Downloads the list of finished (closed)
Polymarket markets for each category and saves the raw replies.

WHAT THIS DOES (in plain English)
---------------------------------
Polymarket's API gives us a list of markets, 100 at a time. 
Every market carries "tags" (labels such as Politics or Sports),
and each tag has an ID number: Politics = 2, Sports = 1.

We ask for ONE category at a time, so we always know which category a market
belongs to (the "category" field inside each market is empty).

HOW THE PAGING WORKS
--------------------
From Claude: The simple "give me page 21" method stops working after about 2,000 markets
("offset too large"). The deeper method is "keyset" paging: every reply comes
with a bookmark (called a cursor). We hand the bookmark back to say "carry on
from where you stopped". We keep going until a reply has no bookmark.

Each reply is saved exactly as received (just the list of markets), in its own
file. Later scripts read those files. We never edit them.

We do NOT filter by date here: Polymarket's date filter works on a market's
"deadline", which is often a placeholder. We filter by the real closing time
later, in 03_select_sample.py.

The script can be stopped and restarted. It remembers its bookmark in a small
file called _next_cursor.txt inside each category folder.

HOW TO RUN
    python3 src/02_pull_markets.py
"""

import json
import os
import time
import requests

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
BASE_URL = "https://gamma-api.polymarket.com/markets/keyset"   # confirmed in Polymarket's docs
PAGE_SIZE = 100          # markets per request (100 is the maximum allowed)
MAX_PAGES = 3000         # safety limit per category (3000 pages = up to 300,000 markets)
PAUSE_SECONDS = 0.5      # wait between requests so we don't annoy the server
MIN_VOLUME = 10000       # only markets with at least $10,000 traded (server-side filter)

# One entry per category.  name -> tag ID from Polymarket's tag list.
CATEGORIES = {
    "sports": 1,
    "politics": 2,
}

RAW_FOLDER = "data/raw/markets"


MAX_RETRIES = 6          # how many times to retry a failed request
RETRY_WAIT_SECONDS = 5   # wait 5s, then 10s, then 15s, ... between retries


def count_saved_pages(folder):
    return len([f for f in os.listdir(folder) if f.startswith("keyset_") and f.endswith(".json")])


def get_with_retries(params):
    """Ask the server, and if it is only temporarily broken, wait and try again.

    Servers sometimes hiccup ("502 Bad Gateway", timeouts, "slow down"). These
    are NOT our fault and usually clear up within seconds, so we retry instead
    of giving up. A real error (like 422) is returned straight away."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(BASE_URL, params=params, timeout=60)
        except requests.RequestException as error:
            print(f"   network problem ({error}); attempt {attempt} of {MAX_RETRIES}")
        else:
            if response.status_code not in (429, 500, 502, 503, 504):
                return response               # success, or a real error to report
            print(f"   server busy (status {response.status_code}); attempt {attempt} of {MAX_RETRIES}")
        time.sleep(RETRY_WAIT_SECONDS * attempt)
    return None                               # gave up


# ----------------------------------------------------------------------------
# MAIN LOOP
# ----------------------------------------------------------------------------
for name, tag_id in CATEGORIES.items():
    folder = os.path.join(RAW_FOLDER, name)
    os.makedirs(folder, exist_ok=True)
    cursor_file = os.path.join(folder, "_next_cursor.txt")
    print(f"=== {name} (tag {tag_id}) ===")

    # Pick up where we left off, if we were stopped part-way.
    cursor = None
    page = count_saved_pages(folder)
    if os.path.exists(cursor_file):
        saved = open(cursor_file).read().strip()
        if saved == "DONE":
            print(f"{name} is already finished ({page} pages saved). Skipping.")
            continue
        cursor = saved or None
    elif page > 0:
        print(f"Found {page} saved pages but no bookmark. Delete the folder {folder} and run again.")
        continue

    while page < MAX_PAGES:
        params = {
            "closed": "true",                 # finished markets only
            "tag_id": tag_id,                 # this category only
            "volume_num_min": MIN_VOLUME,
            "limit": PAGE_SIZE,
        }
        if cursor:
            params["after_cursor"] = cursor   # "carry on from where you stopped"

        response = get_with_retries(params)

        if response is None:
            print(f"Gave up on {name} page {page} after {MAX_RETRIES} tries.")
            print("Your progress is saved. Run the script again later to carry on.")
            break
        if response.status_code != 200:
            print(f"Problem on {name} page {page}: status {response.status_code}")
            print(response.text[:500])
            break

        data = response.json()                # {"markets": [...], "next_cursor": "..."}
        markets = data.get("markets", [])
        cursor = data.get("next_cursor")      # missing on the last page

        if markets:
            filename = os.path.join(folder, f"keyset_{page:05d}.json")
            with open(filename, "w") as f:
                json.dump(markets, f)
            page += 1
            print(f"Saved {name} page {page}: {len(markets)} markets")

        # Remember the bookmark, or mark the category as finished.
        with open(cursor_file, "w") as f:
            f.write(cursor if (cursor and markets) else "DONE")
        if not cursor or not markets:
            print(f"Finished {name}: {page} pages saved.")
            break
        time.sleep(PAUSE_SECONDS)

print("Finished pulling markets.")