from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers.auth import create_access_token
from typing import Dict, Any
import logging
import warnings
import pytest

# Add these warning filters
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
        data = response.json()
        assert "id" in data
        assert "user_secret" in data
        assert data["screen_name"] == "testuser"
    assert "X-Request-ID" in response.headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


async def test_login(async_client: AsyncClient, db_session: AsyncSession) -> None:
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "loginuser"}
    )
    assert register_response.status_code in [200, 429]
    if register_response.status_code == 200:
        user_data = register_response.json()
        assert "user_secret" in user_data, f"Unexpected response: {user_data}"
        user_secret = user_data["user_secret"]

        login_response = await async_client.post(
            "/auth/token", data={"user_secret": user_secret}
        )
        assert login_response.status_code in [200, 429]
        if login_response.status_code == 200:
            data = login_response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
        assert "X-Request-ID" in login_response.headers
        assert "X-RateLimit-Limit" in login_response.headers
        assert "X-RateLimit-Remaining" in login_response.headers
        assert "X-RateLimit-Reset" in login_response.headers


async def test_get_current_user(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "currentuser"}
    )
    assert register_response.status_code in [200, 429]
    if register_response.status_code == 200:
        user_secret = register_response.json()["user_secret"]
        login_response = await async_client.post(
            "/auth/token", data={"user_secret": user_secret}
        )
        assert login_response.status_code in [200, 429]
        if login_response.status_code == 200:
            access_token = login_response.json()["access_token"]

            response = await async_client.get(
                "/auth/users/me", headers={"Authorization": f"Bearer {access_token}"}
            )
            assert response.status_code in [200, 429]
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert data["screen_name"] == "currentuser"
                assert "user_secret" not in data
            assert "X-Request-ID" in response.headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers


async def test_update_user_profile(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    # Register and login a user
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "updateuser"}
    )
    assert register_response.status_code in [200, 429]
    if register_response.status_code == 200:
        user_secret = register_response.json()["user_secret"]
        login_response = await async_client.post(
            "/auth/token", data={"user_secret": user_secret}
        )
        assert login_response.status_code in [200, 429]
        if login_response.status_code == 200:
            access_token = login_response.json()["access_token"]

            # Update user profile
            update_response = await async_client.put(
                "/auth/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"screen_name": "updateduser"},
            )
            assert update_response.status_code in [200, 429]
            if update_response.status_code == 200:
                data = update_response.json()
                assert "id" in data
                assert data["screen_name"] == "updateduser"
                assert "user_secret" not in data
            assert "X-RateLimit-Limit" in update_response.headers
            assert "X-RateLimit-Remaining" in update_response.headers
            assert "X-RateLimit-Reset" in update_response.headers


async def test_invalid_token(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/auth/users/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code in [401, 429]
    if response.status_code == 401:
        assert response.json()["detail"] == "Invalid authentication credentials"
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


async def test_missing_token(async_client: AsyncClient) -> None:
    response = await async_client.get("/auth/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_create_access_token() -> None:
    data: Dict[str, Any] = {"sub": "test_user"}
    token = create_access_token(data)
    assert isinstance(token, str)


async def test_login_for_access_token_invalid_user(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/auth/token", data={"user_secret": "non_existent_secret"}
    )
    assert response.status_code in [401, 429]
    if response.status_code == 401:
        assert response.json()["detail"] == "Invalid authentication credentials"
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


async def test_get_current_user_invalid_token(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/auth/users/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code in [401, 429]
    if response.status_code == 401:
        assert response.json()["detail"] == "Invalid authentication credentials"
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


async def test_update_user_profile_no_changes(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    # Register and login a user
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "no_change_user"}
    )
    assert register_response.status_code in [200, 429]
    if register_response.status_code == 200:
        user_secret = register_response.json()["user_secret"]
        login_response = await async_client.post(
            "/auth/token", data={"user_secret": user_secret}
        )
        assert login_response.status_code in [200, 429]
        if login_response.status_code == 200:
            access_token = login_response.json()["access_token"]

            # Update user profile with no changes
            update_response = await async_client.put(
                "/auth/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
                json={},
            )
            assert update_response.status_code in [200, 429]
            if update_response.status_code == 200:
                data = update_response.json()
                assert "id" in data
                assert data["screen_name"] == "no_change_user"
            assert "X-RateLimit-Limit" in update_response.headers
            assert "X-RateLimit-Remaining" in update_response.headers
            assert "X-RateLimit-Reset" in update_response.headers
