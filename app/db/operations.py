from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import SidekickContext
from app.schemas.sidekick_schema import SidekickContextCreate
import uuid
import logging
from typing import Optional
from app.models import User, SidekickThread
from sqlalchemy import select
from app.schemas.sidekick_schema import SidekickThreadCreate


logger = logging.getLogger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching user by ID: {str(e)}")
        return None


async def get_user_by_secret(db: AsyncSession, user_secret: str) -> Optional[User]:
    try:
        result = await db.execute(select(User).filter(User.user_secret == user_secret))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching user by secret: {str(e)}")
        return None


async def create_user(db: AsyncSession, screen_name: str) -> Optional[User]:
    try:
        new_user = User(
            screen_name=screen_name, user_secret=User.generate_user_secret()
        )
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
            if (
                key != "id" and key != "user_secret"
            ):  # Prevent updating id and user_secret
                setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        await db.rollback()
        return None


# Sidekick methods


async def create_sidekick_thread(
    db: AsyncSession, thread: SidekickThreadCreate
) -> SidekickThread:
    db_thread = SidekickThread(
        id=str(uuid.uuid4()),
        user_id=thread.user_id,
        conversation_history=thread.conversation_history,
    )
    db.add(db_thread)
    await db.commit()
    await db.refresh(db_thread)
    return db_thread


async def get_sidekick_thread(
    db: AsyncSession, thread_id: str
) -> Optional[SidekickThread]:
    result = await db.execute(
        select(SidekickThread).filter(SidekickThread.id == thread_id)
    )
    return result.scalars().first()


async def update_sidekick_thread(
    db: AsyncSession, thread_id: str, conversation_history: List[Dict[str, str]]
) -> Optional[SidekickThread]:
    thread = await get_sidekick_thread(db, thread_id)
    if thread:
        thread.conversation_history = conversation_history
        await db.commit()
        await db.refresh(thread)
    return thread


async def create_sidekick_context(
    db: AsyncSession, context: SidekickContextCreate
) -> SidekickContext:
    db_context = SidekickContext(
        id=str(uuid.uuid4()),
        user_id=context.user_id,
        context_type=context.context_type,
        data=context.data,
    )
    db.add(db_context)
    await db.commit()
    await db.refresh(db_context)
    return db_context


async def get_sidekick_context(
    db: AsyncSession, user_id: str, context_type: str
) -> Optional[SidekickContext]:
    result = await db.execute(
        select(SidekickContext).filter(
            SidekickContext.user_id == user_id,
            SidekickContext.context_type == context_type,
        )
    )
    return result.scalars().first()


async def update_sidekick_context(
    db: AsyncSession, user_id: str, context_type: str, data: List[Dict[str, Any]]
) -> Optional[SidekickContext]:
    context = await get_sidekick_context(db, user_id, context_type)
    if context:
        context.data = data
        await db.commit()
        await db.refresh(context)
    return context


async def update_or_create_sidekick_context(
    db: AsyncSession, context: SidekickContextCreate
) -> SidekickContext | Any:
    existing_context = await get_sidekick_context(
        db, context.user_id, context.context_type
    )
    if existing_context:
        existing_context.data = context.data
        await db.commit()
        await db.refresh(existing_context)
        return existing_context
    else:
        new_context = SidekickContext(
            id=str(uuid.uuid4()),
            user_id=context.user_id,
            context_type=context.context_type,
            data=context.data,
        )
        db.add(new_context)
        await db.commit()
        await db.refresh(new_context)
        return new_context
