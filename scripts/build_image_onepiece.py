"""
Renders Card Cove Collectors' branded "Top N" GRID poster for ONE PIECE
TCG cards (1080x1350, Instagram's recommended 4:5 feed-photo ratio).

v3 design: same grid layout as build_image_pokemon.py (5-column x 2-row
grid, price above each card, rank badge on the card's bottom-right
corner, name + rarity/number below the card). The previous row-list
design lives on in build_image_onepiece_v2.py in case we ever want to go
back to it.

One Piece doesn't have per-set logo art the way Pokemon does, so the
top-right slot is a plain "OP-16"-style set-code badge instead of a big
illustrated logo — same visual weight, just text instead of art.

Card art is downloaded from optcgapi.com's image host. If a download
fails a placeholder box is drawn instead so the pipeline never hard-fails
on a single missing image.
"""
import io
import os
import re
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
BG_TOP = (28, 15, 52)
BG_BOTTOM = (12, 6, 24)
ACCENT_GOLD = (252, 192, 24)
CYAN = (36, 228, 240)
TEAL = (44, 229, 245)  # the logo's brightest teal — used for rank badges 4-10
WHITE = (255, 255, 255)
SUBTLE_TEXT_COLOR = (168, 158, 195)
DIVIDER_COLOR = (52, 38, 82)

MEDAL_COLORS = {
    1: (255, 205, 0),
    2: (222, 226, 232),
    3: (205, 127, 50),
}
# Thin outline ring drawn around each podium badge for extra contrast.
MEDAL_RING = {
    1: (255, 240, 150),
    2: (255, 255, 255),
    3: (255, 200, 150),
}


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0]


def fit_text(draw, text, path, start_size, max_width, min_size=12):
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


def clean_card_name(name):
    """Strip a purely-numeric disambiguation parenthetical like "(079)" —
    optcgapi.com's internal print-order tag, not something a follower
    needs to see. Real qualifiers like "(SP)", "(Manga)", "(Alternate
    Art)" are left alone."""
    return re.sub(r"\s*\(\d+\)", "", name).strip()


def _shrink_to_fit(draw, text, path, start_size, max_width, min_size):
    """Like fit_text but WITHOUT the ellipsis fallback — just shrinks the
    font down to min_size and reports whether that was actually enough,
    so callers can tell "fits" apart from "had to be truncated"."""
    size = start_size
    f = font(path, size)
    while text_w(draw, text, f) > max_width and size > min_size:
        size -= 1
        f = font(path, size)
    return text_w(draw, text, f) <= max_width, text, f


def fit_name(draw, name, path, start_size, max_width, min_size=14):
    """Try the full name first (shrinking font size only). If it still
    won't fit even at min_size, drop a trailing "(Qualifier)" clause
    entirely rather than cutting it off mid-word with an ellipsis — a
    clean shorter name reads better than "Zehahahahaha! (Alternate A...".
    Only falls back to character-ellipsis truncation if the bare name
    (no qualifier) still doesn't fit."""
    fits, text, f = _shrink_to_fit(draw, name, path, start_size, max_width, min_size)
    if fits:
        return text, f

    base = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    if base and base != name:
        fits2, text2, f2 = _shrink_to_fit(draw, base, path, start_size, max_width, min_size)
        if fits2:
            return text2, f2

    return fit_text(draw, name, path, start_size, max_width, min_size)


