from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field, ValidationError



class ReportOut(BaseModel):
    title: str
    steps: List[str]
    expected: str
    actual: str
    severity: str
    attachments: List[str]


# For multipart/form-data we’ll read fields directly in the route, so no “ReportIn”.
class TicketChoice(BaseModel):
    vendor: str          # "gpt-4o", "claude-3-haiku-20240307", …
    draft:  Dict[str, Any]

class InvalidDraft(BaseModel):
    error: str            # human-readable message
    raw:   Dict[str, Any]  # original model output (still returned to UI)