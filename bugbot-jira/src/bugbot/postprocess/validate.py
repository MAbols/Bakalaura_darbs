"""
Ticket JSON validation & retry helper.
"""

from __future__ import annotations
from typing import Any, Dict
from pydantic import ValidationError
from bugbot.ingress.schemas import ReportOut

# one extra instruction we’ll append on retry
FIX_JSON_PROMPT = (
    "The previous answer did not match the required JSON schema. "
    "Please respond again using ONLY valid JSON that matches the schema."
)

def validate(ticket: Dict[str, Any]) -> ReportOut:
    """Raise ValidationError if ticket is malformed."""
    return ReportOut.model_validate(ticket)
