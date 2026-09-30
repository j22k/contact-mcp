# User Information Collector MCP Server

An MCP (Model Context Protocol) server that collects contact information via tools and stores it in a local SQLite database. Includes a browser dashboard for viewing and deleting records.

## Run locally

```powershell
uv sync
uv run .\main.py
```

The server listens on `http://localhost:8008`.

| Page | Purpose |
|---|---|
| `http://localhost:8008/` | Contacts dashboard (view, delete) |
| `http://localhost:8008/docs` | How-to-use reference |
| `http://localhost:8008/mcp` | MCP streamable-HTTP endpoint for clients |

## Run with Docker

```bash
docker compose up -d --build
```

This runs the app behind [Caddy](https://caddyserver.com/) as a reverse proxy. Set `ALLOWED_HOSTS` to this VPS's public IP (e.g. in a `.env` file: `ALLOWED_HOSTS=203.0.113.5`) — compose refuses to start without it. Contact data persists in a named Docker volume (`contacts-data`) across rebuilds.

By default [Caddyfile](Caddyfile) serves plain HTTP on port 80, since there's no domain to get an automatic HTTPS certificate for. Once you point a domain's A record at this VPS, switch to the domain-based block described in `Caddyfile`'s comments — Caddy will then handle HTTPS automatically, and `ALLOWED_HOSTS` should be updated to match.

## Tools

### `insert_contact`

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Trimmed; rejected if empty |
| `phone_number` | string | no | Defaults to empty |
| `email` | string | no | Lowercased; must be unique if provided |

### `delete_contact`

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `contact_id` | integer | yes | The contact's `id`, shown on the dashboard |

Full parameter tables and example calls are on the `/docs` page once the server is running.

## Configuration

Set these as environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_PATH` | `./contacts.db` | Where the SQLite file lives |
| `MCP_DEBUG` | `false` | Enables debug mode and verbose logging |
| `ALLOWED_HOSTS` | *(none — required in Docker)* | Comma-separated Host header(s) to accept, e.g. `203.0.113.5` or `your-domain.example.com`. Enables DNS-rebinding protection; must match the address in `Caddyfile`. |
| `RATE_LIMIT_MAX_REQUESTS` | `120` | Max requests per client IP per window, across all routes (dashboard, delete, `/mcp`). Responds `429` once exceeded. |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window length in seconds for the rate limit above. |

## Security status

There is currently **no authentication** on the dashboard, the delete action, or the `/mcp` endpoint — anyone who can reach the server can read, insert, or delete contacts. This is a deliberate decision to keep the server open to any client; revisit before storing real PII long-term. Two mitigations are in place given that: `ALLOWED_HOSTS` (DNS-rebinding protection) and a per-IP rate limit (`RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`, see [ratelimit.py](ratelimit.py)) — the rate limit is in-memory per instance, so it resets on restart and won't coordinate across multiple replicas. Without a domain, traffic is also unencrypted (plain HTTP) — don't rely on this for sensitive data until you add a domain (for HTTPS) and, ideally, auth. Reasonable options when ready: HTTP basic auth in `Caddyfile`, a bearer-token check in `main.py`, or restricting `Caddyfile` to an IP allowlist/VPN.

## Project layout

| File | Responsibility |
|---|---|
| `main.py` | FastMCP setup, tools, and HTTP routes |
| `config.py` | Environment-driven configuration |
| `db.py` | SQLite schema and queries |
| `ratelimit.py` | Per-IP rate-limiting middleware |
| `templates.py` | Renders `templates/*.html` |
| `templates/dashboard.html` | Contacts page |
| `templates/docs.html` | How-to-use page |
| `static/style.css` | Shared styling for both pages |
