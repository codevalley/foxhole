"""
Function handlers for OpenAI function calls.
These handlers implement the actual database operations for each function.
"""

from typing import Dict, Any, Type
from abc import ABC, abstractmethod
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.openai_functions import (
    PersonSearchParams,
    TaskSearchParams,
    TopicSearchParams,
    NoteSearchParams,
)
from app.schemas.sidekick_schema import (
    Person as PersonSchema,
    Task as TaskSchema,
    Topic as TopicSchema,
    Note as NoteSchema,
)
from app.models import Person, Task, Topic, Note


class FunctionHandler(ABC):
    """Base class for function handlers"""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    @abstractmethod
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the function call with given parameters"""


class GetPeopleHandler(FunctionHandler):
    """Handler for get_people function"""

    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        search_params = PersonSearchParams(**params)
        query = select(Person).where(Person.user_id == self.user_id)

        if search_params.name:
            query = query.where(Person.name.ilike(f"%{search_params.name}%"))
        if search_params.designation:
            query = query.where(
                Person.designation.ilike(f"%{search_params.designation}%")
            )
        if search_params.relation_type:
            query = query.where(Person.relation_type == search_params.relation_type)
        if search_params.importance:
            query = query.where(Person.importance == search_params.importance)

        result = await self.db.execute(query)
        people = result.scalars().all()

        return {
            "results": [
                PersonSchema.model_validate(person).model_dump() for person in people
            ],
            "total": len(people),
        }


class GetTasksHandler(FunctionHandler):
    """Handler for get_tasks function"""

    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        search_params = TaskSearchParams(**params)
        query = select(Task).where(Task.user_id == self.user_id)

        if search_params.query:
            query = query.where(Task.description.ilike(f"%{search_params.query}%"))
        if search_params.type:
            query = query.where(Task.type == search_params.type)
        if search_params.status:
            query = query.where(Task.status == search_params.status)
        if search_params.priority:
            query = query.where(Task.priority == search_params.priority)
        if search_params.owner:
            query = query.where(Task.people["owner"].astext == search_params.owner)

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return {
            "results": [TaskSchema.model_validate(task).model_dump() for task in tasks],
            "total": len(tasks),
        }


class GetTopicsHandler(FunctionHandler):
    """Handler for get_topics function"""

    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        search_params = TopicSearchParams(**params)
        query = select(Topic).where(Topic.user_id == self.user_id)

        if search_params.keyword:
            query = query.where(Topic.keywords.contains([search_params.keyword]))
        if search_params.name:
            query = query.where(Topic.name.ilike(f"%{search_params.name}%"))
        if search_params.description:
            query = query.where(
                Topic.description.ilike(f"%{search_params.description}%")
            )
        if search_params.related_person:
            query = query.where(
                Topic.related_people.contains([search_params.related_person])
            )

        result = await self.db.execute(query)
        topics = result.scalars().all()

        return {
            "results": [
                TopicSchema.model_validate(topic).model_dump() for topic in topics
            ],
            "total": len(topics),
        }


class GetNotesHandler(FunctionHandler):
    """Handler for get_notes function"""

    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        search_params = NoteSearchParams(**params)
        query = select(Note).where(Note.user_id == self.user_id)

        if search_params.query:
            query = query.where(Note.content.ilike(f"%{search_params.query}%"))
        if search_params.related_topic:
            query = query.where(
                Note.related_topics.contains([search_params.related_topic])
            )
        if search_params.related_person:
            query = query.where(
                Note.related_people.contains([search_params.related_person])
            )
        if search_params.related_task:
            query = query.where(
                Note.related_tasks.contains([search_params.related_task])
            )

        result = await self.db.execute(query)
        notes = result.scalars().all()

        return {
            "results": [NoteSchema.model_validate(note).model_dump() for note in notes],
            "total": len(notes),
        }


# Registry of function handlers
FUNCTION_HANDLERS: Dict[str, Type[FunctionHandler]] = {
    "get_people": GetPeopleHandler,
    "get_tasks": GetTasksHandler,
    "get_topics": GetTopicsHandler,
    "get_notes": GetNotesHandler,
}
