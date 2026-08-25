#!/usr/bin/env python3
"""Generate -> compress -> upload the 7 section images for one issue.
Compression happens BEFORE the ImgBB upload (the open item in newsletter-image-weight)."""
import os, sys, json, time, io
from pathlib import Path
import requests
from dotenv import load_dotenv
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

DATE = "2026-08-24"
ASSETS = ROOT / "assets" / "newsletter_images"
TMP = ROOT / ".tmp" / "newsletter_images"
TMP.mkdir(parents=True, exist_ok=True)

GEMINI = os.getenv("GEMINI_API_KEY", "").strip().strip("'\"")
IMGBB = os.getenv("IMGBB_API_KEY", "").strip().strip("'\"")

prompts = {p["section"]: p["prompt"] for p in
           json.loads((ROOT / "prompts" / "weekly_prompts.json").read_text(encoding="utf-8"))["prompts"]}

from google import genai
from google.genai import types
client = genai.Client(api_key=GEMINI)
cfg = types.GenerateContentConfig(
    response_modalities=["IMAGE"],
    image_config=types.ImageConfig(aspect_ratio="16:9", image_size="2K"),
)

def gen(prompt):
    for attempt in range(1, 5):
        try:
            r = client.models.generate_content(
                model="gemini-3.1-flash-image-preview", contents=[prompt], config=cfg)
            for part in r.parts:
                if part.inline_data is not None:
                    return part.inline_data.data
            print("    no image part returned")
        except Exception as e:
            m = str(e)
            print(f"    attempt {attempt} error: {m[:160]}")
            if any(x in m for x in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")):
                time.sleep(20 * attempt)
            else:
                time.sleep(5)
    return None

def compress(src: Path, dst: Path, width=1200, q=82):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w > width:
        im = im.resize((width, round(h * width / w)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
    return dst.stat().st_size

def upload(path: Path):
    for attempt in range(1, 4):
        try:
            with open(path, "rb") as f:
                r = requests.post("https://api.imgbb.com/1/upload",
                                  params={"key": IMGBB}, files={"image": f}, timeout=90)
            if r.ok:
                return r.json()["data"]["url"]
            print(f"    imgbb {r.status_code}: {r.text[:120]}")
        except Exception as e:
            print(f"    imgbb error: {e}")
        time.sleep(5)
    return ""

urls = {}
out_json = TMP / f"urls_{DATE}.json"
if out_json.exists():
    urls = json.loads(out_json.read_text())

for section, prompt in prompts.items():
    full = ASSETS / f"nb2_{DATE}_{section}.jpg"
    web = TMP / f"nb2_{DATE}_{section}_web.jpg"
    if section in urls:
        print(f"[{section}] already uploaded, skipping")
        continue
    if not full.exists():
        print(f"[{section}] generating...")
        b = gen(prompt)
        if not b:
            print(f"[{section}] FAILED")
            continue
        full.write_bytes(b)
        print(f"[{section}] saved {full.stat().st_size//1024} KB")
    size = compress(full, web)
    print(f"[{section}] compressed -> {size//1024} KB")
    u = upload(web)
    if u:
        urls[section] = u
        print(f"[{section}] {u}")
    out_json.write_text(json.dumps(urls, indent=2))

# thumbnail = main story image
if (TMP / f"nb2_{DATE}_main_story_web.jpg").exists():
    import shutil
    shutil.copy(TMP / f"nb2_{DATE}_main_story_web.jpg", TMP / f"nb2_{DATE}_thumbnail.jpg")
    print("thumbnail written")

print(json.dumps(urls, indent=2))
print(f"{len(urls)}/7 uploaded")
