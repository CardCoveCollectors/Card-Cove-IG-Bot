"""
Template-based caption generator for the One Piece pipeline — no LLM API
call, so there's no per-post cost. Same pattern as caption.py, kept as
its own file so wording/hashtags can be tuned per game independently.
"""
import random

HOOKS_EXPENSIVE = [
    "💰 TOP {n} MOST EXPENSIVE cards in {set_name} 🔥",
    "These {n} {set_name} cards are worth serious money 👀",
    "If you pulled any of these from {set_name}, you're winning 🏆",
    "{set_name} chase cards — ranked by real market price 📈",
    "🔥 {set_name}'s TOP {n} chase cards, ranked by price",
    "The {n} priciest pulls in {set_name} right now 💵",
    "{set_name} money cards — how many do you own? 💰",
    "Big money alert: {set_name}'s TOP {n} 📈",
]

HOOKS_CHEAP = [
    "The {n} most affordable Alt Arts in {set_name} 🎨",
    "{set_name} Alt Arts that won't break the bank 👇",
    "{n} {set_name} Alt Arts, ranked cheapest to less-cheap 🪙",
    "Budget Alt Arts from {set_name} — TOP {n} 💵",
    "Chase the art, not the price — {set_name}'s cheapest Alt Arts 🖼️",
    "{set_name} special prints that still won't wreck your wallet 🎨",
]

CLOSERS = [
    "Which one are you chasing? Drop a comment 👇",
    "Got any of these in your binder? Let us know 📖",
    "Tag someone who needs to see #{top_number} 👀",
    "Prices move fast — save this for later 🔖",
    "Which spot surprised you the most?",
    "Would you rather pull #1 or #{top_number}? 🤔",
    "Save this before your next box break 📌",
    "Drop your set wishlist below 👇",
    "Which of these is on your want list? ✨",
]

HASHTAG_SETS = [
    "#onepiecetcg #onepiececardgame #optcg #tcgcommunity #cardcollector",
    "#onepiecetcg #optcg #tcg #cardsofinstagram #onepiececollection",
    "#onepiecetcg #optcg #tcgnews #cardmarket #wholesomecollecting",
    "#onepiece #onepiecetcg #altart #tcgcollector #cardsofinstagram",
    "#onepiececards #tcgcollector #onepiecewishlist #cardpulls #optcgfamily",
    "#onepiecetcg #tcgcollector #optcgcommunity #cardhunting #setcollecting",
]


def build_caption(cards, list_type, set_name, brand_handle="", n=10):
    hooks = HOOKS_EXPENSIVE if list_type == "most_expensive" else HOOKS_CHEAP
    hook = random.choice(hooks).format(n=n, set_name=set_name)
    closer = random.choice(CLOSERS).format(top_number=len(cards))
    hashtags = random.choice(HASHTAG_SETS)

    lines = [hook, ""]
    for i, c in enumerate(cards, 1):
        lines.append(f"{i}. {c['card_name']} — ${c['market_price']:,.2f}")
    lines += ["", closer]
    if brand_handle:
        lines.append(f"\n📍 Shop with us: @{brand_handle}")
    lines += ["", hashtags]

    return "\n".join(lines)


if __name__ == "__main__":
    dummy = [
        {"card_name": f"Sample Card {i}", "market_price": 45.0 / i}
        for i in range(1, 11)
    ]
    print(build_caption(dummy, "most_expensive", "Romance Dawn", brand_handle="cardcovecollectors"))
