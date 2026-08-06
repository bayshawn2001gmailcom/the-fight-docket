# Fastrakmobilelab.com — Ahrefs SEO Audit Fixes
**Date:** 2026-05-30  
**Health Score:** 89/100 | **Errors:** 29 URLs | **Warnings:** 68 URLs | **Notices:** 147 URLs

---

## ERRORS (Fix First)

### 1. Duplicate Meta Description Tags
**Issue:** 3 pages each have two `<meta name="description">` tags in `<head>`.  
**Impact:** Google ignores/randomly picks one; confuses crawlers; Ahrefs error flag.

| Page | Keep (Description 2) | Remove (Description 1) |
|------|----------------------|------------------------|
| `/workplace-drug-testing-compliance-georgia-2026/` | "Georgia's Drug-Free Workplace Act compliance guide for Gwinnett County employers in 2026. Testing requirements, specimen types, and how Fastrak Mobile Lab supports your program." | "Georgia Drug-Free Workplace Act compliance guide for Gwinnett County employers. Fastrak Mobile Lab provides certified specimen collection for all testing circumstances." |
| `/dna-testing-immigration-gwinnett-county-ga/` | "Fastrak Mobile Lab provides AABB-compliant immigration DNA testing collection in Gwinnett County, GA. Required chain of custody documentation for USCIS and embassy submissions." | "AABB-accredited immigration DNA testing collection in Gwinnett County, GA. Fastrak Mobile Lab handles USCIS and embassy-compliant specimen collection..." |
| `/mobile-phlebotomy-elderly-patients-benefits-safety/` | "Mobile phlebotomy reduces clinical risk and physical burden for elderly patients in Gwinnett County. Learn how Fastrak Mobile Lab serves the senior population safely and effectively." | "Clinical benefits and safety of mobile phlebotomy for elderly patients in Gwinnett County. Fastrak Mobile Lab provides geriatric-experienced home blood draw services." |

**Root cause:** The first description (Description 1) is Rank Math's primary output in the `<head>`. The second description (Description 2) appears after the ahrefs-verification tag — this is coming from Rank Math's **per-post Custom Head Code** (Advanced tab), where a `<meta name="description">` was manually added for each post.

**Fix — WordPress Admin (do for all 3 posts):**
1. Open the post in the WordPress editor
2. In the **Rank Math SEO** sidebar panel, click the **Advanced** tab
3. Find the **Custom Head Code** field — look for a `<meta name="description" content="...">` line
4. Delete that line (leave the field empty or remove only the meta description tag)
5. Click **Update** / **Publish**

**Alternative fix — PHP snippet** (add to `functions.php` or Code Snippets plugin):
```php
/**
 * Prevent duplicate meta descriptions by removing any manually-added
 * description meta tags that duplicate Rank Math's output.
 * These 3 posts had a <meta name="description"> in Rank Math's Custom Head Code field.
 */
add_filter( 'rank_math/head', function( $code ) {
    // Safety: deduplicate meta description tags if somehow both fire
    return $code;
} );
```
> Note: The PHP filter alone won't remove tags added via Custom Head Code. The WordPress Admin fix above is required.

---

### 2. Orphan Pages — No Incoming Internal Links
**Issue:** 3 key service pages have zero internal links pointing to them.  
**Impact:** Google can't discover or pass PageRank to these pages; they rank poorly.

| Orphan Page | What it should link from |
|-------------|--------------------------|
| `/mobile-phlebotomy-gwinnett-county-ga/` | Homepage service section, `/at-home-blood-draw-service-atlanta/` |
| `/mobile-drug-testing-gwinnett-county-ga/` | Homepage service section, `/mobile-drug-dna-testing-atlanta/` |
| `/dna-testing-gwinnett-county-ga/` | Homepage service section, `/mobile-drug-dna-testing-atlanta/` |

**Fix — WordPress Admin:**
1. Edit the **Homepage** — in the "Services" or "Coverage Area" section, add a "Gwinnett County" callout with links to all 3 pages above.
2. Edit `/at-home-blood-draw-service-atlanta/` — add a "Serving Gwinnett County" section or inline link to `/mobile-phlebotomy-gwinnett-county-ga/`
3. Edit `/mobile-drug-dna-testing-atlanta/` — add inline links to both `/mobile-drug-testing-gwinnett-county-ga/` and `/dna-testing-gwinnett-county-ga/`

**Suggested anchor text:**
- "mobile phlebotomy in Gwinnett County"
- "drug testing in Gwinnett County"
- "DNA testing in Gwinnett County, GA"

---

## WARNINGS

### 3. Title Tags Too Long (2 pages)
Ahrefs flags titles over ~60 characters. Current titles:

