from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from app.schemas.user_schema import UserCreate, UserResponse, Token, UserUpdate
from app.models import User
from app.db.operations import get_user_by_id, create_user, update_user
from utils.database import get_db
from utils.security import create_access_token, verify_token
from app.exceptions import (
    AuthenticationError,
    UserNotFoundError,
    DatabaseOperationError,
)
import logging

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    new_user = await create_user(db, user.screen_name)
    if not new_user:
        raise DatabaseOperationError("Failed to create user")
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    user_id: str = Form(...), db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise AuthenticationError("Invalid authentication credentials")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    user_id = verify_token(token)
    if not user_id:
        raise AuthenticationError("Invalid authentication credentials")
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError()
    return user


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("/users/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    updated_user = await update_user(
        db, current_user, **user_update.dict(exclude_unset=True)
    )
    if not updated_user:
        raise DatabaseOperationError("Failed to update user")
    return updated_user
