import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from app.models import User
from app.app import app
from app.dependencies import get_db, get_storage_service
from tests.mocks.mock_storage_service import MockStorageService
from httpx import AsyncClient
from fastapi.testclient import TestClient
from typing import AsyncGenerator, Any, Generator
from app.services.websocket_manager import WebSocketManager
from utils.database import create_tables, engine, AsyncSessionLocal
from app.middleware.request_id import RequestIDMiddleware


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    await create_tables()  # Create tables before running tests
    yield engine


@pytest.fixture(scope="function")
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_storage_service] = lambda: MockStorageService()

    # Clear existing middleware and add RequestIDMiddleware
    app.middleware_stack = None
    app.add_middleware(RequestIDMiddleware)

    # Create a new TestClient with the updated app
    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    if hasattr(app.state, "websocket_manager"):
        for websocket in app.state.websocket_manager.active_connections.values():
            await websocket.close()
        app.state.websocket_manager.active_connections.clear()
        app.state.websocket_manager.user_info.clear()

    app.dependency_overrides.clear()
    app.middleware_stack = None

    # Remove the middleware after the test
    app.user_middleware = [
        m for m in app.user_middleware if not isinstance(m.cls, RequestIDMiddleware)
    ]
    app.middleware_stack = None  # Reset the middleware stack


@pytest.fixture(scope="function")
async def async_client(client: TestClient) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(screen_name="testuser")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def authenticated_user(async_client: AsyncClient) -> dict[str, Any]:
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
def test_client(client: TestClient) -> TestClient:
    return client


@pytest.fixture
def mock_storage_service() -> MockStorageService:
    return MockStorageService()
