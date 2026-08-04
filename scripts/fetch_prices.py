"""
Pulls every card in a Pokemon TCG set from the free pokemontcg.io API,
works out a single "market price" per card, and returns the card list
sorted by price.

No API key is required for light use, but pokemontcg.io gives higher
rate limits with a free key (https://pokemontcg.io -> "Get an API Key").
If you have one, set POKEMONTCG_API_KEY as a repo secret / env var and
it'll be picked up automatically.
"""
import os
import time
import requests

API_BASE = "https://api.pokemontcg.io/v2"


def _headers():
    key = os.environ.get("POKEMONTCG_API_KEY")
    return {"X-Api-Key": key} if key else {}


def get_all_sets():
    """Return all sets, newest first."""
    resp = requests.get(
        f"{API_BASE}/sets",
        params={"orderBy": "-releaseDate", "pageSize": 250},
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def card_market_price(card):
    """Best-guess 'market' price for a card: the highest market price
    across all printings/variants (holofoil, reverse holo, etc.)."""
    tcgplayer = card.get("tcgplayer") or {}
    prices = tcgplayer.get("prices") or {}
    market_values = [
        v.get("market") for v in prices.values() if v.get("market") is not None
    ]
    if not market_values:
        return None
    return max(market_values)


def get_cards_for_set(set_id):
    """Fetch every card in a set (paginated), each annotated with
    a `market_price` field. Cards with no price data are dropped."""
    cards = []
    page = 1
    while True:
        resp = requests.get(
            f"{API_BASE}/cards",
            params={"q": f"set.id:{set_id}", "page": page, "pageSize": 250},
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        cards.extend(payload["data"])
        if page * payload["pageSize"] >= payload["totalCount"]:
            break
        page += 1
        time.sleep(0.3)  # be polite to the free API

    priced = []
    for c in cards:
        price = card_market_price(c)
        if price is not None:
            c["market_price"] = price
            priced.append(c)
    return priced


def top_n_by_price(set_id, n=10, most_expensive=True):
    cards = get_cards_for_set(set_id)
    cards.sort(key=lambda c: c["market_price"], reverse=most_expensive)
    return cards[:n]


if __name__ == "__main__":
    # Quick manual test: python fetch_prices.py sv3pt5
    import sys
    import json

    set_id = sys.argv[1] if len(sys.argv) > 1 else "sv3pt5"
    top = top_n_by_price(set_id, n=10, most_expensive=True)
    for i, c in enumerate(top, 1):
        print(f"{i}. {c['name']} (#{c['number']}) - ${c['market_price']:.2f}")
