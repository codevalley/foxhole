from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class UserBase(BaseModel):
    """Base user schema with common attributes."""

    screen_name: Optional[str] = Field(
        None, min_length=3, max_length=50, description="User's display name."
    )


class UserInfo(BaseModel):
    id: str = Field(..., pattern=r"^[\w-]{36}$", description="Unique user identifier.")
    screen_name: str = Field(
        ..., min_length=3, max_length=50, description="User's display name."
    )

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Schema for user creation."""

    screen_name: str = Field(
        ..., min_length=3, max_length=50, description="Desired display name."
    )


class UserUpdate(BaseModel):
    """Schema for user update."""

    screen_name: Optional[str] = Field(
        None, min_length=3, max_length=50, description="Updated display name."
    )


class UserSchema(BaseModel):
    """Schema for user as stored in the database."""

    id: str = Field(..., pattern=r"^[\w-]{36}$", description="Unique user identifier.")
    screen_name: str = Field(
        ..., min_length=3, max_length=50, description="User's display name."
    )
    user_secret: str = Field(
        ..., min_length=32, description="Secret key for user authentication."
    )

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Schema for general user response (without user_secret)."""

    id: str = Field(..., pattern=r"^[\w-]{36}$", description="Unique user identifier.")
    screen_name: str = Field(
        ..., min_length=3, max_length=50, description="User's display name."
    )

    model_config = ConfigDict(from_attributes=True)


class UserRegistrationResponse(UserResponse):
    """Schema for user registration response (includes user_secret)."""

    user_secret: str = Field(
        ..., min_length=32, description="Secret key for user authentication."
    )


class Token(BaseModel):
    """Schema for authentication token."""

    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field(..., description="Type of the token, e.g., Bearer.")
