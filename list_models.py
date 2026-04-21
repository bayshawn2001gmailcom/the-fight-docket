#!/usr/bin/env python3
"""List available Gemini models to find the correct image generation model name."""
import os, sys
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set"); sys.exit(1)
from google import genai
client = genai.Client(api_key=api_key)
print("\nAll available models:")
for m in client.models.list():
    methods = getattr(m, 'supported_actions', []) or getattr(m, 'supported_generation_methods', [])
    print(f"  {m.name}  |  {methods}")
