from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.models import User
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.schemas.user_schema import UserCreate, UserResponse, Token, UserUpdate
from typing import Dict, Any

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create a new JWT access token.

    Args:
        data (Dict[str, Any]): The data to be encoded in the token.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return str(encoded_jwt)  # Explicitly convert to str


@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    user_id = User.generate_user_id()
    db_user = User(id=user_id, screen_name=user.screen_name or "anon_user")
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    user_id: str = Form(...), db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    query = select(User).where(User.id == user_id)
    user = None
    if isinstance(db, AsyncSession):
        result = await db.execute(query)
        user = result.scalar_one_or_none()
    else:
        async for session in db:
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            break
    print(f"Login attempt for user_id: {user_id}")
    print(f"User found: {user}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate the access token and return the current user.

    Args:
        token (str): The JWT token to validate.
        db (AsyncSession): The database session.

    Returns:
        User: The current authenticated user.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
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
    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        stmt = update(User).where(User.id == current_user.id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(current_user)
    return current_user