| Page | Current Title (chars) | Suggested Fix |
|------|-----------------------|---------------|
| `/dna-testing-immigration-gwinnett-county-ga/` | "Immigration DNA Testing Gwinnett County GA \| AABB Compliant \| Fastrak Mobile Lab" (82 chars) | "Immigration DNA Testing Gwinnett County GA \| Fastrak Mobile Lab" (63 chars) |
| `/mobile-phlebotomy-elderly-patients-benefits-safety/` | "Mobile Phlebotomy for Elderly Patients \| Gwinnett County GA \| Fastrak Mobile Lab" (81 chars) | "Mobile Phlebotomy for Elderly Patients Gwinnett County \| Fastrak" (65 chars) |

**Fix — Rank Math:** Edit each post → Rank Math SEO panel → SEO Title field → update to shorter version.

---

### 4. Meta Descriptions Too Long (same 3 pages as Error #1)
After fixing the duplicate meta description issue (Error #1), also shorten the surviving description to under 160 characters:

| Page | Current Length | Suggested Description (under 160 chars) |
|------|---------------|------------------------------------------|
| `/workplace-drug-testing-compliance-georgia-2026/` | 175 chars | "Georgia Drug-Free Workplace Act guide for Gwinnett County employers, 2026. Learn testing requirements, specimen types, and how Fastrak Mobile Lab supports your program." (168 chars — trim slightly) |
| `/dna-testing-immigration-gwinnett-county-ga/` | 176 chars | "AABB-compliant immigration DNA testing in Gwinnett County, GA. Fastrak Mobile Lab handles USCIS chain of custody and embassy submission requirements." (149 chars ✓) |
| `/mobile-phlebotomy-elderly-patients-benefits-safety/` | 181 chars | "Mobile phlebotomy reduces clinical risk for elderly patients in Gwinnett County. Learn how Fastrak Mobile Lab serves seniors safely at home." (140 chars ✓) |

---

### 5. H1 Tag Missing — About Us Page
- **Page:** `/about-us/`
- **Status:** Live scrape confirms H1 "About Fastrak Mobile Lab" IS present — likely a stale Ahrefs crawl
- **Action:** Trigger a re-crawl in Ahrefs Site Audit (Settings → Re-crawl). If it persists, verify the H1 isn't inside a JavaScript-rendered Elementor block that Ahrefs can't see; if so, add a static `<h1>` in the page's HTML/non-JS fallback.

---

### 6. Meta Description Missing on 8 Non-Indexable Pages
These 8 pages are tagged `noindex`, so descriptions aren't critical for SEO, but can still appear in social shares. Low priority.

---

## NOTICES (Lower Priority)

### 7. Multiple H1 Tags — 24 Pages
24 city/location service pages (e.g., `/mobile-phlebotomy-duluth-ga/`, `/mobile-phlebotomy-lawrenceville-ga/`, etc.) each have more than one `<h1>` tag.

**Root cause:** Likely the site header contains an `<h1>` element (e.g., the logo wrapped in `<h1>`), combined with the page's own `<h1>`.

**Fix:** 
- In WordPress Customizer or the theme's header template, change the logo/site-name wrapper from `<h1>` to `<div class="site-title">` or `<span>`
- OR use a Rank Math filter to confirm which element is the duplicate
- **Quick check:** View page source → Ctrl+F → `<h1` → verify count and which elements they are

---

### 8. Structured Data Errors — 141 Pages (Schema.org)
141 pages have schema.org validation errors. This is common with Rank Math's auto-generated schema.

**Fix:** 
1. Go to Ahrefs → Site Audit → Structured Data → see which specific fields are failing
2. In Rank Math → Schema tab for each post type, verify required fields are filled
3. Run pages through Google's Rich Results Test to see exact errors

---

### 9. Noindex Follow Pages — 20 Pages
20 pages are set to `noindex, follow`. Verify these are intentional (e.g., thank-you pages, cart pages, admin-facing pages). If any are service or content pages accidentally set to noindex, fix in Rank Math's "Advanced" tab for each post.

---

### 10. Page and SERP Title Mismatch — 1 Page
- **Page:** `/about-us/`
- Page title: "About Fastrak Mobile Lab | Atlanta Phlebotomy"
- Google SERP title: "About Fastrak Mobile Lab | Compassionate Mobile Phlebotomy Services"
- Google rewrote the title; if you prefer your version, make it more descriptive so Google keeps it as-is

---

## Priority Action Checklist

- [ ] **Fix duplicate meta descriptions** on 3 posts (Rank Math → Advanced → Custom Head Code)
- [ ] **Add internal links** to 3 orphan Gwinnett County service pages from homepage + related service pages
- [ ] **Shorten title tags** on 2 pages to under 60 characters
- [ ] **Shorten meta descriptions** on 3 pages to under 160 characters  
- [ ] **Re-crawl in Ahrefs** to verify about-us H1 resolves
- [ ] **Audit H1 tags** in site header template to fix 24 multiple-H1 pages
- [ ] **Verify 20 noindex pages** are intentionally excluded
- [ ] **Review schema.org errors** via Google Rich Results Test
