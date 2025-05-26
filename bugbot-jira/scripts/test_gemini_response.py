#!/usr/bin/env python
"""
Verify that your GOOGLE_API_KEY can successfully call a Gemini model.

Usage
-----
poetry run python scripts/test_gemini_key.py \
       --model gemini-2.0-flash-lite-001 \
       --prompt "Ping"

# or rely on env/defaults:
poetry run python --env-file .env scripts/test_gemini_key.py
"""

from __future__ import annotations
import argparse, os, sys, textwrap
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

# ── CLI & env -----------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--model",  default=os.getenv("MODEL_ID", "gemini-2.0-flash-lite-001"),
                    help="Model ID to test (default: gemini-1.0-pro)")
parser.add_argument("--prompt", default=os.getenv("PROMPT", "Ping"),
                    help='Prompt to send (default: "Ping")')
args = parser.parse_args()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    sys.exit("❌  Set GOOGLE_API_KEY in your shell or .env first.")

# ── Call the model ------------------------------------------------------------
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(args.model)

print(textwrap.dedent(f"""\
    ▸ Testing Gemini model: {args.model}
    ▸ Prompt: {args.prompt!r}
"""))

try:
    resp = model.generate_content(args.prompt, stream=False)
    print("✅  CALL SUCCEEDED")
    print("-" * 40)
    print(resp.text.strip() or "(empty response)")
    print("-" * 40)
    sys.exit(0)
except Exception as e:
    print("❌  CALL FAILED")
    print(e)
    sys.exit(1)
