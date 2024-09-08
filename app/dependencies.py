from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from app.services.storage_service import StorageService
from app.models import User
from app.routers.auth import verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from typing import Optional
from fastapi import UploadFile

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Temporary stub implementation
class StubStorageService(StorageService):
    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: str
    ) -> Optional[str]:
        return object_name

    async def get_file_url(self, bucket_name: str, object_name: str) -> Optional[str]:
        return f"http://example.com/{bucket_name}/{object_name}"  # noqa: E231

    async def list_files(self, bucket_name: str) -> list[str]:
        return []


def get_storage_service() -> StorageService:
    return StubStorageService()


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
    websocket: WebSocket, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    token = await get_token_from_websocket(websocket)
    if token:
        return await verify_token(token, db)
    return None


async def get_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    token = websocket.headers.get("Authorization")
    if token and isinstance(token, str) and token.startswith("Bearer "):
        return token.split()[1]
    return None
