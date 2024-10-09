from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Callable


class RateLimitInfoMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        if hasattr(request.state, "view_rate_limit"):
            rate_limit = request.state.view_rate_limit
            if isinstance(rate_limit, tuple) and len(rate_limit) == 3:
                limit, remaining, reset = rate_limit
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(reset)
        return response
