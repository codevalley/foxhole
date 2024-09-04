from pydantic import BaseModel

class UserCreate(BaseModel):
    # No fields required for user creation, as the server generates the userID

    class Config:
        orm_mode = True

class UserInDB(BaseModel):
    user_id: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str