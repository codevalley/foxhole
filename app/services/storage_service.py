from abc import ABC, abstractmethod
from fastapi import UploadFile
from minio import Minio
from app.core.config import settings
from utils.logging import get_logger
import io
from typing import Optional, List

logger = get_logger(__name__)


class StorageService(ABC):
    @abstractmethod
    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: str
    ) -> Optional[str]:
        pass

    @abstractmethod
    async def get_file_url(self, bucket_name: str, object_name: str) -> Optional[str]:
        pass

    @abstractmethod
    async def list_files(self, bucket_name: str) -> List[str]:
        pass


class MinioStorageService(StorageService):
    def __init__(self) -> None:
        # Initialize MinIO client with settings from config
        self.client = Minio(
            settings.MINIO_HOST,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )

    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: str
    ) -> Optional[str]:
        # Ensure bucket exists
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

        # Read file content
        file_data = await file.read()
        file_size = len(file_data)
        file_stream = io.BytesIO(file_data)

        # Upload file
        try:
            self.client.put_object(
                bucket_name,
                object_name,
                file_stream,
                file_size,
                content_type=file.content_type,
            )
            logger.info(f"File uploaded successfully: {object_name}")
            return object_name
        except Exception as e:
            logger.error(f"Error uploading file: {e}", exc_info=True)
            return None

    async def get_file_url(self, bucket_name: str, object_name: str) -> Optional[str]:
        try:
            # Generate a presigned URL for the object
            url = self.client.presigned_get_object(bucket_name, object_name)
            logger.info(f"Generated presigned URL for {object_name}")
            return str(url)  # Explicitly convert to str
        except Exception as e:
            logger.error(f"Error getting file URL: {e}", exc_info=True)
            return None

    async def list_files(self, bucket_name: str) -> List[str]:
        try:
            # List objects in the bucket
            objects = self.client.list_objects(bucket_name)
            file_list = [obj.object_name for obj in objects]
            logger.info(f"Listed {len(file_list)} files in bucket {bucket_name}")
            return file_list
        except Exception as e:
            logger.error(f"Error listing files: {e}", exc_info=True)
            return []
