import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
)
from app.models import Base
from app.app import app
from app.dependencies import get_storage_service, get_db
from tests.mocks.mock_storage_service import MockStorageService
from httpx import AsyncClient
from starlette.testclient import TestClient
from typing import AsyncGenerator, Any

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    return create_async_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(scope="function")
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
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
def override_get_db(db_session: AsyncSession) -> Any:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    return _override_get_db


@pytest.fixture
def app_with_mocked_dependencies(
    mock_storage_service: MockStorageService, override_get_db: Any
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
def test_client(app_with_mocked_dependencies: Any) -> TestClient:
    return TestClient(app_with_mocked_dependencies)
