import pytest
from httpx import AsyncClient
import asyncio

pytestmark = pytest.mark.asyncio


async def test_rate_limiting(async_client: AsyncClient) -> None:
    # Register a user
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    assert register_response.status_code in [200, 429]

    if register_response.status_code == 200:
        user_secret = register_response.json()["user_secret"]

        # Try to login 6 times
        for i in range(6):
            response = await async_client.post(
                "/auth/token", data={"user_secret": user_secret}
            )
            assert response.status_code in [200, 429]
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
            await asyncio.sleep(0.1)  # Add a small delay between requests
    else:
        # If the initial registration was rate-limited, just check the headers
        assert "X-RateLimit-Limit" in register_response.headers
        assert "X-RateLimit-Remaining" in register_response.headers
        assert "X-RateLimit-Reset" in register_response.headers


async def test_register_rate_limiting(async_client: AsyncClient) -> None:
    # Try to register 11 times
    success_count = 0
    rate_limited_count = 0
    for i in range(11):
        response = await async_client.post(
            "/auth/register", json={"screen_name": f"testuser{i}"}
        )
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited_count += 1
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        await asyncio.sleep(0.1)  # Add a small delay between requests

    # Ensure we had some successful requests and some rate-limited requests
    assert success_count > 0, "Expected some successful requests"
    assert rate_limited_count > 0, "Expected some rate-limited requests"
    assert (
        success_count + rate_limited_count == 11
    ), "Expected all requests to be either successful or rate-limited"
