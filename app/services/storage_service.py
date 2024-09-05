from abc import ABC, abstractmethod
from fastapi import UploadFile
from minio import Minio
from app.core.config import settings
import io

class StorageService(ABC):
    @abstractmethod
    async def upload_file(self, file: UploadFile, bucket_name: str, object_name: str):
        pass

    @abstractmethod
    async def get_file_url(self, bucket_name: str, object_name: str):
        pass

    @abstractmethod
    async def list_files(self, bucket_name: str):
        pass

class MinioStorageService(StorageService):
    def __init__(self):
        # Initialize MinIO client with settings from config
        self.client = Minio(
            settings.MINIO_HOST,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE
        )

    async def upload_file(self, file: UploadFile, bucket_name: str, object_name: str):
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
                bucket_name, object_name, file_stream, file_size,
                content_type=file.content_type
            )
            return object_name
        except Exception as e:
            # Log the error (implement proper logging)
            print(f"Error uploading file: {e}")
            return None

    async def get_file_url(self, bucket_name: str, object_name: str):
        try:
            # Generate a presigned URL for the object
            return self.client.presigned_get_object(bucket_name, object_name)
        except Exception as e:
            # Log the error (implement proper logging)
            print(f"Error getting file URL: {e}")
            return None

    async def list_files(self, bucket_name: str):
        try:
            # List objects in the bucket
            objects = self.client.list_objects(bucket_name)
            return [obj.object_name for obj in objects]
        except Exception as e:
            # Log the error (implement proper logging)
            print(f"Error listing files: {e}")
            return []