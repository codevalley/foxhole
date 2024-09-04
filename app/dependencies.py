from app.services.storage_service import MinioStorageService
from minio import Minio
from app.core.config import settings

def get_minio_client():
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )

def get_storage_service():
    minio_client = get_minio_client()
    return MinioStorageService(minio_client)