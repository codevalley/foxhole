from fastapi import Depends, HTTPException, status, WebSocket, Query
from fastapi.security import OAuth2PasswordBearer
from app.services.storage_service import StorageService
from app.models import User
from utils.token import verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from typing import Optional
from fastapi import UploadFile
from jose import JWTError, jwt
from app.core.config import settings
from sqlalchemy import select
from minio import Minio
import logging
from utils.user_utils import get_user_info
from app.schemas.user_schema import UserInfo
from minio.error import S3Error

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


logger = logging.getLogger(__name__)


# Temporary stub implementation
class MinioStorageService(StorageService):
    def __init__(self) -> None:
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.ensure_bucket_exists("default-bucket")

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            else:
                logger.info(f"Bucket already exists: {bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")

    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: str
    ) -> Optional[str]:
        try:
            self.ensure_bucket_exists(bucket_name)
            self.client.put_object(bucket_name, object_name, file.file, file.size)
            return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"  # noqa: E231
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None

    async def get_file_url(self, bucket_name: str, object_name: str) -> Optional[str]:
        try:
            self.ensure_bucket_exists(bucket_name)
            return str(self.client.presigned_get_object(bucket_name, object_name))
        except S3Error as e:
            logger.error(f"Error getting file URL: {e}")
            return None

    async def list_files(self, bucket_name: str) -> list[str]:
        try:
            self.ensure_bucket_exists(bucket_name)
            objects = self.client.list_objects(bucket_name)
            return [obj.object_name for obj in objects]
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []


class MockStorageService(StorageService):
    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: str
    ) -> Optional[str]:
        return object_name

    async def get_file_url(self, bucket_name: str, object_name: str) -> Optional[str]:
        return f"http://mock-storage/{bucket_name}/{object_name}"  # noqa: E231

    async def list_files(self, bucket_name: str) -> list[str]:
        return ["mock_file1.txt", "mock_file2.txt"]


def get_storage_service() -> StorageService:
    if settings.USE_MOCK_STORAGE:
        return MockStorageService()
    else:
        return MinioStorageService()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> UserInfo:
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    stmt = select(User).filter(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return get_user_info(user)


async def get_current_user_ws(
    websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.error("Invalid token: sub claim is missing")
            return None
        logger.info(f"Token decoded successfully. User ID: {user_id}")
    except JWTError as e:
        logger.error(f"Failed to decode token: {str(e)}")
        return None

    stmt = select(User).filter(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        logger.error(f"User not found for ID: {user_id}")
        return None
    logger.info(f"User found: {user}")
    return user


async def get_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    token = websocket.headers.get("Authorization")
    if token and isinstance(token, str) and token.startswith("Bearer "):
        return token.split()[1]
    return None
