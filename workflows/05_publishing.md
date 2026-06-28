# Workflow 05: Publishing to Beehiiv

## Objective
Render the final newsletter HTML and post it to Beehiiv, scheduled for Monday noon EDT.

## Trigger
Monday morning after image generation and asset upload are complete.

## Required Inputs
- `newsletter_draft_YYYY-MM-DD.json` in `.tmp/`
- `asset_urls_YYYY-MM-DD.json` in `.tmp/` (or newsletter renders without images)
- `BEEHIIV_API_KEY` and `BEEHIIV_PUBLICATION_ID` in `~/.env`
- `IMGBB_API_KEY` in `~/.env` (for thumbnail upload)

## Full Publishing Pipeline (run in order)

### Step 1 — Generate Images (Sunday evening, ~7pm EDT)
```
python tools/image_generator.py
```
Generates 7 Nano Banana section images → `.tmp/newsletter_images/nb2_*.jpg`

### Step 2 — Upload to ImgBB (immediately after Step 1)
```
python tools/asset_uploader.py
```
Uploads all images → saves `.tmp/asset_urls_YYYY-MM-DD.json`

### Step 3 — Render HTML (Monday morning)
```
python tools/html_renderer.py
```
Reads draft JSON + asset URLs → produces `newsletter_YYYY-MM-DD.html`

### Step 4 — Verify HTML
Open `newsletter_YYYY-MM-DD.html` in a browser and check:
- All 7 sections present
- Images display correctly (or gracefully absent if upload failed)
- No placeholder text like "[HEADLINE]" or "story 1 under 80 chars"
- Voice is consistent — no tonal gaps between sections
- Legal tracker has real case numbers (not just generic placeholder)
- Rumor mill has confidence ratings in the correct format

### Step 5 — Post to Beehiiv
```
python tools/beehiiv_post.py --draft-only
```
Tries the API first. If the API returns 403 (free plan restriction), automatically falls back to `tools/beehiiv_browser_post.py` using Playwright.

**Requires for browser fallback (in `~/.env`):**
```
BEEHIIV_EMAIL=your_login_email
BEEHIIV_PASSWORD=your_login_password
```

**Full auto-schedule (after you've verified the pipeline):**
```
python tools/beehiiv_post.py
```

### Step 6 — Verify via Beehiiv MCP
After posting, confirm the draft was created:
```
mcp__claude_ai_Beehiiv_MCP__list_posts(publication_id=PUBLICATION_ID, status="draft")
```
Check that the correct title and thumbnail appear.

### Step 7 — Archive HTML to Google Drive (optional)
```
mcp__claude_ai_Google_Drive__create_file → newsletter_YYYY-MM-DD.html
```

## API vs. Browser Automation

`beehiiv_post.py` handles the decision automatically:
```
API call → success → Done (scheduled via API)
         → 403 enterprise error → auto-launches beehiiv_browser_post.py
```

Browser automation saves a session to `.beehiiv_session.json` — subsequent runs reuse it without re-logging in.

**Long-term:** Upgrading to Beehiiv Creator ($42/month) unlocks full API, removes the browser fallback dependency, and enables A/B subject line testing and automation rules. See Phase 4 in the main plan.

## Subject Line Selection
The subject line is auto-built from `ig_data.preview_stories[0]`:
```
The Fight Docket | [first preview story, max 60 chars]
```

For better open rates, manually override before posting:
- **Specific over vague:** "Dana White Ordered to Produce Fighter Pay Records" beats "This Week in MMA"
- **Named people and amounts:** Readers click on names and dollar figures
- **No clickbait:** We don't do "You Won't Believe..." — this is a business intelligence newsletter

To override: edit `preview_stories[0]` in `.tmp/weekly_ig_data_YYYY-MM-DD.json` before running `beehiiv_post.py`.

## Retry Logic
If a previous post attempt failed (`.tmp/post_status.json` shows `"posted": false`):
- Run `python tools/beehiiv_post.py` again
- Script detects the failed attempt and sends immediately (not scheduled for noon)
- To reset and start fresh: delete `.tmp/post_status.json`

## Thumbnail
`beehiiv_post.py` automatically uses the first URL from `asset_urls_YYYY-MM-DD.json` as the thumbnail.
If no asset URLs exist, it tries to upload the first local image from `.tmp/newsletter_images/`.
If no images exist, thumbnail is omitted (Beehiiv uses a default).

## Schedule Timing
- Target: Monday noon EDT (16:00 UTC during EDT, 17:00 UTC during EST)
- The script calculates this dynamically based on current time
- If you run the script after noon on Monday, it sends immediately (+5 minutes)
- For a specific send time, edit `send_time_edt()` in `tools/beehiiv_post.py`

## Post-Publish Checklist
After publishing:
1. Check your Beehiiv dashboard confirms the post is scheduled
2. Run `tools/ig_graphics.py` to generate the 4 Instagram cards
3. Run `post_twitter_thread.py` from `../the-fight-docket/` (Monday 10am EDT)
4. Post Instagram cards manually (Monday/Tuesday/Thursday/Saturday)
5. Record story subjects in content history: `python tools/content_history.py`

## Status Tracking
`.tmp/post_status.json` tracks the current post state:
```json
{
  "posted": true,
  "newsletter_file": "newsletter_2026-05-12.html",
  "post_id": "post_abc123",
  "posted_at": "2026-05-12T11:59:00+00:00"
}
```

If `posted` is false and `newsletter_file` is set, the next run of `beehiiv_post.py` will retry that specific newsletter with an immediate send.
