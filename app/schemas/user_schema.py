from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    """Base user schema with common attributes."""

    screen_name: str | None = None


class UserCreate(BaseModel):
    """Schema for user creation."""

    screen_name: str


class UserUpdate(BaseModel):
    """Schema for user update."""

    screen_name: Optional[str] = None


class UserSchema(BaseModel):
    """Schema for user as stored in the database."""

    id: str
    screen_name: str
    user_secret: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for general user response (without user_secret)."""

    id: str
    screen_name: str

    class Config:
        from_attributes = True


class UserRegistrationResponse(UserResponse):
    """Schema for user registration response (includes user_secret)."""

    user_secret: str


class Token(BaseModel):
    """Schema for authentication token."""

    access_token: str
    token_type: str
