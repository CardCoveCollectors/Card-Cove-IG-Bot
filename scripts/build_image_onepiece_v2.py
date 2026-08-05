"""
Renders Card Cove Collectors' branded "Top N" countdown poster for ONE
PIECE TCG cards (1080x1350, Instagram's tallest allowed feed-photo ratio).

Same visual design as build_image_pokemon.py (kept as its own file per
game, so either can be tweaked independently later — e.g. for Lorcana).
Card art is downloaded from optcgapi.com's image host. If a download
fails a placeholder box is drawn instead so the pipeline never hard-fails
on a single missing image.

optcgapi.com doesn't provide an official set-logo image the way
pokemontcg.io does, so the left side always falls back to the tracked
set-name text — that's expected, not a bug.
"""
import io
import os
from datetime import datetime, timezone

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
FONT_BOLD = os.path.join(FONT_DIR, "Poppins-Bold.ttf")
FONT_MEDIUM = os.path.join(FONT_DIR, "Poppins-Medium.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "Poppins-Regular.ttf")
FONT_LIGHT = os.path.join(FONT_DIR, "Poppins-Light.ttf")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")

W, H = 1080, 1350

# Same Card Cove Collectors brand palette as the Pokemon poster.
BG_TOP = (32, 17, 60)
BG_BOTTOM = (14, 7, 27)
ROW_BG_COLOR = (40, 24, 71)
ROW_BG_PODIUM = (49, 30, 86)
ACCENT_COLOR = (252, 192, 24)
CYAN = (36, 228, 240)
SUNSET_ORANGE = (240, 156, 36)
SUNSET_YELLOW = (252, 192, 24)
SUNSET_RED = (222, 64, 58)
HEADER_TEXT_COLOR = (255, 255, 255)
ROW_TEXT_COLOR = (245, 242, 250)
SUBTLE_TEXT_COLOR = (168, 158, 195)
DIVIDER_COLOR = (80, 62, 112)

MEDAL_COLORS = {
    1: (255, 214, 79),
    2: (208, 213, 222),
    3: (216, 148, 92),
}


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0]


def fit_text(draw, text, path, start_size, max_width, min_size=14):
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


