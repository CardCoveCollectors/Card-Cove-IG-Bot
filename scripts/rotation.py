"""
Keeps track of which (set, list_type) combo to post next, so the
pipeline works through config.FEATURED_SETS in order and alternates
between "most expensive" and "least expensive" without repeating.

State is stored in state.json, committed back to the repo by the
GitHub Actions workflow after every run so the rotation persists.
"""
import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "state.json")


def _load():
    if not os.path.exists(STATE_PATH):
        return {"last_index": -1, "last_list_type": "least_expensive", "history": []}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def next_post(featured_sets):
    """Return (set_id, list_type) for the next post and advance the
    rotation. Alternates list_type each run; moves to the next set
    every time we've done both a most- and least-expensive post."""
    state = _load()
    last_type = state.get("last_list_type", "least_expensive")
    next_type = "most_expensive" if last_type == "least_expensive" else "least_expensive"

    advance_set = next_type == "most_expensive"  # we just wrapped back to expensive => new set
    index = state.get("last_index", -1)
    if advance_set or index < 0:
        index = (index + 1) % len(featured_sets)

    set_id = featured_sets[index]

    state["last_index"] = index
    state["last_list_type"] = next_type
    state.setdefault("history", []).append({"set_id": set_id, "list_type": next_type})
    state["history"] = state["history"][-50:]  # keep it from growing forever
    _save(state)

    return set_id, next_type


if __name__ == "__main__":
    from config import FEATURED_SETS

    for _ in range(6):
        print(next_post(FEATURED_SETS))
