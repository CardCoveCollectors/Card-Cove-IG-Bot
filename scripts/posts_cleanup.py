"""
SHARED: deletes a pipeline's own old generated post images before a new
build, so posts/ (and therefore the repo) doesn't grow forever.

Every pipeline calls this with its own filename prefix (e.g. "poke-" for
English Pokemon, "op-" for English One Piece, "news-pokemon-" for Pokemon
News) so cleanup only ever touches that pipeline's own images — never
another pipeline's files or anyone's latest_*.json meta file. This is
genuinely game-agnostic, same spirit as rotation.py.

A generated image only needs to exist long enough to be reachable at a
public raw.githubusercontent.com URL for the few seconds between build
and publish in the same run. Once that run is done, nothing needs the
old file anymore, so it's always safe to clear a pipeline's previous
images right before generating this run's new one(s).
"""
import glob
import os


def cleanup_old_posts(posts_dir, prefix):
    pattern = os.path.join(posts_dir, f"{prefix}*.png")
    removed = 0
    for path in glob.glob(pattern):
        try:
            os.remove(path)
            removed += 1
        except OSError as e:
            print(f"WARNING: couldn't remove old post image {path}: {e}")
    if removed:
        print(f"Cleaned up {removed} old '{prefix}*.png' post image(s)")
    return removed
