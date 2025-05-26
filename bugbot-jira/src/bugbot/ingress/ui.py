from fastapi import APIRouter, Request, UploadFile, Form, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from bugbot.ingress.logic import generate_drafts   # reuse the same logic
from bugbot.llm.selector import complete_many
import uuid, os, tempfile, base64, json, shutil
from pathlib import Path
from bugbot.jira.client   import create_issue

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload_form.html", {"request": request})

@router.post("/drafts", response_class=HTMLResponse)
async def get_drafts(
    request: Request,
    note: str = Form(...),
    files: list[UploadFile] = File(None),
):
    # 1) Persist each UploadFile to disk
    saved: list[Path] = []
    for f in files or []:
        dest = UPLOAD_DIR / f"{uuid.uuid4()}{Path(f.filename).suffix}"
        with dest.open("wb") as out_f:
            shutil.copyfileobj(f.file, out_f)
        saved.append(dest)

    # 2) Call generate_drafts with the real Paths
    resp = await generate_drafts(note, saved)

    return templates.TemplateResponse(
        "ticket_cards.html",
        {"request": request, "tickets": resp}
    )

@router.post("/push")
async def push_to_jira(
    vendor: str       = Form(...),
    draft: str        = Form(...),
    title: str        = Form(...),
    steps: str        = Form(...),
    expected: str     = Form(...),
    actual: str       = Form(...),
    severity: str     = Form(...),
):
    # parse the original draft...
    draft_obj = json.loads(draft)

    # overwrite with whatever the tester just edited:
    draft_obj["title"]    = title
    # split the steps textarea into a list, dropping empty lines
    draft_obj["steps"]    = [line for line in steps.splitlines() if line.strip()]
    draft_obj["expected"] = expected
    draft_obj["actual"]   = actual
    draft_obj["severity"] = severity

    # now rebuild the real file Paths out of the stored filenames
    tmpdir = Path(tempfile.mkdtemp())
    files: list[Path] = []
    for b64name in draft_obj.get("attachments", []):
        if b64name.startswith("data:"):
            header, data = b64name.split(",", 1)
            ext = header.split("/")[1].split(";")[0]
            fp = tmpdir / f"{uuid.uuid4()}.{ext}"
            fp.write_bytes(base64.b64decode(data))
        else:
            fp = UPLOAD_DIR / b64name
        files.append(fp)

    # create the JIRA issue
    try:
        key = create_issue(draft_obj, files)
        return HTMLResponse(
            f"<div class='card'><h3>{vendor}</h3>"
            f"<p>✅ Sent to JIRA as <strong>{key}</strong></p></div>"
        )
    except Exception as e:
        return HTMLResponse(
            f"<div class='card'><h3>{vendor}</h3>"
            f"<p style='color:red'>❌ JIRA error: {e}</p></div>"
        )
