from abc import ABC, abstractmethod
from fastapi import UploadFile

class StorageService(ABC):
    @abstractmethod
    async def upload_file(self, file: UploadFile, bucket_name: str, object_name: str):
        pass

    @abstractmethod
    async def get_file_url(self, bucket_name: str, object_name: str):
        pass

class MinioStorageService(StorageService):
    def __init__(self, minio_client):
        self.client = minio_client

    async def upload_file(self, file: UploadFile, bucket_name: str, object_name: str):
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

            result = self.client.put_object(
                bucket_name, object_name, file.file, file.size,
                content_type=file.content_type
            )
            return result.object_name
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None

    async def get_file_url(self, bucket_name: str, object_name: str):
        try:
            return self.client.presigned_get_object(bucket_name, object_name)
        except Exception as e:
            print(f"Error getting file URL: {e}")
            return None