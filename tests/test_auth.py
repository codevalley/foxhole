import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User

pytestmark = pytest.mark.asyncio


async def test_register_user(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.post("/auth/register", json={"screen_name": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["screen_name"] == "testuser"

    # Verify user was created in the database
    user = await db_session.get(User, data["id"])
    assert user is not None
    assert user.screen_name == "testuser"


async def test_login(client: AsyncClient, db_session: AsyncSession) -> None:
    # First, register a user
    register_response = await client.post(
        "/auth/register", json={"screen_name": "loginuser"}
    )
    user_id = register_response.json()["id"]

    # Now, try to login
    login_response = await client.post("/auth/token", data={"user_id": user_id})
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_get_current_user(client: AsyncClient, db_session: AsyncSession) -> None:
    # Register and login a user
    register_response = await client.post(
        "/auth/register", json={"screen_name": "currentuser"}
    )
    user_id = register_response.json()["id"]
    login_response = await client.post("/auth/token", data={"user_id": user_id})
    access_token = login_response.json()["access_token"]

    # Get current user
    response = await client.get(
        "/auth/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["screen_name"] == "currentuser"


async def test_update_user_profile(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Register and login a user
    register_response = await client.post(
        "/auth/register", json={"screen_name": "updateuser"}
    )
    user_id = register_response.json()["id"]
    login_response = await client.post("/auth/token", data={"user_id": user_id})
    access_token = login_response.json()["access_token"]

    # Update user profile
    update_response = await client.put(
        "/auth/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"screen_name": "updateduser"},
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == user_id
    assert data["screen_name"] == "updateduser"

    # Verify update in the database
    user = await db_session.get(User, user_id)
    assert user is not None
    assert user.screen_name == "updateduser"


async def test_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/auth/users/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


async def test_missing_token(client: AsyncClient) -> None:
    response = await client.get("/auth/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
