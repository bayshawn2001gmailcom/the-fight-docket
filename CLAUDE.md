# The Fight Docket — Claude Instructions

These rules govern Claude's behavior in this project.

---

## Image Generation Workflow

All images are generated with **Nano Banana 2** (Gemini 3.1 Flash Image Preview) via `nano_banana_gen.py` locally or `generate_images_action.py` in GitHub Actions. FLUX is a last-resort fallback only if Nano Banana 2 has a catastrophic, unrecoverable failure.

Images are saved to `assets/newsletter_images/` automatically.

---

### Step 1 — Read the Story, Find the Core

Before writing a prompt, identify:
- **The Subject** — what is this story literally about?
- **The Emotion/Tension** — what does the reader *feel* reading it?

The image should capture both. Let the story's specific theme and emotion drive every creative decision.

---

### Step 2 — Build a Creative, Story-Specific Prompt

Reference `ROLES/IMAGE_STYLE_GUIDE.md` for style options, subject-to-visual mapping, and prompt structure. 

Key principles:
- **Vary the style** — don't default to the same look every week. Rotate through cinematic, documentary, abstract, fine art, atmospheric, etc. based on what serves the story.
- **Let the subject range widely** — legal stories, money stories, fight announcements, human interest, regulatory drama all call for different visuals. Use the full creative range.
- **Color follows mood** — warm for human interest/legacy, cold blue for power/legal, high contrast for action, desaturated for corruption/dispute. Don't apply the same palette to every image.
- **Named fighter matchups** — if a section mentions two fighters by name facing each other, generate a standoff/confrontation image using silhouettes, shadow figures, from-behind shots, or two pairs of gloves. No identifiable faces — right-of-publicity legal line, not a style choice.
- **No faces, no logos** — the only two rules that never change.

---

### Step 3 — Generate

**Nano Banana 2 (default):**
```bash
python nano_banana_gen.py "<your prompt here>"
# Optional flags:
#   --aspect-ratio 16:9   (default: 1:1)
#   --resolution 2K       (default: 1K; choices: 512, 1K, 2K, 4K)
#   --image-only          suppress accompanying text output
```
Requires `GEMINI_API_KEY`. Install once: `pip install google-genai pillow`.

**FLUX (catastrophic fallback only):**
```bash
python flux_gen.py "<your prompt here>"
```
Requires `OPENROUTER_API_KEY`.

---

## Notes

- Never generate an image speculatively. Always tie it to a specific article or section.
- Images land in `assets/newsletter_images/`. Review visually before including in any issue.
- For the weekly automated pipeline: prompts are written to `prompts/weekly_prompts.json` by the Cowork task, then GitHub Actions generates the images at Sunday 7:15 PM EDT.

---

## Beehiiv HTML Injection — Clean Posting Workflow

**Root cause of spacing/font bugs:** Injecting raw HTML via `execCommand('insertHTML')` into Beehiiv's ProseMirror editor creates empty block elements:
- Blank lines between `<p>` tags → empty `<p>` nodes
- `<div class="subtitle">` wrappers → orphaned empty `<div>` nodes

**Fix — always pre-process HTML before injecting:**

```bash
# Step 1: Run the pre-processor on the HTML file
python beehiiv_prep.py Fight_Docket_YYYY-MM-DD.html
# Outputs: Fight_Docket_YYYY-MM-DD_clean.html + Fight_Docket_YYYY-MM-DD.inject.js
```

The `.inject.js` file contains the full browser console script with clean HTML already embedded. Copy-paste it into the Beehiiv editor console.

**If injection was already done without pre-processing**, run this cleanup script in the browser console on the editor page:

```javascript
(function() {
  const editor = document.querySelector('.ProseMirror');
  editor.focus();
  let removed = 0;
  Array.from(editor.querySelectorAll('p')).forEach(p => {
    if (p.textContent.trim() === '') { p.remove(); removed++; }
  });
  Array.from(editor.querySelectorAll('div')).forEach(d => {
    if (d.className === '' && d.textContent.trim() === '' && !d.querySelector('img')) {
      d.remove(); removed++;
    }
  });
  editor.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true }));
  console.log('Removed ' + removed + ' empty elements. Check for Synced status.');
})();
```

Wait for "Synced" status to confirm autosave.

---

## Social Media Accounts (set up April 21, 2026)

### Instagram — @thefightdocket
- Profile photo: `fight_docket_logo.png` (black/red/gold BigShoulders-Bold design)
- Bio: "🥊 Boxing & MMA news, fight breakdowns & the stories behind the sport / 📰 Weekly newsletter — subscribe below"
- Account type: Personal (linked alongside @atlantaturfdoctor and personal account)

### Facebook — The Fight Docket Page
- URL: https://www.facebook.com/profile.php?id=61567987746089
- Category: Sports & recreation
- Cover photo: `fight_docket_fb_cover.png` (text in top 42%, red design fills bottom half — avoids profile circle overlap)
- Profile photo: `fight_docket_logo.png`
- Bio: "Boxing & MMA news, fight breakdowns & the stories behind the sport. Weekly newsletter — subscribe at thefightdocket.com"

