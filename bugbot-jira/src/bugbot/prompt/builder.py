from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Folder containing this file → /prompt/
_BASE = Path(__file__).resolve().parent
_env = Environment(
    loader=FileSystemLoader(_BASE / "templates"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)

def build(ctx: dict, template: str = "bug_report.j2") -> str:
    """
    Render *template* with the supplied context dict.

    Parameters
    ----------
    ctx : dict
        Keys used inside the Jinja template.
    template : str
        Template filename relative to /prompt/templates.
    """
    tpl = _env.get_template(template)
    return tpl.render(**ctx)
