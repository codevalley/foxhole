from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common attributes."""

    screen_name: str | None = None


class UserCreate(UserBase):
    """Schema for user creation."""

    pass


class UserUpdate(UserBase):
    """Schema for user update."""

    pass


class UserInDB(UserBase):
    """Schema for user as stored in the database."""

    id: str

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserInDB):
    """Schema for user response."""

    pass


class Token(BaseModel):
    """Schema for authentication token."""

    access_token: str
    token_type: str
