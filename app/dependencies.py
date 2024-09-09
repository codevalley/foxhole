from fastapi import Depends, HTTPException, status, WebSocket, Query
from fastapi.security import OAuth2PasswordBearer
from app.services.storage_service import StorageService
from app.models import User
from app.routers.auth import verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from typing import Optional
from fastapi import UploadFile
from jose import JWTError, jwt
from app.core.config import settings
from sqlalchemy import select
from minio import Minio
import logging
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

    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: str
    ) -> Optional[str]:
        try:
            # Implement file upload logic here
            return "Placeholder for uploaded file URL"  # TODO:Replace with actual logic
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None

    async def get_file_url(self, bucket_name: str, object_name: str) -> Optional[str]:
        try:
            return str(self.client.presigned_get_object(bucket_name, object_name))
        except S3Error as e:
            logger.error(f"Error getting file URL: {e}")
            return None

    async def list_files(self, bucket_name: str) -> list[str]:
        try:
            # Implement file listing logic here
            return [
                "placeholder_file1.txt",
                "placeholder_file2.txt",
            ]  # TODO:Replace with actual logic
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
) -> Optional[User]:
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_ws(
    websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token"
            )
            return None
    except JWTError:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token"
        )
        return None

    stmt = select(User).filter(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="User not found"
        )
        return None
    return user


async def get_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    token = websocket.headers.get("Authorization")
    if token and isinstance(token, str) and token.startswith("Bearer "):
        return token.split()[1]
    return None
