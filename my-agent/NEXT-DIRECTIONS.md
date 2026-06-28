# Fight Night Watchdog — Next Directions

## v1 — Exact brand-matched result cards
**What:** Generate cards identical to the existing Fight Docket style using Pillow + custom fonts, instead of Gemini-generated images.
**Why:** Gemini images won't exactly match the brand typography and layout used in the existing cards. v0 Gemini images are good enough to ship; brand parity comes next.
**How:** In the environment, download brand fonts from the GitHub repo at startup:
```bash
curl -sL "https://raw.githubusercontent.com/bayshawn2001gmailcom/the-fight-docket/main/canvas-fonts/BigShoulders-Bold.ttf" -o /tmp/BigShoulders-Bold.ttf
```
Then use `ig_templates.py`-style Pillow code to draw the card. Add `Pillow` to environment packages (already included). Ref: `the-fight-docket/ig_templates.py`.

## v2 — Breaking news throughout the week (not just fight nights)
**What:** A second deployment that monitors for non-fight-result breaking news: title shot announcements, fighter signings, contract disputes, retirement announcements.
**Why:** Currently the agent only activates on fight nights. Major signings and announcements happen Monday–Thursday and get no immediate social coverage.
**How:** Separate scheduled deployment: `0 */3 * * 1-5` (every 3 hours, Mon–Fri). Agent searches for breaking news, filters out anything already posted (via same Memory store), generates an announcement card, posts to all platforms. Shares the fight-docket-social-vault credentials with v0.

## v3 — TikTok video posting
**What:** After a fight result, generate a short video (8–15 seconds) with the result graphic and post to TikTok.
**Why:** TikTok's Content Posting API requires video content — static images aren't supported. This needs a video generation pipeline.
**How:** Use Gemini video generation (when available) or ffmpeg to animate the result card (Ken Burns effect / transition). TikTok Content Posting API: `open_api.tiktok.com/v2/post/publish/video/init/`. Requires TikTok Developer App with `video.publish` scope and business account verification.
**Note:** TikTok API access requires a separate approval process from Meta — apply at developers.tiktok.com.

## Always — Re-run evals before promoting any new agent version
Run `evals/run-evals.sh` against the new version before updating the deployment. Promote only when all eval verdicts hold.
