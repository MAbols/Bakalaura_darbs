import numpy as np, cv2, os
from pathlib import Path
from bugbot.preprocess import encode_screenshot, keyframes

def test_encode_screenshot(tmp_path: Path):
    img = np.full((50, 50, 3), (0, 0, 255), dtype=np.uint8)   # red square
    f = tmp_path / "shot.png"
    cv2.imwrite(str(f), img)

    b64 = encode_screenshot(f)
    assert b64.startswith("iVBOR")          # PNG magic after Base64

def test_keyframes_sample(tmp_path: Path):
    vid = tmp_path / "tiny.mp4"
    out = cv2.VideoWriter(
        str(vid), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 64)
    )
    for _ in range(30):                     # 3 s of black video @10 fps
        out.write(np.zeros((64, 64, 3), np.uint8))
    out.release()

    frames = keyframes(vid, every=1.0, max_frames=4)
    assert len(frames) == 3                 # 0 s, 1 s, 2 s
