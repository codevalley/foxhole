import pytest
from unittest.mock import patch, MagicMock, Mock
from app.dependencies import (
    MinioStorageService,
    get_storage_service,
    MockStorageService,
)
from app.core.config import settings
from minio.error import S3Error
from fastapi import UploadFile
from typing import Generator  # Add this import


@pytest.fixture
def mock_minio_client() -> Generator[MagicMock, None, None]:
    with patch("app.dependencies.Minio") as mock_minio:
        yield mock_minio.return_value


@pytest.mark.asyncio
async def test_minio_storage_service_upload_file_error(
    mock_minio_client: MagicMock,
) -> None:
    mock_minio_client.put_object.side_effect = Exception("Upload error")
    service = MinioStorageService()

    result = await service.upload_file(
        MagicMock(spec=UploadFile), "test-bucket", "test-object"
    )
    assert result is None


@pytest.mark.asyncio
async def test_minio_storage_service_get_file_url_error(
    mock_minio_client: MagicMock,
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
    service = MinioStorageService()

    result = await service.get_file_url("test-bucket", "test-object")
    assert result is None


@pytest.mark.asyncio
async def test_minio_storage_service_list_files_error(
    mock_minio_client: MagicMock,
) -> None:
    mock_minio_client.list_objects.side_effect = Exception("List error")
    service = MinioStorageService()

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


# ... existing tests ...
