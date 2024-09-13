from app.services.storage_service import StorageService
from typing import Optional
from fastapi import UploadFile
from typing import List


class MockStorageService(StorageService):
    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: str
    ) -> Optional[str]:
        return object_name

    async def get_file_url(self, bucket_name: str, object_name: str) -> Optional[str]:
        if object_name == "non_existent_object":
            return None
        return f"http://mock-url.com/{bucket_name}/{object_name}"  # noqa: E231

    async def list_files(self, bucket_name: str) -> List[str]:
        return ["file1.txt", "file2.txt"]
