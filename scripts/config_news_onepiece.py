"""
Settings for the One Piece Card Game News pipeline — its own feed, its own
dedup memory, fully independent of the Pokemon news pipeline so neither
franchise's coverage crowds out the other.
"""

BRAND_NAME = "Card Cove Collectors"
BRAND_HANDLE = "cardcovecollectors"
STATE_FILE = "state_news_onepiece.json"

# Same Google News RSS approach as the Pokemon news pipeline — see
# config_news_pokemon.py for why (official sites blocked direct scraping,
# Google's own feed infrastructure doesn't).
NEWS_FEEDS = [
    {
        "topic": "One Piece Card Game",
        "url": "https://news.google.com/rss/search?q=%22One%20Piece%20Card%20Game%22&hl=en-US&gl=US&ceid=US:en",
    },
]

# Only consider articles published within this many hours.
MAX_AGE_HOURS = 48

# A headline needs at least one of these (case-insensitive) to count as
# "newsworthy" for a collector/grader audience.
KEYWORDS = [
    "reveal", "revealed", "reveals",
    "announce", "announced", "announces", "announcement",
    "release", "releases", "released", "releasing",
    "set", "expansion", "series",
    "ban", "banned", "restrict", "restricted", "errata",
    "reprint", "reprinted", "restock", "restocked",
    "price", "prices", "pricing", "value", "spike", "spikes",
    "chase card", "secret rare", "special art", "alt art", "alternate art",
    "parallel", "manga rare",
    "tournament", "championship", "regional", "regionals",
    "box", "booster", "product", "preorder", "pre-order",
    "leak", "leaked", "leaks",
]

# Headline substrings that disqualify a match even if a keyword above hit —
# catches unrelated stories that happen to mention "One Piece" (the anime,
# manga chapters, live-action show, etc.) rather than the card game.
BLOCKLIST = [
    "video game", "anime episode", "manga chapter", "netflix",
    "box office", "live-action", "egghead", "chapter spoilers",
]
