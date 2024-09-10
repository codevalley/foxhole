import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


pytestmark = pytest.mark.asyncio


async def test_register_user(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    assert response.status_code == 200
    # Add more assertions as needed


async def test_login(async_client: AsyncClient, db_session: AsyncSession) -> None:
    # First, register a user
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    assert register_response.status_code == 200
    user_secret = register_response.json()["user_secret"]

    # Now, try to login
    login_response = await async_client.post(
        "/auth/token", data={"user_secret": user_secret}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


async def test_get_user_profile(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    # First, register and login
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    user_secret = register_response.json()["user_secret"]
    login_response = await async_client.post(
        "/auth/token", data={"user_secret": user_secret}
    )
    access_token = login_response.json()["access_token"]

    # Now, get the user profile
    response = await async_client.get(
        "/auth/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "id" in response.json()


async def test_update_user_profile(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    # First, register and login
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    user_secret = register_response.json()["user_secret"]
    login_response = await async_client.post(
        "/auth/token", data={"user_secret": user_secret}
    )
    access_token = login_response.json()["access_token"]

    # Now, update the user profile
    update_response = await async_client.put(
        "/auth/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"screen_name": "updated_testuser"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["screen_name"] == "updated_testuser"


async def test_health_check(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Add more tests for other endpoints and functionalities
