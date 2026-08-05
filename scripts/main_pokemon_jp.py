"""
Orchestrator for the Japanese Pokemon TCG pipeline — mirrors main_pokemon.py
in shape, kept as its own file so it can be tuned without risk of breaking
the English pipeline. Posts to the same @cardcovecollectors Instagram
account, just on its own day (see .github/workflows/post_pokemon_jp.yml).

  python main_pokemon_jp.py build     -> picks the next set from the JP
                                          rotation, fetches prices, and
                                          renders BOTH Top-10 lists (most
                                          expensive + cheapest Art Rares)
                                          for that set as a pair.

  python main_pokemon_jp.py publish   -> reads posts/latest_pokemon_jp.json
                                          and publishes both images to
                                          Instagram back-to-back.

Uses its own state file (state_pokemon_jp.json) and meta file
(posts/latest_pokemon_jp.json) so this never collides with the English
Pokemon pipeline's state_pokemon.json / posts/latest_pokemon.json.
"""
import argparse
import json
import os
import sys
import time

import requests

from config_pokemon_jp import LIST_LENGTH, BRAND_NAME, BRAND_HANDLE, CHEAPEST_RARITIES, STATE_FILE
from rotation import next_set
from fetch_prices_pokemon_jp import top_n_by_price, get_jp_sets, get_all_featured_set_codes
from build_image_pokemon import build_list_image
from caption_pokemon_jp import build_caption

ROOT = os.path.join(os.path.dirname(__file__), "..")
POSTS_DIR = os.path.join(ROOT, "posts")
LATEST_META = os.path.join(POSTS_DIR, "latest_pokemon_jp.json")
STATE_PATH = os.path.join(ROOT, STATE_FILE)


def _set_name(set_code):
    for s in get_jp_sets():
        if (s.get("set_code") or "").lower() == set_code.lower():
            return s["name"]
    return set_code


def _safe_top_n(set_code, list_type):
    """Wraps top_n_by_price so a transient API hiccup is treated the same
    as "this set has no priced cards" — skip forward instead of crashing
    the whole run."""
    try:
        rarities = CHEAPEST_RARITIES if list_type == "least_expensive" else None
        top, expected_count, priced_count = top_n_by_price(
            set_code, n=LIST_LENGTH, most_expensive=(list_type == "most_expensive"), rarities=rarities
        )
        return top
    except requests.exceptions.RequestException as e:
        print(f"WARNING: fetch failed for {set_code} ({list_type}) — {e} — skipping to next", file=sys.stderr)
        return []


def cmd_build(args):
    # Pulled fresh every run — spans PokeWallet's ENTIRE JP catalog
    # (450+ sets back to 2004), not a curated shortlist, per Marc's call
    # that the rotation shouldn't stop after a small modern-only set.
    featured_sets = get_all_featured_set_codes()

    posts_meta = []
    set_code = set_name = None
    # Capped at 50 consecutive skips (not len(featured_sets)+1) as a
    # safety valve: some genuinely obscure 20-year-old promo sets may have
    # no TCGPlayer JP pricing at all, and each skip costs at least one API
    # call — an unbounded skip loop over 450+ sets could burn through the
    # free tier's hourly rate limit in one run. The rotation position
    # itself still advances every attempt, so a run that hits this cap
    # just tries again next time from where it left off.
    max_attempts = min(len(featured_sets) + 1, 50)
    for attempt in range(max_attempts):
        set_code = next_set(featured_sets, state_path=STATE_PATH)
        set_name = _set_name(set_code)
        posts_meta = []
        ok = True
        for list_type in ("most_expensive", "least_expensive"):
            cards = _safe_top_n(set_code, list_type)
            if not cards:
                if ok:
                    print(f"WARNING: 0 priced cards for {set_code} ({list_type}) — skipping whole set", file=sys.stderr)
                ok = False
                break

            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"pokejp-{set_code}-{list_type}-{timestamp}.png"
            rel_path = os.path.join("posts", filename)
            abs_path = os.path.join(ROOT, rel_path)

            build_list_image(
                cards, list_type, set_name, abs_path,
                brand_name=f"@{BRAND_HANDLE}" if BRAND_HANDLE else BRAND_NAME,
                n=LIST_LENGTH,
                data_source="TCGplayer (Japan)",
                cheapest_label="ARS",
            )
            caption = build_caption(cards, list_type, set_name, brand_handle=BRAND_HANDLE, n=LIST_LENGTH)
            posts_meta.append({
                "image_rel_path": rel_path.replace(os.sep, "/"),
                "caption": caption,
                "set_id": set_code,
                "list_type": list_type,
            })
        if ok:
            break
    else:
        raise RuntimeError(f"No priced set found in {max_attempts} consecutive attempts — PokeWallet may be having issues, or an unusually long run of unpriced sets was hit. Safe to just retry.")

    os.makedirs(POSTS_DIR, exist_ok=True)
    with open(LATEST_META, "w", encoding="utf-8") as f:
        json.dump(posts_meta, f, indent=2)

    types = " + ".join(p["list_type"] for p in posts_meta)
    print(f"Built {len(posts_meta)} post(s) for {set_name} ({types}) -> posts/")


def cmd_publish(args):
    with open(LATEST_META, "r", encoding="utf-8") as f:
        posts_meta = json.load(f)

    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    from publish_instagram import post_image

    for i, meta in enumerate(posts_meta):
        image_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{meta['image_rel_path']}"
        print(f"Publishing ({meta['list_type']}): {image_url}")
        media_id = post_image(image_url, meta["caption"])
        print(f"Published. Media ID: {media_id}")
        if i < len(posts_meta) - 1:
            time.sleep(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    sub.add_parser("publish")
    args = parser.parse_args()

    if args.command == "build":
        cmd_build(args)
    elif args.command == "publish":
        cmd_publish(args)
