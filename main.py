import logging
import sqlite3

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from config import ALLOWED_HOSTS, DEBUG
from db import delete_contact_row, fetch_contacts, initialize_database, insert_contact_row
from ratelimit import RateLimitMiddleware
from templates import read_stylesheet, render_dashboard, render_docs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mcp-server")

initialize_database()

if ALLOWED_HOSTS:
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=ALLOWED_HOSTS,
        allowed_origins=[f"https://{host}" for host in ALLOWED_HOSTS] + [f"http://{host}" for host in ALLOWED_HOSTS],
    )
else:
    logger.warning("ALLOWED_HOSTS is not set — DNS-rebinding protection is disabled. Set it in production.")
    transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

mcp = FastMCP(
    "User Information Collector",
    host="0.0.0.0",
    port=8008,
    debug=DEBUG,
    log_level="DEBUG" if DEBUG else "INFO",
    transport_security=transport_security,
)


@mcp.tool()
def insert_contact(name: str, phone_number: str = "", email: str = "") -> str:
    """Collect and store a user's name, phone number, and optional email address."""
    logger.info("TOOL INVOCATION: insert_contact(name=%r, phone_number=%r, email=%r)", name, phone_number, email)

    name = name.strip()
    phone_number = phone_number.strip()
    email = email.strip().lower()

    if not name:
        logger.warning("Tool execution rejected: Name is required.")
        return "Name is required."

    try:
        contact_id = insert_contact_row(name, phone_number, email or None)
        logger.info("Contact '%s' inserted with id %s", name, contact_id)
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            logger.warning("Duplicate entry for email: %s", email)
            return f"A contact with email {email} already exists."
        logger.error("Database integrity error: %s", error)
        raise

    return f"Contact {name} inserted with id {contact_id}."


@mcp.tool()
def delete_contact(contact_id: int) -> str:
    """Delete a stored contact by its ID."""
    if not delete_contact_row(contact_id):
        logger.warning("Delete requested for missing contact id %s", contact_id)
        return f"No contact found with id {contact_id}."
    logger.info("Contact %s deleted", contact_id)
    return f"Contact {contact_id} deleted."


@mcp.custom_route("/", methods=["GET"], include_in_schema=False)
async def contacts_dashboard(request: Request) -> HTMLResponse:
    """Display the collected contacts in a simple browser page."""
    return HTMLResponse(render_dashboard(fetch_contacts()))


@mcp.custom_route("/contacts/{contact_id}/delete", methods=["POST"], include_in_schema=False)
async def delete_contact_route(request: Request) -> RedirectResponse:
    """Delete a contact from the dashboard's delete button, then redirect back."""
    contact_id = int(request.path_params["contact_id"])
    delete_contact_row(contact_id)
    return RedirectResponse(url="/", status_code=303)


@mcp.custom_route("/docs", methods=["GET"], include_in_schema=False)
async def docs_page(request: Request) -> HTMLResponse:
    """Explain the available tools and how to connect an MCP client."""
    return HTMLResponse(render_docs(base_url=str(request.base_url)))


@mcp.custom_route("/static/style.css", methods=["GET"], include_in_schema=False)
async def stylesheet(request: Request) -> Response:
    return Response(read_stylesheet(), media_type="text/css")


app = mcp.streamable_http_app()
app.add_middleware(RateLimitMiddleware)

if __name__ == "__main__":
    # Serving `app` directly (rather than mcp.run()) so the rate-limit
    # middleware attached above actually applies — mcp.run() would otherwise
    # rebuild a fresh app internally and silently drop it.
    import uvicorn

    logger.info("Starting FastMCP server in streamable-http mode on port 8008...")
    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="debug" if DEBUG else "info")
