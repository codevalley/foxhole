import json
from typing import List, Dict, Any, Optional, cast, Tuple
from openai import OpenAI

from app.core.config import settings
from app.schemas.sidekick_schema import (
    SidekickInput,
    SidekickOutput,
    TokenUsage,
    LLMResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.operations import (
    get_sidekick_thread,
    update_sidekick_thread,
    create_sidekick_thread,
    create_person,
    update_person,
    create_task,
    update_task,
    create_topic,
    update_topic,
    create_note,
    update_note,
    get_person,
    get_task,
    get_topic,
    get_note,
    get_people_for_user,
    get_tasks_for_user,
    get_topics_for_user,
    get_notes_for_user,
)
from app.schemas.sidekick_schema import (
    SidekickThreadCreate,
    PersonCreate,
    TaskCreate,
    TopicCreate,
    NoteCreate,
)
from app.models import SidekickThread, Person, Task, Topic, Note
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class SidekickService:
    def __init__(self) -> None:
        self.client = OpenAI()

    async def fetch_entities_by_ids(
        self, db: AsyncSession, affected_entities: Dict[str, List[str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch full entity objects based on their IDs from affected_entities
        """
        entities: Dict[str, List[Dict[str, Any]]] = {
            "people": [],
            "tasks": [],
            "topics": [],
            "notes": [],
        }

        # Fetch people
        for person_id in affected_entities.get("people", []):
            if person := await get_person(db, person_id):
                entities["people"].append(self.person_to_dict(cast(Person, person)))

        # Fetch tasks
        for task_id in affected_entities.get("tasks", []):
            if task := await get_task(db, task_id):
                entities["tasks"].append(self.task_to_dict(cast(Task, task)))

        # Fetch topics
        for topic_id in affected_entities.get("topics", []):
            if topic := await get_topic(db, topic_id):
                entities["topics"].append(self.topic_to_dict(cast(Topic, topic)))

        # Fetch notes
        for note_id in affected_entities.get("notes", []):
            if note := await get_note(db, note_id):
                entities["notes"].append(self.note_to_dict(cast(Note, note)))

        return entities

    async def process_input(
        self, db: AsyncSession, user_id: str, sidekick_input: SidekickInput
    ) -> SidekickOutput:
        try:
            # Get or create thread
            thread = await self.get_or_create_thread(
                db, user_id, sidekick_input.thread_id
            )

            # Update conversation history
            updated_history = thread.conversation_history + [
                {"role": "user", "content": sidekick_input.user_input}
            ]

            # Construct prompt with user context
            prompt = await self.construct_prompt(db, user_id, updated_history)

            # Call OpenAI API
            llm_response, token_usage = await self.call_openai_api(prompt)

            # Process LLM response
            processed_response = self.process_data(llm_response)

            # Update thread with new conversation history
            final_history = updated_history + [
                {"role": "assistant", "content": json.dumps(llm_response.model_dump())}
            ]
            await update_sidekick_thread(db, thread.id, final_history)

            # Update entities based on LLM response
            context_updates, _ = await self.update_entities(
                db, processed_response["data"], user_id
            )

            # Fetch complete entities based on affected_entities
            affected_entities = processed_response["instructions"]["affected_entities"]
            inflated_entities = await self.fetch_entities_by_ids(db, affected_entities)

            # Check if thread is complete and create a new one if necessary
            is_thread_complete = (
                processed_response["instructions"]["status"] == "complete"
            )
            new_thread_id = ""
            if is_thread_complete:
                new_thread = await create_sidekick_thread(
                    db, SidekickThreadCreate(user_id=user_id)
                )
                new_thread_id = new_thread.id

            return SidekickOutput(
                response=processed_response["instructions"]["followup"],
                thread_id=new_thread_id if is_thread_complete else thread.id,
                status=processed_response["instructions"]["status"],
                new_prompt=processed_response["instructions"].get("new_prompt"),
                is_thread_complete=is_thread_complete,
                updated_entities=context_updates,
                entities=inflated_entities,
                token_usage=token_usage,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in process_input: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_or_create_thread(
        self, db: AsyncSession, user_id: str, thread_id: Optional[str]
    ) -> SidekickThread:
        if thread_id:
            thread = await get_sidekick_thread(db, thread_id)
            if not thread or thread.user_id != user_id:
                raise HTTPException(status_code=404, detail="Thread not found")
            return thread
        else:
            return await create_sidekick_thread(
                db, SidekickThreadCreate(user_id=user_id)
            )

    async def update_entities(
        self, db: AsyncSession, data: Dict[str, List[Dict[str, Any]]], user_id: str
    ) -> Tuple[Dict[str, int], Dict[str, List[Dict[str, Any]]]]:
        context_updates = {"tasks": 0, "people": 0, "topics": 0, "notes": 0}
        updated_entities: Dict[str, List[Dict[str, Any]]] = {
            "tasks": [],
            "people": [],
            "topics": [],
            "notes": [],
        }

        for entity_type, entities in data.items():
            for entity in entities:
                try:
                    if entity_type == "people":
                        updated_entity = await self.update_or_create_person(
                            db, entity, user_id
                        )
                    elif entity_type == "tasks":
                        updated_entity = await self.update_or_create_task(
                            db, entity, user_id
                        )
                    elif entity_type == "topics":
                        updated_entity = await self.update_or_create_topic(
                            db, entity, user_id
                        )
                    elif entity_type == "notes":
                        updated_entity = await self.update_or_create_note(
                            db, entity, user_id
                        )
                    else:
                        continue

                    if updated_entity:
                        context_updates[entity_type] += 1
                        updated_entities[entity_type].append(updated_entity)
                except Exception as e:
                    logger.error(f"Error updating {entity_type}: {str(e)}")
                    # Continue with the next entity

        return context_updates, updated_entities

    async def update_or_create_person(
        self, db: AsyncSession, person_data: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        try:
            # Set a default importance if it's missing or has an empty/whitespace-only value
            if not person_data.get("importance", "").strip():
                person_data["importance"] = "medium"

            person_create = PersonCreate(**person_data)
            existing_person = await get_person(db, person_data["person_id"])
            if existing_person:
                updated_person = await update_person(
                    db, person_data["person_id"], person_create
                )
            else:
                updated_person = await create_person(db, person_create, user_id)

            if updated_person:
                return self.person_to_dict(cast(Person, updated_person))
            else:
                logger.warning(
                    f"Failed to create or update person: {person_data['person_id']}"
                )
                return None
        except Exception as e:
            logger.error(f"Error in update_or_create_person: {str(e)}")
            return None

    async def update_or_create_task(
        self, db: AsyncSession, task_data: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        try:
            task_create = TaskCreate(**task_data)
            existing_task = await get_task(db, task_data["task_id"])
            if existing_task:
                updated_task = await update_task(db, task_data["task_id"], task_create)
            else:
                updated_task = await create_task(db, task_create, user_id)

            if updated_task:
                return self.task_to_dict(cast(Task, updated_task))
            else:
                logger.warning(
                    f"Failed to create or update task: {task_data['task_id']}"
                )
                return None
        except Exception as e:
            logger.error(f"Error in update_or_create_task: {str(e)}")
            return None

    async def update_or_create_topic(
        self, db: AsyncSession, topic_data: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        try:
            topic_create = TopicCreate(**topic_data)
            existing_topic = await get_topic(db, topic_data["topic_id"])
            if existing_topic:
                updated_topic = await update_topic(
                    db, topic_data["topic_id"], topic_create
                )
            else:
                updated_topic = await create_topic(db, topic_create, user_id)

            if updated_topic:
                return self.topic_to_dict(cast(Topic, updated_topic))
            else:
                logger.warning(
                    f"Failed to create or update topic: {topic_data['topic_id']}"
                )
                return None
        except Exception as e:
            logger.error(f"Error in update_or_create_topic: {str(e)}")
            return None

    async def update_or_create_note(
        self, db: AsyncSession, note_data: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        try:
            note_create = NoteCreate(**note_data)
            existing_note = await get_note(db, note_data["note_id"])
            if existing_note:
                updated_note = await update_note(db, note_data["note_id"], note_create)
            else:
                updated_note = await create_note(db, note_create, user_id)

            if updated_note:
                return self.note_to_dict(cast(Note, updated_note))
            else:
                logger.warning(
                    f"Failed to create or update note: {note_data['note_id']}"
                )
                return None
        except Exception as e:
            logger.error(f"Error in update_or_create_note: {str(e)}")
            return None

    async def construct_prompt(
        self, db: AsyncSession, user_id: str, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        try:
            context = await self.get_user_context(db, user_id)
            messages = [
                {"role": "system", "content": settings.SIDEKICK_SYSTEM_PROMPT},
                {"role": "user", "content": f"Current context: {json.dumps(context)}"},
            ]
            messages.extend(conversation_history)
            return messages
        except Exception as e:
            logger.error(f"Error in construct_prompt: {str(e)}")
            raise

    async def get_user_context(
        self, db: AsyncSession, user_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        context: Dict[str, List[Dict[str, Any]]] = {
            "people": [],
            "tasks": [],
            "topics": [],
            "notes": [],
        }

        # Fetch people
        people = await get_people_for_user(db, user_id)
        context["people"] = [self.person_to_dict(person) for person in people]

        # Fetch tasks
        tasks = await get_tasks_for_user(db, user_id)
        context["tasks"] = [self.task_to_dict(task) for task in tasks]

        # Fetch topics
        topics = await get_topics_for_user(db, user_id)
        context["topics"] = [self.topic_to_dict(topic) for topic in topics]

        # Fetch notes
        notes = await get_notes_for_user(db, user_id)
        context["notes"] = [self.note_to_dict(note) for note in notes]

        return context

    def person_to_dict(self, person: Person) -> Dict[str, Any]:
        return {
            "person_id": person.person_id,
            "name": person.name,
            "designation": person.designation,
            "relation_type": person.relation_type,
            "importance": person.importance,
            "notes": person.notes,
            "contact": person.contact,
        }

    def task_to_dict(self, task: Task) -> Dict[str, Any]:
        return {
            "task_id": task.task_id,
            "type": task.type,
            "description": task.description,
            "status": task.status,
            "actions": task.actions,
            "people": task.people,
            "dependencies": task.dependencies,
            "schedule": task.schedule,
            "priority": task.priority,
        }

    def topic_to_dict(self, topic: Topic) -> Dict[str, Any]:
        return {
            "topic_id": topic.topic_id,
            "name": topic.name,
            "description": topic.description,
            "keywords": topic.keywords,
            "related_people": topic.related_people,
            "related_tasks": topic.related_tasks,
        }

    def note_to_dict(self, note: Note) -> Dict[str, Any]:
        return {
            "note_id": note.note_id,
            "content": note.content,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "related_people": note.related_people,
            "related_tasks": note.related_tasks,
            "related_topics": note.related_topics,
        }

    async def call_openai_api(
        self, messages: List[Dict[str, str]]
    ) -> tuple[LLMResponse, TokenUsage]:
        try:
            # Ensure all messages are properly encoded
            sanitized_messages = []
            for msg in messages:
                if isinstance(msg["content"], str):
                    content = (
                        msg["content"].encode("utf-8", errors="replace").decode("utf-8")
                    )
                else:
                    content = (
                        str(msg["content"])
                        .encode("utf-8", errors="replace")
                        .decode("utf-8")
                    )

                sanitized_messages.append({"role": msg["role"], "content": content})

            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=sanitized_messages,
                response_format={"type": "json_object"},
            )

            # Get content from response using new API
            raw_response = response.choices[0].message.content
            logger.debug(f"Raw OpenAI API response: {raw_response}")

            try:
                api_response = LLMResponse.model_validate_json(raw_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Raw response that caused the error: {raw_response}")
                raise HTTPException(
                    status_code=500, detail="Unable to parse OpenAI response as JSON"
                )

            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            return api_response, token_usage

        except Exception as e:
            logger.error(f"Unexpected error in call_openai_api: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {str(e)}"
            )

    def process_data(self, llm_response: LLMResponse) -> Dict[str, Any]:
        processed = llm_response.model_dump()
        logger.info(f"Processed LLM response: {processed}")
        return cast(Dict[str, Any], processed)
