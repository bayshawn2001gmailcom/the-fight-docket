#!/usr/bin/env python3
"""
The Fight Docket — Instagram Graphics Tool (WAT Framework)
Reads .tmp/weekly_ig_data_YYYY-MM-DD.json → generates 4 branded 1080x1080 IG cards + captions.

Font resolution order:
  1. CANVAS_FONTS_DIR env var
  2. tools/canvas-fonts/ (copy fonts here for portability)
  3. ../the-fight-docket/canvas-fonts/ (existing project sibling)

Run: python tools/ig_graphics.py
     python tools/ig_graphics.py 2026-05-12   (specific date)
"""
import os, sys, json, glob as _glob
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

TMP_DIR = ROOT / ".tmp"
OUT_DIR = TMP_DIR / "ig"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Font path resolution ─────────────────────────────────────────

def _find_fonts() -> str:
    candidates = [
        os.environ.get("CANVAS_FONTS_DIR", ""),
        str(Path(__file__).parent / "canvas-fonts"),
        str(ROOT.parent / "the-fight-docket" / "canvas-fonts"),
    ]
    for path in candidates:
        if path and Path(path).is_dir():
            return path
    raise RuntimeError(
        "Canvas fonts not found. Either:\n"
        "  1. Set CANVAS_FONTS_DIR=/path/to/canvas-fonts in .env\n"
        "  2. Copy canvas-fonts/ into Fight Newsletter/tools/\n"
        "  3. Ensure the-fight-docket/ is a sibling directory"
    )

FONTS = _find_fonts()

# ── Brand colors (from brand guidelines) ─────────────────────────
BG    = "#0D0D0D"
RED   = "#DE1E20"
GOLD  = "#C5A059"
WHITE = "#F2F2E8"
DGRAY = "#1C1C1C"
MGRAY = "#2A2A2A"
W = H = 1080


# ── PIL helpers ──────────────────────────────────────────────────

def _get_pil():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return Image, ImageDraw, ImageFont
    except ImportError:
        raise SystemExit("Missing: pip install pillow")

def _base(scanlines=True):
    Image, ImageDraw, _ = _get_pil()
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)
    if scanlines:
        for y in range(0, H, 4):
            d.line([(0, y), (W, y)], fill="#111111", width=1)
    return img, d

def _font(name, size):
    _, _, ImageFont = _get_pil()
    return ImageFont.truetype(f"{FONTS}/{name}", size)

def _red_bar(d, side="left", thickness=14):
    if side == "left":
        d.rectangle([(0, 0), (thickness, H)], fill=RED)
    elif side == "top":
        d.rectangle([(0, 0), (W, thickness)], fill=RED)

def _rule(d, y, color=GOLD, margin=60, thickness=2):
    d.line([(margin, y), (W - margin, y)], fill=color, width=thickness)

def _watermark(d):
    f = _font("InstrumentSans-Regular.ttf", 28)
    d.text((W - 220, H - 44), "THE FIGHT DOCKET", font=f, fill="#333333")

