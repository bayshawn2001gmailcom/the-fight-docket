"""
The Fight Docket — Instagram Content Templates
Brand: black bg, crimson red, gold, white | BigShoulders-Bold + InstrumentSans
All outputs: 1080x1080 PNG
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap, os, math, glob as _glob

# ── Dynamic path resolution (session-ID-independent) ─────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _find_fonts():
    """Locate canvas-design fonts regardless of which session is active."""
    # 1. Fonts copied into the workspace (most stable, always works)
    local = os.path.join(_SCRIPT_DIR, "canvas-fonts")
    if os.path.isdir(local):
        return local
    # 2. Session-mounted skills path (works during any Cowork session)
    matches = _glob.glob("/sessions/*/mnt/.claude/skills/canvas-design/canvas-fonts")
    if matches:
        return matches[0]
    raise RuntimeError(
        "Canvas fonts not found. Copy the canvas-fonts folder into "
        "'The fight Docket/' or run inside a Cowork session."
    )

FONTS = _find_fonts()
OUT   = os.path.join(_SCRIPT_DIR, "instagram_content")
os.makedirs(OUT, exist_ok=True)

# ── Brand colors ──────────────────────────────────────────────
BG      = "#0A0A0A"
RED     = "#C8102E"
GOLD    = "#C9A84C"
WHITE   = "#F0EDE8"
DGRAY   = "#1C1C1C"
MGRAY   = "#2A2A2A"

W = H = 1080

def _base(scanlines=True):
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)
    if scanlines:
        for y in range(0, H, 4):
            d.line([(0,y),(W,y)], fill="#111111", width=1)
    return img, d

def _font(name, size):
    return ImageFont.truetype(f"{FONTS}/{name}", size)

def _red_bar(d, side="left", thickness=14):
    if side == "left":
        d.rectangle([(0,0),(thickness,H)], fill=RED)
    elif side == "top":
        d.rectangle([(0,0),(W,thickness)], fill=RED)

def _rule(d, y, color=GOLD, margin=60, thickness=2):
    d.line([(margin, y),(W-margin, y)], fill=color, width=thickness)

def _watermark(d):
    f = _font("InstrumentSans-Regular.ttf", 28)
    d.text((W-220, H-44), "THE FIGHT DOCKET", font=f, fill="#333333")

def _wrap_text(d, text, font, x, y, max_width, fill=WHITE, line_spacing=1.25):
    """Draw wrapped text, return final y position."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = d.textbbox((0,0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    lh = int((d.textbbox((0,0), "Ag", font=font)[3]) * line_spacing)
    for line in lines:
        d.text((x, y), line, font=font, fill=fill)
        y += lh
    return y


# ═══════════════════════════════════════════════════════════════
# 1. NEWSLETTER PREVIEW CARD
# ═══════════════════════════════════════════════════════════════
def newsletter_preview(date_label, stories, filename="newsletter_preview.png"):
    """
    date_label: e.g. "APRIL 13, 2026"
    stories: list of 3 short headline strings
    """
    img, d = _base()

    # Red slash diagonal
    slash = [(W*0.6,0),(W*0.78,0),(W*0.52,H),(W*0.34,H)]
    d.polygon(slash, fill=RED)

    # Dark overlay left side
    overlay = Image.new("RGBA",(W,H),(10,10,10,0))
    od = ImageDraw.Draw(overlay)
    for x in range(W):
        a = max(0, int(200*(1 - x/(W*0.65))))
        od.line([(x,0),(x,H)], fill=(10,10,10,a))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d   = ImageDraw.Draw(img)

    _red_bar(d)

    # "NEW ISSUE" chip
    chip_f = _font("InstrumentSans-Bold.ttf", 26)
    chip_w = 160; chip_h = 38
    d.rectangle([(60, 80),(60+chip_w, 80+chip_h)], fill=RED)
    d.text((60+14, 80+6), "NEW ISSUE", font=chip_f, fill=WHITE)

    # Date label
    date_f = _font("InstrumentSans-Regular.ttf", 34)
    d.text((60, 134), date_label.upper(), font=date_f, fill=GOLD)

    # "THIS WEEK" heading
    title_f = _font("BigShoulders-Bold.ttf", 148)
    d.text((50, 168), "THIS", font=title_f, fill=WHITE)
    d.text((50, 290), "WEEK", font=title_f, fill=WHITE)

    _rule(d, 456, margin=60)

    # Story bullets
    bullet_f = _font("InstrumentSans-Regular.ttf", 38)
    bold_f   = _font("InstrumentSans-Bold.ttf", 38)
    y = 476
    for i, story in enumerate(stories[:3]):
        # Gold bullet number
        d.text((60, y), f"0{i+1}", font=bold_f, fill=RED)
        y = _wrap_text(d, story, bullet_f, 114, y, 580, fill=WHITE, line_spacing=1.3)
        y += 28

    _rule(d, 880, margin=60)

    # Footer
    footer_f = _font("InstrumentSans-Regular.ttf", 30)
    d.text((60, 900), "thefightdocket.com  ·  BOXING & MMA", font=footer_f, fill=GOLD)

    _watermark(d)
    path = f"{OUT}/{filename}"
    img.save(path, "PNG")
    print(f"✓ Saved: {path}")
    return path


