import warnings
import pytest
from unittest.mock import patch, MagicMock, Mock
from app.dependencies import (
    MinioStorageService,
    get_storage_service,
    MockStorageService,
    StorageConfig,
)
from app.core.config import settings
from minio.error import S3Error
from fastapi import UploadFile
from typing import Generator  # Add this import
from app.dependencies import get_current_user_ws, get_token_from_websocket
from sqlalchemy.ext.asyncio import AsyncSession


warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.jwt")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="minio.time")


@pytest.fixture
def mock_minio_client() -> Generator[MagicMock, None, None]:
    with patch("app.dependencies.Minio") as mock_minio:
        yield mock_minio.return_value


@pytest.fixture
def storage_config() -> StorageConfig:
    return StorageConfig(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


@pytest.mark.asyncio
async def test_minio_storage_service_upload_file_error(
    mock_minio_client: MagicMock,
    storage_config: StorageConfig,
) -> None:
    mock_minio_client.put_object.side_effect = Exception("Upload error")
    service = MinioStorageService(storage_config)

    result = await service.upload_file(
        MagicMock(spec=UploadFile), "test-bucket", "test-object"
    )
    assert result is None


@pytest.mark.asyncio
async def test_minio_storage_service_get_file_url_error(
    mock_minio_client: MagicMock,
    storage_config: StorageConfig,
) -> None:
    mock_response = Mock()
    mock_minio_client.presigned_get_object.side_effect = S3Error(
        code="S3 error",
        message="An error occurred",
        resource="resource",
        request_id="request_id",
        host_id="host_id",
        response=mock_response,
    )
    service = MinioStorageService(storage_config)

    result = await service.get_file_url("test-bucket", "test-object")
    assert result is None


@pytest.mark.asyncio
async def test_minio_storage_service_list_files_error(
    mock_minio_client: MagicMock,
    storage_config: StorageConfig,
) -> None:
    mock_minio_client.list_objects.side_effect = Exception("List error")
    service = MinioStorageService(storage_config)

    result = await service.list_files("test-bucket")
    assert result == []


def test_get_storage_service_mock() -> None:
    with patch.object(settings, "USE_MOCK_STORAGE", True):
        service = get_storage_service()
        assert isinstance(service, MockStorageService)


def test_get_storage_service_minio() -> None:
    with patch.object(settings, "USE_MOCK_STORAGE", False):
        service = get_storage_service()
        assert isinstance(service, MinioStorageService)


@pytest.mark.asyncio
async def test_get_current_user_ws_missing_sub_claim(db_session: AsyncSession) -> None:
    mock_websocket = MagicMock()
    with patch("app.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {}  # Missing 'sub' claim
        result = await get_current_user_ws(mock_websocket, "valid_token", db_session)
        assert result is None


@pytest.mark.asyncio
async def test_get_token_from_websocket_invalid_format() -> None:
    mock_websocket = MagicMock()
    mock_websocket.headers = {"Authorization": "InvalidFormat token"}
    token = await get_token_from_websocket(mock_websocket)
    assert token is None


def test_minio_storage_service_init(storage_config: StorageConfig) -> None:
    with patch("app.dependencies.Minio") as mock_minio:
        service = MinioStorageService(storage_config)
        mock_minio.assert_called_once_with(
            storage_config.endpoint,
            access_key=storage_config.access_key,
            secret_key=storage_config.secret_key,
            secure=storage_config.secure,
        )
        assert service.client == mock_minio.return_value
