import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_rate_limiting(async_client: AsyncClient):
    # Register a user
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    assert register_response.status_code == 200
    user_secret = register_response.json()["user_secret"]

    # Try to login 6 times (all should succeed due to mocked rate limiter)
    for i in range(6):
        response = await async_client.post(
            "/auth/token", data={"user_secret": user_secret}
        )
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers


async def test_register_rate_limiting(async_client: AsyncClient):
    # Try to register 11 times (all should succeed due to mocked rate limiter)
    for i in range(11):
        response = await async_client.post(
            "/auth/register", json={"screen_name": f"testuser{i}"}
        )
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers