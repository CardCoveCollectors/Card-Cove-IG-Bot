# TCG Instagram Auto-Poster

Fully automated "Top 10 Most/Least Expensive Cards" posts, styled after
accounts like gorilla.tcg, posted 3x/week with $0 in ongoing subscription
costs.

## How it works

Every scheduled run:

1. Picks the next set + list type (most expensive / least expensive) from
   the rotation in `scripts/config.py`.
2. Pulls every card in that set and its live market price from the free
   [pokemontcg.io](https://pokemontcg.io) API.
3. Renders a branded countdown poster image with `scripts/build_image.py`
   (Pillow — no paid image-generation API).
4. Writes a caption in the style of countdown-format TCG accounts with
   `scripts/caption.py` (template-based — no LLM API cost).
5. Commits the image to this repo (so it has a public URL) and publishes
   it to Instagram via the Meta Graph API.

Everything runs on GitHub Actions' free tier — no server, no n8n, no
Buffer/Ayrshare subscription.

## One-time setup

Do these in order:

1. **SETUP_GITHUB.md** — push this repo to GitHub, then run the
   **Generate Preview Post** workflow to see a real, finished post (real
   card art, real set logo, live prices) with zero Instagram involvement.
2. **SETUP_META.md** — only once you're happy with the preview: connect
   your Instagram Business account to the Meta Graph API (free, no App
   Review needed for your own account), then go live per the last section
   of SETUP_GITHUB.md.

## Ongoing costs

$0. The only thing to maintain is regenerating the Instagram access token
roughly every 60 days (2-minute task, covered in SETUP_META.md).

## Customizing

- `scripts/config.py` — which sets get featured, how many cards per post,
  your brand name/handle.
- `scripts/build_image.py` — colors, fonts, layout of the poster.
- `scripts/caption.py` — hooks/closers/hashtags used in captions.
- `.github/workflows/post.yml` — posting schedule (currently Mon/Wed/Fri
  18:00 UTC).

## Folder structure

```
scripts/
  config.py            - your settings (edit this first)
  fetch_prices.py       - pulls card + price data
  build_image.py        - renders the poster image
  caption.py             - writes the caption
  rotation.py            - tracks which set/list-type is next
  publish_instagram.py   - posts to Instagram via the Graph API
  main.py                - ties it all together (build / publish)
assets/fonts/            - bundled fonts used by build_image.py
assets/logo.png            - your brand logo, composited onto every post
.github/workflows/post.yml    - the live posting schedule (publishes to IG)
.github/workflows/preview.yml - manual, safe test run (no IG, artifact download only)
state.json                - rotation memory (auto-updated by each run)
posts/                     - generated images land here (auto-created)
```
