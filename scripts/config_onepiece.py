"""
One Piece TCG configuration — mirrors config.py's shape, kept as a fully
separate file (per set) so the Pokemon and One Piece pipelines can be
tuned independently without risk of breaking one while editing the other.

Data source is optcgapi.com (free, no API key, run by a community
developer — same spirit as pokemontcg.io, just for One Piece).

One Piece has no "Illustration Rare" rarity code the way Pokemon does —
Alt Art / special-print cards keep the SAME rarity (C/UC/R/SR/SEC/L) as
their normal counterpart. The only way to tell them apart is a suffix in
the card's name itself, and that suffix has changed across the game's
eras. So instead of a rarity filter, "cheapest" is scoped by checking the
card name for any of these markers:
"""
ALT_ART_MARKERS = [
    "Alternate Art",
    "Parallel",
    "Box Topper",
    "Manga",
    "Full Art",
    "(SP)",
    "(TR)",
]
# ^ If a future set uses a new special-print label we haven't seen yet,
# a "cheapest" list might fall back to literal cheapest-common (same
# safety fallback pattern as the Pokemon pipeline) — just add the new
# marker text here once you spot it.

# Newest sets first. optcgapi.com covers OP-01 through the present, plus
# Extra Boosters (EB-xx) and Premium Boosters (PRB-xx). Structure decks
# and promos use different endpoints and aren't included here.
FEATURED_SETS = [
    "OP-16",       # The Time of Battle
    "OP15-EB04",   # Adventure on Kami's Island
    "EB-03",       # Extra Booster: One Piece Heroines Edition
    "OP14-EB04",   # The Azure Sea's Seven
    "OP-13",       # Carrying On His Will
    "PRB-02",      # Premium Booster - The Best - Vol. 2
    "PRB-01",      # Premium Booster - The Best
    "OP-12",       # Legacy of the Master
    "EB-02",       # Extra Booster: Anime 25th Collection
    "OP-11",       # A Fist of Divine Speed
    "OP-10",       # Royal Blood
    "OP-09",       # Emperors in the New World
    "OP-08",       # Two Legends
    "EB-01",       # Extra Booster: Memorial Collection
    "OP-07",       # 500 Years in the Future
    "OP-06",       # Wings of the Captain
    "OP-05",       # Awakening of the New Era
    "OP-04",       # Kingdoms of Intrigue
    "OP-03",       # Pillars of Strength
    "OP-02",       # Paramount War
    "OP-01",       # Romance Dawn
]

# How many cards to feature per post.
LIST_LENGTH = 10

# Same brand identity as the Pokemon pipeline — same Instagram account.
BRAND_NAME = "Card Cove Collectors"
BRAND_HANDLE = "cardcovecollectors"

# Which state file this game's rotation uses — keeps it fully independent
# from the Pokemon rotation's state.json.
STATE_FILE = "state_onepiece.json"
