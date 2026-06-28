#!/usr/bin/env python3
"""Temporary draft generator using pre-fetched news content (Firecrawl credits exhausted)."""
import os, json
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path.home() / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

ROOT    = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

TODAY        = date.today()
DATE_DISPLAY = TODAY.strftime("%B %d, %Y").upper()
DATE_SLUG    = TODAY.strftime("%b%d_%Y").lower()
DATE_ISO     = TODAY.isoformat()

NEWS_CONTENT = """
=== ESPN Boxing / MMA ===
FIGHT RESULTS (this week):
- Oleksandr Usyk (25-0, 16 KOs) defeated Rico Verhoeven via controversial Round 11 TKO stoppage to retain heavyweight titles. Verhoeven has filed a protest. Usyk's coach Peter Fury called for a rematch. Usyk stated he is "unbothered" by the controversy. Turki Alalshikh hopes Usyk will face Kabayel and have rematches. Usyk announced another special event in 2027.
- Jack Catterall won the WBA regular lightweight belt via decision over Shakhram Giyasov, including a first-round knockdown. Catterall wants Rolando Romero next.
- Hamzah Sheeraz stopped Alem Begic in Round 2 to capture the vacant WBO super welterweight belt — his first world title.
- Keyshawn Davis (15-0) dominated Nahir Albright in a rematch but missed weight for the SECOND TIME in three fights — a serious red flag for his lightweight campaign and Top Rank/DAZN partnership.
- Siyakholwa Kuse won WBC strawweight title over Melvin Jerusalem.

UPCOMING FIGHTS:
- O'Shaquie Foster vs. Anthony Ford, May 30, Fertitta Center, Houston TX, DAZN (WBC super featherweight title defense)
- Xander Zayas vs. Jaron Ennis; Ben Whittaker vs. Richard Rivera — June 27, DAZN, Brooklyn
- Edward Vazquez vs. Daniel Lugo — June 5, ProBox TV, Arlington, Texas
- Canelo Alvarez vs. Christian Mbilli — September 2026

UFC/MMA:
- UFC Freedom 250: Michael Chandler defeated Tony Ferguson via knockout
- Conor McGregor returning vs Max Holloway for International Fight Week
- Colby Covington notified UFC of retirement
- PFL Brussels: Henderson KO by Habirora in 20 seconds

=== Boxing Scene ===
- Frank Sanchez defeated Richard Torrez decisively and called out Usyk
- Usyk vs Verhoeven scorecards showed Usyk winning before the stoppage; calls for rematch growing
- Verhoeven's corner did NOT throw the towel — referee stopped it; hence the protest
- Devin Haney potentially facing Rolando Romero next
- Canelo ranked among world highest-paid athletes (Forbes)

=== MAJOR LEGAL/LEGISLATIVE NEWS ===
- Muhammad Ali Boxing Reform Act passed the U.S. House of Representatives. The Act targets fighter pay and contract reforms in professional boxing. This is the most significant boxing legislation in years. Senate passage required for it to become law.

=== Business Intel ===
- Floyd Mayweather suing a former associate for alleged $175 million fraud scheme
- Top Rank staged inaugural DAZN event (Keyshawn Davis headlined) last week — new distribution partnership live. Davis's weight miss complicates the narrative.
- Matchroom Boxing-Bruin Sports Capital alliance announced for US market expansion
- Zuffa Boxing 08: De Los Santos vs. Valenzuela, June 28, Cosmopolitan Las Vegas
- Ring Magazine p4p rankings: Inoue #1, Usyk #2, Shakur Stevenson #3, Jesse Rodriguez #4, Benavidez #5
- Turki Alalshikh's Saudi boxing matchmaking influence continues to grow — post-Usyk/Verhoeven he is actively brokering next fights

=== Johnson v. Zuffa Antitrust Update ===
- Johnson v. Zuffa, LLC (D. Nev. 2:21-cv-01189) — ongoing UFC antitrust case, parties in discovery/pretrial motions, class certification hearings upcoming
"""