---

## Instagram Content Automation

### Brand assets
- Logo: `fight_docket_logo.png` (1080x1080, also used as FB profile photo)
- FB Cover: `fight_docket_fb_cover.png` (1640x624, text in top 42% only)
- Brand colors: Black `#0A0A0A`, Red `#C8102E`, Gold `#C9A84C`, White `#F0EDE8`
- Fonts: BigShoulders-Bold (headlines), InstrumentSans (body/tags), Lora-Bold (quotes)

### Content pipeline
- Templates: `ig_templates.py` — 4 functions: `newsletter_preview()`, `fight_announcement()`, `fight_result()`, `quote_card()`
- Generator: `generate_weekly_ig.py` — edit the `WEEK = {}` block each issue, then run to produce all 4 graphics
- Output folder: `instagram_content/` — PNGs + captions txt file per issue
- Scheduled task: **fight-docket-ig-content-reminder** — runs every Monday 9am, auto-reads newsletter, updates generator, produces graphics + captions

### Weekly posting schedule
| Day | Post type |
|-----|-----------|
| Monday | Newsletter Preview (new issue announcement) |
| Tuesday | Fight Result (weekend recap) |
| Thursday | Fight Announcement (upcoming card hype) |
| Saturday | Quote Card (engagement post before fight night) |

### To generate content manually
```bash
# 1. Edit the WEEK = {} block in generate_weekly_ig.py with this issue's data
# 2. Run:
python "The fight Docket/generate_weekly_ig.py"
# 3. Review PNGs in instagram_content/
# 4. Use captions from [issue]_captions.txt
```

---

## Full Automation Pipeline (as of May 2, 2026)

**Account credentials:**
- Instagram: `thefightdocket@gmail.com` / `@thefightdocket`
- Twitter/X: `@thefightdocket`
- GitHub repo: https://github.com/bayshawn2001gmailcom/the-fight-docket

**Weekly automation schedule:**
| Day/Time | Workflow | Script |
|----------|----------|--------|
| Fri 6pm EDT | `friday-crawl-fights.yml` | `upcoming_fights_crawler.py` → upcoming_fights.json |
| Fri 9pm/11pm/12:30am EDT | `friday-night-results.yml` | `post_live_result.py` → live tweets + IG cards (deduped) |
| Sat 9pm/11pm EDT | `saturday-night-results.yml` | `post_live_result.py` → live tweets + IG cards (deduped) |
| Sun 1–4am EDT | `sunday-post-results.yml` | `post_fight_results.py` → full result recap image + Instagram |
| Sun 7:15pm EDT | `generate_images.yml` | `generate_images_action.py` → newsletter images from prompts |
| Mon 8am EDT | `newsletter_pipeline.yml` | `newsletter_generator.py` → newsletter HTML (covers weekend results) |
| Mon 10am EDT | `twitter_thread.yml` | `post_twitter_thread.py` → 6-tweet thread to @thefightdocket |
| Mon 11am EDT | `weekly_ig_content.yml` | `ig_content_generator.py` → 4 IG graphics + captions |

**Key scripts:**
- `newsletter_generator.py` — Firecrawl + Gemini full newsletter automation
- `ig_content_generator.py` — auto-generates 4 IG graphics from weekly_ig_data.json
- `post_twitter_thread.py` — Gemini writes + tweepy posts thread to @thefightdocket
- `post_live_result.py` — Friday/Saturday night live results: crawl → dedup → tweet → IG card
- `post_fight_results.py` — Sunday recap: crawls results, generates image, posts to Instagram
- `upcoming_fights_crawler.py` — Friday pre-crawl via Firecrawl
- `beehiiv_prep.py` — pre-processes newsletter HTML for clean Beehiiv injection
- `generate_weekly_ig.py` — manual fallback for IG content (edit WEEK block)

**Deduplication:** `posted_results.json` tracks every result posted live so re-runs don't double-post.

**GitHub Secrets set:**
`GEMINI_API_KEY`, `FIRECRAWL_API_KEY`, `INSTAGRAM_USERNAME`, `INSTAGRAM_PASSWORD`,
`TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`,
`TWITTER_BEARER_TOKEN`, `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`

**Instagram note:** instagrapi with session persistence is implemented but may still be blocked
from GitHub Actions IPs. Images + captions always committed to `instagram_content/` for manual backup posting.

---

## Google Cloud — SEO Tool (added May 4, 2026)

We now have **Google Cloud** available as a tool to increase SEO for **fastrakmobilelab.com** and other projects.

- Use Google Cloud services (e.g., Cloud Run, Cloud Functions, BigQuery, Vertex AI) to build and automate SEO workflows.
- Google Search Console data can be pulled programmatically via the Google Search Console API (authenticated through Google Cloud service accounts).
- Potential use cases: automated keyword tracking, crawl analysis, content gap identification, structured data generation, and search performance dashboards.
- Credentials/service account keys should be stored as GitHub Secrets and never committed to the repo.
