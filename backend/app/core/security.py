"""Request logging, security headers and a small in-process rate limiter.

The limiter is per process and keyed on the socket peer address. Behind a reverse proxy run
uvicorn with ``--proxy-headers`` and ``FORWARDED_ALLOW_IPS`` set to the proxy so the real
client address is used. It is a basic abuse guard, not a substitute for edge rate limiting.
"""
from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

log = logging.getLogger("app.request")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = uuid.uuid4().hex[:12]
        started = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:  # path only: query strings may contain user-supplied text
            log.info("request", extra={
                "request_id": request_id, "method": request.method, "path": request.url.path,
                "status": status, "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            })


class RateLimitMiddleware(BaseHTTPMiddleware):
    WINDOW_S = 60.0

    def __init__(self, app, limit_per_minute: int, exempt_paths: tuple[str, ...] = ("/api/health",)):
        super().__init__(app)
        self._limit = limit_per_minute
        self._exempt = exempt_paths
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._limit <= 0 or request.url.path in self._exempt:
            return await call_next(request)
        now = time.monotonic()
        client = request.client.host if request.client else "unknown"
        hits = self._hits[client]
        while hits and now - hits[0] > self.WINDOW_S:
            hits.popleft()
        if len(hits) >= self._limit:
            retry_after = max(1, int(self.WINDOW_S - (now - hits[0])))
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429,
                                headers={"Retry-After": str(retry_after)})
        hits.append(now)
        if len(self._hits) > 10_000:  # bound memory: drop idle clients
            for key in [k for k, v in self._hits.items() if not v or now - v[-1] > self.WINDOW_S]:
                del self._hits[key]
        return await call_next(request)