SYSTEM_PROMPT = f"""You are the editor of The Fight Docket — an institutional-grade combat sports intelligence newsletter covering the financial, legal, and operational drivers of MMA and professional boxing.

MISSION: Provide definitive, institutional-grade analysis. Target audience: industry professionals, analysts, promoters, agents, and institutional-level stakeholders.

VOICE:
- Authoritative and unbiased. Never hedging, never hype.
- Strategic framing: every story is about what it means operationally or financially.
- Technical precision: case numbers, dollar figures, contract terms, record stats.
- First-person analytical: "My read is...", "The filing reveals...", "What this signals to the market is..."
- Benchmark: Bloomberg Businessweek meets legal trade press, applied to combat sports.

DARK THEME: ALL inline HTML styles must use:
- Body text: color:#F2F2E8
- Secondary/meta text: color:#888888
- Links: color:#DE1E20
- Bold/emphasis: color:#F2F2E8
Do NOT use dark text colors like #333 or #1a1a1a.

TODAY: {DATE_DISPLAY}

Output ONLY valid JSON — no markdown fences:

{{
  "editors_note_html": "<p style='color:#F2F2E8'>...</p>",
  "main_story_headline": "Specific headline max 80 chars",
  "main_story_html": "<p style='color:#F2F2E8'>...</p>",
  "legal_tracker_headline": "The Docket",
  "legal_tracker_html": "...",
  "has_legal_content": true,
  "rumor_mill_html": "...",
  "fight_previews_headline": "What's on Deck",
  "fight_previews_html": "<p style='color:#F2F2E8'>...</p>",
  "business_intel_headline": "Business Intel",
  "business_intel_html": "<p style='color:#F2F2E8'>...</p>",
  "fighter_spotlight_name": "Fighter Full Name",
  "fighter_spotlight_html": "<p style='color:#F2F2E8'>...</p>",
  "image_prompts": [
    {{"section": "thumbnail", "topic": "Newsletter cover image", "prompt": "Wide editorial thumbnail image: a heavyweight boxing champion standing victorious in a flood-lit arena after a controversial stoppage, dramatic silhouette, gold championship belt visible. Cinematic banner composition, dramatic arena spotlight lighting, black background (#0D0D0D), deep crimson red (#DE1E20) and gold (#C5A059) color palette, premium sports magazine cover style, high contrast. No faces clearly visible, no text, no logos, no watermarks."}},
    {{"section": "intro", "topic": "MMA and boxing combat sports intelligence", "prompt": "Two MMA fighters squaring off in an octagon, dramatic silhouette, cinematic arena lighting from above, black background (#0D0D0D), deep crimson red (#DE1E20) and gold (#C5A059) color palette, dark editorial atmosphere, premium sports magazine style. No faces visible, no text, no logos."}},
    {{"section": "main_story", "topic": "Usyk vs Verhoeven controversial stoppage", "prompt": "Dramatic editorial boxing scene: heavyweight champion in the ring under dramatic arena spotlights after a controversial stoppage, referee visible in background, championship belts prominent. Black background with deep red and gold accents, cinematic lighting. No text, no logos."}},
    {{"section": "legal", "topic": "Muhammad Ali Act boxing legislation", "prompt": "Capitol building silhouette merged with boxing gloves and legal scales, dramatic dark editorial composition. Black background, gold and deep red palette, dramatic shadows, premium editorial style. No text, no faces, no logos."}},
    {{"section": "rumor", "topic": "Combat sports intelligence", "prompt": "Shadowy atmospheric scene, dark fight gym or press room, whisper aesthetic, cinematic noir, dramatic directional lighting, black and gold palette. No faces, no text."}},
    {{"section": "fight_previews", "topic": "O'Shaquie Foster vs Anthony Ford", "prompt": "Dramatic face-off between two super featherweight boxers in a championship fight pose, intense expressions, dramatic arena lighting, black background with deep red and gold accents. No text, no logos."}},
    {{"section": "business_intel", "topic": "Combat sports media rights and business", "prompt": "Abstract representation of combat sports business: streaming platform screens, broadcast rights contracts, arena infrastructure. Black background, deep red and gold palette, premium editorial style. No faces, no text, no logos."}},
    {{"section": "fighter_spotlight", "topic": "Hamzah Sheeraz new WBO champion", "prompt": "Dramatic close-up portrait of a world champion boxer raising his first world title belt in victory, cinematic arena lighting, premium sports magazine editorial aesthetic. Black background with deep red and gold light. No text, no logos."}}
  ],
  "ig_data": {{
    "date": "{DATE_DISPLAY}",
    "issue": "{DATE_SLUG}",
    "preview_stories": ["story 1 under 80 chars", "story 2 under 80 chars", "story 3 under 80 chars"],
    "announcement": {{
      "fighter1": "Foster", "fighter2": "Ford",
      "event": "DAZN Boxing", "date": "May 30 · Houston, TX",
      "weight_class": "Super Featherweight", "filename": "foster_vs_ford_announcement.png"
    }},
    "result": {{
      "winner": "Usyk", "loser": "Verhoeven", "method": "TKO",
      "round_num": "R11", "time": "2:30", "event": "Usyk vs. Verhoeven",
      "filename": "usyk_result.png"
    }},
    "quote": {{
      "quote": "It's not my job to worry about controversy. I won.", "attribution": "Oleksandr Usyk",
      "context": "Post-fight press conference", "filename": "usyk_quote_card.png"
    }}
  }}
}}

SECTION REQUIREMENTS:
- editors_note_html: 3 paragraphs. Personal, analytically grounded tone. Set the institutional lens for the week — the theme is: controversy in the ring as a business and regulatory signal.
- main_story_html: 600-800 words, 4-5 paragraphs. MAIN STORY: Usyk stops Verhoeven R11 in controversial fashion. Cover: the stoppage circumstances (referee-stopped, corner did NOT throw towel), Verhoeven's protest, what this means for Turki Alalshikh's Saudi boxing matchmaking ecosystem, Usyk's path forward (Kabayel, Fury rematch, 2027 event), and the broader commercial implications of this result for heavyweight boxing.
- legal_tracker_html: Lead with the Muhammad Ali Boxing Reform Act passing the U.S. House — most significant boxing legislation in years, covers fighter pay and contract reforms, still needs Senate passage. Also include Johnson v. Zuffa (D. Nev. 2:21-cv-01189) status.
- has_legal_content: true
- rumor_mill_html: 3 items with exact color-coded div format. HIGH confidence (#C5A059): Verhoeven-Usyk rematch talks accelerating per Saudi sources. MEDIUM confidence (#888888): Devin Haney vs Rolando Romero being discussed for Q3. LOW confidence (#444444): Canelo camp quietly monitoring Benavidez at 168 as Mbilli fallback.
- fight_previews_html: O'Shaquie Foster vs Anthony Ford (May 30 DAZN, WBC super featherweight) + one other upcoming fight.
- business_intel_html: Floyd Mayweather $175M fraud lawsuit (financial exposure, implications), Top Rank/DAZN inaugural event Davis weight miss (reputational risk for new partnership), Matchroom-Bruin US expansion.
- fighter_spotlight_html: Hamzah Sheeraz — new WBO super welterweight champion. Career arc, British market value, what the Begic stoppage signals about his power, who he fights next (Tim Tszyu? Jermell Charlo?), earnings trajectory.

LEGAL TRACKER FORMAT:
<p style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:2px; color:#DE1E20; margin:0 0 20px 0;">Legislative Update</p>
Then case details. Close with a 1-sentence analytical note.

RUMOR MILL FORMAT (use EXACTLY — HIGH=#C5A059, MEDIUM=#888888, LOW=#444444):
<div style="border-left:3px solid COLOR; padding:4px 0 4px 18px; margin-bottom:28px;"><p style="font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:3px; color:COLOR; margin:0 0 10px 0;">HIGH CONFIDENCE &mdash; 0.85</p><p style="margin:0; color:#F2F2E8; line-height:1.8;">Rumor text here.</p></div>
"""

