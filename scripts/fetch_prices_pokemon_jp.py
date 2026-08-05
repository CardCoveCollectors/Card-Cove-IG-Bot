"""
Pulls Japanese Pokemon TCG pricing from the free PokeWallet API
(api.pokewallet.io) — the same platform/key as BerryWallet (One Piece).
Unlike pokemontcg.io (English-only, no Japanese data at all), PokeWallet
indexes Japanese sets directly with real TCGPlayer USD pricing and a real
`rarity` field (unlike the One Piece side, which had none).

IMPORTANT quirk this script works around: PokeWallet's free tier returns
real card *metadata* from `/sets/:setCode` but with EMPTY price arrays —
bulk pricing per set is a paid-plan feature there. The one endpoint that
DOES return populated prices on the free tier is `/search`, but it's a
loose text search (querying a set code can return cards from unrelated
sets too), so results are filtered down to cards whose `card_info.set_id`
exactly matches the set we asked for.

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


def _resolve_jp_set(set_code):
    """Look up a JP set's exact numeric set_id + card_count from its
    set_code, so /search results (a loose text match) can be filtered
    down to precisely this set and we know when we've seen them all."""
    matches = [s for s in get_jp_sets() if (s.get("set_code") or "").lower() == set_code.lower()]
    if not matches:
        raise ValueError(f"No Japanese set found with set_code={set_code!r}")
    return matches[0]


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


def get_cards_for_set(set_code, max_pages=20, page_size=100):
    """Fetch every priced card in a JP set via /search (the only endpoint
    that returns POPULATED bulk pricing on the free tier). Normalized
    into the same shape build_image_pokemon.py expects: name, number,
    rarity, market_price, images. Cards with no TCGPlayer price are
    dropped. Returns (cards, expected_card_count) so callers can tell
    "nothing priced" apart from "search never found this set".

    NOTE: `images` is always empty here — PokeWallet's /images/:id
    endpoint requires the API key as an auth header, but
    build_image_pokemon.py's downloader makes a plain unauthenticated
    request, so real card art isn't wired up yet (same known limitation
    we hit on the One Piece JP side). Posts render with placeholder card
    art until/unless we add authenticated image fetching."""
    set_info = _resolve_jp_set(set_code)
    target_set_id = set_info["set_id"]
    expected_count = set_info.get("card_count", 0)

    cards = []
    seen_ids = set()
    page = 1
    while page <= max_pages:
        resp = _session.get(
            f"{API_BASE}/search",
            params={"q": set_code, "page": page, "limit": page_size},
            headers=_headers(), timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        batch = payload.get("results", [])
        if not batch:
            break

        for c in batch:
            info = c.get("card_info") or {}
            if info.get("set_id") != target_set_id:
                continue
            cid = c.get("id")
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            cards.append(c)

        # NOTE: deliberately NOT stopping early once len(cards) reaches the
        # set's nominal card_count — that count only reflects base numbered
        # slots, while high-value chase variants (Special Art Rare, etc.)
        # get their own card_number (e.g. "201/165" in a "165"-card set) and
        # can sort later in /search's relevance ordering. Stopping early on
        # count caused the priciest cards to get cut off before we ever saw
        # them. Page through everything instead.
        total_pages = (payload.get("pagination") or {}).get("total_pages", page)
        if page >= total_pages:
            break
        page += 1

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
    return priced, expected_count


def top_n_by_price(set_code, n=10, most_expensive=True, rarities=None):
    """`rarities`, if given, restricts the pool to cards whose `rarity`
    field is in that list before ranking — e.g. so a "cheapest" list can
    be scoped to Art Rare / Special Art Rare instead of literal bulk
    commons. Falls back to the full pool if the filter would leave
    nothing to show."""
    cards, expected_count = get_cards_for_set(set_code)
    if rarities:
        filtered = [c for c in cards if c.get("rarity") in rarities]
        if filtered:
            cards = filtered
    cards.sort(key=lambda c: c["market_price"], reverse=most_expensive)
    return cards[:n], expected_count, len(cards)


if __name__ == "__main__":
    # Quick manual test: python fetch_prices_pokemon_jp.py SV2a
    import sys

    set_code = sys.argv[1] if len(sys.argv) > 1 else "SV2a"
    top, expected_count, priced_count = top_n_by_price(set_code, n=10, most_expensive=True)
    print(f"[diagnostic] set_code={set_code}: set has {expected_count} cards, {priced_count} matched with a TCGPlayer price")
    for i, c in enumerate(top, 1):
        print(f"{i}. {c['name']} (#{c['number']} {c['rarity']}) - ${c['market_price']:.2f}")
