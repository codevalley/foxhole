import pytest
from httpx import AsyncClient
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Any


@pytest.mark.asyncio
async def test_health_check_success(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    # Ensure the database is working
    await db_session.execute(text("SELECT 1"))
    await db_session.commit()

    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.APP_VERSION
    assert data["database_status"] == "ok"


@pytest.mark.asyncio
async def test_health_check_db_error(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_db_execute(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database connection error")

    monkeypatch.setattr("sqlalchemy.ext.asyncio.AsyncSession.execute", mock_db_execute)

    response = await async_client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Service Unavailable"
