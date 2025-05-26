from atlassian import Jira
from bugbot.config import get_settings
from pathlib import Path
import logging
settings = get_settings()
log = logging.getLogger(__name__)
if not all([settings.jira_base, settings.jira_user,
            settings.jira_token, settings.jira_project]):
    raise RuntimeError("JIRA_* env vars missing")

_jira = Jira(
    url=settings.jira_base,
    username=settings.jira_user,
    password=settings.jira_token,
    cloud=True,
    api_version='2',
)

SEVERITY_TO_PRIORITY = {
    "critical": "Highest",
    "major":    "High",
    "minor":    "Medium",
}

def create_issue(draft: dict, files: list[Path]) -> str:
    """Return the created issue key, e.g. BUG-123."""
    description = (
        "*Steps to reproduce*\n"
        + "\n".join(f"# {s}" for s in draft["steps"])
        + "\n\n*Expected*\n"   + draft["expected"]
        + "\n\n*Actual*\n"     + draft["actual"]
    )

    issue = _jira.issue_create({
        "project": {"key": settings.jira_project},
        "summary": draft["title"],
        "description": description,
        "issuetype": {"name": "Bug"},
        "priority":  {"name": SEVERITY_TO_PRIORITY[draft["severity"]]},
    })

    key = issue["key"]

    # 3) attach every real file, skip stubs
    for f in files:
        if not f.exists():
            log.warning("attachment %s not found, skipping", f)
            continue

        # Jira.add_attachment signature is (issue_key, attachment, filename=None)
        try:
            _jira.add_attachment(key, str(f))
        except Exception as e:
            log.error("failed to attach %s to %s: %s", f, key, e)

    return key
