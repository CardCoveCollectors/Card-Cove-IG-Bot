"""
One-off batch preview: renders the new grid poster for every set Card
Cove Collectors tracks — the 16 mainline OP-01 through OP-16 releases,
plus every Extra Booster (EB) and Premium Booster (PRB) that's come out
— both list types each, so you can see how the whole run of sets will
look before it's live. This does NOT touch the normal rotation state
(state_onepiece.json) or publish anything — it's purely a visual check,
meant to be run manually and its output downloaded as a GitHub Actions
artifact.

    python preview_all_onepiece.py

Note: OP-14 and OP-15 were never released as their own standalone
booster on optcgapi.com — they shipped bundled with an Extra Booster as
"OP14-EB04" and "OP15-EB04". Those combined-set codes are used here in
their place so all 16 numbered mainline releases are covered.

This list is just SET_LIST grouped for readability (mainline, then EB,
then PRB) — it covers the exact same 21 sets as FEATURED_SETS in
config_onepiece.py, just not in rotation order. If a new EB/PRB or a
future OP-17+ set gets added to FEATURED_SETS, add it here too.
"""
import os
import sys
import time

import requests

from config_onepiece import LIST_LENGTH, BRAND_NAME, BRAND_HANDLE, ALT_ART_MARKERS, FEATURED_SETS
from fetch_prices_onepiece import get_cards_for_set, get_all_sets, is_alt_art
from build_image_onepiece import build_list_image

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(ROOT, "preview_all_onepiece")

# OP-01 through OP-16 (mainline, using the combined codes for OP-14/15),
# then every Extra Booster, then every Premium Booster.
SET_LIST = [
    "OP-01", "OP-02", "OP-03", "OP-04", "OP-05", "OP-06", "OP-07",
    "OP-08", "OP-09", "OP-10", "OP-11", "OP-12", "OP-13",
    "OP14-EB04", "OP15-EB04", "OP-16",
    "EB-01", "EB-02", "EB-03",
    "PRB-01", "PRB-02",
]

# Safety net: if FEATURED_SETS ever gets a set added that isn't reflected
# in the hand-written list above (e.g. a new EB/PRB or OP-17), catch it
# here instead of silently leaving it out of the preview.
_missing = set(FEATURED_SETS) - set(SET_LIST)
if _missing:
    print(f"NOTE: {_missing} are in FEATURED_SETS but not in this preview's SET_LIST — add them above.", file=sys.stderr)


def _set_name(set_id, all_sets):
    for s in all_sets:
        if s["set_id"] == set_id:
            return s["set_name"]
    return set_id


def _safe_get_cards(set_id):
    """Fetch a set's cards ONCE — both the most-expensive and cheapest
    lists are derived from this same in-memory list below, instead of
    hitting the API a second time for the same data. Halves the request
    count for this batch script (21 calls instead of 42), which is
    gentler on optcgapi.com's single VPS."""
    try:
        return get_cards_for_set(set_id)
    except requests.exceptions.RequestException as e:
        print(f"WARNING: fetch failed for {set_id} — {e} — skipping", file=sys.stderr)
        return []


def _rank(cards, list_type, n=LIST_LENGTH):
    """Mirrors fetch_prices_onepiece.top_n_by_price's sort/filter logic,
    but operates on an already-fetched card list instead of re-fetching."""
    most_expensive = list_type == "most_expensive"
    pool = cards
    if list_type == "least_expensive":
        filtered = [c for c in cards if is_alt_art(c, ALT_ART_MARKERS)]
        if filtered:
            pool = filtered
    pool = sorted(pool, key=lambda c: c["market_price"], reverse=most_expensive)
    return pool[:n]


def _get_all_sets_with_retry(attempts=3, wait_seconds=30):
    """get_all_sets() already retries transient errors internally, but
    optcgapi.com is a single hobbyist VPS that occasionally has longer
    outages than that budget covers. Give it a few more, longer-spaced
    tries here, and fail with a clear message instead of a raw traceback
    if it's genuinely down."""
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return get_all_sets()
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"WARNING: optcgapi.com unreachable (attempt {attempt}/{attempts}) — {e}", file=sys.stderr)
            if attempt < attempts:
                time.sleep(wait_seconds)
    print(
        "\nERROR: Couldn't reach optcgapi.com after several tries. "
        "This is almost always a temporary outage on their end (it's a "
        "hobbyist-run API), not a problem with this pipeline. Just "
        "re-run this workflow in a few minutes.",
        file=sys.stderr,
    )
    sys.exit(1)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    all_sets = _get_all_sets_with_retry()

    built = 0
    for set_id in SET_LIST:
        set_name = _set_name(set_id, all_sets)
        raw_cards = _safe_get_cards(set_id)

        for list_type in ("most_expensive", "least_expensive"):
            cards = _rank(raw_cards, list_type) if raw_cards else []
            if not cards:
                print(f"WARNING: 0 priced cards for {set_id} ({list_type}) — skipping", file=sys.stderr)
                continue

            filename = f"{set_id}-{list_type}.png"
            out_path = os.path.join(OUT_DIR, filename)
            build_list_image(
                cards, list_type, set_name, out_path,
                brand_name=f"@{BRAND_HANDLE}" if BRAND_HANDLE else BRAND_NAME,
                n=LIST_LENGTH, set_id=set_id,
            )
            print(f"Built {filename}")
            built += 1

        time.sleep(2)  # be gentle with optcgapi.com — one pause per set, not per image

    print(f"\nDone — {built} images written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
