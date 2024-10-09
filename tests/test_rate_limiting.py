import pytest
from httpx import AsyncClient
import asyncio
from app.core.config import settings  # Add this import
from app.core.rate_limit import limiter
from typing import AsyncGenerator


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def reset_rate_limiter() -> AsyncGenerator[None, None]:
    limiter.reset()
    yield


async def test_rate_limiting(
    async_client: AsyncClient, reset_rate_limiter: AsyncGenerator[None, None]
) -> None:
    # Register a user
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    assert register_response.status_code == 200

    user_secret = register_response.json()["user_secret"]

    # Use the correct rate limit from settings
    limit = int(settings.RATE_LIMIT_AUTH_TOKEN.split("/")[0])

    success_count = 0
    rate_limited_count = 0
    for i in range(limit + 1):
        response = await async_client.post(
            "/auth/token", data={"user_secret": user_secret}
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
    assert (
        success_count == limit
    ), f"Expected {limit} successful requests, got {success_count}"
    assert (
        rate_limited_count == 1
    ), f"Expected 1 rate-limited request, got {rate_limited_count}"


async def test_register_rate_limiting(
    async_client: AsyncClient, reset_rate_limiter: AsyncGenerator[None, None]
) -> None:
    # Use the correct rate limit from settings
    limit = int(settings.RATE_LIMIT_AUTH_REGISTER.split("/")[0])

    success_count = 0
    rate_limited_count = 0
    for i in range(limit + 1):
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
    assert (
        success_count == limit
    ), f"Expected {limit} successful requests, got {success_count}"
    assert (
        rate_limited_count == 1
    ), f"Expected 1 rate-limited request, got {rate_limited_count}"
