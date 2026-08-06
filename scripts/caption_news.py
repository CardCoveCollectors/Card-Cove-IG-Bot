"""
Template-based caption generator for the news pipeline — same $0 approach
as caption_pokemon.py / caption_onepiece.py, no LLM API call. Picks a
random hook/closer and fills in the real headline + source.
"""
import random

HOOKS = [
    "🚨 TCG NEWS: {headline}",
    "👀 Heads up, collectors — {headline}",
    "📰 Just in: {headline}",
    "🔥 Big {topic} news — {headline}",
    "Breaking from the {topic} world: {headline}",
    "This just dropped: {headline}",
]

CLOSERS = [
    "Thoughts on this one? Drop a comment 👇",
    "How does this change your want list? 🤔",
    "Save this so you don't miss the drop 🔖",
    "Tag someone who needs to see this 👀",
    "Are you excited or nervous about this? 😅",
    "Let us know what you think below 👇",
]

HASHTAG_SETS = [
    "#pokemontcg #onepiecetcg #tcgnews #cardcollector #tcgcommunity",
    "#tcgnews #pokemontcg #onepiececardgame #cardsofinstagram #collectorscommunity",
    "#pokemontcg #onepiecetcg #tcgcommunity #cardnews #wholesomecollecting",
]


def build_caption(item, brand_handle=""):
    hook = random.choice(HOOKS).format(headline=item["title"], topic=item["topic"])
    closer = random.choice(CLOSERS)
    hashtags = random.choice(HASHTAG_SETS)

    lines = [hook, ""]
    if item.get("source"):
        lines.append(f"Source: {item['source']}")
        lines.append("")
    lines.append(closer)
    if brand_handle:
        lines.append(f"\n📍 Shop with us: @{brand_handle}")
    lines += ["", hashtags]

    return "\n".join(lines)


if __name__ == "__main__":
    dummy = {
        "topic": "Pokemon TCG",
        "title": "New Pokemon TCG Set Revealed With Reprinted Fan-Favorite Illustration Rares",
        "source": "PokeBeach",
    }
    print(build_caption(dummy, brand_handle="yourshophandle"))
