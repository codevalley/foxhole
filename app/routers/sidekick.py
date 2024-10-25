from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.operations import (
    get_sidekick_thread,
    get_topics_for_user,
    get_tasks_for_user,
    get_people_for_user,
    get_notes_for_user,
    create_topic,
    create_task,
    create_person,
    create_note,
    update_topic,
    update_task,
    update_person,
    update_note,
    delete_topic,
    delete_task,
    delete_person,
    delete_note,
)
from app.schemas.sidekick_schema import (
    SidekickInput,
    SidekickOutput,
    TopicCreate,
    TaskCreate,
    PersonCreate,
    NoteCreate,
    PaginatedResponse,
    Topic as TopicSchema,
    Task as TaskSchema,
    Person as PersonSchema,
    Note as NoteSchema,
)

from app.services.sidekick_service import SidekickService
from app.dependencies import get_current_user
from utils.database import get_db
from app.schemas.user_schema import UserInfo
from app.core.rate_limit import limiter
from app.core.config import settings
import logging
from typing import cast

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=SidekickOutput, tags=["sidekick"])
@limiter.limit(settings.rate_limits["default"])
async def process_sidekick_input(
    request: Request,
    sidekick_input: SidekickInput,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SidekickOutput:
    try:
        if sidekick_input.thread_id:
            thread = await get_sidekick_thread(db, sidekick_input.thread_id)
            if not thread or thread.user_id != current_user.id:
                raise HTTPException(status_code=404, detail="Thread not found")

        sidekick_service = SidekickService()
        result = await sidekick_service.process_input(
            db, current_user.id, sidekick_input
        )
        logger.info(f"Processed sidekick input for user {current_user.id}")
        logger.info(f"API RESPONSE: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing sidekick input for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/topics", response_model=PaginatedResponse[TopicSchema], tags=["topics"])
async def list_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TopicSchema]:
    topics = await get_topics_for_user(db, current_user.id)
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse[TopicSchema](
        items=[TopicSchema.model_validate(topic) for topic in topics[start:end]],
        total=len(topics),
        page=page,
        page_size=page_size,
    )


@router.post("/topics", response_model=TopicSchema, tags=["topics"])
async def create_new_topic(
    topic: TopicCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TopicSchema:
    db_topic = await create_topic(db, topic, current_user.id)
    return cast(TopicSchema, TopicSchema.model_validate(db_topic))


@router.put("/topics/{topic_id}", response_model=TopicSchema, tags=["topics"])
async def update_existing_topic(
    topic_id: str,
    topic: TopicCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TopicSchema:
    updated_topic = await update_topic(db, topic_id, topic)
    if not updated_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return cast(TopicSchema, TopicSchema.model_validate(updated_topic))


@router.delete("/topics/{topic_id}", tags=["topics"])
async def delete_existing_topic(
    topic_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    success = await delete_topic(db, topic_id)
    if not success:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic deleted successfully"}


@router.get("/tasks", response_model=PaginatedResponse[TaskSchema], tags=["tasks"])
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TaskSchema]:
    tasks = await get_tasks_for_user(db, current_user.id)
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse[TaskSchema](
        items=[TaskSchema.model_validate(task) for task in tasks[start:end]],
        total=len(tasks),
        page=page,
        page_size=page_size,
    )


@router.post("/tasks", response_model=TaskSchema, tags=["tasks"])
async def create_new_task(
    task: TaskCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskSchema:
    db_task = await create_task(db, task, current_user.id)
    return cast(TaskSchema, TaskSchema.model_validate(db_task))


@router.put("/tasks/{task_id}", response_model=TaskSchema, tags=["tasks"])
async def update_existing_task(
    task_id: str,
    task: TaskCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskSchema:
    updated_task = await update_task(db, task_id, task)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return cast(TaskSchema, TaskSchema.model_validate(updated_task))


@router.delete("/tasks/{task_id}", tags=["tasks"])
async def delete_existing_task(
    task_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    success = await delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.get("/people", response_model=PaginatedResponse[PersonSchema], tags=["people"])
async def list_people(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PersonSchema]:
    people = await get_people_for_user(db, current_user.id)
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse[PersonSchema](
        items=[PersonSchema.model_validate(person) for person in people[start:end]],
        total=len(people),
        page=page,
        page_size=page_size,
    )


@router.post("/people", response_model=PersonSchema, tags=["people"])
async def create_new_person(
    person: PersonCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PersonSchema:
    db_person = await create_person(db, person, current_user.id)
    return cast(PersonSchema, PersonSchema.model_validate(db_person))


@router.put("/people/{person_id}", response_model=PersonSchema, tags=["people"])
async def update_existing_person(
    person_id: str,
    person: PersonCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PersonSchema:
    updated_person = await update_person(db, person_id, person)
    if not updated_person:
        raise HTTPException(status_code=404, detail="Person not found")
    return cast(PersonSchema, PersonSchema.model_validate(updated_person))


@router.delete("/people/{person_id}", tags=["people"])
async def delete_existing_person(
    person_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    success = await delete_person(db, person_id)
    if not success:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"message": "Person deleted successfully"}


@router.get("/notes", response_model=PaginatedResponse[NoteSchema], tags=["notes"])
async def list_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[NoteSchema]:
    notes = await get_notes_for_user(db, current_user.id)
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse[NoteSchema](
        items=[NoteSchema.model_validate(note) for note in notes[start:end]],
        total=len(notes),
        page=page,
        page_size=page_size,
    )


@router.post("/notes", response_model=NoteSchema, tags=["notes"])
async def create_new_note(
    note: NoteCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteSchema:
    db_note = await create_note(db, note, current_user.id)
    return cast(NoteSchema, NoteSchema.model_validate(db_note))


@router.put("/notes/{note_id}", response_model=NoteSchema, tags=["notes"])
async def update_existing_note(
    note_id: str,
    note: NoteCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteSchema:
    updated_note = await update_note(db, note_id, note)
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")
    return cast(NoteSchema, NoteSchema.model_validate(updated_note))


@router.delete("/notes/{note_id}", tags=["notes"])
async def delete_existing_note(
    note_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    success = await delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}
