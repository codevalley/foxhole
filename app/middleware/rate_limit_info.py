from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Callable


class RateLimitInfoMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        if hasattr(request.state, "view_rate_limit"):
            response.headers["X-RateLimit-Limit"] = str(
                request.state.view_rate_limit.limit
            )
            response.headers["X-RateLimit-Remaining"] = str(
                request.state.view_rate_limit.remaining
            )
            response.headers["X-RateLimit-Reset"] = str(
                request.state.view_rate_limit.reset
            )
        return response
