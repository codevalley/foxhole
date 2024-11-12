from fastapi import APIRouter, Depends, Form, HTTPException, status, Body, Request
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
from app.schemas.error_schema import ErrorResponse
from pydantic import SecretStr
from app.core.rate_limit import limiter
from app.core.config import settings

logger = logging.getLogger("foxhole.auth")

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
@limiter.limit(settings.rate_limits["auth_register"])
async def register(
    request: Request,
    user: UserCreate = Body(..., description="User registration details"),
    db: AsyncSession = Depends(get_db),
) -> UserRegistrationResponse:
    """
    Register a new user.

    Args:
        request (Request): The request object.
        user (UserCreate): User registration details.
        db (AsyncSession): Database session.

    Returns:
        UserRegistrationResponse: Newly created user information including user_secret.

    Raises:
        HTTPException: If registration fails due to database error or unexpected issues.
    """
    logger.info(f"Attempting to register user with screen_name: {user.screen_name}")
    try:
        new_user = await create_user(db, user.screen_name)
        if not new_user:
            logger.error("Failed to create user in the database")
            raise DatabaseOperationError("Failed to create user")
        logger.info(f"User registered successfully: {new_user.id}")
        return UserRegistrationResponse(
            id=new_user.id,
            screen_name=new_user.screen_name,
            user_secret=new_user.user_secret,
        )
    except DatabaseOperationError as e:
        logger.exception(f"Database operation error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration",
        )


@router.post(
    "/token",
    response_model=Token,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
@limiter.limit(settings.rate_limits["auth_token"])
async def login_for_access_token(
    request: Request,
    user_secret: SecretStr = Form(
        ..., description="User's secret key for authentication"
    ),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate a user and return an access token.

    Args:
        request (Request): The request object.
        user_secret (SecretStr): User's secret key for authentication.
        db (AsyncSession): Database session.

    Returns:
        Token: Access token for authenticated user.

    Raises:
        HTTPException: If authentication fails or unexpected issues occur.
    """
    logger.info("Login attempt received")
    try:
        user = await get_user_by_secret(db, user_secret.get_secret_value())
        if not user:
            logger.warning("Invalid user_secret provided")
            raise AuthenticationError("Invalid authentication credentials")
        access_token = create_access_token(data={"sub": str(user.id)})
        logger.info(f"User logged in successfully: {user.id}")
        return Token(access_token=access_token, token_type="bearer")
    except AuthenticationError as e:
        logger.exception(f"Authentication error during login: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login",
        )


# TODO: Add rate limiting to this endpoint
@router.get(
    "/users/me",
    response_model=UserInfo,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def read_users_me(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """
    Get the current authenticated user's information.

    Args:
        current_user (UserInfo): Current authenticated user (injected by dependency).

    Returns:
        UserInfo: Current user's information.
    """
    logger.debug(f"Retrieving profile for user: {current_user.id}")
    return current_user


# TODO: Add rate limiting to this endpoint
@router.put(
    "/users/me",
    response_model=UserInfo,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def update_user_profile(
    user_update: UserUpdate = Body(..., description="User profile update details"),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserInfo:
    """
    Update the current user's profile.

    Args:
        user_update (UserUpdate): User profile update details.
        current_user (UserInfo): Current authenticated user (injected by dependency).
        db (AsyncSession): Database session.

    Returns:
        UserInfo: Updated user information.

    Raises:
        HTTPException: If user is not found, update fails, or other unexpected issues occur.
    """
    logger.info(f"User {current_user.id} is attempting to update their profile")
    try:
        user = await get_user_by_id(db, current_user.id)
        if not user:
            logger.error(f"User not found: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        update_data = user_update.model_dump(exclude_unset=True)
        updated_user = await update_user(db, user, **update_data)

        if not updated_user:
            logger.error(f"Failed to update user: {current_user.id}")
            raise DatabaseOperationError("Failed to update user")

        logger.info(f"User profile updated successfully: {updated_user.id}")
        return get_user_info(updated_user)
    except DatabaseOperationError as e:
        logger.exception(f"Database operation error during profile update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error during profile update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during profile update",
        )
