"""
Renders a branded "Top N" countdown poster (1080x1350, Instagram's
tallest allowed feed-photo ratio) from a list of priced cards.

Card art is downloaded from pokemontcg.io's image CDN. If a download
fails (no network, bad URL, etc.) a placeholder box is drawn instead
so the pipeline never hard-fails on a single missing image.
"""
import io
import os
from datetime import datetime, timezone

import requests
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")

W, H = 1080, 1350

# Card Cove Collectors brand palette, sampled from the logo.
BG_COLOR = (24, 12, 48)            # deep navy/purple (logo's outline color)
ROW_BG_COLOR = (37, 22, 66)        # lighter navy for row cards
ACCENT_COLOR = (252, 192, 24)      # sunset gold — rank badges / price text
CYAN = (36, 228, 240)              # brand cyan — eyebrow text, footer
SUNSET_ORANGE = (240, 156, 36)
SUNSET_YELLOW = (252, 192, 24)
HEADER_TEXT_COLOR = (255, 255, 255)
ROW_TEXT_COLOR = (240, 240, 245)
SUBTLE_TEXT_COLOR = (165, 155, 190)


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0]


def fit_text(draw, text, path, start_size, max_width, min_size=14):
    """Shrink font size until text fits max_width; ellipsize if still too long."""
    size = start_size
    f = font(path, size)
    while text_w(draw, text, f) > max_width and size > min_size:
        size -= 1
        f = font(path, size)
    if text_w(draw, text, f) > max_width:
        while text and text_w(draw, text + "...", f) > max_width:
            text = text[:-1]
        text = text + "..."
    return text, f


def download_card_image(url, size, timeout=15):
    """Returns a square-cropped PIL Image of the given size, or None."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        return None

    # Center-crop to square, then resize.
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((size, size), Image.LANCZOS)
    return img


def placeholder_image(size, label="?"):
    img = Image.new("RGBA", (size, size), (50, 40, 75, 255))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD, size // 3)
    tw = text_w(d, label, f)
    d.text(((size - tw) / 2, size / 3), label, font=f, fill=(200, 200, 200))
    return img


def sunset_gradient_bar(width, height, colors):
    """Horizontal strip that blends through a list of RGB colors, evoking
    the logo's sunset sky."""
    bar = Image.new("RGB", (width, height))
    px = bar.load()
    n = len(colors) - 1
    for x in range(width):
        t = x / max(width - 1, 1) * n
        i = min(int(t), n - 1)
        frac = t - i
        c0, c1 = colors[i], colors[i + 1]
        r = int(c0[0] + (c1[0] - c0[0]) * frac)
        g = int(c0[1] + (c1[1] - c0[1]) * frac)
        b = int(c0[2] + (c1[2] - c0[2]) * frac)
        for y in range(height):
            px[x, y] = (r, g, b)
    return bar


def load_logo(size):
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
    except Exception:
        return None
    logo.thumbnail((size, size), Image.LANCZOS)
    return logo


