#!/usr/bin/env python
"""
Quick probe: do all three LLMs see these images?

Usage
-----
poetry run python scripts/test_multimodal_models.py <image1> [<image2> ...]
"""

import sys, os
import base64
import asyncio

# ─── TEST-ONLY API-KEY OVERRIDES ─────────────────────────────────────────────
# Replace the strings below with your real keys:
os.environ["OPENAI_API_KEY"]    = 
# ─────────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv()  # still safe to call, but hard-coded above takes precedence

# now pull them back out
OPENAI_KEY    = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_KEY")
GOOGLE_KEY    = os.getenv("GOOGLE_API_KEY")

assert OPENAI_KEY,    "OPENAI_API_KEY is missing"
assert ANTHROPIC_KEY, "ANTHROPIC_KEY is missing"
assert GOOGLE_KEY,    "GOOGLE_API_KEY is missing"

# Import each client
import openai, anthropic, google.generativeai as genai

# Initialize clients
openai_client   = openai.AsyncOpenAI(api_key=OPENAI_KEY)
anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)
genai.configure(api_key=GOOGLE_KEY)
gemini_model    = genai.GenerativeModel("gemini-2.0-flash-lite-001")

async def run_openai(img_bytes_list):
    parts = [{"type":"text","text":"Describe this image"}]
    for b in img_bytes_list:
        b64 = base64.b64encode(b).decode()
        parts.insert(0, {
            "type":"image_url",
            "image_url":{"url":f"data:image/png;base64,{b64}"}
        })
    resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
          {"role":"system","content":"You are a helpful assistant."},
          {"role":"user", "content": parts},
        ]
    )
    return resp.choices[0].message.content

async def run_claude(img_bytes_list):
    contents = []
    for b in img_bytes_list:
        contents.append({
            "type":"image",
            "source":{
                "type":"base64",
                "media_type":"image/png",
                "data":base64.b64encode(b).decode()
            }
        })
    contents.append({"type":"text","text":"Describe this image"})
    resp = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        system="You are a helpful assistant.",
        messages=[{"role":"user","content":contents}],
        max_tokens=500
    )
    return resp.content[0].text

def run_gemini(img_bytes_list):
    parts = []
    for b in img_bytes_list:
        parts.append({"mime_type":"image/png","data":b})
    parts.append("You are a helpful assistant. Describe this image.")
    return gemini_model.generate_content(parts).text

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_multimodal_models.py <img1> [<img2> ...]")
        sys.exit(1)

    # load all images
    img_paths = sys.argv[1:]
    img_bytes = [open(p, "rb").read() for p in img_paths]

    print("=== GPT-4o-mini ===")
    try:
        o = await run_openai(img_bytes)
        print(o, "\n")
    except Exception as e:
        print("ERROR:", e, "\n")

    print("=== Claude-3.5-sonnet ===")
    try:
        c = await run_claude(img_bytes)
        print(c, "\n")
    except Exception as e:
        print("ERROR:", e, "\n")

    print("=== Gemini-2.0-flash-lite-001 ===")
    try:
        g = run_gemini(img_bytes)
        print(g, "\n")
    except Exception as e:
        print("ERROR:", e, "\n")

if __name__ == "__main__":
    asyncio.run(main())
