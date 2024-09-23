from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitInfoMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
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
