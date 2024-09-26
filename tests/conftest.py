import pytest
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from app.app import app
from tests.mocks.mock_storage_service import MockStorageService
from httpx import AsyncClient
from fastapi.testclient import TestClient
from typing import AsyncGenerator, Any, Callable, Awaitable
from app.services.websocket_manager import WebSocketManager
from utils.database import create_tables, engine, AsyncSessionLocal
import warnings
from fastapi import Response
from app.core.rate_limit import limiter
from fastapi import Request


# Remove the custom event_loop fixture

# Add this at the top of the file to suppress DeprecationWarnings from jwt and minio
warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.jwt")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="minio.time")


@pytest.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    await create_tables()  # Create tables before running tests
    yield engine


@pytest.fixture(scope="function")
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_user(
    async_client: AsyncClient, db_session: AsyncSession
) -> dict:
    user_data = {"screen_name": "testuser"}
    response = await async_client.post("/auth/register", json=user_data)
    assert response.status_code == 200, f"Registration failed: {response.text}"
    user_info = response.json()

    token_response = await async_client.post(
        "/auth/token", data={"user_secret": user_info["user_secret"]}
    )
    assert (
        token_response.status_code == 200
    ), f"Token retrieval failed: {token_response.text}"
    token = token_response.json()["access_token"]

    return {"token": token, "user_data": user_info}


@pytest.fixture
def websocket_manager() -> WebSocketManager:
    return WebSocketManager()


@pytest.fixture(autouse=True)
def configure_logging() -> None:
    import logging

    logging.basicConfig(level=logging.INFO)


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_storage_service() -> MockStorageService:
    return MockStorageService()


class DummyLimiter:
    async def __call__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def reset(self) -> None:
        pass


@pytest.fixture(autouse=True)
def disable_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_limiter = DummyLimiter()

    # Replace the limiter on the FastAPI app
    app.state.limiter = dummy_limiter

    # Replace all limited routes with unlimited ones
    for route in app.routes:
        if hasattr(route, "decorators"):
            route.decorators = [
                d for d in route.decorators if not isinstance(d, limiter.__class__)
            ]


@pytest.fixture(autouse=True)
def mock_rate_limit_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_dispatch(
        self: Any, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = "1000"
        response.headers["X-RateLimit-Remaining"] = "999"
        response.headers["X-RateLimit-Reset"] = "3600"
        return response

    monkeypatch.setattr(
        "app.middleware.rate_limit_info.RateLimitInfoMiddleware.dispatch", mock_dispatch
    )


# Keep other fixtures as they are
