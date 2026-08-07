# Card Cove Collectors — TCG Instagram Auto-Poster

Fully automated Instagram content for @cardcovecollectors — card pricing
countdown posts styled after accounts like gorilla.tcg, plus TCG news
updates — with $0 in ongoing subscription costs.

## Pipelines at a glance

Every pipeline below is fully independent (its own fetch/build/caption/
publish scripts and its own GitHub Actions workflow) and shares only the
generic plumbing described in "Shared files" further down. This table is
the one place to look to see everything the account is doing — update it
whenever a pipeline is added, retired, or rescheduled.

| Pipeline | Schedule (Eastern) | Data source | File prefix | Status |
|---|---|---|---|---|
| English Pokemon | Mon/Wed/Fri ~6pm | [pokemontcg.io](https://pokemontcg.io) | `*_pokemon.py` | Live |
| English One Piece | Tue/Thu/Sat ~7pm | [optcgapi.com](https://optcgapi.com) | `*_onepiece.py` | Live |
| Japanese Pokemon | Tue/Thu/Sat ~10am | [PokeWallet API](https://pokewallet.io) | `*_pokemon_jp.py` | Live |
| Japanese One Piece | — | BerryWallet API | `*_onepiece_jp.py` | Tabled — pricing data proved unreliable (variant/reprint collisions in the free tier's TCGPlayer matching). Revisit if a better JP OPTCG price source shows up. |
| Pokemon News | Daily ~8:43am, only when something new is found | Google News RSS search (aggregates PokeBeach, Serebii, PokeGuardian, official coverage, etc.) | `*_news_pokemon.py` | In progress |
| One Piece News | Daily ~8:51am, only when something new is found | Google News RSS search (same approach as Pokemon News) | `*_news_onepiece.py` | In progress |
| Character Spotlight (Pokemon + One Piece) | — | Curated AI-generated character art (manually reviewed) + real card price data | `*_spotlight.py` (planned) | In design — hero art pool being generated/reviewed, pipeline not yet built |

## How the pricing pipelines work

Every scheduled run:

1. Picks the next set from that pipeline's rotation file (e.g.
   `scripts/config_pokemon.py`), and builds BOTH the most-expensive and
   cheapest lists for it together, as a pair.
2. Pulls every card in that set and its live market price from that
   pipeline's API (see table above).
3. Renders a branded countdown poster image with that pipeline's
   `build_image_*.py` (Pillow — no paid image-generation API).
4. Writes a caption in the style of countdown-format TCG accounts with
   that pipeline's `caption_*.py` (template-based — no LLM API cost).

   English One Piece only: the poster also gets a small rotating
   character-art "flag" in the top-left corner (see `assets/character_art/`
   and `character_rotation.py`), so a post reads as One Piece content at a
   glance. It's a manually-curated pool you add images to yourself — every
   image gets used once before any repeat, and the expensive/cheapest pair
   always uses two different characters. No other pipeline has this.
5. Commits the image to this repo (so it has a public URL) and publishes
   it to Instagram via the Instagram Platform API.

## How the news pipelines work (in progress)

Pokemon News and One Piece News are two fully independent daily pipelines
(own feed, own dedup memory, own schedule) so one franchise's news volume
never crowds out the other's coverage:

1. Pulls headlines from a Google News RSS search for that franchise —
   this aggregates coverage from PokeBeach, Serebii, PokeGuardian, and
   official announcements as reported by outlets, without depending on
   any single site's own feed (several block direct scraping with bot
   protection; Google's own feed infrastructure doesn't).
2. Filters for newsworthy keywords (new set announcements, reprints,
   bans/restrictions, errata, etc.) and skips anything already posted
   (tracked in that pipeline's own state file).
3. If nothing new is found, the run exits cleanly with no post — it never
   forces a post just to hit a schedule.
4. If something new is found, renders a templated graphic + caption (same
   $0 approach as the pricing posts, no LLM cost) and publishes it.

Everything runs on GitHub Actions' free tier — no server, no n8n, no
Buffer/Ayrshare subscription.

## Character Spotlight pipeline (in design)

A "Top 10 [Character] Cards" carousel format, inspired by accounts like
@win.the.card. Not live yet — currently in the design/content-prep stage:

1. **Hero art** is AI-generated (pollinations.ai, free, no API key) rather
   than fully automated per-post, because free general-purpose image
   models are unreliable without review (wrong art style, malformed
   hands, generic look instead of the actual character). Run the
   **Generate Character Art Pool** workflow manually whenever you want a
   fresh batch to review; it never posts or commits anything on its own.
2. You review the batch, keep the good ones, and add approved images to
   `assets/character_art/` yourself.
3. Once there's an approved pool, the real pipeline (still to be built)
   will pull real card price data the same way the pricing pipelines do,
   and rotate through the approved art pool for each post's cover image.

## One-time setup

Do these in order:

1. **SETUP_GITHUB.md** — push this repo to GitHub, then run the
   **Generate Preview Post** workflow for a pipeline to see a real,
   finished post (real card art, real set logo/source, live data) with
   zero Instagram involvement.
2. **SETUP_META.md** — only once you're happy with the preview: connect
   your Instagram Business account via the Instagram API with Instagram
   Login (free, no App Review needed for your own account), then go live
   per the last section of SETUP_GITHUB.md.

## Ongoing costs

$0. The only thing to maintain is regenerating the Instagram access token
roughly every 60 days (2-minute task, covered in SETUP_META.md — a
scheduled reminder is already set up for this).

## Customizing

- `scripts/config_*.py` — which sets/feeds get featured, how many
  cards per post, your brand name/handle.
- `scripts/build_image_*.py` — colors, fonts, layout of the poster.
- `scripts/caption_*.py` — hooks/closers/hashtags used in captions.
- `.github/workflows/post_*.yml` — posting schedules.

## Folder structure

Every pipeline-specific file is named with that pipeline's suffix (see
the table at the top). A handful of files are genuinely shared and
game-agnostic — those are called out below.

```
scripts/
  config_pokemon.py           - English Pokemon settings
  fetch_prices_pokemon.py     - pulls Pokemon card + price data (pokemontcg.io)
  build_image_pokemon.py      - renders the Pokemon poster image (shared by EN + JP Pokemon)
  caption_pokemon.py          - writes the English Pokemon caption
  main_pokemon.py             - ties the English Pokemon pipeline together (build / publish)

  config_onepiece.py          - English One Piece settings
  fetch_prices_onepiece.py    - pulls One Piece card + price data (optcgapi.com)
  build_image_onepiece.py     - renders the One Piece poster image, including the
                                 rotating character-art corner flag (English One Piece
                                 only — no other pipeline has this)
  character_rotation.py       - shuffle-bag picker for assets/character_art/: hands out
                                 2 distinct images per run so the expensive/cheapest pair
                                 never shares a character, and no image repeats until the
                                 whole pool has had a turn. English One Piece only.
  caption_onepiece.py         - writes the One Piece caption
  main_onepiece.py            - ties the English One Piece pipeline together (build / publish)

  config_pokemon_jp.py        - Japanese Pokemon settings (no static set list — rotates every JP set)
  fetch_prices_pokemon_jp.py  - pulls JP Pokemon card + price data (PokeWallet API)
  caption_pokemon_jp.py       - writes the Japanese Pokemon caption (Art Rare / Special Art Rare wording)
  main_pokemon_jp.py          - ties the Japanese Pokemon pipeline together (build / publish)

  config_news_pokemon.py      - Pokemon News feed, keywords, brand info
  fetch_news_pokemon.py       - pulls + filters + dedups Pokemon TCG news headlines
  main_news_pokemon.py        - ties the Pokemon News pipeline together (build / publish)

  config_news_onepiece.py     - One Piece News feed, keywords, brand info
  fetch_news_onepiece.py      - pulls + filters + dedups One Piece Card Game news headlines
  main_news_onepiece.py       - ties the One Piece News pipeline together (build / publish)

  rotation.py                 - SHARED: tracks which set is next, for any pricing pipeline
  publish_instagram.py        - SHARED: posts to Instagram via the Instagram Platform API
                                 (Instagram API with Instagram Login — same account/secrets
                                 for every pipeline)
  build_image_news.py         - SHARED: renders the news graphic for either news pipeline
                                 (genuinely game-agnostic — takes a topic label + accent
                                 color, doesn't know or care which franchise it's for)
  caption_news.py             - SHARED: writes the news caption for either news pipeline

  generate_character_art_pool.py - MANUAL/ONE-OFF: batch-generates candidate AI character
                                 art for the (not-yet-built) Character Spotlight pipeline,
                                 for human review. Not part of daily posting.

assets/fonts/                 - bundled fonts used by every build_image_*.py file
assets/logo.png                - your brand logo, composited onto every post
assets/character_art/         - approved One Piece character cutouts (transparent PNGs,
                                 downscaled to fit their small display size) that the
                                 English One Piece pricing pipeline rotates through as a
                                 corner-flag graphic. Not used by any other pipeline.

.github/workflows/
  post_pokemon.yml            - live English Pokemon schedule (Mon/Wed/Fri ~6pm ET)
  preview_pokemon.yml         - manual, safe English Pokemon test run (no IG)
  post_onepiece.yml           - live English One Piece schedule (Tue/Thu/Sat ~7pm ET)
  preview_onepiece.yml        - manual, safe English One Piece test run (no IG)
  post_pokemon_jp.yml         - live Japanese Pokemon schedule (Tue/Thu/Sat ~10am ET)
  preview_pokemon_jp.yml      - manual, safe Japanese Pokemon test run (no IG)
  post_news_pokemon.yml       - live Pokemon News schedule (daily ~8:43am ET, only if something's new)
  preview_news_pokemon.yml    - manual, safe Pokemon News test run (no IG)
  post_news_onepiece.yml      - live One Piece News schedule (daily ~8:51am ET, only if something's new)
  preview_news_onepiece.yml   - manual, safe One Piece News test run (no IG)
  generate_character_art_pool.yml - manual: batch-generates candidate AI character art for review (no IG, no auto-commit)

state_pokemon.json            - English Pokemon rotation memory (auto-updated by each run)
state_onepiece.json           - English One Piece rotation memory (auto-updated by each run)
state_onepiece_charart.json   - English One Piece character-art shuffle-bag memory (auto-updated)
state_pokemon_jp.json         - Japanese Pokemon rotation memory (auto-updated by each run)
state_news_pokemon.json       - Pokemon News dedup memory: which stories have already been posted
state_news_onepiece.json      - One Piece News dedup memory: which stories have already been posted
posts/                        - generated images land here (auto-created)
```