def draw_tracked_text(draw, xy, text, f, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += text_w(draw, ch, f) + tracking
    return x


def tracked_text_w(draw, text, f, tracking=0):
    return sum(text_w(draw, ch, f) + tracking for ch in text) - (tracking if text else 0)


def download_card_image(url, size, timeout=15):
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        return None

    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((size, size), Image.LANCZOS)
    return img


def placeholder_image(size, label="?"):
    img = Image.new("RGBA", (size, size), (54, 42, 82, 255))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD, size // 3)
    tw = text_w(d, label, f)
    d.text(((size - tw) / 2, size / 3), label, font=f, fill=(210, 202, 225))
    return img


def sunset_gradient_bar(width, height, colors):
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


def vertical_gradient(width, height, top_color, bottom_color):
    col = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        col.putpixel((0, y), (r, g, b))
    return col.resize((width, height))


def make_shadow(w, h, blur=12, opacity=110, radius=16, ellipse=False):
    pad = blur * 3
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    box = [pad, pad, pad + w, pad + h]
    if ellipse:
        d.ellipse(box, fill=(0, 0, 0, opacity))
    else:
        d.rounded_rectangle(box, radius=radius, fill=(0, 0, 0, opacity))
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    return canvas, pad


def paste_shadow(base, box, blur=12, opacity=110, radius=16, offset=(0, 6), ellipse=False):
    x0, y0, x1, y1 = box
    shadow, pad = make_shadow(x1 - x0, y1 - y0, blur=blur, opacity=opacity, radius=radius, ellipse=ellipse)
    base.alpha_composite(shadow, (x0 - pad + offset[0], y0 - pad + offset[1]))


def load_logo(size):
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
    except Exception:
        return None
    logo.thumbnail((size, size), Image.LANCZOS)
    return logo


def download_logo_image(url, max_h, timeout=15):
    """Kept for parity with build_image_pokemon.py in case optcgapi.com
    (or a future source) ever adds set-logo images — currently unused
    since no set_logo_url is ever passed in for One Piece."""
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
                      data_source="TCGplayer/Cardmarket", set_logo_url=None):
    cards = cards[:n]
    title = "MOST EXPENSIVE" if list_type == "most_expensive" else "CHEAPEST ALT ARTS"

    img = vertical_gradient(W, H, BG_TOP, BG_BOTTOM).convert("RGBA")
    draw = ImageDraw.Draw(img)

    stripe_h = 16
    stripe = sunset_gradient_bar(W, stripe_h, [SUNSET_YELLOW, SUNSET_ORANGE, SUNSET_RED]).convert("RGBA")
    img.paste(stripe, (0, 0))
    glow, gpad = make_shadow(W, 6, blur=14, opacity=70, radius=0)
    img.alpha_composite(glow, (-gpad, stripe_h - gpad))

    # ---- Header ---- (same symmetric layout as the Pokemon poster: set
    # mark on the left, brand logo on the right, title centered between.)
    pad = 40
    HEADER_BOTTOM = 250
    logo_zone_top = stripe_h + 6
    rows_start = HEADER_BOTTOM + 24
    logo_zone_h = rows_start - logo_zone_top - 4
    max_side_w = 260

    brand_logo = load_logo(logo_zone_h)
    right_reserved = 0
    if brand_logo is not None:
        logo_x = W - pad - brand_logo.width
        logo_y = logo_zone_top + (logo_zone_h - brand_logo.height) // 2
        paste_shadow(img, (logo_x, logo_y, logo_x + brand_logo.width, logo_y + brand_logo.height),
                     blur=10, opacity=90, radius=20, offset=(0, 5))
        img.paste(brand_logo, (logo_x, logo_y), brand_logo)
        right_reserved = brand_logo.width + 32

    # Left side: no official set-logo image source for One Piece yet, so
    # this is always the tracked-caps set-name fallback.
    set_logo = download_logo_image(set_logo_url, logo_zone_h) if set_logo_url else None
    if set_logo is not None and set_logo.width > max_side_w:
        scale = max_side_w / set_logo.width
        set_logo = set_logo.resize(
            (max_side_w, max(1, int(set_logo.height * scale))), Image.LANCZOS
        )
    left_reserved = 0
    if set_logo is not None:
        sx = pad
        sy = logo_zone_top + (logo_zone_h - set_logo.height) // 2
        paste_shadow(img, (sx, sy, sx + set_logo.width, sy + set_logo.height),
                     blur=10, opacity=90, radius=20, offset=(0, 5))
        img.paste(set_logo, (sx, sy), set_logo)
        left_reserved = set_logo.width + 32
    else:
        eyebrow = f"{set_name.upper()}"
        eyebrow_font = font(FONT_MEDIUM, 28)
        eyebrow_w = tracked_text_w(draw, eyebrow, eyebrow_font, tracking=3)
        ey = logo_zone_top + (logo_zone_h - eyebrow_font.size) // 2
        draw_tracked_text(draw, (pad, ey), eyebrow, eyebrow_font, CYAN, tracking=3)
        left_reserved = eyebrow_w + 32

    title_x0 = pad + left_reserved
    title_x1 = W - pad - right_reserved
    title_max_w = max(title_x1 - title_x0, 100)

    header_text = f"TOP {len(cards)} {title}"
    header_text, header_font = fit_text(draw, header_text, FONT_BOLD, 62, title_max_w)
    bbox = draw.textbbox((0, 0), header_text, font=header_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = title_x0 + (title_max_w - tw) // 2
    ty = logo_zone_top + (logo_zone_h - th) // 2 - bbox[1]
    draw.text((tx + 2, ty + 3), header_text, font=header_font, fill=(0, 0, 0, 90))
    draw.text((tx, ty), header_text, font=header_font, fill=HEADER_TEXT_COLOR)

    divider_accent_w = 130
    accent_line = sunset_gradient_bar(divider_accent_w, 3, [ACCENT_COLOR, DIVIDER_COLOR]).convert("RGBA")
    img.paste(accent_line, (pad, HEADER_BOTTOM - 1), accent_line)
    draw.line([(pad + divider_accent_w, HEADER_BOTTOM), (W - pad, HEADER_BOTTOM)],
              fill=DIVIDER_COLOR, width=2)

    y = rows_start

    # ---- Rows ----
    row_gap = 14
    row_h = (H - y - 84 + row_gap) // len(cards)
    thumb_size = min(row_h - row_gap - 10, 100)

    for i, card in enumerate(cards):
        rank = i + 1
        is_podium = rank in MEDAL_COLORS
        rank_color = MEDAL_COLORS.get(rank, ACCENT_COLOR)
        row_top = y + i * row_h
        row_bottom = row_top + row_h - row_gap

        row_bg = ROW_BG_PODIUM if is_podium else ROW_BG_COLOR
        paste_shadow(img, (pad, row_top, W - pad, row_bottom),
                     blur=10, opacity=70, radius=16, offset=(0, 4))
        draw.rounded_rectangle(
            [(pad, row_top), (W - pad, row_bottom)], radius=16, fill=row_bg
        )
        if is_podium:
            draw.rounded_rectangle(
                [(pad, row_top), (W - pad, row_top + 6)], radius=3, fill=rank_color
            )
            draw.rounded_rectangle(
                [(pad, row_top), (W - pad, row_bottom)], radius=16, outline=rank_color, width=2
            )

        badge_r = 30 if is_podium else 25
        badge_cx = pad + 50
        badge_cy = (row_top + row_bottom) // 2
        paste_shadow(img, (badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r),
                     blur=6, opacity=100, radius=0, offset=(0, 3), ellipse=True)
        draw.ellipse(
            [(badge_cx - badge_r, badge_cy - badge_r), (badge_cx + badge_r, badge_cy + badge_r)],
            fill=rank_color,
        )
        rank_font = font(FONT_BOLD, 32 if is_podium else 27)
        rt = str(rank)
        rtw = text_w(draw, rt, rank_font)
        draw.text((badge_cx - rtw / 2, badge_cy - rank_font.size / 1.7), rt, font=rank_font, fill=(24, 16, 10))

        # Card thumbnail. optcgapi.com's `card_image` field is already a
        # full, direct image URL.
        thumb_x = pad + 100
        thumb_y = (row_top + row_bottom) // 2 - thumb_size // 2
        image_url = card.get("card_image")
        thumb = download_card_image(image_url, thumb_size) if image_url else None
        if thumb is None:
            # Card IDs here (e.g. "OP16-098_p1") are too long to fit a
            # small placeholder box legibly — fall back to just the
            # rarity code instead, which is short either way.
            thumb = placeholder_image(thumb_size, label=str(card.get("rarity", "?")))
        mask = rounded_mask(thumb_size, radius=13)
        paste_shadow(img, (thumb_x, thumb_y, thumb_x + thumb_size, thumb_y + thumb_size),
                     blur=8, opacity=90, radius=15, offset=(0, 4))
        border_w = 3 if is_podium else 2
        draw.rounded_rectangle(
            [(thumb_x - border_w, thumb_y - border_w),
             (thumb_x + thumb_size + border_w, thumb_y + thumb_size + border_w)],
            radius=15, outline=rank_color, width=border_w,
        )
        img.paste(thumb, (thumb_x, thumb_y), mask)

        # Name + card ID/rarity. One Piece collectors refer to cards by
        # their full set code (e.g. "OP01-001"), not a bare number, so
        # that's shown as-is rather than prefixed with "#".
        text_x = thumb_x + thumb_size + 26
        name_max_w = W - pad - 190 - text_x
        name = card.get("card_name", "Unknown")
        name, name_font = fit_text(draw, name, FONT_BOLD, 32, name_max_w)
        draw.text((text_x, row_top + row_h * 0.30 - 22), name, font=name_font, fill=ROW_TEXT_COLOR)

        rarity = card.get("rarity") or ""
        card_id = card.get("card_set_id", "")
        sub = f"{card_id}   ·   {rarity}" if rarity else card_id
        sub_font = font(FONT_REGULAR, 21)
        draw.text((text_x, row_top + row_h * 0.30 + 22), sub, font=sub_font, fill=SUBTLE_TEXT_COLOR)

        price = card.get("market_price", 0.0)
        price_text = f"${price:,.2f}"
        price_font = font(FONT_BOLD, 34)
        price_text, price_font = fit_text(draw, price_text, FONT_BOLD, 34, 160)
        pw = text_w(draw, price_text, price_font)
        draw.text(
            (W - pad - 26 - pw, (row_top + row_bottom) // 2 - 20),
            price_text,
            font=price_font,
            fill=rank_color,
        )

    # ---- Footer ----
    footer_y = H - 58
    draw.line([(pad, footer_y - 16), (W - pad, footer_y - 16)], fill=(52, 38, 82), width=1)

    if brand_name:
        f = font(FONT_MEDIUM, 26)
        draw.text((pad, footer_y), brand_name, font=f, fill=CYAN)

    stamp = datetime.now(timezone.utc).strftime("%b %-d, %Y")
    credit_text = f"Prices via {data_source}  ·  {stamp}"
    credit_font = font(FONT_LIGHT, 20)
    credit_text, credit_font = fit_text(draw, credit_text, FONT_LIGHT, 20, W - 2 * pad - 220)
    cw = text_w(draw, credit_text, credit_font)
    draw.text((W - pad - cw, footer_y + 3), credit_text, font=credit_font, fill=SUBTLE_TEXT_COLOR)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    dummy_cards = [
        {"card_name": f"Sample Card {i}", "card_set_id": f"OP01-{i:03d}", "rarity": "SR",
         "market_price": 45.0 / i}
        for i in range(1, 11)
    ]
    path = build_list_image(
        dummy_cards, "most_expensive", "Romance Dawn", "../out/preview_op.png",
        brand_name="@cardcovecollectors", n=10,
    )
    print("Wrote", path)
