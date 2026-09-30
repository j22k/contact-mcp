"""Per-client-IP rate limiting, since this server has no authentication.

In-memory only: state resets on restart and is not shared across replicas.
Fine for a single instance; if this ever runs with multiple workers/replicas,
move the counters to a shared store (e.g. Redis) instead.
"""

import time
from collections import deque

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS

_CLEANUP_EVERY_N_REQUESTS = 1000


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._hits: dict[str, deque[float]] = {}
        self._request_count = 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = _client_ip(Request(scope))
        now = time.monotonic()
        hits = self._hits.setdefault(client_ip, deque())

        while hits and now - hits[0] > RATE_LIMIT_WINDOW_SECONDS:
            hits.popleft()

        if len(hits) >= RATE_LIMIT_MAX_REQUESTS:
            response = JSONResponse(
                {"error": "Too many requests. Please slow down and try again shortly."},
                status_code=429,
                headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
            )
            await response(scope, receive, send)
            return

        hits.append(now)

        self._request_count += 1
        if self._request_count % _CLEANUP_EVERY_N_REQUESTS == 0:
            self._cleanup(now)

        await self.app(scope, receive, send)

    def _cleanup(self, now: float) -> None:
        stale_ips = [
            ip for ip, hits in self._hits.items() if not hits or now - hits[-1] > RATE_LIMIT_WINDOW_SECONDS
        ]
        for ip in stale_ips:
            del self._hits[ip]


def _client_ip(request: Request) -> str:
    # Trusts X-Forwarded-For because this app is only reachable through Caddy
    # in the Docker setup (the app port isn't published to the host). Don't
    # trust this header if the app is ever exposed directly to clients.
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
