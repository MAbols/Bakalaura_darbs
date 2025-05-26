#!/usr/bin/env python3
"""
Probe your real _OpenAI, _Claude and _GeminiStudio adapters
but remove the JSON_INSTRUCTION so they’ll freely describe images.

Usage:
    poetry run python scripts/test_selector_path_nojson.py <img1> [<img2> …]
"""

import sys, asyncio, base64, os
# ─── ensure `src/` is on the import path ────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))      # e.g. .../src/tests
ROOT = os.path.dirname(HERE)                           # .../src
sys.path.insert(0, ROOT)
# ──────────────────────────────────────────────────────────────────────
# 1) Disable the JSON‐only system prompt
import bugbot.llm.selector as selector_module
selector_module.JSON_INSTRUCTION = ""
selector_module._safe_load = lambda raw: raw

# 2) Now import your real adapters
from bugbot.llm.selector import _OpenAI, _Claude, _GeminiStudio

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_selector_path_nojson.py <img1> [<img2> …]")
        return

    # read raw bytes
    imgs = [open(p, "rb").read() for p in sys.argv[1:]]

    prompt = "Describe this image."

    clients = [
        _OpenAI(),
        _Claude(),
        _GeminiStudio(),
    ]

    for client in clients:
        print(f"\n=== {client.name} ===")
        try:
            # pass same raw bytes to each
            resp = await client.chat(prompt, image_bytes=imgs)
            # pretty-print whatever comes back
            if isinstance(resp, dict):
                # sometimes safe_load still wraps dicts
                import json
                print(json.dumps(resp, indent=2))
            else:
                print(resp)
        except Exception as e:
            print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(main())
