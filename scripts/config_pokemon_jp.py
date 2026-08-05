"""
Japanese Pokemon TCG settings. Mirrors config_pokemon.py's structure and
purpose, but pulls from PokeWallet's Japanese-language sets instead of
pokemontcg.io (which has no Japanese data at all).

Unlike the English pipeline's FEATURED_SETS (a hand-picked, static list),
the JP rotation is generated at runtime by
fetch_prices_pokemon_jp.get_all_featured_set_codes() — it pulls EVERY
Japanese set with a real set_code and at least one card (currently
450+ sets, going all the way back to 2004), newest first, and loops back
to the top once it's been all the way through. See that function's
docstring for the full explanation. There's nothing to edit here to
change which sets are included; that list is always whatever PokeWallet
currently has.

NOTE: Japanese rarity naming differs from English's for the chase-card
tier this pipeline cares about — "Art Rare" (AR) and "Special Art Rare"
(SAR) are the JP equivalents of English's "Illustration Rare" (IR) and
"Special Illustration Rare" (SIR). Hence CHEAPEST_RARITIES below uses the
JP names, and the poster's cheapest-list title says "ARS" not "IRS".
"""

# How many cards to feature per post.
LIST_LENGTH = 10

# JP equivalents of English's "Illustration Rare" / "Special Illustration
# Rare" — see the module docstring above.
CHEAPEST_RARITIES = ["Art Rare", "Special Art Rare"]

# Business/brand name shown on the image + used in captions.
BRAND_NAME = "Card Cove Collectors"

# Instagram handle (without @) used in the caption sign-off.
BRAND_HANDLE = "cardcovecollectors"

# Rotation-state filename — kept fully separate from the English Pokemon
# pipeline's state_pokemon.json so the two rotations never interfere.
STATE_FILE = "state_pokemon_jp.json"
