from __future__ import annotations
from pathlib import Path
from typing import Iterable, List

import cv2                      # OpenCV
import numpy as np
from pybase64 import b64encode  # faster

# ────────────────────────── helpers ──────────────────────────

def _b64(img: np.ndarray, *, fmt: str = ".png") -> str:
    """Encode a BGR image → Base64 **string** (no newlines)."""
    ok, buf = cv2.imencode(fmt, img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise ValueError("cv2.imencode failed")
    return b64encode(buf).decode()          # bytes → str


# ───────────────────────── screenshots ───────────────────────

def encode_screenshot(path: str | Path) -> str:
    """
    Load an image from *path* and return a Base64-encoded PNG string.
    Raises FileNotFoundError if the file can’t be read by OpenCV.
    """
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)
    return _b64(img)


# ───────────────────────── videos ────────────────────────────

def keyframes(
    video_path: str | Path,
    *,
    every: float = 2.0,
    max_frames: int | None = 10,
) -> List[str]:
    """
    Return Base64 PNG strings by sampling one frame every *every* seconds.
    Stops after *max_frames* (None = no cap).
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    interval = int(every * fps)
    frames: list[str] = []
    idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if idx % interval == 0:
            frames.append(_b64(frame))
            if max_frames and len(frames) >= max_frames:
                break
        idx += 1

    cap.release()
    return frames
