#!/usr/bin/env python3
"""
beehiiv_prep.py — Pre-process Fight Docket HTML for clean Beehiiv injection.

PROBLEM: Injecting raw HTML via execCommand('insertHTML') into Beehiiv's
ProseMirror editor creates:
  - Empty <p> elements from blank lines between block tags
  - Empty <div> elements from <div class="subtitle"> and similar wrappers
  - Noisy class/style attributes ProseMirror ignores anyway

USAGE:
  python beehiiv_prep.py Fight_Docket_April_27_2026.html

OUTPUT:
  Prints clean inner HTML ready to copy-paste into the browser console
  injection script. Also saves to <filename>_clean.html for reference.

INJECTION SCRIPT (run in browser console on the Beehiiv editor page):
  (1) Copy the output of this script into CLEAN_HTML below
  (2) Run the inject + cleanup block
"""

import sys
import re
from html.parser import HTMLParser
from pathlib import Path


def extract_body(html: str) -> str:
    """Extract content between <body> tags."""
    match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else html


def clean_for_prosemirror(html: str) -> str:
    """
    Transforms HTML so ProseMirror doesn't create empty nodes on injection.

    Rules:
    1. Strip <head>, <style>, <html>, <body> wrappers → work only on body content
    2. Convert <div class="subtitle"> and similar divs → <p>
    3. Remove class="" and style="" attributes from block elements
       (ProseMirror ignores them and they pollute the DOM)
    4. Collapse multiple blank lines between block-level tags → single newline
       (blank lines = empty <p> nodes after insertHTML)
    5. Remove trailing <br> inside block elements before closing tag
    """
    # Step 1: Work on body content only
    body = extract_body(html)

    # Step 2: Convert <div class="..."> wrappers to <p>
    # These become orphaned empty <div> elements in ProseMirror
    body = re.sub(
        r'<div\s+class="[^"]*">(.*?)</div>',
        lambda m: f'<p>{m.group(1)}</p>',
        body,
        flags=re.DOTALL
    )
    # Also catch standalone empty <div> tags
    body = re.sub(r'<div\s*/?>(\s*)</div>', '', body)

    # Step 3: Strip class attributes from block elements only.
    # Do NOT strip style attributes — inline style="color:#F2F2E8;" etc. are required
    # because Beehiiv strips the <style> block on paste, leaving the page with no color rules.
    block_tags = r'(?:h[1-6]|p|blockquote|li|ul|ol|div)'
    body = re.sub(
        rf'(<{block_tags})\s+class="[^"]*"',
        r'\1',
        body,
        flags=re.IGNORECASE
    )
    # Handle multiple attributes on same tag
    body = re.sub(
        rf'(<{block_tags}[^>]*?)\s+class="[^"]*"',
        r'\1',
        body,
        flags=re.IGNORECASE
    )

    # Step 4: Collapse blank lines between block-level closing/opening tags
    # e.g. </p>\n\n<p> → </p>\n<p>
    # Blank lines between blocks are the #1 source of empty <p> nodes
    body = re.sub(r'(</(?:p|h[1-6]|blockquote|div|ul|ol|li|img[^>]*>)>)\s*\n\s*\n\s*', r'\1\n', body)
    body = re.sub(r'\n\s*\n\s*(</(?:p|h[1-6]|blockquote)>)', r'\n\1', body)

    # Step 5: Also collapse blank lines between any block tags (more aggressive)
    body = re.sub(r'\n{3,}', '\n\n', body)  # max 2 newlines anywhere
    body = re.sub(r'>\s*\n\s*\n\s*<', '>\n<', body)  # no blank line between tags

    # Step 6: Remove trailing <br> inside block elements just before closing tag
    # e.g. <p>text<br></p> → <p>text</p>
    body = re.sub(r'<br\s*/?>\s*(</(?:p|h[1-6]|li)>)', r'\1', body, flags=re.IGNORECASE)

    # Step 7: Normalize &nbsp; sequences (often cause spacing artifacts)
    body = re.sub(r'(&nbsp;){3,}', ' ', body)

    # Strip leading/trailing whitespace
    body = body.strip()

    return body


def generate_injection_js(clean_html: str) -> str:
    """
    Generate the browser console script for injecting clean HTML into Beehiiv
    and running post-injection cleanup.
    """
    # Escape backticks and backslashes for template literal
    escaped = clean_html.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

    return f'''// ============================================================
// BEEHIIV INJECTION SCRIPT — The Fight Docket
// Run this in the browser console on the Beehiiv editor page
// ============================================================

(async function injectAndClean() {{
  const editor = document.querySelector('.ProseMirror');
  if (!editor) {{ console.error('ProseMirror editor not found'); return; }}

  // Step 1: Focus and select all existing content
  editor.focus();
  document.execCommand('selectAll', false, null);

  // Step 2: Inject clean HTML
  const CLEAN_HTML = `{escaped}`;
  document.execCommand('insertHTML', false, CLEAN_HTML);

  // Step 3: Wait one tick for ProseMirror to process
  await new Promise(r => setTimeout(r, 500));

  // Step 4: Post-injection cleanup — remove any stray empty block elements
  const allBlocks = Array.from(editor.querySelectorAll('p, div'));
  let removed = 0;
  allBlocks.forEach(el => {{
    if (el.textContent.trim() === '' && !el.querySelector('img')) {{
      el.remove();
      removed++;
    }}
  }});

  // Step 5: Fire input event so Beehiiv autosave picks up the changes
  editor.dispatchEvent(new InputEvent('input', {{ bubbles: true, cancelable: true }}));

  console.log(`✅ Injected successfully. Cleaned up ${{removed}} empty block elements.`);
}})();
'''


def main():
    if len(sys.argv) < 2:
        print("Usage: python beehiiv_prep.py <html_file>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    raw_html = input_path.read_text(encoding='utf-8')
    clean_html = clean_for_prosemirror(raw_html)

    # Save clean HTML for reference
    clean_path = input_path.with_stem(input_path.stem + '_clean')
    clean_path.write_text(clean_html, encoding='utf-8')
    print(f"Clean HTML saved to: {clean_path}")

    # Generate and save injection JS
    js_path = input_path.with_suffix('.inject.js')
    js_code = generate_injection_js(clean_html)
    js_path.write_text(js_code, encoding='utf-8')
    print(f"Injection script saved to: {js_path}")

    # Stats
    orig_lines = raw_html.count('\n')
    clean_lines = clean_html.count('\n')
    print(f"\nStats: {orig_lines} lines → {clean_lines} lines ({orig_lines - clean_lines} blank lines removed)")
    print("\nRun the injection script in the browser console on the Beehiiv editor page.")


if __name__ == '__main__':
    main()
