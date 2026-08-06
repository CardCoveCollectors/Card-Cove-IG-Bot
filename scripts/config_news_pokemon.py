"""
Settings for the Pokemon TCG News pipeline — its own feed, its own dedup
memory, fully independent of the One Piece news pipeline so neither
franchise's coverage crowds out the other.
"""

BRAND_NAME = "Card Cove Collectors"
BRAND_HANDLE = "cardcovecollectors"
STATE_FILE = "state_news_pokemon.json"

# Google News' own public RSS search feed — not tied to any one site, so it
# doesn't break when an individual news site adds bot protection (PokeBeach,
# Serebii, and the official One Piece TCG site all blocked direct scraping
# when we tested them; Google's own feed infrastructure doesn't). It
# aggregates coverage from PokeBeach, Serebii, PokeGuardian, official
# announcements as reported by outlets, etc.
NEWS_FEEDS = [
    {
        "topic": "Pokemon TCG",
        "url": "https://news.google.com/rss/search?q=%22Pokemon%20TCG%22&hl=en-US&gl=US&ceid=US:en",
    },
]

# Only consider articles published within this many hours. Google News
# search results include older matches too — this keeps the pipeline from
# surfacing week-old news the first time it runs, or after any gap.
MAX_AGE_HOURS = 48

# A headline needs at least one of these (case-insensitive) to count as
# "newsworthy" for a collector/grader audience, vs. generic chatter that
# happens to mention the game.
KEYWORDS = [
    "reveal", "revealed", "reveals",
    "announce", "announced", "announces", "announcement",
    "release", "releases", "released", "releasing",
    "set", "expansion", "series",
    "ban", "banned", "restrict", "restricted", "errata",
    "reprint", "reprinted", "restock", "restocked",
    "price", "prices", "pricing", "value", "spike", "spikes",
    "chase card", "secret rare", "special art", "alt art", "alternate art",
    "illustration rare",
    "tournament", "championship", "worlds", "regional", "regionals",
    "box", "booster", "product", "preorder", "pre-order",
    "leak", "leaked", "leaks",
]

# Headline substrings that disqualify a match even if a keyword above hit —
# catches unrelated stories that happen to mention "Pokemon" (the anime,
# the video games, unrelated merch, etc.).
BLOCKLIST = [
    "video game", "nintendo switch", "pokemon go", "anime episode",
    "manga chapter", "netflix", "box office", "live-action",
    "scarlet and violet dlc", "legends z-a",
]
