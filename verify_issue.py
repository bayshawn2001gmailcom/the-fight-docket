#!/usr/bin/env python3
"""
verify_issue.py — render an issue the way Beehiiv will actually mangle it, and
report the two failures that are invisible in the source.

Beehiiv strips the <style> block AND fragments the paste into separate editor
blocks, so any section that depended on an ancestor for its dark background
renders light-on-white. Separately, images that are too heavy never finish
loading and the issue ships looking image-less. Neither shows up until it is
rendered, which is why this script exists.

Run: python verify_issue.py [newsletter_YYYY-MM-DD.html]
Exit code is 0 only if every image loads and every paragraph is readable.
"""
import re
import sys
from pathlib import Path

from issue_selector import latest_issue

SCRIPT_DIR = Path(__file__).parent
MIN_CONTRAST = 3.0          # anything below this is unreadable body copy
IMG_SETTLE_MS = 9000        # cold ImgBB URLs can take 5-11s on first fetch
MIN_IMAGE_WIDTH = 600       # real section images upload at 1200px; 404 placeholders are tiny


def worst_case_html(html: str) -> str:
    """Reproduce what Beehiiv leaves behind: no style block, no outer container,
    dropped onto a white page."""
    body = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
    m = re.search(r"<body[^>]*>(.*)</body>", body, flags=re.S)
    inner = m.group(1) if m else body
    inner = re.sub(r'<div style="max-width:680px;[^"]*">', "", inner, count=1)
    return "<body style='background:#fff; margin:0'>" + inner + "</body>"


def _luminance(css_color: str):
    nums = re.findall(r"[\d.]+", css_color)[:3]
    if len(nums) < 3:
        return None
    r, g, b = (float(n) / 255 for n in nums)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def verify(path: Path, screenshot: bool = True) -> int:
    html = path.read_text(encoding="utf-8")
    tmp_dir = SCRIPT_DIR / ".tmp" / "newsletter_images"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    test_file = tmp_dir / f"worstcase_{path.stem}.html"
    test_file.write_text(worst_case_html(html), encoding="utf-8")

    from playwright.sync_api import sync_playwright

    problems = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 700, "height": 1200})

        # A dead ImgBB URL returns a ~1KB placeholder PNG with a 404, which the
        # browser decodes happily — naturalWidth alone cannot see it. Watch the
        # network for the real status.
        bad_status = {}
        def _on_response(resp):
            if resp.request.resource_type == "image" and resp.status >= 400:
                bad_status[resp.url] = resp.status
        page.on("response", _on_response)

        # domcontentloaded, not load — waiting on remote images times out
        page.goto(test_file.resolve().as_uri(), wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(IMG_SETTLE_MS)

        # Real section images are uploaded at 1200px wide; a placeholder is tiny.
        imgs = page.evaluate("""(minW) => {
            const i = [...document.images];
            const ok = x => x.naturalWidth >= minW;
            return {total: i.length,
                    ok: i.filter(ok).length,
                    broken: i.filter(x => !ok(x)).map(
                        x => `${x.alt || x.src} (${x.naturalWidth}x${x.naturalHeight})`)};
        }""", MIN_IMAGE_WIDTH)
        for url, status in bad_status.items():
            imgs["broken"].append(f"HTTP {status}: {url}")
            imgs["ok"] = max(0, imgs["ok"] - 1)
        print(f"  images loaded: {imgs['ok']}/{imgs['total']}")
        if imgs["broken"]:
            for b in imgs["broken"]:
                print(f"    BROKEN: {b}")
            problems.append(f"{len(imgs['broken'])} image(s) did not load")
        if imgs["total"] != 7:
            problems.append(f"expected 7 section images, found {imgs['total']}")

        paras = page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('p').forEach(p => {
                const color = getComputedStyle(p).color;
                let el = p, bg = 'rgba(0, 0, 0, 0)';
                while (el) {
                    const b = getComputedStyle(el).backgroundColor;
                    if (b && b !== 'rgba(0, 0, 0, 0)') { bg = b; break; }
                    el = el.parentElement;
                }
                out.push({color, bg, text: (p.textContent || '').trim().slice(0, 40)});
            });
            return out;
        }""")

        unreadable = []
        for row in paras:
            lc, lb = _luminance(row["color"]), _luminance(row["bg"])
            if lc is None or lb is None:
                continue
            contrast = (max(lc, lb) + 0.05) / (min(lc, lb) + 0.05)
            if contrast < MIN_CONTRAST:
                unreadable.append((round(contrast, 2), row["text"]))

        print(f"  paragraphs checked: {len(paras)}, unreadable: {len(unreadable)}")
        for c, t in unreadable[:15]:
            print(f"    LOW CONTRAST ({c}): {t}")
        if unreadable:
            problems.append(f"{len(unreadable)} paragraph(s) below {MIN_CONTRAST}:1 contrast")

        if screenshot:
            shot = tmp_dir / f"worstcase_{path.stem}.png"
            page.screenshot(path=str(shot), full_page=True)
            print(f"  screenshot: {shot}")
        browser.close()

    # Cheap source-level checks that catch known regressions
    if re.search(r"—|&mdash;", html):
        problems.append("contains em-dashes (see the no-em-dashes rule)")

    print()
    if problems:
        print("  FAILED:")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("  PASSED — safe to paste into Beehiiv")
    return 0


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            raise SystemExit(f"File not found: {path}")
    else:
        _, path = latest_issue(SCRIPT_DIR, max_age_days=None)
    print(f"\n  Verify Issue Render")
    print(f"  File: {path.name}")
    print("=" * 55)
    sys.exit(verify(path))


if __name__ == "__main__":
    main()
