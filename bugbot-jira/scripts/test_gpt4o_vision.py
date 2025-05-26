#!/usr/bin/env python
"""
Quick probe: does GPT-4o read the attached image?

Usage
-----
poetry run python scripts/test_gpt4o_vision.py screenshot.png

Requires:
  • OPENAI_API_KEY in env / .env
  • openai>=1.30 installed
"""

from __future__ import annotations
import sys, base64, os, asyncio, openai
from dotenv import load_dotenv
load_dotenv()

if len(sys.argv) != 2:
    sys.exit("Usage: python test_gpt4o_vision.py <image-path>")

IMAGE_PATH = sys.argv[1]
API_KEY = os.getenv("OPENAI_KEY")
if not API_KEY:
    sys.exit("Set OPENAI_API_KEY first.")

img_b64 = base64.b64encode(open(IMAGE_PATH, "rb").read()).decode()
client  = openai.AsyncOpenAI(api_key=API_KEY)

async def main():
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_b64}"
                            },
                        },
                        {"type": "text", "text": "Describe this image."},
                    ],
                }
            ],
            max_tokens=120,
        )
        print("✅  SUCCESS\n", resp.choices[0].message.content.strip())
    except Exception as e:
        import traceback, json
        print("❌  ERROR\n", json.dumps(e.__dict__, default=str, indent=2))
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
