"""
Orchestrator. Run as two steps (see .github/workflows/post_pokemon.yml):

  python main_pokemon.py build     -> picks the next set from the rotation,
                                       fetches prices, and renders BOTH
                                       Top-10 lists (most expensive +
                                       cheapest) for that one set as a
                                       pair, writing them under posts/.
                                       (git commit + push happens in the
                                       workflow, so the images are live
                                       at public URLs.)

  python main_pokemon.py publish   -> reads posts/latest_pokemon.json
                                       (written by `build`, a list of the
                                       pair's two posts), builds the
                                       raw.githubusercontent.com URL for
                                       each image that was just pushed,
                                       and publishes both to Instagram
                                       back-to-back.

Splitting it this way is required because Instagram's API needs each image
to already be reachable at a public URL before you ask it to fetch it.

Uses its own state file (state_pokemon.json) and meta file
(posts/latest_pokemon.json) so this never collides with the One Piece
pipeline's own state_onepiece.json / posts/latest_onepiece.json.
"""
import argparse
import json
import os
import sys
import time

import requests

from config_pokemon import FEATURED_SETS, LIST_LENGTH, BRAND_NAME, BRAND_HANDLE, CHEAPEST_RARITIES, STATE_FILE
from rotation import next_set
from fetch_prices_pokemon import top_n_by_price, get_all_sets
from build_image_pokemon import build_list_image
from caption_pokemon import build_caption

ROOT = os.path.join(os.path.dirname(__file__), "..")
POSTS_DIR = os.path.join(ROOT, "posts")
LATEST_META = os.path.join(POSTS_DIR, "latest_pokemon.json")
STATE_PATH = os.path.join(ROOT, STATE_FILE)


def _set_info(set_id):
    for s in get_all_sets():
        if s["id"] == set_id:
            return s["name"], (s.get("images") or {}).get("logo")
    return set_id, None


def _safe_top_n(set_id, list_type):
    """Wraps top_n_by_price so a transient pokemontcg.io outage (500s that
    outlast our retry budget) is treated the same as "this set has no
    priced cards" — skip forward instead of crashing the whole run."""
    try:
        rarities = CHEAPEST_RARITIES if list_type == "least_expensive" else None
        return top_n_by_price(set_id, n=LIST_LENGTH, most_expensive=(list_type == "most_expensive"), rarities=rarities)
    except requests.exceptions.RequestException as e:
        print(f"WARNING: fetch failed for {set_id} ({list_type}) — {e} — skipping to next", file=sys.stderr)
        return []


def cmd_build(args):
    # Each posting day covers ONE set with BOTH its Top-10 lists (most
    # expensive + cheapest) built and posted together as a pair. Very
    # new/obscure sets sometimes have zero TCGPlayer pricing data yet on
    # pokemontcg.io (or the API has a bad moment) — skip the whole set
    # forward through the rotation instead of crashing.
    posts_meta = []
    set_id = set_name = None
    for attempt in range(len(FEATURED_SETS) + 1):
        set_id = next_set(FEATURED_SETS, state_path=STATE_PATH)
        set_name, set_logo_url = _set_info(set_id)
        posts_meta = []
        ok = True
        for list_type in ("most_expensive", "least_expensive"):
            cards = _safe_top_n(set_id, list_type)
            if not cards:
                if ok:  # only print the "0 priced cards" flavor once per set
                    print(f"WARNING: 0 priced cards for {set_id} ({list_type}) — skipping whole set", file=sys.stderr)
                ok = False
                break

            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"poke-{set_id}-{list_type}-{timestamp}.png"
            rel_path = os.path.join("posts", filename)
            abs_path = os.path.join(ROOT, rel_path)

            build_list_image(
                cards, list_type, set_name, abs_path,
                brand_name=f"@{BRAND_HANDLE}" if BRAND_HANDLE else BRAND_NAME,
                n=LIST_LENGTH,
                set_logo_url=set_logo_url,
            )
            caption = build_caption(cards, list_type, set_name, brand_handle=BRAND_HANDLE, n=LIST_LENGTH)
            posts_meta.append({
                "image_rel_path": rel_path.replace(os.sep, "/"),
                "caption": caption,
                "set_id": set_id,
                "list_type": list_type,
            })
        if ok:
            break
    else:
        raise RuntimeError("No featured set had priced cards for both lists — check FEATURED_SETS in config_pokemon.py")

    os.makedirs(POSTS_DIR, exist_ok=True)
    with open(LATEST_META, "w", encoding="utf-8") as f:
        json.dump(posts_meta, f, indent=2)

    types = " + ".join(p["list_type"] for p in posts_meta)
    print(f"Built {len(posts_meta)} post(s) for {set_name} ({types}) -> posts/")


def cmd_publish(args):
    with open(LATEST_META, "r", encoding="utf-8") as f:
        posts_meta = json.load(f)

    repo = os.environ["GITHUB_REPOSITORY"]  # e.g. "marc/tcg-instagram-bot"
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    from publish_instagram import post_image

    for i, meta in enumerate(posts_meta):
        image_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{meta['image_rel_path']}"
        print(f"Publishing ({meta['list_type']}): {image_url}")
        media_id = post_image(image_url, meta["caption"])
        print(f"Published. Media ID: {media_id}")
        if i < len(posts_meta) - 1:
            time.sleep(30)  # brief gap between the pair's two posts


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
