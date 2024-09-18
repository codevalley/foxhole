import warnings
import pytest
from httpx import AsyncClient
from app.services.storage_service import StorageService
from tests.mocks.mock_storage_service import MockStorageService
from fastapi import FastAPI
from app.dependencies import get_storage_service
from app.routers.auth import create_access_token
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.app import app as fastapi_app  # Import the FastAPI app
from typing import AsyncGenerator

warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.jwt")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="minio.time")

pytestmark = pytest.mark.asyncio


@pytest.fixture
def app() -> FastAPI:
    return fastapi_app


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user_id = str(uuid.uuid4())
    user = User(id=user_id, screen_name="testuser")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def access_token(test_user: User) -> str:
    return create_access_token({"sub": test_user.id})


@pytest.fixture
def mock_storage_service() -> StorageService:
    return MockStorageService()


@pytest.fixture
async def override_get_storage_service(
    mock_storage_service: StorageService, app: FastAPI
) -> AsyncGenerator[None, None]:
    """
    Override the get_storage_service dependency to use the mock.
    """
    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    yield
    app.dependency_overrides.pop(get_storage_service, None)


async def test_upload_file(
    async_client: AsyncClient, access_token: str, override_get_storage_service: None
) -> None:
    response = await async_client.post(
        "/files/upload",
        files={"file": ("test.txt", b"test content")},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded successfully"
    assert (
        response.json()["object_name"] == "test.txt"
    )  # Assuming the mock returns the filename


async def test_list_files(
    async_client: AsyncClient, access_token: str, override_get_storage_service: None
) -> None:
    response = await async_client.get(
        "/files/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "files" in response.json()
    assert response.json()["files"] == ["file1.txt", "file2.txt"]


async def test_get_file_url(
    async_client: AsyncClient, access_token: str, override_get_storage_service: None
) -> None:
    response = await async_client.get(
        "/files/file/test_object", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"url": "http://mockstorage/default-bucket/test_object"}


async def test_get_file_url_not_found(
    async_client: AsyncClient, access_token: str, override_get_storage_service: None
) -> None:
    response = await async_client.get(
        "/files/file/non_existent_object",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"
