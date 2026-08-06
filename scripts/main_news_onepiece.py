"""
Orchestrator for the One Piece Card Game News pipeline. Run as two steps
(see .github/workflows/post_news_onepiece.yml):

  python main_news_onepiece.py build     -> checks the One Piece Card Game
                                             news feed for anything new +
                                             newsworthy that hasn't been
                                             posted before. If it finds
                                             something, renders the
                                             graphic + caption and writes
                                             posts/latest_news_onepiece.json.
                                             If NOT, it deletes any stale
                                             file left over from a previous
                                             run and exits cleanly (exit
                                             code 0) — a quiet news day is
                                             not a failure.

  python main_news_onepiece.py publish   -> reads
                                             posts/latest_news_onepiece.json
                                             (written by `build`), builds
                                             the raw.githubusercontent.com
                                             URL for the image that was
                                             just pushed, and publishes it
                                             to Instagram.

Uses its own state file (state_news_onepiece.json, a set of normalized
headlines already posted) and is fully independent of the Pokemon news
pipeline (main_news_pokemon.py / state_news_pokemon.json) so neither
franchise's coverage crowds out the other.
"""
import argparse
import json
import os
import re
import time

from config_news_onepiece import BRAND_HANDLE, STATE_FILE
from fetch_news_onepiece import fetch_candidates, dedup_key
from build_image_news import build_news_image
from caption_news import build_caption

ROOT = os.path.join(os.path.dirname(__file__), "..")
POSTS_DIR = os.path.join(ROOT, "posts")
LATEST_META = os.path.join(POSTS_DIR, "latest_news_onepiece.json")
STATE_PATH = os.path.join(ROOT, STATE_FILE)

MAX_HISTORY = 300


def _load_state():
    if not os.path.exists(STATE_PATH):
        return {"posted_keys": []}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _slugify(text, max_len=40):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].strip("-") or "news"


def cmd_build(args):
    if os.path.exists(LATEST_META):
        os.remove(LATEST_META)

    state = _load_state()
    posted_keys = set(state.get("posted_keys", []))

    candidates = fetch_candidates()
    fresh = [c for c in candidates if dedup_key(c) not in posted_keys]

    if not fresh:
        print(f"No new One Piece Card Game news found this run ({len(candidates)} candidate(s) seen, all already posted or none matched).")
        return

    item = fresh[0]
    print(f"Selected: {item['title']}")

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"news-onepiece-{_slugify(item['title'])}-{timestamp}.png"
    rel_path = os.path.join("posts", filename)
    abs_path = os.path.join(ROOT, rel_path)

    build_news_image(item, abs_path, brand_name=f"@{BRAND_HANDLE}")
    caption = build_caption(item, brand_handle=BRAND_HANDLE)

    os.makedirs(POSTS_DIR, exist_ok=True)
    with open(LATEST_META, "w", encoding="utf-8") as f:
        json.dump({
            "image_rel_path": rel_path.replace(os.sep, "/"),
            "caption": caption,
            "topic": item["topic"],
            "title": item["title"],
        }, f, indent=2)

    key = dedup_key(item)
    posted_keys.add(key)
    state["posted_keys"] = list(posted_keys)[-MAX_HISTORY:]
    _save_state(state)

    print(f"Built news post for '{item['title']}' -> {rel_path}")


def cmd_publish(args):
    if not os.path.exists(LATEST_META):
        print("No post to publish (build found no fresh news this run) — skipping.")
        return

    with open(LATEST_META, "r", encoding="utf-8") as f:
        meta = json.load(f)

    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    from publish_instagram import post_image

    image_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{meta['image_rel_path']}"
    print(f"Publishing: {image_url}")
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
