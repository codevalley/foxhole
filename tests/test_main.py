import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app  # Import the app instance directly
from app.models import Base, User
from app.core.config import settings
from utils.database import get_db
from utils.cache import get_cache
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select  # Add this import
from fakeredis.aioredis import FakeRedis

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create a new engine instance
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)

# Create a new session factory
TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# Override the database dependency
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# Override the cache dependency
async def override_get_cache():
    return FakeRedis()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_cache] = override_get_cache
app.state.testing = True

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def test_db():
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    # Drop tables after all tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        return test_db
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = lambda: FakeRedis()
    with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"screen_name": "testuser"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["screen_name"] == "testuser"
    return data["id"]

@pytest.mark.asyncio
async def test_login(client, test_db):
    user_id = await test_register_user(client)
    print(f"Registered user ID: {user_id}")
    
    # Verify user in database
    query = select(User).where(User.id == user_id)
    result = await test_db.execute(query)
    user = result.scalar_one_or_none()
    print(f"User in database: {user}")
    
    response = client.post(
        "/auth/token",
        data={"user_id": user_id}
    )
    print(f"Login response status: {response.status_code}")
    print(f"Login response body: {response.json()}")
    assert response.status_code == 200, f"Response: {response.json()}"
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

@pytest.mark.asyncio
async def test_get_user_profile(client, test_db):
    access_token = await test_login(client, test_db)
    response = client.get(
        "/auth/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "screen_name" in data

@pytest.mark.asyncio
async def test_update_user_profile(client, test_db):
    access_token = await test_login(client, test_db)
    response = client.put(
        "/auth/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"screen_name": "updated_testuser"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["screen_name"] == "updated_testuser"

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Add more tests for other endpoints and functionalities