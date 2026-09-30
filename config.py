"""Environment-driven configuration for the MCP server."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "contacts.db"))
DEBUG = os.environ.get("MCP_DEBUG", "false").lower() == "true"

# Comma-separated list of Host header values this server should accept, e.g.
# "your-domain.example.com" or a bare IP like "203.0.113.5". Leave unset for
# local development; set it in production to enable DNS-rebinding protection.
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]

# Per-client-IP request cap, since this server has no authentication.
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "120"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))

DOGRAH_API_ENDPOINT = os.environ.get(
    "DOGRAH_API_ENDPOINT", "https://zyli.zoftcares.com"
).rstrip("/")
# Loader script host for the Dograh widget. Defaults to a local dev instance —
# override with the real deployment host when running outside localhost.
DOGRAH_WIDGET_SRC = os.environ.get(
    "DOGRAH_WIDGET_SRC", "http://localhost:3010/embed/dograh-widget.js"
)
DOGRAH_WIDGET_TOKEN = os.environ.get(
    "DOGRAH_WIDGET_TOKEN", "emb_oHIwUz_gC67zPoqNZYvYMhMUOZd0MmSPFjw5ASvclgY"
)
