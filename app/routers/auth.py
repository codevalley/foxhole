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
import logging


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    user: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserRegistrationResponse:
    logger.info(
        f"Attempting to register user with screen_name: {user.screen_name}"
    )  # Added logging
    try:
        new_user = await create_user(db, user.screen_name)
        if not new_user:
            logger.error("Failed to create user in the database")  # Added logging
            raise DatabaseOperationError("Failed to create user")
        logger.info(f"User registered successfully: {new_user.id}")  # Added logging
        return UserRegistrationResponse(
            id=new_user.id,
            screen_name=new_user.screen_name,
            user_secret=new_user.user_secret,
        )
    except DatabaseOperationError as e:
        logger.exception(
            f"Database operation error during registration: {e}"
        )  # Added logging
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during registration: {e}")  # Added logging
        raise DatabaseOperationError("An unexpected error occurred during registration")


@router.post("/token", response_model=Token)
async def login_for_access_token(
    user_secret: str = Form(...), db: AsyncSession = Depends(get_db)
) -> Token:
    logger.info(f"Login attempt with user_secret: {user_secret}")  # Added logging
    try:
        user = await get_user_by_secret(db, user_secret)
        if not user:
            logger.warning("Invalid user_secret provided")  # Added logging
            raise AuthenticationError("Invalid authentication credentials")
        access_token = create_access_token(data={"sub": str(user.id)})
        logger.info(f"User logged in successfully: {user.id}")  # Added logging
        return Token(access_token=access_token, token_type="bearer")
    except AuthenticationError as e:
        logger.exception(f"Authentication error during login: {e}")  # Added logging
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")  # Added logging
        raise AuthenticationError("An unexpected error occurred during login")


@router.get("/users/me", response_model=UserInfo)
async def read_users_me(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    logger.debug(f"Retrieving profile for user: {current_user.id}")  # Added logging
    return current_user


@router.put("/users/me", response_model=UserInfo)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserInfo:
    logger.info(
        f"User {current_user.id} is attempting to update their profile"
    )  # Added logging
    try:
        user = await get_user_by_id(db, current_user.id)
        if not user:
            logger.error(f"User not found: {current_user.id}")  # Added logging
            raise DatabaseOperationError("Failed to retrieve user")

        update_data = user_update.model_dump(exclude_unset=True)
        updated_user = await update_user(db, user, **update_data)

        if not updated_user:
            logger.error(f"Failed to update user: {current_user.id}")  # Added logging
            raise DatabaseOperationError("Failed to update user")

        logger.info(
            f"User profile updated successfully: {updated_user.id}"
        )  # Added logging
        return get_user_info(updated_user)
    except DatabaseOperationError as e:
        logger.exception(
            f"Database operation error during profile update: {e}"
        )  # Added logging
        raise
    except Exception as e:
        logger.exception(
            f"Unexpected error during profile update: {e}"
        )  # Added logging
        raise DatabaseOperationError(
            "An unexpected error occurred during profile update"
        )
