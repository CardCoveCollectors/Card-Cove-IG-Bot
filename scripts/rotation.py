"""
Keeps track of which set to feature next, so a pipeline works through its
FEATURED_SETS in order and loops back to the top when it runs out.

Each posting day covers ONE set with BOTH its Top-10 lists (most expensive
+ cheapest) built and posted together, so the rotation only needs to track
which set we're on — not the list type.

State is stored in a JSON file (default: state.json, next to this folder),
committed back to the repo by the GitHub Actions workflow after every run
so the rotation persists. Pass a different `state_path` to run a totally
separate, independent rotation — e.g. main_onepiece.py uses state_onepiece.json
so the Pokemon and One Piece rotations never interfere with each other.
"""
import json
import os

DEFAULT_STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "state.json")


def _load(state_path):
    if not os.path.exists(state_path):
        return {"last_index": -1, "history": []}
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(state, state_path):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def next_set(featured_sets, state_path=DEFAULT_STATE_PATH):
    """Return the set_id to feature next and advance the rotation by one
    full day. Call this once per scheduled run — main.py then builds
    both the most-expensive and cheapest lists for whatever it returns."""
    state = _load(state_path)
    index = (state.get("last_index", -1) + 1) % len(featured_sets)
    set_id = featured_sets[index]

    state["last_index"] = index
    state.setdefault("history", []).append(set_id)
    state["history"] = state["history"][-50:]  # keep it from growing forever
    _save(state, state_path)

    return set_id


if __name__ == "__main__":
    from config import FEATURED_SETS

    for _ in range(6):
        print(next_set(FEATURED_SETS))
