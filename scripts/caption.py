"""
Template-based caption generator — no LLM API call, so there's no
per-post cost. Picks a random hook/closer combo styled after
countdown-format TCG accounts (gorilla.tcg and similar) and fills in
the real set name, price, and top card.

To add more variety over time, just add lines to HOOKS / CLOSERS /
HASHTAG_SETS below.
"""
import random

HOOKS_EXPENSIVE = [
    "💰 TOP {n} MOST EXPENSIVE cards in {set_name} 🔥",
    "These {n} {set_name} cards are worth serious money 👀",
    "If you pulled any of these from {set_name}, you're winning 🏆",
    "{set_name} chase cards — ranked by real market price 📈",
]

HOOKS_CHEAP = [
    "The {n} CHEAPEST cards in {set_name} 📉",
    "Don't sleep on these — {set_name}'s bulk tier, ranked 👇",
    "{n} {set_name} cards you can grab for pocket change 🪙",
]

CLOSERS = [
    "Which one are you chasing? Drop a comment 👇",
    "Got any of these in your binder? Let us know 📖",
    "Tag someone who needs to see #{top_number} 👀",
    "Prices move fast — save this for later 🔖",
    "Which spot surprised you the most?",
]

HASHTAG_SETS = [
    "#pokemontcg #pokemoncards #tcgcommunity #pokemoncollector #cardcollector",
    "#pokemontcg #pokemon151 #tcg #cardsofinstagram #pokemoncollection",
    "#pokemontcg #pokemoncards #tcgnews #pokemonmarket #wholesomecollecting",
]


def build_caption(cards, list_type, set_name, brand_handle="", n=10):
    top_card = cards[0]
    hooks = HOOKS_EXPENSIVE if list_type == "most_expensive" else HOOKS_CHEAP
    hook = random.choice(hooks).format(n=n, set_name=set_name)
    closer = random.choice(CLOSERS).format(top_number=len(cards))
    hashtags = random.choice(HASHTAG_SETS)

    lines = [hook, ""]
    for i, c in enumerate(cards, 1):
        lines.append(f"{i}. {c['name']} — ${c['market_price']:,.2f}")
    lines += ["", closer]
    if brand_handle:
        lines.append(f"\n📍 Shop with us: @{brand_handle}")
    lines += ["", hashtags]

    return "\n".join(lines)


if __name__ == "__main__":
    dummy = [
        {"name": f"Sample Card {i}", "market_price": 120.0 / i}
        for i in range(1, 11)
    ]
    print(build_caption(dummy, "most_expensive", "151", brand_handle="yourshophandle"))
