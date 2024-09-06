import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User

pytestmark = pytest.mark.asyncio

async def test_register_user(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/auth/register",
        json={"screen_name": "testuser"}
    )
    assert response.status_code == 200
    # Add more assertions as needed

async def test_login(client: AsyncClient, db_session: AsyncSession):
    # First, register a user
    register_response = await client.post(
        "/auth/register",
        json={"screen_name": "testuser"}
    )
    assert register_response.status_code == 200
    user_id = register_response.json()["id"]

    # Now, try to login
    login_response = await client.post(
        "/auth/token",
        data={"user_id": user_id}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

async def test_get_user_profile(client: AsyncClient, db_session: AsyncSession):
    # First, register and login
    register_response = await client.post(
        "/auth/register",
        json={"screen_name": "testuser"}
    )
    user_id = register_response.json()["id"]
    login_response = await client.post(
        "/auth/token",
        data={"user_id": user_id}
    )
    access_token = login_response.json()["access_token"]

    # Now, get the user profile
    response = await client.get(
        "/auth/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == user_id

async def test_update_user_profile(client: AsyncClient, db_session: AsyncSession):
    # First, register and login
    register_response = await client.post(
        "/auth/register",
        json={"screen_name": "testuser"}
    )
    user_id = register_response.json()["id"]
    login_response = await client.post(
        "/auth/token",
        data={"user_id": user_id}
    )
    access_token = login_response.json()["access_token"]

    # Now, update the user profile
    update_response = await client.put(
        "/auth/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"screen_name": "updated_testuser"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["screen_name"] == "updated_testuser"

async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Add more tests for other endpoints and functionalities