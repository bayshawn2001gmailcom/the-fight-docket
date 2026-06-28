#!/usr/bin/env python3
import os, json, sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
IMGBB_API_KEY  = os.getenv("IMGBB_API_KEY", "")

prompts_file = ROOT / ".tmp" / "weekly_prompts_2026-06-22.json"
prompts = json.loads(prompts_file.read_text())
thumb   = next(p for p in prompts["prompts"] if p["section"] == "thumbnail")
prompt  = thumb["prompt"]

print("Generating thumbnail via Gemini...")
from google import genai
from google.genai import types
import requests

client = genai.Client(api_key=GEMINI_API_KEY)

for model in ["gemini-2.0-flash-preview-image-generation", "gemini-3.1-flash-image-preview"]:
    try:
        resp = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="16:9"),
            )
        )
        for part in resp.parts:
            if part.inline_data:
                ext = "jpg" if "jpeg" in part.inline_data.mime_type else "png"
                out = ROOT / ".tmp" / "newsletter_images" / f"nb2_2026-06-22_thumbnail.{ext}"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(part.inline_data.data)
                print(f"  Saved: {out.name} ({len(part.inline_data.data)//1024} KB)")

                with open(out, "rb") as f:
                    r = requests.post("https://api.imgbb.com/1/upload",
                        params={"key": IMGBB_API_KEY}, files={"image": f}, timeout=60)
                r.raise_for_status()
                url = r.json()["data"]["url"]
                print(f"  ImgBB URL: {url}")

                asset_file = ROOT / ".tmp" / "asset_urls_2026-06-22.json"
                existing = json.loads(asset_file.read_text()) if asset_file.exists() else {}
                existing["thumbnail"] = url
                asset_file.write_text(json.dumps(existing, indent=2))
                print("  Updated asset_urls_2026-06-22.json")
                sys.exit(0)

        print(f"  {model}: no image in response, trying next...")
    except Exception as e:
        print(f"  {model}: {e}")

print("FAILED — could not generate thumbnail")
sys.exit(1)
