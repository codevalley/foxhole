import pytest
from httpx import AsyncClient
from app.services.storage_service import StorageService
import logging
from typing import TypedDict

logger = logging.getLogger(__name__)


pytestmark = pytest.mark.asyncio


class RegisterResponse(TypedDict):
    user_secret: str


class LoginResponse(TypedDict):
    access_token: str


async def get_access_token(async_client: AsyncClient) -> str:
    register_response = await async_client.post(
        "/auth/register", json={"screen_name": "testuser"}
    )
    register_data = register_response.json()
    if "user_secret" not in register_data:
        raise ValueError("Register response missing user_secret")
    user_secret = register_data["user_secret"]
    if not isinstance(user_secret, str):
        raise TypeError("user_secret is not a string")

    login_response = await async_client.post(
        "/auth/token", data={"user_secret": user_secret}
    )
    login_data = login_response.json()
    if "access_token" not in login_data:
        raise ValueError("Login response missing access_token")
    access_token = login_data["access_token"]
    if not isinstance(access_token, str):
        raise TypeError("access_token is not a string")

    return access_token


async def test_upload_file(
    async_client: AsyncClient, mock_storage_service: StorageService
) -> None:
    access_token = await get_access_token(async_client)
    response = await async_client.post(
        "/files/upload",
        files={"file": ("test.txt", b"test content")},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded successfully"


async def test_list_files(
    async_client: AsyncClient, mock_storage_service: StorageService
) -> None:
    access_token = await get_access_token(async_client)
    response = await async_client.get(
        "/files/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "files" in response.json()


async def test_get_file_url(
    async_client: AsyncClient, mock_storage_service: StorageService
) -> None:
    response = await async_client.get("/files/file/test_object")
    assert response.status_code == 200
    assert response.json() == {"url": "http://mock-url.com/default-bucket/test_object"}


async def test_get_file_url_not_found(
    async_client: AsyncClient, mock_storage_service: StorageService
) -> None:
    response = await async_client.get("/files/file/non_existent_object")
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"