from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)
prompt = SYSTEM_PROMPT + "\n\nCRAWLED NEWS CONTENT:\n" + NEWS_CONTENT + "\n\nGenerate the newsletter JSON now:"

print(f"Calling Gemini for {DATE_DISPLAY} draft...")
GEMINI_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]

data = None
for model in GEMINI_MODELS:
    try:
        response = client.models.generate_content(
            model=model,
            contents=[prompt],
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)
        print(f"  Generated with {model}")
        break
    except json.JSONDecodeError:
        text = response.text.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
            if text.endswith("```"):
                text = text[:-3]
        try:
            data = json.loads(text)
            print(f"  Generated with {model} (stripped fences)")
            break
        except Exception:
            pass
        print(f"  {model}: JSON parse error")
    except Exception as e:
        print(f"  {model} failed: {str(e)[:80]}")

if not data:
    raise SystemExit("Draft generation failed.")

data["issue_date"]         = DATE_ISO
data["issue_date_display"] = DATE_DISPLAY
data["issue_slug"]         = DATE_SLUG

draft_path   = TMP_DIR / f"newsletter_draft_{DATE_ISO}.json"
prompts_path = TMP_DIR / f"weekly_prompts_{DATE_ISO}.json"
ig_path      = TMP_DIR / f"weekly_ig_data_{DATE_ISO}.json"

draft_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
prompts_path.write_text(json.dumps({"issue_date": DATE_ISO, "prompts": data.get("image_prompts", [])}, indent=2), encoding="utf-8")
ig_path.write_text(json.dumps(data.get("ig_data", {}), indent=2), encoding="utf-8")

print(f"\n  Draft      : {draft_path.name}")
print(f"  Main story : {data.get('main_story_headline','')}")
print(f"  Spotlight  : {data.get('fighter_spotlight_name','')}")
print(f"  Legal      : {data.get('has_legal_content')}")
print(f"  IG stories : {data.get('ig_data', {}).get('preview_stories', [])}")
