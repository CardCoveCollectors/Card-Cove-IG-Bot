"""
Pulls Japanese Pokemon TCG pricing from the free PokeWallet API
(api.pokewallet.io) — the same platform/key as BerryWallet (One Piece).
Unlike pokemontcg.io (English-only, no Japanese data at all), PokeWallet
indexes Japanese sets directly with real TCGPlayer USD pricing and a real
`rarity` field (unlike the One Piece side, which had none) — so this
script mirrors fetch_prices_pokemon.py almost exactly, just pointed at a
different API.

One thing that DOES differ from English: Japanese rarity naming uses
"Art Rare" (AR) and "Special Art Rare" (SAR) where English uses
"Illustration Rare" (IR) and "Special Illustration Rare" (SIR) — see
config_pokemon_jp.py's CHEAPEST_RARITIES.

Requires the POKEWALLET_API_KEY env var (same key used for
fetch_prices_onepiece_jp.py).
"""
import os

import requests
from requests.adapters import HTTPAdapter, Retry

API_BASE = "https://api.pokewallet.io"

_session = requests.Session()
_retries = Retry(
    total=5,
    backoff_factor=2,  # 2s, 4s, 8s, 16s, 32s
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
_session.mount("https://", HTTPAdapter(max_retries=_retries))


def _headers():
    return {"X-API-Key": os.environ["POKEWALLET_API_KEY"]}


def get_all_sets():
    """Return every set PokeWallet knows about (Pokemon, all languages)."""
    resp = _session.get(f"{API_BASE}/sets", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]


def get_jp_sets():
    """Return only the Japanese-language sets."""
    return [s for s in get_all_sets() if s.get("language") == "jap"]


def card_market_price(card):
    """Best-guess 'market' price for a card: the highest market price
    across all TCGPlayer printings/variants (Normal, Holofoil, etc.),
    same selection rule as the English pipeline's card_market_price()."""
    tcgplayer = card.get("tcgplayer") or {}
    prices = tcgplayer.get("prices") or []
    market_values = [p.get("market_price") for p in prices if p.get("market_price") is not None]
    if not market_values:
        return None
    return max(market_values)


def get_cards_for_set(set_id, max_pages=10, page_size=200):
    """Fetch every card in a set (paginated by set_id, the numeric
    identifier from /sets — avoids the set_code disambiguation issue for
    codes shared across languages). Normalized into the same shape
    build_image_pokemon.py expects: name, number, rarity, market_price,
    images. Cards with no TCGPlayer price are dropped. Returns
    (cards, raw_total) so callers can tell "nothing priced" apart from
    "set is genuinely empty / wrong ID".

    NOTE: `images` is always empty here — PokeWallet's /images/:id
    endpoint requires the API key as an auth header, but
    build_image_pokemon.py's downloader makes a plain unauthenticated
    request, so real card art isn't wired up yet (same known limitation
    we hit on the One Piece JP side). Posts render with placeholder card
    art until/unless we add authenticated image fetching."""
    cards = []
    page = 1
    while page <= max_pages:
        resp = _session.get(
            f"{API_BASE}/sets/{set_id}",
            params={"page": page, "limit": page_size},
            headers=_headers(), timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        batch = payload.get("cards", [])
        cards.extend(batch)
        if len(batch) < page_size:
            break
        page += 1

    raw_total = len(cards)
    priced = []
    for c in cards:
        price = card_market_price(c)
        if price is None:
            continue
        info = c.get("card_info") or {}
        priced.append({
            "name": info.get("name") or info.get("clean_name") or "Unknown",
            "number": info.get("card_number", ""),
            "rarity": info.get("rarity") or "",
            "market_price": price,
            "images": {},
        })
    return priced, raw_total


def top_n_by_price(set_id, n=10, most_expensive=True, rarities=None):
    """`rarities`, if given, restricts the pool to cards whose `rarity`
    field is in that list before ranking — e.g. so a "cheapest" list can
    be scoped to Art Rare / Special Art Rare instead of literal bulk
    commons. Falls back to the full pool if the filter would leave
    nothing to show."""
    cards, raw_total = get_cards_for_set(set_id)
    if rarities:
        filtered = [c for c in cards if c.get("rarity") in rarities]
        if filtered:
            cards = filtered
    cards.sort(key=lambda c: c["market_price"], reverse=most_expensive)
    return cards[:n], raw_total, len(cards)


if __name__ == "__main__":
    # Quick manual test: python fetch_prices_pokemon_jp.py 23599
    import sys

    set_id = sys.argv[1] if len(sys.argv) > 1 else "23599"
    top, raw_total, priced_count = top_n_by_price(set_id, n=10, most_expensive=True)
    print(f"[diagnostic] set_id={set_id}: {raw_total} total card entries fetched, {priced_count} with a TCGPlayer price")
    for i, c in enumerate(top, 1):
        print(f"{i}. {c['name']} (#{c['number']} {c['rarity']}) - ${c['market_price']:.2f}")
