import pytest
from httpx import AsyncClient
from app.services.storage_service import StorageService

pytestmark = pytest.mark.asyncio


async def test_upload_file(
    async_client: AsyncClient, mock_storage_service: StorageService
) -> None:
    response = await async_client.post(
        "/files/upload", files={"file": ("test.txt", b"test content")}
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "File uploaded successfully",
        "object_name": "test.txt",
    }


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


async def test_list_files(
    async_client: AsyncClient, mock_storage_service: StorageService
) -> None:
    response = await async_client.get("/files/")
    assert response.status_code == 200
    assert response.json() == {"files": ["file1.txt", "file2.txt"]}
