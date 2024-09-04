from minio import Minio
from app.core.config import settings

def get_storage_service():
    return Minio(
        settings.MINIO_HOST,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE
    )