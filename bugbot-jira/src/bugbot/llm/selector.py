"""Select the first healthy LLM backend (OpenAI ▸ Claude ▸ Gemini)."""

from __future__ import annotations

import asyncio
import json
import logging
import os                             # CHANGED: added for log file path and GenAI SDK config
import base64                         # CHANGED: added for encoding image bytes
from typing import Any, Dict, List
import re

from bugbot.config import get_settings
from bugbot.postprocess.validate import validate, FIX_JSON_PROMPT
from bugbot.ingress.schemas import InvalidDraft
from pydantic import ValidationError

settings = get_settings()
log = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────
# CHANGED: configure a FileHandler so we capture full DEBUG payloads (incl. base64)
LOG_PATH = os.path.join(os.getcwd(), "llm_payload.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
file_h = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
file_h.setLevel(logging.DEBUG)
file_h.setFormatter(
    logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
)
log.addHandler(file_h)
# Also capture external libs
logging.getLogger("openai").addHandler(file_h)
logging.getLogger("anthropic").addHandler(file_h)
# ────────────────────────────────────────────────────────────────────────

# Force every model to answer in strict JSON
JSON_INSTRUCTION = """
You are BugBot, a senior QA assistant.
Respond **only** with valid JSON in this exact schema:
{
  "title": string,
  "steps": string[],          // each list item is one action step
  "expected": string,
  "actual": string,
  "severity": "critical" | "major" | "minor",
  "attachments": string[]     // filenames the tester attached, may be empty
}
 When an image is attached, analyze visible UI elements and error messages to refine *steps*,*expected*, *actual*, and *severity*.
Do NOT add any extra keys or commentary.
""".strip()

def _safe_load(raw: str) -> Dict[str, Any]:
    """
    Best-effort: extract the first {...} block if the model wrapped JSON
    in markdown or added text around it.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            return json.loads(match.group(0))
        raise

# ────────────────────────────────────────────────────────────────────────
# Optional SDK imports (only loaded when DRY_RUN is False)
# ────────────────────────────────────────────────────────────────────────
if not settings.dry_run:
    log.setLevel(logging.DEBUG)
    import openai
    import anthropic
    import google.generativeai as genai
# ────────────────────────────────────────────────────────────────────────

class _Base:
    name: str
    async def chat(self, prompt: str) -> Dict[str, Any]: ...

# ────────────────────────────────────────────────────────────────────────
# OpenAI (GPT-4 / GPT-4o)
# ────────────────────────────────────────────────────────────────────────
class _OpenAI(_Base):
    name = "gpt-4o-mini"

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(api_key=settings.openai_key)

    async def chat(self, prompt: str, *, image_bytes: list[bytes] | None = None):
        content_parts: list[Any] = [{"type": "text", "text": prompt}]
        if image_bytes:
            for b in image_bytes:
                b64 = base64.b64encode(b).decode()
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                })
        messages = [
            {"role": "system", "content": JSON_INSTRUCTION},
            {"role": "user", "content": content_parts},
        ]
        resp = await self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
        )
        # CHANGED: log the exact outgoing payload (truncated in-list for readability)
        log.debug(
            "▶️ OpenAI.chat called\n"
            "    prompt=%r\n"
            "    image_bytes=%d items\n"
            "    messages=%r",
            prompt,
            len(image_bytes or []),
            [{"role": m["role"], "content": (
                m["content"][:100] if isinstance(m["content"], str)
                else f"<{len(m['content'])} parts>"
            )} for m in messages]
        )
        return _safe_load(resp.choices[0].message.content)

# ────────────────────────────────────────────────────────────────────────
# Anthropic Claude 3 Sonnet
# ────────────────────────────────────────────────────────────────────────
class _Claude(_Base):
    name = "claude-3-5-sonnet-20240620"

    def __init__(self):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_key)

    async def chat(self, prompt: str, *, image_bytes: list[bytes] | None = None):
        contents: list[dict] = []
        for b in image_bytes or []:
            contents.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64.b64encode(b).decode()
                }
            })
        contents.append({"type": "text", "text": prompt})

        resp = await self._client.messages.create(
            model=self.name,
            system=JSON_INSTRUCTION,
            messages=[{"role": "user", "content": contents}],
            max_tokens=1024,
        )
        # CHANGED: debug log for Claude payload
        try:
            sent = resp.request.kwargs["json"]["messages"]
        except Exception:
            sent = "‹unable to extract payload›"
        log.debug(
            "▶️ Claude.chat called\n"
            "    prompt=%r\n"
            "    messages=%r",
            prompt,
            sent,
        )
        return _safe_load(resp.content[0].text)

# ────────────────────────────────────────────────────────────────────────
# Gemini via Google Gen-AI SDK (multimodal)
# ────────────────────────────────────────────────────────────────────────
class _GeminiStudio(_Base):
    name = "gemini-2.0-flash-lite-001"

    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self._model = genai.GenerativeModel(self.name)

    async def chat(self, prompt: str, *, image_bytes: list[bytes] | None = None):
        parts: list[Any] = []
        for b in image_bytes or []:
            parts.append({"mime_type": "image/png", "data": b})
        parts.append(JSON_INSTRUCTION)
        parts.append(prompt)

        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(
                parts,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 1024,
                },
            ),
        )
        # CHANGED: (optional) you could log here similarly if desired
        return _safe_load(resp.text)

# ────────────────────────────────────────────────────────────────────────
# Build active client list (order = fallback order)
# ────────────────────────────────────────────────────────────────────────
CLIENTS: list[_Base] = []
if settings.openai_key:
    CLIENTS.append(_OpenAI())
if settings.anthropic_key:
    CLIENTS.append(_Claude())
if os.getenv("GOOGLE_API_KEY"):
    CLIENTS.append(_GeminiStudio())

# ────────────────────────────────────────────────────────────────────────
# Public helper: single complete
# ────────────────────────────────────────────────────────────────────────
async def complete(prompt: str) -> Dict[str, Any]:
    """Return the first successful LLM response as a dict."""
    if settings.dry_run or not CLIENTS:
        log.warning("DRY-RUN mode – returning stub LLM response")
        return {
            "title": prompt[:60].splitlines()[0].capitalize(),
            "steps": ["1. TBD", "2. TBD"],
            "expected": "TBD",
            "actual": "TBD",
            "severity": "critical",
            "attachments": [],
        }

    for client in CLIENTS:
        try:
            return await client.chat(prompt)
        except Exception as exc:
            log.error("LLM %s failed: %s", client.name, exc, exc_info=False)
    raise RuntimeError("All LLM backends failed")

# ────────────────────────────────────────────────────────────────────────
# Public helper: fan-out to all backends
# ────────────────────────────────────────────────────────────────────────
async def complete_many(
    prompt: str,
    *, image_bytes: List[bytes] | None = None
) -> list[tuple[str, Dict[str, Any]]]:
    """
    Run the prompt against every healthy backend in parallel.
    Returns list of (model_name, ticket_json) tuples – order is fixed.
    """
    if settings.dry_run or not CLIENTS:
        return [("stub", await complete(prompt))]  # reuse stub

    async def _call(client: _Base):
        try:
            raw = await client.chat(prompt, image_bytes=image_bytes)
            try:
                validate(raw)
                return client.name, raw
            except ValidationError as ve:
                # one retry with fixer instruction
                try:
                    fixed_raw = await client.chat(
                        prompt + "\n\n" + FIX_JSON_PROMPT,
                        image_bytes=image_bytes,
                    )
                    validate(fixed_raw)
                    return client.name, fixed_raw
                except ValidationError as ve2:
                    return client.name, InvalidDraft(
                        error=f"validation failed: {ve2.errors()[:2]}",
                        raw=fixed_raw if 'fixed_raw' in locals() else raw,
                    ).model_dump()
        except Exception as exc:
            log.error("LLM %s failed: %s", client.name, exc, exc_info=False)
            return client.name, {"error": str(exc)}

    return await asyncio.gather(*(_call(c) for c in CLIENTS))
