from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching user by ID: {str(e)}")
        return None


async def create_user(db: AsyncSession, screen_name: str) -> Optional[User]:
    try:
        new_user = User(id=User.generate_user_id(), screen_name=screen_name)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        await db.rollback()
        return None


async def update_user(db: AsyncSession, user: User, **kwargs: Any) -> Optional[User]:
    try:
        for key, value in kwargs.items():
            setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        await db.rollback()
        return None
