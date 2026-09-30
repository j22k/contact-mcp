"""Renders the dashboard and docs pages from the templates/ directory."""

from html import escape
from pathlib import Path

from config import DOGRAH_API_ENDPOINT, DOGRAH_WIDGET_SRC, DOGRAH_WIDGET_TOKEN

TEMPLATES_DIR = Path(__file__).with_name("templates")
DASHBOARD_TEMPLATE = TEMPLATES_DIR / "dashboard.html"
DOCS_TEMPLATE = TEMPLATES_DIR / "docs.html"
STYLESHEET_PATH = Path(__file__).with_name("static") / "style.css"

_COLUMN_LABELS = ("ID", "Name", "Phone", "Email", "Created")


def render_dashboard(contacts: list[tuple]) -> str:
    template = DASHBOARD_TEMPLATE.read_text(encoding="utf-8")
    rows = "".join(_render_row(contact) for contact in contacts) if contacts else _empty_row()

    return (
        template.replace("{{rows}}", rows)
        .replace("{{count}}", str(len(contacts)))
        .replace("{{dograh_widget_src}}", DOGRAH_WIDGET_SRC)
        .replace("{{dograh_widget_token}}", DOGRAH_WIDGET_TOKEN)
        .replace("{{dograh_api_endpoint}}", DOGRAH_API_ENDPOINT)
    )


def render_docs(base_url: str) -> str:
    template = DOCS_TEMPLATE.read_text(encoding="utf-8")
    mcp_endpoint = f"{base_url.rstrip('/')}/mcp"
    return template.replace("{{mcp_endpoint}}", escape(mcp_endpoint))


def read_stylesheet() -> str:
    return STYLESHEET_PATH.read_text(encoding="utf-8")


def _render_row(contact: tuple) -> str:
    contact_id = contact[0]
    cells = "".join(
        f'<td data-label="{label}">{escape(str(value or ""))}</td>'
        for label, value in zip(_COLUMN_LABELS, contact)
    )
    action_cell = (
        '<td data-label="Actions" class="actions-cell">'
        f'<form method="post" action="/contacts/{contact_id}/delete" '
        'onsubmit="return confirm(\'Delete this contact?\');">'
        '<button type="submit" class="delete-btn">Delete</button>'
        "</form></td>"
    )
    return f"<tr>{cells}{action_cell}</tr>"


def _empty_row() -> str:
    return f'<tr class="empty-row"><td colspan="{len(_COLUMN_LABELS) + 1}">No contacts collected yet.</td></tr>'
