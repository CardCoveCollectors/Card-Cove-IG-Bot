"""
Orchestrator. Run as two steps (see .github/workflows/post.yml):

  python main.py build     -> fetches prices, renders the image + caption,
                               writes them under posts/, and picks the next
                               (set, list_type) from the rotation.
                               (git commit + push happens in the workflow,
                               so the image is live at a public URL.)

  python main.py publish   -> reads posts/latest.json (written by `build`),
                               builds the raw.githubusercontent.com URL for
                               the image that was just pushed, and publishes
                               it to Instagram.

Splitting it this way is required because Instagram's API needs the image
to already be reachable at a public URL before you ask it to fetch it.
"""
import argparse
import json
import os
import sys
import time

from config import FEATURED_SETS, LIST_LENGTH, BRAND_NAME, BRAND_HANDLE
from rotation import next_post
from fetch_prices import top_n_by_price, get_all_sets
from build_image import build_list_image
from caption import build_caption

ROOT = os.path.join(os.path.dirname(__file__), "..")
POSTS_DIR = os.path.join(ROOT, "posts")
LATEST_META = os.path.join(POSTS_DIR, "latest.json")


def _set_info(set_id):
    for s in get_all_sets():
        if s["id"] == set_id:
            return s["name"], (s.get("images") or {}).get("logo")
    return set_id, None


def cmd_build(args):
    # Very new/obscure sets sometimes have zero TCGPlayer pricing data yet
    # on pokemontcg.io — skip forward through the rotation instead of
    # crashing on an empty card list.
    cards = []
    for attempt in range(len(FEATURED_SETS) * 2 + 2):
        set_id, list_type = next_post(FEATURED_SETS)
        set_name, set_logo_url = _set_info(set_id)
        most_expensive = list_type == "most_expensive"
        cards = top_n_by_price(set_id, n=LIST_LENGTH, most_expensive=most_expensive)
        if cards:
            break
        print(f"WARNING: 0 priced cards for {set_id} ({list_type}) — skipping to next", file=sys.stderr)
    else:
        raise RuntimeError("No featured set had any priced cards — check FEATURED_SETS in config.py")

    if len(cards) < LIST_LENGTH:
        print(f"WARNING: only found {len(cards)} priced cards for {set_id}", file=sys.stderr)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{set_id}-{list_type}-{timestamp}.png"
    rel_path = os.path.join("posts", filename)
    abs_path = os.path.join(ROOT, rel_path)

    build_list_image(
        cards, list_type, set_name, abs_path,
        brand_name=f"@{BRAND_HANDLE}" if BRAND_HANDLE else BRAND_NAME,
        n=LIST_LENGTH,
        set_logo_url=set_logo_url,
    )
    caption = build_caption(cards, list_type, set_name, brand_handle=BRAND_HANDLE, n=LIST_LENGTH)

    os.makedirs(POSTS_DIR, exist_ok=True)
    with open(LATEST_META, "w", encoding="utf-8") as f:
        json.dump({"image_rel_path": rel_path.replace(os.sep, "/"), "caption": caption,
                   "set_id": set_id, "list_type": list_type}, f, indent=2)

    print(f"Built post for {set_name} ({list_type}) -> {rel_path}")


def cmd_publish(args):
    with open(LATEST_META, "r", encoding="utf-8") as f:
        meta = json.load(f)

    repo = os.environ["GITHUB_REPOSITORY"]  # e.g. "marc/tcg-instagram-bot"
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    image_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{meta['image_rel_path']}"

    print(f"Publishing {image_url}")
    from publish_instagram import post_image
    media_id = post_image(image_url, meta["caption"])
    print(f"Published. Media ID: {media_id}")


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