# ═══════════════════════════════════════════════════════════════
# 2. FIGHT ANNOUNCEMENT CARD
# ═══════════════════════════════════════════════════════════════
def fight_announcement(fighter1, fighter2, event, date, weight_class, filename="fight_announcement.png"):
    """
    fighter1/2: fighter names (last name or full)
    event: event name e.g. "UFC 328"
    date: e.g. "JUNE 14, 2026"
    weight_class: e.g. "HEAVYWEIGHT"
    """
    img, d = _base()

    # Top red band
    d.rectangle([(0,0),(W,160)], fill=RED)

    # VS zone — dark card center
    d.rectangle([(0,160),(W,750)], fill=DGRAY)

    # Bottom section
    d.rectangle([(0,750),(W,H)], fill=MGRAY)

    # Scanline texture over dark zones
    for y in range(160, 750, 4):
        d.line([(0,y),(W,y)], fill="#1F1F1F", width=1)

    # "FIGHT ANNOUNCED" in red band
    ann_f = _font("BigShoulders-Bold.ttf", 62)
    bbox = d.textbbox((0,0),"FIGHT ANNOUNCED", font=ann_f)
    d.text(((W - bbox[2])//2, 50), "FIGHT ANNOUNCED", font=ann_f, fill=WHITE)

    # Weight class chip
    wc_f  = _font("InstrumentSans-Bold.ttf", 28)
    wc_bbox = d.textbbox((0,0), weight_class.upper(), font=wc_f)
    wc_w  = wc_bbox[2] + 40
    d.rectangle([((W-wc_w)//2, 188),((W+wc_w)//2, 228)], fill="#111111")
    d.text(((W-wc_bbox[2])//2, 194), weight_class.upper(), font=wc_f, fill=GOLD)

    # Fighter 1 — left aligned, large
    f1_size = min(130, max(60, 130 - max(0, len(fighter1)-8)*7))
    f1_font = _font("BigShoulders-Bold.ttf", f1_size)
    f1_bbox = d.textbbox((0,0), fighter1.upper(), font=f1_font)
    d.text(((W//2 - f1_bbox[2])//2 + 30, 310), fighter1.upper(), font=f1_font, fill=WHITE)

    # VS
    vs_f    = _font("BigShoulders-Bold.ttf", 86)
    vs_bbox = d.textbbox((0,0),"VS", font=vs_f)
    d.text(((W-vs_bbox[2])//2, 460), "VS", font=vs_f, fill=RED)

    # Fighter 2 — right aligned
    f2_size = min(130, max(60, 130 - max(0, len(fighter2)-8)*7))
    f2_font = _font("BigShoulders-Bold.ttf", f2_size)
    f2_bbox = d.textbbox((0,0), fighter2.upper(), font=f2_font)
    f2_x    = W - (W//2 - f2_bbox[2])//2 - 30 - f2_bbox[2]
    d.text((f2_x, 560), fighter2.upper(), font=f2_font, fill=WHITE)

    # Gold divider
    _rule(d, 750, color=GOLD, margin=0, thickness=3)

    # Bottom info: event + date
    ev_f   = _font("BigShoulders-Bold.ttf", 56)
    ev_bbox = d.textbbox((0,0), event.upper(), font=ev_f)
    d.text(((W-ev_bbox[2])//2, 776), event.upper(), font=ev_f, fill=WHITE)

    dt_f   = _font("InstrumentSans-Regular.ttf", 36)
    dt_bbox = d.textbbox((0,0), date.upper(), font=dt_f)
    d.text(((W-dt_bbox[2])//2, 848), date.upper(), font=dt_f, fill=GOLD)

    # Red left accent bar
    _red_bar(d)

    _watermark(d)
    path = f"{OUT}/{filename}"
    img.save(path, "PNG")
    print(f"✓ Saved: {path}")
    return path


# ═══════════════════════════════════════════════════════════════
# 3. FIGHT RESULT CARD
# ═══════════════════════════════════════════════════════════════
def fight_result(winner, loser, method, round_num, time, event, filename="fight_result.png"):
    """
    winner/loser: fighter names
    method: e.g. "KO/TKO" | "SUBMISSION" | "DECISION"
    round_num: e.g. "R1" | "R3"
    time: e.g. "3:45"
    event: e.g. "UFC 327"
    """
    img, d = _base()

    # Bold gold top band
    d.rectangle([(0,0),(W,20)], fill=GOLD)

    # Dark mid section
    d.rectangle([(0,20),(W,H-20)], fill=DGRAY)
    for y in range(20, H-20, 4):
        d.line([(0,y),(W,y)], fill="#1F1F1F", width=1)

    d.rectangle([(0,H-20),(W,H)], fill=GOLD)
    _red_bar(d)

    # "RESULT" label
    res_f  = _font("InstrumentSans-Bold.ttf", 32)
    d.text((60, 48), f"OFFICIAL RESULT  ·  {event.upper()}", font=res_f, fill=GOLD)
    _rule(d, 102, margin=60, color="#333333")

    # WINNER label
    win_label_f = _font("InstrumentSans-Bold.ttf", 28)
    d.text((60, 126), "WINNER", font=win_label_f, fill=RED)

    # Winner name — massive
    w_size  = min(160, max(70, 160 - max(0, len(winner)-8)*9))
    win_f   = _font("BigShoulders-Bold.ttf", w_size)
    d.text((60, 158), winner.upper(), font=win_f, fill=WHITE)

    # Thin rule under winner
    winner_bbox = d.textbbox((60,158), winner.upper(), font=win_f)
    _rule(d, winner_bbox[3] + 20, margin=60, color="#333333")

    # DEF. label
    def_y = winner_bbox[3] + 44
    def_f = _font("InstrumentSans-Regular.ttf", 34)
    d.text((60, def_y), "def.", font=def_f, fill="#888888")

    # Loser name
    l_size = min(100, max(50, 100 - max(0, len(loser)-8)*6))
    los_f  = _font("BigShoulders-Bold.ttf", l_size)
    d.text((60, def_y + 46), loser.upper(), font=los_f, fill="#888888")
    loser_bbox = d.textbbox((60, def_y+46), loser.upper(), font=los_f)

    _rule(d, loser_bbox[3] + 30, margin=60)

    # Method / Round / Time chips
    info_y  = loser_bbox[3] + 60
    chip_data = [(method.upper(), RED, WHITE), (round_num.upper(), MGRAY, GOLD), (time, MGRAY, WHITE)]
    cx = 60
    chip_f = _font("BigShoulders-Bold.ttf", 48)
    gap = 24
    for label, bg_c, fg_c in chip_data:
        bbox = d.textbbox((0,0), label, font=chip_f)
        cw   = bbox[2] + 36; ch = bbox[3] + 20
        d.rectangle([(cx, info_y),(cx+cw, info_y+ch)], fill=bg_c)
        d.text((cx+18, info_y+10), label, font=chip_f, fill=fg_c)
        cx += cw + gap

    _watermark(d)
    path = f"{OUT}/{filename}"
    img.save(path, "PNG")
    print(f"✓ Saved: {path}")
    return path


# ═══════════════════════════════════════════════════════════════
# 4. QUOTE / NEWS CARD
# ═══════════════════════════════════════════════════════════════
def quote_card(quote, attribution, context="", filename="quote_card.png"):
    """
    quote: the pull quote (keep under 120 chars for best layout)
    attribution: who said it / source
    context: optional small context line e.g. "UFC 327 · Post-Fight"
    """
    img, d = _base()

    # Thick red top bar
    d.rectangle([(0,0),(W,80)], fill=RED)

    # Giant faded quotation mark as background element
    big_q_f = _font("BigShoulders-Bold.ttf", 600)
    big_q_bbox = d.textbbox((0,0), "\u201C", font=big_q_f)
    d.text((W - big_q_bbox[2] - 40, -80), "\u201C", font=big_q_f, fill="#181818")

    _red_bar(d, side="left")

    # "THE DOCKET SAYS" label
    label_f = _font("InstrumentSans-Bold.ttf", 30)
    if context:
        d.text((60, 104), context.upper(), font=label_f, fill=GOLD)
    else:
        d.text((60, 104), "FROM THE DOCKET", font=label_f, fill=GOLD)

    _rule(d, 156, margin=60, color="#2A2A2A")

    # Quote text — large, centered-left
    q_font_size = 68 if len(quote) < 80 else 54 if len(quote) < 120 else 44
    q_font = _font("Lora-Bold.ttf", q_font_size)
    _wrap_text(d, f"\u201C{quote}\u201D", q_font, 60, 190, 940, fill=WHITE, line_spacing=1.35)

    # Attribution
    _rule(d, 870, margin=60)
    attr_f = _font("InstrumentSans-Regular.ttf", 36)
    d.text((60, 892), f"— {attribution}", font=attr_f, fill=GOLD)

    # Bottom brand strip
    d.rectangle([(0, H-64),(W, H)], fill="#111111")
    brand_f = _font("BigShoulders-Bold.ttf", 38)
    d.text((60, H-52), "THE FIGHT DOCKET", font=brand_f, fill=RED)

    _watermark(d)
    path = f"{OUT}/{filename}"
    img.save(path, "PNG")
    print(f"✓ Saved: {path}")
    return path


if __name__ == "__main__":
    print("Fight Docket Instagram Templates loaded.")
