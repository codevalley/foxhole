import warnings
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.core.config import settings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.jwt")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="minio.time")

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


async def test_register_user(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    assert response.status_code in [200, 429]
    if response.status_code == 200:
        assert "id" in response.json()
        assert "user_secret" in response.json()
        assert response.json()["screen_name"] == "testuser"
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


async def test_login(async_client: AsyncClient, db_session: AsyncSession) -> None:
    # First, register a user
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    assert register_response.status_code in [200, 429]

    if register_response.status_code == 200:
        user_secret = register_response.json()["user_secret"]

        # Now, try to login
        login_response = await async_client.post(
            "/auth/token", data={"user_secret": user_secret}
        )
        assert login_response.status_code in [200, 429]
        if login_response.status_code == 200:
            assert "access_token" in login_response.json()

    assert "X-RateLimit-Limit" in login_response.headers
    assert "X-RateLimit-Remaining" in login_response.headers
    assert "X-RateLimit-Reset" in login_response.headers


async def test_health_check(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.APP_VERSION
    assert data["database_status"] == "ok"


async def test_invalid_login(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    login_response = await async_client.post(
        "/auth/token", data={"user_secret": "invalid_secret"}
    )
    assert login_response.status_code in [401, 429]
    if login_response.status_code == 401:
        assert login_response.json()["detail"] == "Invalid authentication credentials"
    assert "X-RateLimit-Limit" in login_response.headers
    assert "X-RateLimit-Remaining" in login_response.headers
    assert "X-RateLimit-Reset" in login_response.headers


async def test_update_nonexistent_user(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    # Try to update a user profile with an invalid token
    update_response = await async_client.put(
        "/auth/users/me",
        headers={"Authorization": "Bearer invalid_token"},
        json={"screen_name": "updated_testuser"},
    )
    assert update_response.status_code in [401, 429]
    if update_response.status_code == 401:
        assert "detail" in update_response.json()
    assert "X-RateLimit-Limit" in update_response.headers
    assert "X-RateLimit-Remaining" in update_response.headers
    assert "X-RateLimit-Reset" in update_response.headers
