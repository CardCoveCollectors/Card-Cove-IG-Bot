"""
Pulls Japanese One Piece TCG pricing from the free BerryWallet API
(api.pokewallet.io) — the same platform ("PokeWallet") that also covers
Pokemon TCG under one shared API key. Unlike optcgapi.com (English-only),
every Japanese OPCG set is indexed here as a "CardMarket-only" set
(negative group_id), sourced from CardMarket + TCGPlayer listings of
Japanese singles rather than Bandai's own card database — so these
records don't carry gameplay metadata like rarity, card_type, or color.
Only name, card code (parsed out of the name), variant, and price.

Requires the POKEWALLET_API_KEY env var (same key will cover Pokemon
TCG's future JP pipeline too).
"""
import os
import re

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

# Matches the set+number code embedded in the name field, e.g.
# "Alvida (OP01-064) (V.1)" -> "OP01-064", "Kouzuki Oden (EB01-001)" -> "EB01-001"
_CODE_RE = re.compile(r"\(([A-Za-z]+\d*-\d+)\)")
# Matches a trailing variant tag like "(V.1)" / "(V.2)"
_VARIANT_RE = re.compile(r"\((V\.\d+)\)\s*$")


def _headers():
    return {"X-API-Key": os.environ["POKEWALLET_API_KEY"]}


def get_jp_sets():
    """Return every Japanese One Piece set: [{"name", "set_code", "group_id", "release_date"}, ...]."""
    resp = _session.get(f"{API_BASE}/op/sets", params={"language": "jp"}, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]


def _parse_name(raw_name):
    """Split a raw JP card name into (display_name, code, variant).
    e.g. "Alvida (OP01-064) (V.1)" -> ("Alvida", "OP01-064", "V.1")
         "Arlong (OP01-063)"       -> ("Arlong", "OP01-063", None)
    """
    code_match = _CODE_RE.search(raw_name)
    code = code_match.group(1) if code_match else ""

    variant_match = _VARIANT_RE.search(raw_name)
    variant = variant_match.group(1) if variant_match else None

    display = raw_name[:code_match.start()].rstrip() if code_match else raw_name
    display = _VARIANT_RE.sub("", display).strip()
    return display, code, variant


def get_cards_for_set(group_id, max_pages=5, page_size=200):
    """Fetch every card in a JP set (paginated), normalized into the same
    shape build_image_onepiece.py expects: card_name, card_set_id, rarity
    (repurposed here to hold the V.1/V.2 variant tag, since JP data has no
    real rarity), market_price. Entries with no TCGPlayer price (like the
    "DON!!" filler card) are dropped."""
    cards = []
    page = 1
    while page <= max_pages:
        resp = _session.get(
            f"{API_BASE}/op/sets/{group_id}",
            params={"page": page, "limit": page_size},
            headers=_headers(), timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        batch = payload.get("data", [])
        cards.extend(batch)
        if page * page_size >= payload.get("total", 0):
            break
        page += 1

    out = []
    for c in cards:
        tcg = c.get("tcgplayer")
        if not tcg or tcg.get("prices", {}).get("market_price") is None:
            continue
        raw_name = c.get("name") or "Unknown"
        display_name, code, variant = _parse_name(raw_name)
        out.append({
            "card_name": display_name or raw_name,
            "card_set_id": code,
            "rarity": variant or "",
            "market_price": tcg["prices"]["market_price"],
        })
    return out


def top_n_by_price(group_id, n=10, most_expensive=True):
    cards = get_cards_for_set(group_id)
    cards.sort(key=lambda c: c["market_price"], reverse=most_expensive)
    return cards[:n]


if __name__ == "__main__":
    # Quick manual test: python fetch_prices_onepiece_jp.py -3
    import sys

    group_id = sys.argv[1] if len(sys.argv) > 1 else "-3"
    top = top_n_by_price(group_id, n=10, most_expensive=True)
    for i, c in enumerate(top, 1):
        tag = f" {c['rarity']}" if c["rarity"] else ""
        print(f"{i}. {c['card_name']} ({c['card_set_id']}{tag}) - ${c['market_price']:.2f}")