def download_card_art(url, w, h, timeout=15):
    """Real trading cards are already ~2.5:3.5 (the box we're given here
    matches that ratio), so this "covers" the target box — scales up to
    fully fill it, then center-crops any small overhang."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        return None

    iw, ih = img.size
    if iw == 0 or ih == 0:
        return None
    scale = max(w / iw, h / ih)
    new_size = (max(1, round(iw * scale)), max(1, round(ih * scale)))
    img = img.resize(new_size, Image.LANCZOS)
    left = (img.width - w) // 2
    top = (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def placeholder_card(w, h, label="?"):
    img = Image.new("RGBA", (w, h), (44, 27, 78, 255))
    d = ImageDraw.Draw(img)
    for i in range(0, w + h, 18):
        d.line([(i, 0), (0, i)], fill=(255, 255, 255, 12), width=6)
    d.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=14, outline=(255, 255, 255, 40), width=2)
    f = font(FONT_BOLD, max(14, w // 5))
    tw = text_w(d, label, f)
    d.text(((w - tw) / 2, h / 2 - f.size / 2), label, font=f, fill=(210, 202, 225))
    return img


def vertical_gradient(width, height, top_color, bottom_color):
    col = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        col.putpixel((0, y), (r, g, b))
    return col.resize((width, height))


def make_shadow(w, h, blur=10, opacity=100, radius=14, ellipse=False):
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


def paste_shadow(base, box, blur=10, opacity=100, radius=14, offset=(0, 5), ellipse=False):
    x0, y0, x1, y1 = box
    shadow, pad = make_shadow(x1 - x0, y1 - y0, blur=blur, opacity=opacity, radius=radius, ellipse=ellipse)
    base.alpha_composite(shadow, (x0 - pad + offset[0], y0 - pad + offset[1]))


def rounded_mask(w, h, radius):
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)
    return mask


def set_code_badge(max_h, code_text):
    """One Piece has no per-set logo art, so the top-right slot is just
    the set code (e.g. "OP-16") in a badge matching the same visual
    weight as the Pokemon version's real set-logo image."""
    pad_x = 34
    f = font(FONT_BOLD, int(max_h * 0.42))
    small_f = font(FONT_MEDIUM, int(max_h * 0.14))
    dummy = Image.new("RGBA", (10, 10))
    dd = ImageDraw.Draw(dummy)

    main_bbox = dd.textbbox((0, 0), code_text, font=f)
    main_w, main_h = main_bbox[2] - main_bbox[0], main_bbox[3] - main_bbox[1]
    small_text = "ONE PIECE TCG"
    small_bbox = dd.textbbox((0, 0), small_text, font=small_f)
    small_w, small_h = small_bbox[2] - small_bbox[0], small_bbox[3] - small_bbox[1]

    w = main_w + pad_x * 2
    h = max_h
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=18, fill=(20, 12, 34, 235))
    d.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=18, outline=TEAL, width=3)

    # Center the whole (main text + gap + small text) block vertically so
    # there's no leftover empty space above/below it.
    gap = 10
    block_h = main_h + gap + small_h
    block_top = (h - block_h) / 2

    tx = (w - main_w) / 2 - main_bbox[0]
    ty = block_top - main_bbox[1]
    d.text((tx, ty), code_text, font=f, fill=WHITE)

    sx = (w - small_w) / 2 - small_bbox[0]
    sy = block_top + main_h + gap - small_bbox[1]
    d.text((sx, sy), small_text, font=small_f, fill=TEAL)
    return img


