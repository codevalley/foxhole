import pytest
import logging  # Add this import
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
)
from app.models import Base
from app.app import app
from app.dependencies import get_db, get_storage_service
from tests.mocks.mock_storage_service import MockStorageService
from httpx import AsyncClient
from fastapi.testclient import TestClient  # Ensure this import is here
from typing import AsyncGenerator, Callable, Any
from app.services.websocket_manager import WebSocketManager
from app.routers import websocket as websocket_router  # Add this import

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    return create_async_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(scope="function")
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_storage_service() -> MockStorageService:
    return MockStorageService()


@pytest.fixture
def override_get_db(
    db_session: AsyncSession,
) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    return _override_get_db


@pytest.fixture
def app_with_mocked_dependencies(
    mock_storage_service: MockStorageService,
    override_get_db: Callable[[], AsyncGenerator[AsyncSession, None]],
) -> Any:
    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(
    app_with_mocked_dependencies: Any,
) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        app=app_with_mocked_dependencies, base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def websocket_manager() -> WebSocketManager:
    return WebSocketManager()


@pytest.fixture
def test_client(
    websocket_manager: WebSocketManager, app_with_mocked_dependencies: Any
) -> TestClient:
    websocket_router.init_websocket_manager(websocket_manager)
    return TestClient(app_with_mocked_dependencies)


@pytest.fixture(autouse=True)
def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def authenticated_user(client: TestClient) -> dict[str, Any]:
    # Create a test user
    user_data = {"screen_name": "testuser"}
    response = client.post("/auth/register", json=user_data)
    print(f"Registration response: {response.status_code} - {response.text}")
    assert response.status_code == 200, f"Registration failed: {response.text}"
    user_id = response.json()["id"]

    # Now, let's get an access token for this user
    login_data = {"user_id": user_id}
    token_response = client.post("/auth/token", data=login_data)
    print(f"Token response: {token_response.status_code} - {token_response.text}")
    assert (
        token_response.status_code == 200
    ), f"Token retrieval failed: {token_response.text}"
    token = token_response.json()["access_token"]

    return {"token": token, "user_data": user_data, "user_id": user_id}
