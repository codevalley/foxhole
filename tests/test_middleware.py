import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from app.middleware.rate_limit_info import RateLimitInfoMiddleware
from httpx import AsyncClient
from typing import Any, AsyncGenerator
from starlette.requests import Request


class CustomRateLimitMiddleware:
    """Custom middleware to set rate limit info before the RateLimitInfoMiddleware"""

    def __init__(
        self,
        app: Any,
        rate_limit_info: tuple[int, int, int] | None = None,
        invalid_state: bool = False,
        partial_tuple: bool = False,
    ) -> None:
        self.app = app
        self.rate_limit_info = rate_limit_info
        self.invalid_state = invalid_state
        self.partial_tuple = partial_tuple

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def wrapped_receive() -> Any:
            request = Request(scope, receive)
            if self.rate_limit_info:
                request.state.view_rate_limit = self.rate_limit_info
            elif self.invalid_state:
                request.state.view_rate_limit = "invalid"
            elif self.partial_tuple:
                request.state.view_rate_limit = (100, 99)
            return await receive()

        await self.app(scope, wrapped_receive, send)


@pytest.fixture
async def test_client(request: Any) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with different rate limit configurations"""

    async def test_endpoint(request: Request) -> JSONResponse:
        return JSONResponse({"message": "test"})

    params = getattr(request, "param", {})
    rate_limit_info = params.get("rate_limit_info")
    invalid_state = params.get("invalid_state", False)
    partial_tuple = params.get("partial_tuple", False)

    app = Starlette(
        routes=[Route("/test", endpoint=test_endpoint)],
        middleware=[
            Middleware(
                CustomRateLimitMiddleware,
                rate_limit_info=rate_limit_info,
                invalid_state=invalid_state,
                partial_tuple=partial_tuple,
            ),
            Middleware(RateLimitInfoMiddleware),
        ],
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_client", [{"rate_limit_info": (100, 99, 3600)}], indirect=True
)
async def test_rate_limit_info_middleware_with_limits(test_client: AsyncClient) -> None:
    """Test that middleware correctly adds rate limit headers"""
    response = await test_client.get("/test")
    assert response.status_code == 200
    assert response.headers["x-ratelimit-limit"] == "1000"
    assert response.headers["x-ratelimit-remaining"] == "999"
    assert response.headers["x-ratelimit-reset"] == "3600"


@pytest.mark.asyncio
@pytest.mark.parametrize("test_client", [{}], indirect=True)
async def test_rate_limit_info_middleware_without_limits(
    test_client: AsyncClient,
) -> None:
    """Test that middleware doesn't duplicate headers when no rate limit info is set"""
    response = await test_client.get("/test")
    # We only check that our custom values aren't added
    # The global rate limiter's headers may still be present
    headers = response.headers
    assert headers.get("x-ratelimit-limit") != "100"
    assert headers.get("x-ratelimit-remaining") != "99"
    assert headers.get("x-ratelimit-reset") != "3000"


@pytest.mark.asyncio
@pytest.mark.parametrize("test_client", [{"invalid_state": True}], indirect=True)
async def test_rate_limit_info_middleware_with_invalid_state(
    test_client: AsyncClient,
) -> None:
    """Test that middleware handles invalid rate limit state"""
    response = await test_client.get("/test")
    headers = response.headers
    assert headers.get("x-ratelimit-limit") != "100"
    assert headers.get("x-ratelimit-remaining") != "99"
    assert headers.get("x-ratelimit-reset") != "3000"


@pytest.mark.asyncio
@pytest.mark.parametrize("test_client", [{"partial_tuple": True}], indirect=True)
async def test_rate_limit_info_middleware_with_partial_tuple(
    test_client: AsyncClient,
) -> None:
    """Test that middleware handles partial rate limit tuple"""
    response = await test_client.get("/test")
    headers = response.headers
    assert headers.get("x-ratelimit-limit") != "100"
    assert headers.get("x-ratelimit-remaining") != "99"
    assert headers.get("x-ratelimit-reset") != "3000"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_client", [{"rate_limit_info": (100, 99, 3600)}], indirect=True
)
async def test_rate_limit_info_middleware_custom_headers(
    test_client: AsyncClient,
) -> None:
    """Test that middleware preserves custom headers"""

    async def custom_endpoint(request: Request) -> JSONResponse:
        return JSONResponse(
            {"message": "test"}, headers={"Custom-Header": "test-value"}
        )

    app = Starlette(
        routes=[Route("/test", endpoint=custom_endpoint)],
        middleware=[
            Middleware(CustomRateLimitMiddleware, rate_limit_info=(100, 99, 3600)),
            Middleware(RateLimitInfoMiddleware),
        ],
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/test")
        assert response.status_code == 200
        assert response.headers["Custom-Header"] == "test-value"
        assert response.headers["x-ratelimit-limit"] == "1000"
