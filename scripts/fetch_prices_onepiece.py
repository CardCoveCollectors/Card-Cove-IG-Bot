"""
Pulls every printing of every card in a One Piece TCG set from the free
optcgapi.com API (no key required — it's a hobbyist-run, community API,
same spirit as pokemontcg.io but for One Piece) and returns cards sorted
by price.

Unlike Pokemon's pokemontcg.io, each printing/variant (normal, Parallel,
Alternate Art, Box Topper, etc.) comes back as its OWN row in the card
list rather than nested under one card — and importantly, those special
prints keep the SAME rarity code as their normal counterpart (e.g. both
show "SR"). So "cheapest Alt Art" is scoped by checking each card's name
for one of config_onepiece.ALT_ART_MARKERS, not by rarity.
"""
import time
import requests
from requests.adapters import HTTPAdapter, Retry

API_BASE = "https://optcgapi.com/api"

# This runs on one person's VPS out of pocket, so retry gently on
# transient failures rather than hammering it, same courtesy pattern
# used for pokemontcg.io.
_session = requests.Session()
_retries = Retry(
    total=5,
    backoff_factor=2,  # 2s, 4s, 8s, 16s, 32s
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
_session.mount("https://", HTTPAdapter(max_retries=_retries))


def get_all_sets():
    """Return all sets known to optcgapi.com, as [{"set_name", "set_id"}, ...]."""
    resp = _session.get(f"{API_BASE}/allSets/", timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_cards_for_set(set_id):
    """Fetch every printing of every card in a set. Entries with no
    market_price yet are dropped."""
    resp = _session.get(f"{API_BASE}/sets/{set_id}/", timeout=30)
    resp.raise_for_status()
    cards = resp.json()
    return [c for c in cards if c.get("market_price") is not None]


def is_alt_art(card, markers):
    name = card.get("card_name") or ""
    return any(marker.lower() in name.lower() for marker in markers)


def top_n_by_price(set_id, n=10, most_expensive=True, alt_art_markers=None):
    """`alt_art_markers`, if given, restricts the pool to cards whose name
    contains one of those marker strings before ranking — e.g. so a
    "cheapest" list can be scoped to Alt Art / special prints instead of
    literal common-card bulk. Falls back to the full pool if the filter
    would leave nothing to show."""
    cards = get_cards_for_set(set_id)
    if alt_art_markers:
        filtered = [c for c in cards if is_alt_art(c, alt_art_markers)]
        if filtered:
            cards = filtered
    cards.sort(key=lambda c: c["market_price"], reverse=most_expensive)
    return cards[:n]


if __name__ == "__main__":
    # Quick manual test: python fetch_prices_onepiece.py OP-01
    import sys

    set_id = sys.argv[1] if len(sys.argv) > 1 else "OP-01"
    top = top_n_by_price(set_id, n=10, most_expensive=True)
    for i, c in enumerate(top, 1):
        print(f"{i}. {c['card_name']} ({c['card_set_id']}) - ${c['market_price']:.2f}")
