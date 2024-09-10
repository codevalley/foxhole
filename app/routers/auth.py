from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import (
    UserCreate,
    UserRegistrationResponse,
    Token,
    UserUpdate,
    UserResponse,
)
from app.models import User
from app.db.operations import get_user_by_secret, create_user, update_user
from utils.database import get_db
from utils.security import create_access_token
from app.exceptions import AuthenticationError, DatabaseOperationError
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    user: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserRegistrationResponse:
    """
    Register a new user.

    This endpoint creates a new user account and returns a user_secret.
    The user_secret should be securely stored by the client as it will be
    required for future authentication.

    Args:
    - user: UserCreate object containing the user's screen name

    Returns:
    - UserRegistrationResponse object containing id, screen_name, and user_secret
    """
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
    """
    Authenticate a user and return an access token.

    This endpoint authenticates a user using their user_secret and returns
    a JWT access token for use in subsequent authenticated requests.

    Args:
    - user_secret: The secret key provided during user registration

    Returns:
    - Token object containing access_token and token_type
    """
    user = await get_user_by_secret(db, user_secret)
    if not user:
        raise AuthenticationError("Invalid authentication credentials")
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get the current authenticated user's information.

    This endpoint returns the profile information of the currently
    authenticated user.

    Returns:
    - UserResponse object containing id and screen_name
    """
    return UserResponse(id=current_user.id, screen_name=current_user.screen_name)


@router.put("/users/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update the current user's profile.

    This endpoint allows the authenticated user to update their profile information.

    Args:
    - user_update: UserUpdate object containing the fields to be updated

    Returns:
    - UserResponse object containing the updated user information
    """
    updated_user = await update_user(
        db, current_user, **user_update.model_dump(exclude_unset=True)
    )
    if not updated_user:
        raise DatabaseOperationError("Failed to update user")
    return UserResponse(id=updated_user.id, screen_name=updated_user.screen_name)
