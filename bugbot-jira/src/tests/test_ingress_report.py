# tests/test_ingress_report.py
import numpy as np, cv2
import pytest, asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from bugbot.ingress.api import app
from bugbot.llm import selector


client = TestClient(app)

def test_report_roundtrip(tmp_path: Path):
    # create a valid 1×1 white PNG
    png = tmp_path / "shot.png"
    cv2.imwrite(str(png), np.full((1, 1, 3), 255, np.uint8))

    resp = client.post(
        "/report",
        data={"note": "OMG 😱 app crashed!"},
        files=[("files", (png.name, png.read_bytes(), "image/png"))],
    )
    j = resp.json()
    assert resp.status_code == 200
    assert j["severity"] == "critical"
    assert "shot.png" in j["attachments"]
@pytest.mark.asyncio
async def test_llm_dry_run(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    out = await selector.complete("Hello world")
    assert isinstance(out, dict)
    assert out["severity"] == "critical"