def download_logo_image(url, max_h, timeout=15):
    """Set logos (e.g. the '151' or 'Prismatic Evolutions' wordmark) are
    wide, not square — scale by height only and keep native aspect ratio."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        return None
    w, h = img.size
    if h == 0:
        return None
    new_w = int(w * (max_h / h))
    return img.resize((new_w, max_h), Image.LANCZOS)


def rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
    return mask


def build_list_image(cards, list_type, set_name, out_path, brand_name="", n=10,
                      data_source="TCGplayer", set_logo_url=None):
    cards = cards[:n]
    title = "MOST EXPENSIVE" if list_type == "most_expensive" else "CHEAPEST"

    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Thin sunset gradient stripe across the very top, echoing the logo's sky.
    stripe_h = 14
    stripe = sunset_gradient_bar(W, stripe_h, [SUNSET_YELLOW, SUNSET_ORANGE, (228, 60, 48)])
    img.paste(stripe, (0, 0))

    # ---- Header ---- (positions fixed exactly as approved — only the
    # brand logo's size changes below; nothing else here moves.)
    pad = 40
    y = 50
    HEADER_BOTTOM = 250

    # Left side: the Pokemon set's own logo image (e.g. the "151" wordmark)
    # instead of typing the set name out as text. Falls back to text if the
    # image can't be fetched.
    eyebrow_h = 40
    set_logo = download_logo_image(set_logo_url, eyebrow_h) if set_logo_url else None
    if set_logo is not None:
        img.paste(set_logo, (pad, y + 2), set_logo)
        eyebrow_right_edge = pad + set_logo.width
    else:
        eyebrow = f"{set_name.upper()}"
        eyebrow_font = font(FONT_BOLD, 30)
        draw.text((pad, y), eyebrow, font=eyebrow_font, fill=CYAN)
        eyebrow_right_edge = pad + text_w(draw, eyebrow, eyebrow_font)
    y += 44

    # Right side: brand logo, sized to fill all the *unused* vertical room
    # between the top stripe and where the row list starts — bigger than
    # before, without moving the title, divider, or rows.
    logo_zone_top = stripe_h + 6
    rows_start = HEADER_BOTTOM + 24
    logo = load_logo(rows_start - logo_zone_top - 4)
    reserved_w = (logo.width + 28) if logo is not None else 0

    header_text = f"TOP {len(cards)} {title}"
    header_font = font(FONT_BOLD, 62)
    header_max_w = W - 2 * pad - reserved_w
    header_text, header_font = fit_text(draw, header_text, FONT_BOLD, 62, header_max_w)
    draw.text((pad, y), header_text, font=header_font, fill=HEADER_TEXT_COLOR)

    draw.line([(pad, HEADER_BOTTOM), (W - pad, HEADER_BOTTOM)], fill=(70, 55, 100), width=2)

    if logo is not None:
        logo_x = W - pad - logo.width
        logo_y = logo_zone_top
        img.paste(logo, (logo_x, logo_y), logo)

    y = rows_start

    # ---- Rows ----
    row_h = (H - y - 90) // len(cards)
    thumb_size = min(row_h - 12, 96)

    for i, card in enumerate(cards):
        rank = i + 1
        row_top = y + i * row_h
        row_bottom = row_top + row_h - 8

        draw.rounded_rectangle(
            [(pad, row_top), (W - pad, row_bottom)], radius=14, fill=ROW_BG_COLOR
        )

        # Rank badge
        badge_cx = pad + 46
        badge_cy = (row_top + row_bottom) // 2
        draw.ellipse(
            [(badge_cx - 26, badge_cy - 26), (badge_cx + 26, badge_cy + 26)],
            fill=ACCENT_COLOR,
        )
        rank_font = font(FONT_BOLD, 30 if rank < 10 else 24)
        rt = str(rank)
        rtw = text_w(draw, rt, rank_font)
        draw.text((badge_cx - rtw / 2, badge_cy - 18), rt, font=rank_font, fill=(20, 20, 20))

        # Card thumbnail — rounded corners + thin gold border so real card
        # art reads as a clean, deliberate frame once it's populated.
        thumb_x = pad + 92
        thumb_y = (row_top + row_bottom) // 2 - thumb_size // 2
        image_url = (card.get("images") or {}).get("small")
        thumb = download_card_image(image_url, thumb_size) if image_url else None
        if thumb is None:
            thumb = placeholder_image(thumb_size, label=str(card.get("number", "?")))
        mask = rounded_mask(thumb_size, radius=12)
        draw.rounded_rectangle(
            [(thumb_x - 2, thumb_y - 2), (thumb_x + thumb_size + 2, thumb_y + thumb_size + 2)],
            radius=14, outline=ACCENT_COLOR, width=2,
        )
        img.paste(thumb, (thumb_x, thumb_y), mask)

        # Name + rarity
        text_x = thumb_x + thumb_size + 24
        name_max_w = W - pad - 190 - text_x
        name = card.get("name", "Unknown")
        name, name_font = fit_text(draw, name, FONT_BOLD, 32, name_max_w)
        draw.text((text_x, row_top + row_h * 0.28 - 20), name, font=name_font, fill=ROW_TEXT_COLOR)

        rarity = card.get("rarity") or ""
        num = card.get("number", "")
        sub = f"#{num}  ·  {rarity}" if rarity else f"#{num}"
        sub_font = font(FONT_REGULAR, 22)
        draw.text((text_x, row_top + row_h * 0.28 + 24), sub, font=sub_font, fill=SUBTLE_TEXT_COLOR)

        # Price
        price = card.get("market_price", 0.0)
        price_text = f"${price:,.2f}"
        price_font = font(FONT_BOLD, 34)
        price_text, price_font = fit_text(draw, price_text, FONT_BOLD, 34, 160)
        pw = text_w(draw, price_text, price_font)
        draw.text(
            (W - pad - 24 - pw, (row_top + row_bottom) // 2 - 20),
            price_text,
            font=price_font,
            fill=ACCENT_COLOR,
        )

    # ---- Footer ----
    footer_y = H - 60
    if brand_name:
        f = font(FONT_BOLD, 28)
        draw.text((pad, footer_y), brand_name, font=f, fill=CYAN)

    # Bottom-right: data source credit + a date/time stamp so the post is
    # self-documenting about when the prices were pulled.
    stamp = datetime.now(timezone.utc).strftime("%b %-d, %Y")
    credit_text = f"Prices via {data_source} · {stamp}"
    credit_font = font(FONT_REGULAR, 20)
    credit_text, credit_font = fit_text(draw, credit_text, FONT_REGULAR, 20, W - 2 * pad - 220)
    cw = text_w(draw, credit_text, credit_font)
    draw.text((W - pad - cw, footer_y + 4), credit_text, font=credit_font, fill=SUBTLE_TEXT_COLOR)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    # Render with dummy data so the layout can be checked with no network.
    dummy_cards = [
        {"name": f"Sample Card {i}", "number": str(i), "rarity": "Rare Holo",
         "market_price": 120.0 / i, "images": {}}
        for i in range(1, 11)
    ]
    path = build_list_image(
        dummy_cards, "most_expensive", "Test Set", "../out/preview.png",
        brand_name="@yourshophandle", n=10,
    )
    print("Wrote", path)
