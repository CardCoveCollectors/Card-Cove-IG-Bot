# Step 2: Put this project on GitHub and schedule it

GitHub Actions is the free scheduler that actually runs the pipeline —
Mon/Wed/Fri, no server or subscription required. This is also where the
generated images get hosted (Instagram's API requires images to be at a
public URL, and a public GitHub repo gives you that for free).

## 1. Create the repo

1. If you don't have a GitHub account, sign up free at
   [github.com](https://github.com).
2. Click **New repository**. Name it something like `tcg-instagram-bot`.
   Set it to **Public** (needed so the raw image URLs are reachable without
   auth — there's nothing sensitive in the repo itself; your token lives in
   Secrets, never in the code).
3. Don't add a README/gitignore in the creation wizard — we already have files.

## 2. Push this folder to it

First, delete anything already inside the `posts/` folder — those are just
leftover test renders from our design session, not meant to ship.

Then, from this project folder, run (in a terminal, e.g. VS Code's terminal
or Terminal/PowerShell):

```
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tcg-instagram-bot.git
git push -u origin main
```

(Replace `YOUR_USERNAME` and the repo name with your actual values — GitHub
shows you this exact command block on the empty repo's page too.)

## 3. Edit your brand details

Open `scripts/config.py` in this folder and confirm `BRAND_NAME` and
`BRAND_HANDLE` are correct, then commit and push if you change anything.

## 4. See a finished post — no Instagram credentials needed yet

There's a second, safe workflow just for this: `.github/workflows/preview.yml`.
It builds one real post (real card art, real set logo, live prices) and
hands you the image as a download — it never touches Instagram.

1. On GitHub, go to the **Actions** tab → **Generate Preview Post (no
   Instagram)** → **Run workflow** button → Run.
2. Wait ~30-60 seconds, then open the finished run → scroll to **Artifacts**
   → download `preview-post` → unzip it to see the actual PNG and caption
   (`latest.json`).
3. Run it again any time — each run advances the rotation by one step
   (next set / most-vs-least-expensive) but only inside that run, nothing
   is committed back, so it won't disturb the real schedule later.

## 5. When you're ready to actually go live

Only then do you need SETUP_META.md (the Instagram/Meta side). Once you
have `IG_USER_ID` and `IG_ACCESS_TOKEN`:

1. In the repo: **Settings → Secrets and variables → Actions → New
   repository secret**. Add:

   | Name | Value |
   |---|---|
   | `IG_USER_ID` | The numeric Instagram Business Account ID from SETUP_META.md |
   | `IG_ACCESS_TOKEN` | The long-lived access token from SETUP_META.md |
   | `POKEMONTCG_API_KEY` | Optional — a free key from [pokemontcg.io](https://pokemontcg.io) if you want higher rate limits. Fine to skip at this posting volume. |

2. On GitHub, go to the **Actions** tab → **Post to Instagram** workflow →
   **Run workflow** → Run. This one *does* publish — only do this when
   you're actually ready for a live post.
3. Check your Instagram account — the post should appear.

## 6. Let it run on schedule

Once step 5 works, you're done — it'll fire automatically Mon/Wed/Fri per
`.github/workflows/post.yml`. Edit the `cron` line in that file (and push
the change) any time you want a different schedule.
