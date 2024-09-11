from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import (
    UserCreate,
    UserRegistrationResponse,
    Token,
    UserUpdate,
    UserInfo,
)

from app.db.operations import (
    get_user_by_secret,
    create_user,
    update_user,
    get_user_by_id,
)
from utils.database import get_db
from utils.security import create_access_token
from app.exceptions import AuthenticationError, DatabaseOperationError
from app.dependencies import get_current_user
from utils.user_utils import get_user_info
from sqlalchemy.exc import SQLAlchemyError


router = APIRouter()


@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    user: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserRegistrationResponse:
    new_user = await create_user(db, user.screen_name)
    if not new_user:
        raise DatabaseOperationError("Failed to create user")
    return UserRegistrationResponse(
        id=new_user.id,
        screen_name=new_user.screen_name,
        user_secret=new_user.user_secret,
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    user_secret: str = Form(...), db: AsyncSession = Depends(get_db)
) -> Token:
    user = await get_user_by_secret(db, user_secret)
    if not user:
        raise AuthenticationError("Invalid authentication credentials")
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=UserInfo)
async def read_users_me(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    return current_user


@router.put("/users/me", response_model=UserInfo)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserInfo:
    user = await get_user_by_id(db, current_user.id)
    if not user:
        raise DatabaseOperationError("Failed to retrieve user")

    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = await update_user(db, user, **update_data)

    if not updated_user:
        raise DatabaseOperationError("Failed to update user")

    return get_user_info(updated_user)

    try:
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseOperationError(f"Failed to update user: {str(e)}")

    return get_user_info(user)
