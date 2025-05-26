from __future__ import annotations
from fastapi import FastAPI, File, UploadFile, Form
from bugbot.ingress.schemas import TicketChoice
from bugbot.ingress.logic  import generate_drafts
from bugbot.ingress        import ui
import logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title="BugBot API", version="0.1.0")   # ① create app first
app.include_router(ui.router)                        # ② mount UI pages


@app.post(
    "/report",
    response_model=list[TicketChoice],
    summary="Create draft JIRA ticket(s) from every LLM",
)
async def create_report(
    note: str = Form(..., description="Free-form tester note"),
    files: list[UploadFile] = File(default=[]),
):
    # One call does everything: preprocess → LLMs → validation
    return await generate_drafts(note, files)        # ③


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
