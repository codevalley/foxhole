from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import datetime, timedelta
from utils.database import get_db
from models.user import User
from schemas.user import UserCreate, UserInDB, Token
from utils.security import generate_user_id
from config import settings

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_user(db: AsyncSession, user_id: str):
    """
    Retrieve a user from the database by user_id
    """
    result = await db.execute(User.__table__.select().where(User.user_id == user_id))
    return result.scalar_one_or_none()

@router.post("/register", response_model=UserInDB)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user by generating a unique userID
    """
    # Generate a unique userID
    user_id = generate_user_id()
    
    # Check if the generated userID already exists (very unlikely, but good to check)
    while await get_user(db, user_id):
        user_id = generate_user_id()
    
    # Create a new user with the generated userID
    new_user = User(user_id=user_id)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.post("/token", response_model=Token)
async def login(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generate an access token for a given userID
    """
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid userID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Validate the access token and return the current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

@router.get("/users/me", response_model=UserInDB)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Return the current user's information
    """
    return current_user