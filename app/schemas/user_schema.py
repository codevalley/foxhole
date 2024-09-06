from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    screen_name: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


class UserInDB(UserBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserInDB):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str
