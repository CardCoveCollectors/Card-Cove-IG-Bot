"""
Renders Card Cove Collectors' branded "TCG News" flash card (1080x1350,
same canvas size and footer treatment as build_image_pokemon.py /
build_image_onepiece.py, for a consistent look across the whole account).

Unlike the pricing posters, there's no card art to lay out — this is a
headline card: a topic pill, a wrapped headline, a source credit line, and
the same brand footer. No AI image generation involved, same $0 approach
as everything else in this repo.

Kept self-contained (doesn't import from build_image_pokemon.py) so this
file can be edited/retired independently, matching how build_image_pokemon
and build_image_onepiece are already independent of each other.
"""
import os
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
FONT_BOLD = os.path.join(FONT_DIR, "Poppins-Bold.ttf")
FONT_MEDIUM = os.path.join(FONT_DIR, "Poppins-Medium.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "Poppins-Regular.ttf")
FONT_LIGHT = os.path.join(FONT_DIR, "Poppins-Light.ttf")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")

W, H = 1080, 1350

# Same brand palette as the pricing posters, so this reads as the same
# account, not a bolted-on feature.
BG_TOP = (28, 15, 52)
BG_BOTTOM = (12, 6, 24)
CYAN = (36, 228, 240)
TEAL = (44, 229, 245)
WHITE = (255, 255, 255)
SUBTLE_TEXT_COLOR = (168, 158, 195)
DIVIDER_COLOR = (52, 38, 82)

# Per-topic accent so a Pokemon story and a One Piece story are visually
# distinct at a glance even with an identical layout.
TOPIC_COLORS = {
    "Pokemon TCG": (255, 205, 0),
    "One Piece Card Game": (235, 64, 52),
}
DEFAULT_ACCENT = (252, 192, 24)


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


def vertical_gradient(width, height, top_color, bottom_color):
    col = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        col.putpixel((0, y), (r, g, b))
    return col.resize((width, height))


def make_shadow(w, h, blur=10, opacity=100, radius=14):
    pad = blur * 3
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], radius=radius, fill=(0, 0, 0, opacity))
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    return canvas, pad


def paste_shadow(base, box, blur=10, opacity=100, radius=14, offset=(0, 5)):
    x0, y0, x1, y1 = box
    shadow, pad = make_shadow(x1 - x0, y1 - y0, blur=blur, opacity=opacity, radius=radius)
    base.alpha_composite(shadow, (x0 - pad + offset[0], y0 - pad + offset[1]))


def _wrap_headline(draw, text, path, start_size, max_width, max_lines=6, min_size=34):
    """Shrinks font size until the headline wraps into at most max_lines
    lines that all fit max_width. Falls back to truncating the last line
    with an ellipsis if even min_size can't make it fit."""
    size = start_size
    while size >= min_size:
        f = font(path, size)
        words = text.split()
        lines, current = [], ""
        for word in words:
            trial = f"{current} {word}".strip()
            if text_w(draw, trial, f) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        if len(lines) <= max_lines:
            return lines, f
        size -= 2

    f = font(path, min_size)
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if text_w(draw, trial, f) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    elif len(lines) >= max_lines:
        last, lf = fit_text(draw, lines[-1], path, min_size, max_width)
        lines[-1] = last
    return lines[:max_lines], f


def build_news_image(item, out_path, brand_name=""):
    """`item` is one of fetch_news.fetch_candidates()'s dicts — needs at
    least "title" and "topic"; "source" is optional."""
    accent = TOPIC_COLORS.get(item["topic"], DEFAULT_ACCENT)

    img = vertical_gradient(W, H, BG_TOP, BG_BOTTOM).convert("RGBA")
    draw = ImageDraw.Draw(img)

    pad = 60

    # ---- "TCG NEWS UPDATE" kicker + topic pill badge ----
    kicker_font = font(FONT_MEDIUM, 26)
    kicker_text = "TCG NEWS UPDATE"
    kicker_y = 80
    draw.text((pad + 2, kicker_y + 2), kicker_text, font=kicker_font, fill=(0, 0, 0, 90))
    draw.text((pad, kicker_y), kicker_text, font=kicker_font, fill=SUBTLE_TEXT_COLOR)

    badge_font = font(FONT_BOLD, 32)
    badge_text = item["topic"].upper()
    btw = text_w(draw, badge_text, badge_font)
    badge_pad_x, badge_pad_y = 26, 14
    badge_w = btw + badge_pad_x * 2
    badge_h = badge_font.size + badge_pad_y * 2
    badge_y = kicker_y + kicker_font.size + 20
    paste_shadow(img, (pad, badge_y, pad + badge_w, badge_y + badge_h), blur=8, opacity=90, radius=badge_h // 2)
    draw.rounded_rectangle([(pad, badge_y), (pad + badge_w, badge_y + badge_h)], radius=badge_h // 2, fill=accent)
    draw.text((pad + badge_pad_x, badge_y + badge_pad_y - 2), badge_text, font=badge_font, fill=(20, 14, 8))

    # ---- Footer geometry (computed up front, same family as the pricing
    # posters) ----
    ref_font = font(FONT_MEDIUM, 24)
    logo_target_h = (ref_font.size + 6) * 3
    bottom_margin = 26
    footer_content_bottom = H - bottom_margin
    footer_content_top = footer_content_bottom - logo_target_h
    divider_y = footer_content_top - 16
    footer_reserve = H - divider_y + 14

    # ---- Headline, wrapped and vertically centered in the space between
    # the badge and the footer ----
    headline_top = badge_y + badge_h + 60
    headline_max_w = W - 2 * pad
    headline_avail_h = H - footer_reserve - headline_top

    lines, hf = _wrap_headline(draw, item["title"], FONT_BOLD, 68, headline_max_w, max_lines=6, min_size=34)
    line_h = int(hf.size * 1.22)
    block_h = line_h * len(lines)
    start_y = headline_top + max(0, (headline_avail_h - block_h - 60) // 2)

    for i, line in enumerate(lines):
        ly = start_y + i * line_h
        draw.text((pad + 2, ly + 2), line, font=hf, fill=(0, 0, 0, 100))
        draw.text((pad, ly), line, font=hf, fill=WHITE)

    # ---- Source credit, just under the headline block ----
    if item.get("source"):
        src_font = font(FONT_REGULAR, 28)
        src_text = f"via {item['source']}"
        src_text, src_font = fit_text(draw, src_text, FONT_REGULAR, 28, headline_max_w)
        draw.text((pad, start_y + block_h + 24), src_text, font=src_font, fill=accent)

    # ---- Footer: same family as the pricing posters (@handle left, brand
    # logo centered, date stamp right) ----
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
    credit_font = font(FONT_LIGHT, 16)
    credit_text, credit_font = fit_text(draw, stamp, FONT_LIGHT, 16, W - 2 * pad - 260)
    cw = text_w(draw, credit_text, credit_font)
    draw.text((W - pad - cw, footer_content_top + (logo_target_h - credit_font.size) // 2), credit_text, font=credit_font, fill=SUBTLE_TEXT_COLOR)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    dummy_item = {
        "topic": "Pokemon TCG",
        "title": "New Pokemon TCG Set Revealed With Reprinted Fan-Favorite Illustration Rares",
        "source": "PokeBeach",
    }
    path = build_news_image(dummy_item, "../out/preview_news.png", brand_name="@yourshophandle")
    print("Wrote", path)
