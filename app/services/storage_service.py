from abc import ABC, abstractmethod
from fastapi import UploadFile
from typing import Optional, List


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
