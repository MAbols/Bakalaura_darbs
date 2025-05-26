from __future__ import annotations
from typing import List
from pathlib import Path

from bugbot.preprocess import clean_freeform, encode_screenshot, keyframes
from bugbot.prompt     import build
from bugbot.llm.selector import complete_many
from bugbot.ingress.schemas import TicketChoice

# supported extensions
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

async def generate_drafts(
    note: str,
    files: list[Path],          # list of real upload Paths (images & videos)
) -> list[TicketChoice]:
    # 1) Text clean-up
    cleaned = clean_freeform(note)

    # 2) Vision prep: collect base64 frames & raw image bytes
    b64_images: List[str] = []
    raw_bytes:  List[bytes] = []

    for p in files:
        ext = p.suffix.lower()
        if ext in _IMAGE_EXTS:
            # regular image: send the encoded screenshot + raw bytes
            b64_images.append(encode_screenshot(p))
            raw_bytes.append(p.read_bytes())

        elif ext in _VIDEO_EXTS:
            # video: extract keyframes as context, but no raw_bytes
            frames = keyframes(p, every=2.0)
            b64_images.extend(frames)

        else:
            # skip any other file types
            continue

    # 3) Build prompt
    prompt = build({
        "cleaned_text": cleaned,
        "b64_images":   b64_images,
    })

    # 4) Dispatch to all LLM backends
    results = await complete_many(prompt, image_bytes=raw_bytes)

    # 5) Wrap into TicketChoice, override attachments with real filenames
    tickets: list[TicketChoice] = []
    filenames = [p.name for p in files]
    for vendor, draft in results:
        draft["attachments"] = filenames.copy()
        tickets.append(TicketChoice(vendor=vendor, draft=draft))

    return tickets
