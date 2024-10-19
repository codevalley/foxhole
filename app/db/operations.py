from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models import User, Person, Task, Topic, Note, SidekickThread
from app.schemas.sidekick_schema import (
    SidekickThreadCreate,
    PersonCreate,
    TaskCreate,
    TopicCreate,
    NoteCreate,
)
import uuid
import logging

logger = logging.getLogger(__name__)


# User operations
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


# Person operations
async def create_person(db: AsyncSession, person: PersonCreate) -> Person:
    db_person = Person(**person.model_dump())
    db.add(db_person)
    await db.commit()
    await db.refresh(db_person)
    return db_person


async def get_person(db: AsyncSession, person_id: str) -> Optional[Person]:
    result = await db.execute(select(Person).filter(Person.person_id == person_id))
    return result.scalars().first()


async def update_person(
    db: AsyncSession, person_id: str, person_data: PersonCreate
) -> Optional[Person]:
    person = await get_person(db, person_id)
    if person:
        for key, value in person_data.model_dump().items():
            setattr(person, key, value)
        await db.commit()
        await db.refresh(person)
    return person


async def delete_person(db: AsyncSession, person_id: str) -> bool:
    person = await get_person(db, person_id)
    if person:
        await db.delete(person)
        await db.commit()
        return True
    return False


async def get_people_for_user(db: AsyncSession, user_id: str) -> List[Person]:
    result = await db.execute(select(Person).filter(Person.user_id == user_id))
    return list(result.scalars().all())


# Task operations
async def create_task(db: AsyncSession, task: TaskCreate) -> Task:
    db_task = Task(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def get_task(db: AsyncSession, task_id: str) -> Optional[Task]:
    result = await db.execute(select(Task).filter(Task.task_id == task_id))
    return result.scalars().first()


async def update_task(
    db: AsyncSession, task_id: str, task_data: TaskCreate
) -> Optional[Task]:
    task = await get_task(db, task_id)
    if task:
        for key, value in task_data.model_dump().items():
            setattr(task, key, value)
        await db.commit()
        await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    task = await get_task(db, task_id)
    if task:
        await db.delete(task)
        await db.commit()
        return True
    return False


async def get_tasks_for_user(db: AsyncSession, user_id: str) -> List[Task]:
    result = await db.execute(select(Task).filter(Task.user_id == user_id))
    return list(result.scalars().all())


# Topic operations
async def create_topic(db: AsyncSession, topic: TopicCreate) -> Topic:
    db_topic = Topic(**topic.model_dump())
    db.add(db_topic)
    await db.commit()
    await db.refresh(db_topic)
    return db_topic


async def get_topic(db: AsyncSession, topic_id: str) -> Optional[Topic]:
    result = await db.execute(select(Topic).filter(Topic.topic_id == topic_id))
    return result.scalars().first()


async def update_topic(
    db: AsyncSession, topic_id: str, topic_data: TopicCreate
) -> Optional[Topic]:
    topic = await get_topic(db, topic_id)
    if topic:
        for key, value in topic_data.model_dump().items():
            setattr(topic, key, value)
        await db.commit()
        await db.refresh(topic)
    return topic


async def delete_topic(db: AsyncSession, topic_id: str) -> bool:
    topic = await get_topic(db, topic_id)
    if topic:
        await db.delete(topic)
        await db.commit()
        return True
    return False


async def get_topics_for_user(db: AsyncSession, user_id: str) -> List[Topic]:
    result = await db.execute(select(Topic).filter(Topic.user_id == user_id))
    return list(result.scalars().all())


# Note operations
async def create_note(db: AsyncSession, note: NoteCreate) -> Note:
    db_note = Note(**note.model_dump())
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note


async def get_note(db: AsyncSession, note_id: str) -> Optional[Note]:
    result = await db.execute(select(Note).filter(Note.note_id == note_id))
    return result.scalars().first()


async def update_note(
    db: AsyncSession, note_id: str, note_data: NoteCreate
) -> Optional[Note]:
    note = await get_note(db, note_id)
    if note:
        for key, value in note_data.model_dump().items():
            setattr(note, key, value)
        await db.commit()
        await db.refresh(note)
    return note


async def delete_note(db: AsyncSession, note_id: str) -> bool:
    note = await get_note(db, note_id)
    if note:
        await db.delete(note)
        await db.commit()
        return True
    return False


async def get_notes_for_user(db: AsyncSession, user_id: str) -> List[Note]:
    result = await db.execute(select(Note).filter(Note.user_id == user_id))
    return list(result.scalars().all())


# SidekickThread operations
async def create_sidekick_thread(
    db: AsyncSession, thread: SidekickThreadCreate
) -> SidekickThread:
    db_thread = SidekickThread(**thread.model_dump(), id=str(uuid.uuid4()))
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


async def delete_sidekick_thread(db: AsyncSession, thread_id: str) -> bool:
    thread = await get_sidekick_thread(db, thread_id)
    if thread:
        await db.delete(thread)
        await db.commit()
        return True
    return False


# Database purge operation
async def purge_database(db: AsyncSession) -> None:
    await db.execute(delete(Person))
    await db.execute(delete(Task))
    await db.execute(delete(Topic))
    await db.execute(delete(Note))
    await db.execute(delete(SidekickThread))
    await db.commit()
