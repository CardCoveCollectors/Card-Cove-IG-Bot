# Step 1: Connect Instagram to the Meta Graph API (free, no App Review needed)

This only needs to be done once. Because you're only ever going to publish
to *your own* Instagram account (not accounts belonging to other people),
Meta doesn't require the 2-4 week App Review process — apps in
"Development Mode" can publish to any account that has a role (Admin/
Developer/Tester) on the app, which you will by default.

## 1. Confirm your Instagram account is Business/Creator + linked to a Page

- Instagram app → Settings → Account type and tools → make sure it says
  Professional account (Business or Creator).
- Go to [Meta Business Suite](https://business.facebook.com) and confirm
  a Facebook Page is linked to that Instagram account. If you don't have
  a Page yet, Business Suite will walk you through creating one — it's free
  and can be totally bare-bones, it's just required plumbing for the API.

## 2. Create a Meta Developer App

1. Go to [developers.facebook.com](https://developers.facebook.com) and
   log in with the same Facebook account that manages your Page.
2. My Apps → Create App → choose **Business** as the app type.
3. Name it anything (e.g. "YourShop Instagram Bot") and finish creation.

## 3. Add the Instagram product to the app

1. In your new app's dashboard, find **Instagram** in the products list
   (sometimes labeled "Instagram API setup with Instagram login" or
   "Instagram Graph API" — Meta renames this occasionally) and click **Set up**.
2. Follow the prompts to connect your Instagram Business account. You'll
   be asked to log in / authorize — this is you granting your own app
   access to your own account, so it's safe.
3. The setup page will show you two things you need — copy both somewhere
   safe (you'll paste them into GitHub as secrets in the next step, not
   here):
   - **Instagram Business Account ID** (a numeric ID)
   - **Access Token** — use the long-lived option if offered (lasts ~60
     days); if you're only offered a short-lived one, there's a token-exchange
     step documented on the same setup page ("Generate a long-lived token").

## 4. Note the expiry

Long-lived tokens last about 60 days. Put a reminder on your calendar to
come back to this page and regenerate the token before it expires —
refreshing it takes two minutes. (Automating the refresh is possible later
if this becomes annoying — just ask.)

## What you'll hand off to the next step

- `IG_USER_ID` — the numeric Instagram Business Account ID
- `IG_ACCESS_TOKEN` — the long-lived access token

Keep these private — don't paste them into chat. The next step
(SETUP_GITHUB.md) shows you where to enter them securely.
