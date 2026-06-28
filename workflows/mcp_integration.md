# Workflow: MCP Tool Integration

## Overview

MCP (Model Context Protocol) tools run inside Claude's conversation context — they can't be called from Python scripts or GitHub Actions. The pattern is:

- **Python scripts** handle deterministic, scheduled, or headless work
- **MCP tools** handle interactive sessions, verification, research, and integrations that benefit from real-time judgment

This document maps every available MCP tool to its role in the Fight Docket pipeline.

---

## Active Integrations

### Beehiiv MCP — Verification and Analytics

**Available tools:** `get_publication`, `list_posts`, `get_post`, `get_post_stats`, `get_publication_stats`, `list_subscriptions`

**When to use:**
- After `beehiiv_post.py` or `beehiiv_browser_post.py` runs → call `list_posts` (status: draft) to confirm the post was created
- Weekly: call `get_publication_stats` to check subscriber growth
- Before posting: call `list_posts` to verify no duplicate drafts exist

**Example agent step:**
```
After beehiiv_post.py completes:
→ mcp__claude_ai_Beehiiv_MCP__list_posts(publication_id=PUBLICATION_ID, status="draft")
→ Confirm the new draft appears with correct title and thumbnail
```

**Does NOT replace:** `beehiiv_post.py` or `beehiiv_browser_post.py` — post creation is not available on free plan

---

### Firecrawl MCP — Research and Deep Dives

**Available tools:** `firecrawl_scrape`, `firecrawl_search`, `firecrawl_crawl`, `firecrawl_extract`, `firecrawl_agent`

**When to use (Phase 2+):**
- In `research_crawl.py` — when building the targeted deep-research step, call `firecrawl_scrape` on the 3-4 source URLs identified by Perplexity, then pass the extracted text to Gemini
- Ad-hoc research: when you need to read a specific fight contract, legal filing, or news article mid-session
- Court filing research: scrape CourtListener case pages before writing the Legal Tracker section

**Replaces:** The 9-homepage Firecrawl REST calls in `newsletter_draft.py` (Phase 2 only — current Phase 1 pipeline uses REST)

**Phase 2 integration point in `research_crawl.py`:**
```python
# Instead of: requests.post("https://api.firecrawl.dev/v1/scrape", ...)
# Claude as agent calls: mcp__claude_ai_Firecrawl__firecrawl_scrape(url=target_url)
# Then passes result directly to build_draft()
```

---

### Google Drive MCP — Newsletter Archive

**Available tools:** `create_file`, `read_file_content`, `search_files`, `list_recent_files`, `get_file_metadata`

**When to use:**
- After `html_renderer.py` runs → upload `newsletter_YYYY-MM-DD.html` to Google Drive for backup and team review
- When reviewing past issues for content history (instead of reading local `.tmp/` files)
- Store brand assets, templates, and editorial calendar

**Agent step (after each issue):**
```
→ mcp__claude_ai_Google_Drive__create_file(
    name="newsletter_2026-05-08.html",
    content=<html content>,
    folder="Fight Docket / Issues"
  )
```

---

### Canva MCP — Instagram Card Generation (Phase 2 Evaluation)

**Available tools:** `generate-design`, `generate-design-structured`, `list-brand-kits`, `export-design`

**When to use (evaluate vs. Pillow/ig_graphics.py):**
- Test: generate one of the 4 weekly Instagram cards via Canva MCP and compare quality/brand consistency vs. the Pillow-rendered version
- If Canva output is better: replace `ig_graphics.py` with Canva MCP calls for the card generation step
- Canva brand kit can lock in exact brand colors and fonts, eliminating manual color code maintenance

**Current status:** Evaluate after Phase 2. Run `ig_graphics.py` for now.

---

### Gmail MCP — Tip Monitoring

**Available tools:** `search_threads`, `get_thread`, `list_labels`

**When to use (Phase 3):**
- At the start of the research step: search for new emails to tips@thefightdocket.com (if Gmail is connected to that address)
- Flag any sourced tips with named fighters/events for inclusion in Rumor Mill
- Create a label "fight-docket-tips" for organization

---

### Google Calendar MCP — Fight Schedule

**Available tools:** `list_events`, `create_event`, `get_event`

**When to use (Phase 2):**
- Pull scheduled UFC/boxing events from a shared fight calendar
- Cross-reference against `fight_odds.json` to ensure all upcoming fights are covered
- Create calendar reminders for pipeline runs (Friday research, Monday publish)

---

### Ahrefs MCP — SEO Tracking (Phase 4)

**Available tools:** `site-explorer-organic-keywords`, `site-explorer-metrics`, `gsc-keywords`, `web-analytics-stats`

**When to use:**
- Monthly: pull organic keyword data for thefightdocket.com to see which newsletter topics drive search traffic
- Identify high-volume fight-related keywords to bias story selection toward SEO-valuable topics

---

### Cloudflare MCP — Static Preview Hosting (Optional)

**Available tools:** `kv_namespace_create`, `workers_list`, `r2_bucket_create`

**When to use:**
- Deploy `newsletter_YYYY-MM-DD.html` to Cloudflare Pages for shareable preview URLs
- Allows team to review newsletter on mobile before posting to Beehiiv
- R2 as alternative image hosting (instead of ImgBB)

---

## Pipeline Map: Python Scripts vs. MCP Tools

| Step | Primary | MCP Layer |
|------|---------|-----------|
| Story discovery (Phase 2) | `research_crawl.py` | Firecrawl MCP for targeted article scrapes |
| Draft generation | `newsletter_draft.py` | — |
| Image generation | `image_generator.py` | — |
| Image upload | `asset_uploader.py` | — |
| HTML render | `html_renderer.py` | — |
| HTML archive | — | Google Drive MCP → upload to Drive |
| Post to Beehiiv | `beehiiv_post.py` → `beehiiv_browser_post.py` fallback | Beehiiv MCP → verify draft created |
| Instagram cards | `ig_graphics.py` | Canva MCP (evaluate Phase 2) |
| Analytics review | — | Beehiiv MCP → publication/post stats |
| Tip monitoring (Phase 3) | — | Gmail MCP |
| Fight schedule (Phase 2) | — | Google Calendar MCP |

---

## Agent Session Checklist

When running a publishing session interactively (not automated), use this MCP checklist:

**Before draft generation:**
- [ ] `mcp__claude_ai_Beehiiv_MCP__list_posts` → confirm no leftover drafts from last week

**After beehiiv_post.py:**
- [ ] `mcp__claude_ai_Beehiiv_MCP__list_posts` (status: draft) → confirm post created with correct title
- [ ] `mcp__claude_ai_Google_Drive__create_file` → archive newsletter HTML

**Weekly (Monday afternoon):**
- [ ] `mcp__claude_ai_Beehiiv_MCP__get_publication_stats` → log subscriber count + growth

---

## Adding New MCP Tools

When a new MCP server becomes available:
1. Test it with one real query in a conversation
2. Identify which pipeline step it improves or replaces
3. Add an entry to this document under its section
4. Update the Pipeline Map table
5. If it replaces a Python script, mark that script for deprecation in `tools/`
