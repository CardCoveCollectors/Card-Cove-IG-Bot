"""
Edit this list any time to control which sets get featured. Newest sets
are listed first — each posting day now covers ONE set with BOTH its
Top-10 lists (most expensive + cheapest) posted together, then the
rotation moves to the next set on the next scheduled day, looping back
to the top when it runs out.

Find more set IDs at https://api.pokemontcg.io/v2/sets (the "id" field),
or ask me to pull the current list.

NOTE: "me5" (Pitch Black), "me4" (Chaos Rising), "me3" (Perfect Order),
and "me2pt5" (Ascended Heroes) are deliberately left out — as of Aug 2026
pokemontcg.io simply has no TCGplayer pricing data at all for these (very
new) sets, so every card query for them comes back empty. Add them back
here once pokemontcg.io backfills pricing for them.
"""

FEATURED_SETS = [
    "me2",       # Phantasmal Flames
    "me1",       # Mega Evolution
    "zsv10pt5",  # Black Bolt
    "rsv10pt5",  # White Flare
    "sv10",      # Destined Rivals
    "sv9",       # Journey Together
    "sv8pt5",    # Prismatic Evolutions
    "sv8",       # Surging Sparks
    "sv7",       # Stellar Crown
    "sv6pt5",    # Shrouded Fable
    "sv6",       # Twilight Masquerade
    "sv5",       # Temporal Forces
    "sv4pt5",    # Paldean Fates
    "sv4",       # Paradox Rift
    "sv3pt5",    # 151
    "sv3",       # Obsidian Flames
]

# How many cards to feature per post.
LIST_LENGTH = 10

# The "cheapest" list only considers cards with one of these rarities, so
# it surfaces the most affordable *desirable* chase cards (full-art
# Illustration Rares) instead of literal bulk commons nobody wants. The
# "most expensive" list is left unfiltered since chase cards already rise
# to the top there naturally. If a set has none of these rarities priced
# yet, it automatically falls back to the unfiltered cheapest card.
CHEAPEST_RARITIES = ["Illustration Rare", "Special Illustration Rare"]

# Business/brand name shown on the image + used in captions.
BRAND_NAME = "Card Cove Collectors"

# Instagram handle (without @) used in the caption sign-off.
# Double check this matches your real handle before going live.
BRAND_HANDLE = "cardcovecollectors"

# Rotation-state filename (kept separate from One Piece's state_onepiece.json
# so the two pipelines' rotations never interfere with each other).
STATE_FILE = "state_pokemon.json"
