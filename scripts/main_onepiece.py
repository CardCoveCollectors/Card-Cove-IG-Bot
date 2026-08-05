"""
Orchestrator for the One Piece TCG pipeline — mirrors main.py exactly in
shape, kept as its own file (per game) so either can be tuned without
risk of breaking the other. Both post to the same @cardcovecollectors
Instagram account, just on different days (see .github/workflows).

  python main_onepiece.py build     -> picks the next set from the One
                                        Piece rotation, fetches prices,
                                        and renders BOTH Top-10 lists
                                        (most expensive + cheapest Alt
                                        Art) for that set as a pair.

  python main_onepiece.py publish   -> reads posts/latest_onepiece.json
                                        and publishes both images to
                                        Instagram back-to-back.

Uses a separate state file (state_onepiece.json) and a separate meta
file (posts/latest_onepiece.json) so this never collides with the
Pokemon pipeline's own state.json / posts/latest.json.
"""
import argparse
import json
import os
import sys
import time

import requests

from config_onepiece import FEATURED_SETS, LIST_LENGTH, BRAND_NAME, BRAND_HANDLE, ALT_ART_MARKERS, STATE_FILE
from rotation import next_set
from fetch_prices_onepiece import top_n_by_price, get_all_sets
from build_image_onepiece import build_list_image
from caption_onepiece import build_caption

ROOT = os.path.join(os.path.dirname(__file__), "..")
POSTS_DIR = os.path.join(ROOT, "posts")
LATEST_META = os.path.join(POSTS_DIR, "latest_onepiece.json")
STATE_PATH = os.path.join(ROOT, STATE_FILE)


def _set_name(set_id):
    for s in get_all_sets():
        if s["set_id"] == set_id:
            return s["set_name"]
    return set_id


def _safe_top_n(set_id, list_type):
    """Wraps top_n_by_price so a transient optcgapi.com outage is treated
    the same as "this set has no priced cards" — skip forward instead of
    crashing the whole run."""
    try:
        markers = ALT_ART_MARKERS if list_type == "least_expensive" else None
        return top_n_by_price(set_id, n=LIST_LENGTH, most_expensive=(list_type == "most_expensive"), alt_art_markers=markers)
    except requests.exceptions.RequestException as e:
        print(f"WARNING: fetch failed for {set_id} ({list_type}) — {e} — skipping to next", file=sys.stderr)
        return []


def cmd_build(args):
    posts_meta = []
    set_id = set_name = None
    for attempt in range(len(FEATURED_SETS) + 1):
        set_id = next_set(FEATURED_SETS, state_path=STATE_PATH)
        set_name = _set_name(set_id)
        posts_meta = []
        ok = True
        for list_type in ("most_expensive", "least_expensive"):
            cards = _safe_top_n(set_id, list_type)
            if not cards:
                if ok:
                    print(f"WARNING: 0 priced cards for {set_id} ({list_type}) — skipping whole set", file=sys.stderr)
                ok = False
                break

            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"op-{set_id}-{list_type}-{timestamp}.png"
            rel_path = os.path.join("posts", filename)
            abs_path = os.path.join(ROOT, rel_path)

            build_list_image(
                cards, list_type, set_name, abs_path,
                brand_name=f"@{BRAND_HANDLE}" if BRAND_HANDLE else BRAND_NAME,
                n=LIST_LENGTH, set_id=set_id,
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
        raise RuntimeError("No featured set had priced cards for both lists — check FEATURED_SETS in config_onepiece.py")

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