def build_list_image(cards, list_type, set_name, out_path, brand_name="", n=10,
                      data_source="TCGplayer/Cardmarket", set_logo_url=None, set_id=None):
    cards = cards[:n]
    title = "MOST EXPENSIVE" if list_type == "most_expensive" else "CHEAPEST ALT ARTS"

    img = vertical_gradient(W, H, BG_TOP, BG_BOTTOM).convert("RGBA")
    draw = ImageDraw.Draw(img)

    pad = 40
    top_y = 44

    # ---- Header: set-code badge top-right, two-line title top-left ----
    badge = set_code_badge(150, set_id) if set_id else None
    if badge is not None:
        lx = W - pad - badge.width
        ly = top_y - 6
        paste_shadow(img, (lx, ly, lx + badge.width, ly + badge.height), blur=10, opacity=100, radius=18)
        img.paste(badge, (lx, ly), badge)
        title_max_w = lx - pad - 24
    else:
        title_max_w = W - 2 * pad

    title_line1 = f"TOP {len(cards)}"
    title_line2 = title
    t1, f1 = fit_text(draw, title_line1, FONT_BOLD, 54, title_max_w)
    t2, f2 = fit_text(draw, title_line2, FONT_BOLD, 54, title_max_w)
    draw.text((pad + 2, top_y + 2), t1, font=f1, fill=(0, 0, 0, 90))
    draw.text((pad, top_y), t1, font=f1, fill=WHITE)
    y2 = top_y + f1.size + 8
    draw.text((pad + 2, y2 + 2), t2, font=f2, fill=(0, 0, 0, 90))
    draw.text((pad, y2), t2, font=f2, fill=WHITE)

    grid_top = y2 + f2.size + 36

    # ---- Footer geometry (computed up front so the grid above can size
    # itself around it) ----
    ref_font = font(FONT_MEDIUM, 24)
    logo_target_h = (ref_font.size + 6) * 3
    bottom_margin = 26
    footer_content_bottom = H - bottom_margin
    footer_content_top = footer_content_bottom - logo_target_h
    divider_y = footer_content_top - 16
    footer_reserve = H - divider_y + 14

    # ---- Grid: 5 columns x 2 rows for Top 10 ----
    cols, rows = 5, 2
    gutter = 18
    cell_w = (W - 2 * pad - gutter * (cols - 1)) // cols
    card_h = round(cell_w * 1.4)  # standard 2.5" x 3.5" trading-card ratio

    price_h = 42
    name_h = 26
    sub_h = 22
    below_gap = 6
    row_gap = 28
    rank_r = 20

    row_content_h = price_h + card_h + name_h + sub_h + below_gap
    avail_h = H - grid_top - footer_reserve
    leftover = max(0, avail_h - (row_content_h * rows + row_gap * (rows - 1)))

    # Spread the ENTIRE leftover proportionally instead of dumping it all
    # as one empty void above the grid: 25% becomes a bit of extra room
    # right under the header, 45% becomes the gap between the two rows
    # (the biggest single chunk, since a gap there reads as an intentional
    # section break), and the remaining 30% is left unassigned here, which
    # naturally becomes pre-footer breathing room since the grid ends
    # before footer_reserve begins — giving a light top margin, a
    # deliberate mid-gap, and a matching bottom margin.
    grid_top = int(grid_top + leftover * 0.25)
    row_gap = int(row_gap + leftover * 0.45)
    row_h = row_content_h + row_gap

    for i, card in enumerate(cards):
        col = i % cols
        row = i // cols
        cx0 = pad + col * (cell_w + gutter)
        cy0 = grid_top + row * row_h

        price = card.get("market_price", 0.0)
        price_text = f"${price:,.2f}"
        pf_size = 28 if len(price_text) <= 7 else 22
        price_text, pf = fit_text(draw, price_text, FONT_BOLD, pf_size, cell_w)
        pw = text_w(draw, price_text, pf)
        draw.text((cx0 + (cell_w - pw) / 2 + 1, cy0 + 1), price_text, font=pf, fill=(0, 0, 0, 90))
        draw.text((cx0 + (cell_w - pw) / 2, cy0), price_text, font=pf, fill=WHITE)

        card_y0 = cy0 + price_h
        paste_shadow(img, (cx0, card_y0, cx0 + cell_w, card_y0 + card_h), blur=8, opacity=80, radius=14, offset=(0, 4))
        image_url = card.get("card_image")
        art = download_card_art(image_url, cell_w, card_h) if image_url else None
        if art is None:
            art = placeholder_card(cell_w, card_h, label=str(card.get("rarity", "?")))
        mask = rounded_mask(cell_w, card_h, radius=14)
        img.paste(art, (cx0, card_y0), mask)

        rank = i + 1
        border_color = MEDAL_COLORS.get(rank, DIVIDER_COLOR)
        border_w = 3 if rank in MEDAL_COLORS else 1
        draw.rounded_rectangle(
            [(cx0 - border_w, card_y0 - border_w), (cx0 + cell_w + border_w, card_y0 + card_h + border_w)],
            radius=14, outline=border_color, width=border_w,
        )

        # Rank badge, bottom-right corner. #1-3 keep the medal
        # gold/silver/bronze (plus a thin outline ring so they read clearly
        # distinct at small size); #4-10 use the logo's teal instead of gold.
        is_podium = rank in MEDAL_COLORS
        badge_color = MEDAL_COLORS.get(rank, TEAL)
        badge_text_fill = (20, 14, 8) if is_podium else (8, 26, 30)
        bcx = cx0 + cell_w - rank_r - 6
        bcy = card_y0 + card_h - rank_r - 6
        paste_shadow(img, (bcx - rank_r, bcy - rank_r, bcx + rank_r, bcy + rank_r), blur=5, opacity=100, radius=0, offset=(0, 2), ellipse=True)
        if is_podium:
            ring = MEDAL_RING[rank]
            draw.ellipse([(bcx - rank_r - 2, bcy - rank_r - 2), (bcx + rank_r + 2, bcy + rank_r + 2)], fill=ring)
        draw.ellipse([(bcx - rank_r, bcy - rank_r), (bcx + rank_r, bcy + rank_r)], fill=badge_color)
        rf = font(FONT_BOLD, 18)
        rtxt = f"#{rank}"
        rtw = text_w(draw, rtxt, rf)
        draw.text((bcx - rtw / 2, bcy - rf.size / 1.6), rtxt, font=rf, fill=badge_text_fill)

        # Name + card ID/rarity below the card. One Piece collectors refer
        # to cards by their full set code (e.g. "OP16-098"), number first.
        name_y = card_y0 + card_h + below_gap
        name = clean_card_name(card.get("card_name", "Unknown"))
        name_text, nf = fit_name(draw, name, FONT_MEDIUM, 20, cell_w)
        nw = text_w(draw, name_text, nf)
        draw.text((cx0 + (cell_w - nw) / 2, name_y), name_text, font=nf, fill=WHITE)

        rarity = card.get("rarity") or ""
        card_id = card.get("card_set_id", "")
        sub_text = f"{card_id}  {rarity}" if rarity else card_id
        sub_text, sf = fit_text(draw, sub_text, FONT_REGULAR, 16, cell_w)
        sw = text_w(draw, sub_text, sf)
        draw.text((cx0 + (cell_w - sw) / 2, name_y + name_h - 4), sub_text, font=sf, fill=SUBTLE_TEXT_COLOR)

    # ---- Footer: @handle left in teal, brand logo centered at 3x size,
    # data-source credit + date stamp on the right ----
    draw.line([(pad, divider_y), (W - pad, divider_y)], fill=DIVIDER_COLOR, width=1)

    if brand_name:
        handle_y = footer_content_top + (logo_target_h - ref_font.size) // 2
        draw.text((pad, handle_y), brand_name, font=ref_font, fill=CYAN)

    try:
        brand_logo = Image.open(LOGO_PATH).convert("RGBA")
        bw, bh = brand_logo.size
        brand_logo = brand_logo.resize((int(bw * (logo_target_h / bh)), logo_target_h), Image.LANCZOS)
        blx = (W - brand_logo.width) // 2
        img.paste(brand_logo, (blx, footer_content_top), brand_logo)
    except Exception:
        pass

    stamp = datetime.now(timezone.utc).strftime("%b %-d, %Y")
    credit_text = f"Prices via {data_source}  ·  {stamp}"
    credit_font = font(FONT_LIGHT, 16)
    credit_text, credit_font = fit_text(draw, credit_text, FONT_LIGHT, 16, W - 2 * pad - 260)
    cw = text_w(draw, credit_text, credit_font)
    draw.text((W - pad - cw, footer_content_top + (logo_target_h - credit_font.size) // 2), credit_text, font=credit_font, fill=SUBTLE_TEXT_COLOR)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    dummy_cards = [
        {"card_name": f"Sample Card {i}", "card_set_id": f"OP16-{i:03d}", "rarity": "SR",
         "market_price": 45.0 / i}
        for i in range(1, 11)
    ]
    path = build_list_image(
        dummy_cards, "most_expensive", "Romance Dawn", "../out/preview_op.png",
        brand_name="@cardcovecollectors", n=10, set_id="OP-16",
    )
    print("Wrote", path)
