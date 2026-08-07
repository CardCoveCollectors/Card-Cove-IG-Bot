"""
Shuffle-bag rotation for the rotating character-art pool used by the
English One Piece pricing pipeline's corner-flag graphic. No other
pipeline uses this yet — genuinely shared/game-agnostic code (same spirit
as rotation.py), just only called from main_onepiece.py today.

Guarantees every image in the pool gets used once before any image
repeats, while still feeling random (the pool is shuffled, not cycled in
a fixed order) — this avoids the same character showing up twice in a
short stretch just by bad luck, which is what actually reads as
"repetitive" to a viewer, not pool size alone.

Each build run needs `count` DISTINCT images (main_onepiece.py asks for
2 — one for "most expensive", one for "cheapest") so the same character
never covers both of the same day's posts.
"""
import glob
import json
import os
import random


def _load_pool(art_dir):
    if not os.path.isdir(art_dir):
        return []
    files = sorted(glob.glob(os.path.join(art_dir, "*.png")))
    return [os.path.basename(f) for f in files]


def _load_state(state_path):
    if not os.path.exists(state_path):
        return {"shuffled_queue": [], "pool_snapshot": []}
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(state, state_path):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def next_images(art_dir, state_path, count=1):
    """Returns `count` distinct image filenames (not full paths) for this
    run, drawn from a shuffled no-repeat-until-exhausted queue.

    If the pool on disk doesn't have at least `count` images (including
    an empty/missing folder), returns [] instead of raising — callers
    should treat that as "skip the character art for this run" so a
    thin or not-yet-populated pool never breaks posting.

    If the pool changed since the last run (images added/removed), the
    queue is reshuffled fresh so new images enter rotation immediately
    instead of waiting for the old cycle to finish.
    """
    pool = _load_pool(art_dir)
    if len(pool) < count:
        return []

    state = _load_state(state_path)
    queue = state.get("shuffled_queue", [])
    snapshot = state.get("pool_snapshot", [])

    if sorted(snapshot) != sorted(pool):
        queue = []

    picked = []
    for _ in range(count):
        if not queue:
            fresh = pool[:]
            random.shuffle(fresh)
            queue = fresh
        idx = 0
        while queue[idx] in picked and idx < len(queue) - 1:
            idx += 1
        picked.append(queue.pop(idx))

    state["shuffled_queue"] = queue
    state["pool_snapshot"] = pool
    _save_state(state, state_path)
    return picked


if __name__ == "__main__":
    import sys

    test_dir = sys.argv[1] if len(sys.argv) > 1 else "../assets/character_art"
    test_state = "../_test_charart_state.json"
    for _ in range(10):
        print(next_images(test_dir, test_state, count=2))