def _wrap_text(d, text, font, x, y, max_width, fill=WHITE, line_spacing=1.25, max_lines=None):
    _, ImageDraw, _ = _get_pil()
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = d.textbbox((0, 0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip() + "…"
    lh = int(d.textbbox((0, 0), "Ag", font=font)[3] * line_spacing)
    for line in lines:
        d.text((x, y), line, font=font, fill=fill)
        y += lh
    return y

def _save(img, filename: str) -> str:
    path = str(OUT_DIR / filename)
    img.save(path, "PNG")
    print(f"  Saved: {filename}")
    return path


# ── Card generators ──────────────────────────────────────────────

def newsletter_preview(date_label: str, stories: list, filename: str = "newsletter_preview.png") -> str:
    Image, ImageDraw, _ = _get_pil()
    img, d = _base()

    slash = [(W * 0.6, 0), (W * 0.78, 0), (W * 0.52, H), (W * 0.34, H)]
    d.polygon(slash, fill=RED)

    overlay = Image.new("RGBA", (W, H), (10, 10, 10, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(W):
        a = max(0, int(200 * (1 - x / (W * 0.65))))
        od.line([(x, 0), (x, H)], fill=(10, 10, 10, a))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    _red_bar(d)

    chip_f = _font("InstrumentSans-Bold.ttf", 26)
    d.rectangle([(60, 80), (220, 118)], fill=RED)
    d.text((74, 86), "NEW ISSUE", font=chip_f, fill=WHITE)

    d.text((60, 134), date_label.upper(), font=_font("InstrumentSans-Regular.ttf", 34), fill=GOLD)

    title_f = _font("BigShoulders-Bold.ttf", 148)
    d.text((50, 168), "THIS", font=title_f, fill=WHITE)
    d.text((50, 290), "WEEK", font=title_f, fill=WHITE)

    _rule(d, 456, margin=60)

    bullet_f = _font("InstrumentSans-Regular.ttf", 36)
    bold_f   = _font("InstrumentSans-Bold.ttf", 36)
    y = 476
    for i, story in enumerate(stories[:3]):
        d.text((60, y), f"0{i + 1}", font=bold_f, fill=RED)
        y = _wrap_text(d, story, bullet_f, 114, y, 580, fill=WHITE, line_spacing=1.25, max_lines=2)
        y += 20

    _rule(d, 880, margin=60)
    d.text((60, 900), "thefightdocket.com  ·  BOXING & MMA",
           font=_font("InstrumentSans-Regular.ttf", 30), fill=GOLD)
    _watermark(d)
    return _save(img, filename)


def fight_announcement(fighter1: str, fighter2: str, event: str, date_str: str,
                       weight_class: str, filename: str = "fight_announcement.png") -> str:
    img, d = _base()

    d.rectangle([(0, 0), (W, 160)], fill=RED)
    d.rectangle([(0, 160), (W, 750)], fill=DGRAY)
    d.rectangle([(0, 750), (W, H)], fill=MGRAY)

    for y in range(160, 750, 4):
        d.line([(0, y), (W, y)], fill="#1F1F1F", width=1)

    ann_f  = _font("BigShoulders-Bold.ttf", 62)
    bbox   = d.textbbox((0, 0), "FIGHT ANNOUNCED", font=ann_f)
    d.text(((W - bbox[2]) // 2, 50), "FIGHT ANNOUNCED", font=ann_f, fill=WHITE)

    wc_f   = _font("InstrumentSans-Bold.ttf", 28)
    wc_bbox = d.textbbox((0, 0), weight_class.upper(), font=wc_f)
    wc_w   = wc_bbox[2] + 40
    d.rectangle([((W - wc_w) // 2, 188), ((W + wc_w) // 2, 228)], fill="#111111")
    d.text(((W - wc_bbox[2]) // 2, 194), weight_class.upper(), font=wc_f, fill=GOLD)

    f1_size = min(130, max(60, 130 - max(0, len(fighter1) - 8) * 7))
    f1_font = _font("BigShoulders-Bold.ttf", f1_size)
    f1_bbox = d.textbbox((0, 0), fighter1.upper(), font=f1_font)
    d.text(((W // 2 - f1_bbox[2]) // 2 + 30, 310), fighter1.upper(), font=f1_font, fill=WHITE)

    vs_f   = _font("BigShoulders-Bold.ttf", 86)
    vs_bbox = d.textbbox((0, 0), "VS", font=vs_f)
    d.text(((W - vs_bbox[2]) // 2, 460), "VS", font=vs_f, fill=RED)

    f2_size = min(130, max(60, 130 - max(0, len(fighter2) - 8) * 7))
    f2_font = _font("BigShoulders-Bold.ttf", f2_size)
    f2_bbox = d.textbbox((0, 0), fighter2.upper(), font=f2_font)
    f2_x    = W - (W // 2 - f2_bbox[2]) // 2 - 30 - f2_bbox[2]
    d.text((f2_x, 560), fighter2.upper(), font=f2_font, fill=WHITE)

    _rule(d, 750, color=GOLD, margin=0, thickness=3)

    ev_f  = _font("BigShoulders-Bold.ttf", 56)
    ev_bbox = d.textbbox((0, 0), event.upper(), font=ev_f)
    d.text(((W - ev_bbox[2]) // 2, 776), event.upper(), font=ev_f, fill=WHITE)

    dt_f  = _font("InstrumentSans-Regular.ttf", 36)
    dt_bbox = d.textbbox((0, 0), date_str.upper(), font=dt_f)
    d.text(((W - dt_bbox[2]) // 2, 848), date_str.upper(), font=dt_f, fill=GOLD)

    _red_bar(d)
    _watermark(d)
    return _save(img, filename)


def fight_result(winner: str, loser: str, method: str, round_num: str,
                 time: str, event: str, filename: str = "fight_result.png") -> str:
    img, d = _base()

    d.rectangle([(0, 0), (W, 20)], fill=GOLD)
    d.rectangle([(0, 20), (W, H - 20)], fill=DGRAY)
    for y in range(20, H - 20, 4):
        d.line([(0, y), (W, y)], fill="#1F1F1F", width=1)
    d.rectangle([(0, H - 20), (W, H)], fill=GOLD)
    _red_bar(d)

    res_f = _font("InstrumentSans-Bold.ttf", 32)
    d.text((60, 48), f"OFFICIAL RESULT  ·  {event.upper()}", font=res_f, fill=GOLD)
    _rule(d, 102, margin=60, color="#333333")

    d.text((60, 126), "WINNER", font=_font("InstrumentSans-Bold.ttf", 28), fill=RED)

    w_size  = min(160, max(70, 160 - max(0, len(winner) - 8) * 9))
    win_f   = _font("BigShoulders-Bold.ttf", w_size)
    d.text((60, 158), winner.upper(), font=win_f, fill=WHITE)

    winner_bbox = d.textbbox((60, 158), winner.upper(), font=win_f)
    _rule(d, winner_bbox[3] + 20, margin=60, color="#333333")

    def_y = winner_bbox[3] + 44
    d.text((60, def_y), "def.", font=_font("InstrumentSans-Regular.ttf", 34), fill="#888888")

    l_size = min(100, max(50, 100 - max(0, len(loser) - 8) * 6))
    los_f  = _font("BigShoulders-Bold.ttf", l_size)
    d.text((60, def_y + 46), loser.upper(), font=los_f, fill="#888888")
    loser_bbox = d.textbbox((60, def_y + 46), loser.upper(), font=los_f)

    _rule(d, loser_bbox[3] + 30, margin=60)

    info_y = loser_bbox[3] + 60
    chip_data = [(method.upper(), RED, WHITE), (round_num.upper(), MGRAY, GOLD), (time, MGRAY, WHITE)]
    cx, chip_f = 60, _font("BigShoulders-Bold.ttf", 48)
    for label, bg_c, fg_c in chip_data:
        bbox = d.textbbox((0, 0), label, font=chip_f)
        cw, ch = bbox[2] + 36, bbox[3] + 20
        d.rectangle([(cx, info_y), (cx + cw, info_y + ch)], fill=bg_c)
        d.text((cx + 18, info_y + 10), label, font=chip_f, fill=fg_c)
        cx += cw + 24

    _watermark(d)
    return _save(img, filename)


def quote_card(quote: str, attribution: str, context: str = "", filename: str = "quote_card.png") -> str:
    Image, ImageDraw, _ = _get_pil()
    img, d = _base()

    d.rectangle([(0, 0), (W, 80)], fill=RED)

    big_q_f    = _font("BigShoulders-Bold.ttf", 600)
    big_q_bbox = d.textbbox((0, 0), "“", font=big_q_f)
    d.text((W - big_q_bbox[2] - 40, -80), "“", font=big_q_f, fill="#181818")

    _red_bar(d, side="left")

    label_f = _font("InstrumentSans-Bold.ttf", 30)
    d.text((60, 104), context.upper() if context else "FROM THE DOCKET", font=label_f, fill=GOLD)
    _rule(d, 156, margin=60, color="#2A2A2A")

    q_font_size = 68 if len(quote) < 80 else 54 if len(quote) < 120 else 44
    q_font = _font("Lora-Bold.ttf", q_font_size)
    _wrap_text(d, f"“{quote}”", q_font, 60, 190, 940, fill=WHITE, line_spacing=1.35)

    _rule(d, 870, margin=60)
    d.text((60, 892), f"— {attribution}", font=_font("InstrumentSans-Regular.ttf", 36), fill=GOLD)

    d.rectangle([(0, H - 64), (W, H)], fill="#111111")
    d.text((60, H - 52), "THE FIGHT DOCKET", font=_font("BigShoulders-Bold.ttf", 38), fill=RED)

    _watermark(d)
    return _save(img, filename)


# ── Main ─────────────────────────────────────────────────────────

def main():
    date_iso = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    ig_files = sorted(TMP_DIR.glob(f"weekly_ig_data_{date_iso}.json")) or \
               sorted(TMP_DIR.glob("weekly_ig_data_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

    if not ig_files:
        raise SystemExit("No weekly_ig_data_*.json found. Run tools/newsletter_draft.py first.")

    ig_file = ig_files[0]
    week    = json.loads(ig_file.read_text(encoding="utf-8"))

    issue    = week.get("issue", date.today().strftime("%b%d_%Y").lower())
    date_lbl = week.get("date", "")

    print(f"\n  Fight Docket — IG Content Generator")
    print(f"  Issue: {date_lbl or issue}\n")

    # 1. Newsletter Preview
    print("[1/4] Newsletter preview card...")
    newsletter_preview(
        date_label=date_lbl,
        stories=week.get("preview_stories", []),
        filename=f"{issue}_newsletter_preview.png",
    )

    # 2. Fight Announcement
    a = week.get("announcement", {})
    if a:
        print("[2/4] Fight announcement card...")
        fight_announcement(
            fighter1=a.get("fighter1", ""),
            fighter2=a.get("fighter2", ""),
            event=a.get("event", ""),
            date_str=a.get("date", ""),
            weight_class=a.get("weight_class", ""),
            filename=f"{issue}_{a.get('filename', 'announcement.png')}",
        )
    else:
        print("[2/4] Skipped (no announcement data)")

    # 3. Fight Result
    r = week.get("result", {})
    if r:
        print("[3/4] Fight result card...")
        fight_result(
            winner=r.get("winner", ""),
            loser=r.get("loser", ""),
            method=r.get("method", ""),
            round_num=r.get("round_num", ""),
            time=r.get("time", ""),
            event=r.get("event", ""),
            filename=f"{issue}_{r.get('filename', 'result.png')}",
        )
    else:
        print("[3/4] Skipped (no result data)")

    # 4. Quote Card
    q = week.get("quote", {})
    if q:
        print("[4/4] Quote card...")
        quote_card(
            quote=q.get("quote", ""),
            attribution=q.get("attribution", ""),
            context=q.get("context", ""),
            filename=f"{issue}_{q.get('filename', 'quote.png')}",
        )
    else:
        print("[4/4] Skipped (no quote data)")

    # Write captions
    a      = week.get("announcement", {}) or {}
    r      = week.get("result", {})       or {}
    q      = week.get("quote", {})        or {}
    stories = week.get("preview_stories", [])

    captions = f"""The Fight Docket — {date_lbl}
Generated: {date.today().isoformat()}
=========================================

--- MONDAY: Newsletter Preview ---
\U0001f4f0 NEW ISSUE — The Fight Docket is out.

{chr(10).join(f"  → {s}" for s in stories)}

Full breakdown at thefightdocket.com
Subscribe free 👉 link in bio
#FightDocket #MMA #Boxing #CombatSports #UFC

--- TUESDAY: Fight Result ---
\U0001f94a RESULT

{r.get("winner","").upper()} def. {r.get("loser","").upper()}
{r.get("method","")} · {r.get("round_num","")} · {r.get("time","")}

Full card breakdown in this week's Fight Docket.
Subscribe free 👉 link in bio
#MMA #UFC #Boxing #FightResults #CombatSports

--- THURSDAY: Fight Announcement ---
\U0001f94a IT'S OFFICIAL

{a.get("fighter1","")} vs. {a.get("fighter2","")}
{a.get("event","")} · {a.get("date","")}

Full preview in this week's Fight Docket.
Subscribe free 👉 link in bio
#UFC #MMA #FightAnnouncement #{a.get("event","").replace(" ","")}

--- SATURDAY: Quote Card ---
"{q.get("quote","")}"
— {q.get("attribution","")}

Subscribe free 👉 link in bio
#FightDocket #MMA #Boxing #CombatSports
"""

    captions_file = OUT_DIR / f"{issue}_captions.txt"
    captions_file.write_text(captions, encoding="utf-8")
    print(f"\n  Captions: {captions_file.name}")
    print(f"\n  All graphics + captions ready in .tmp/ig/")
    print("  Posting schedule: Mon (Preview) · Tue (Result) · Thu (Announcement) · Sat (Quote)")


if __name__ == "__main__":
    main()
