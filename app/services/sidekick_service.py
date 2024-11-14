import json
from typing import List, Dict, Any, Optional, cast, Tuple, Literal
from openai import OpenAI
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import asyncio
from nanoid import generate
from app.core.config import settings
from app.schemas.sidekick_schema import (
    SidekickInput,
    SidekickOutput,
    TokenUsage,
    LLMResponse,
    Person as PersonSchema,
    Task as TaskSchema,
    Topic as TopicSchema,
    Note as NoteSchema,
    PersonContact,
    TaskPeople,
)
from dataclasses import dataclass
from app.models import SidekickThread
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
from app.models import Person, Task, Topic, Note
from fastapi import HTTPException
import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class EntityProcessingError(Exception):
    """Custom exception for entity processing errors"""

    def __init__(self, entity_type: str, entity_id: str, error: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.error = error
        super().__init__(f"Error processing {entity_type} {entity_id}: {error}")


class SidekickService:
    def __init__(self) -> None:
        self.client = OpenAI()

    async def fetch_entities_by_ids(
        self, db: AsyncSession, affected_entities: Dict[str, List[str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch full entity objects based on their IDs from affected_entities with improved error handling
        """
        entities: Dict[str, List[Dict[str, Any]]] = {
            "people": [],
            "tasks": [],
            "topics": [],
            "notes": [],
        }
        logger.info(
            f"Starting fetch_entities_by_ids with affected_entities: {affected_entities}"
        )

        # Helper function to safely fetch and convert entities
        async def safe_fetch_entity(
            entity_type: str, entity_id: str, fetch_func: Any, convert_func: Any
        ) -> Optional[Dict[str, Any]]:
            try:
                if entity := await fetch_func(db, entity_id):
                    return cast(Dict[str, Any], convert_func(entity))
            except Exception as e:
                logger.error(f"Error fetching {entity_type} {entity_id}: {str(e)}")
                return None
            return None

        # Log person fetching specifically
        person_ids = affected_entities.get("people", [])
        logger.info(f"Attempting to fetch people with IDs: {person_ids}")
        # Fetch each type of entity
        for person_id in person_ids:
            try:
                if person := await get_person(db, person_id):
                    logger.info(f"Successfully fetched person: {person}")
                    person_dict = self.person_to_dict(person)
                    logger.info(f"Converted person to dict: {person_dict}")
                    entities["people"].append(person_dict)
                else:
                    logger.warning(f"No person found for ID: {person_id}")
            except Exception as e:
                logger.error(f"Error fetching person {person_id}: {str(e)}")

        for task_id in affected_entities.get("tasks", []):
            if result := await safe_fetch_entity(
                "task", task_id, get_task, self.task_to_dict
            ):
                entities["tasks"].append(result)

        for topic_id in affected_entities.get("topics", []):
            if result := await safe_fetch_entity(
                "topic", topic_id, get_topic, self.topic_to_dict
            ):
                entities["topics"].append(result)

        for note_id in affected_entities.get("notes", []):
            if result := await safe_fetch_entity(
                "note", note_id, get_note, self.note_to_dict
            ):
                entities["notes"].append(result)

        logger.info(f"Final entities after fetching: {entities}")

        return entities

    async def process_input(
        self, db: AsyncSession, user_id: str, sidekick_input: SidekickInput
    ) -> SidekickOutput:
        """Main entry point for processing user input"""
        try:
            # Handle conversation thread
            thread, updated_history = await self._handle_conversation_thread(
                db, user_id, sidekick_input
            )

            # Get LLM response
            processed_response, token_usage = await self._get_llm_response(
                db, user_id, updated_history
            )

            # Update conversation history
            await self._update_conversation_history(
                db, thread.id, updated_history, processed_response
            )

            # Process entities
            inflated_entities, context_updates = await self._process_entities(
                db, user_id, processed_response
            )

            # Handle thread completion
            thread_info = await self._handle_thread_completion(
                db, user_id, thread.id, processed_response
            )

            return SidekickOutput(
                response=processed_response["instructions"]["followup"],
                thread_id=thread_info.new_thread_id or thread.id,
                status=processed_response["instructions"]["status"],
                new_prompt=processed_response["instructions"].get("new_prompt"),
                is_thread_complete=thread_info.is_complete,
                updated_entities=context_updates,
                entities=inflated_entities,
                token_usage=token_usage,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in process_input: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def _handle_conversation_thread(
        self, db: AsyncSession, user_id: str, sidekick_input: SidekickInput
    ) -> Tuple[SidekickThread, List[Dict[str, str]]]:
        """Handle thread creation/retrieval and history update"""
        try:
            thread = await self.get_or_create_thread(
                db, user_id, sidekick_input.thread_id
            )
            updated_history = thread.conversation_history + [
                {"role": "user", "content": sidekick_input.user_input}
            ]
            return thread, updated_history
        except Exception as e:
            logger.error(f"Error handling conversation thread: {str(e)}")
            return thread, [{"role": "user", "content": sidekick_input.user_input}]

    async def _get_llm_response(
        self, db: AsyncSession, user_id: str, conversation_history: List[Dict[str, str]]
    ) -> Tuple[Dict[str, Any], TokenUsage]:
        """Get and process LLM response"""
        try:
            prompt = await self.construct_prompt(db, user_id, conversation_history)
        except Exception as e:
            logger.error(f"Error constructing prompt: {str(e)}")
            prompt = [
                {"role": "system", "content": settings.SIDEKICK_SYSTEM_PROMPT},
                {"role": "user", "content": conversation_history[-1]["content"]},
            ]

        llm_response, token_usage = await self.call_openai_api(prompt)
        return self.process_data(llm_response), token_usage

    async def _update_conversation_history(
        self,
        db: AsyncSession,
        thread_id: str,
        current_history: List[Dict[str, str]],
        processed_response: Dict[str, Any],
    ) -> None:
        """Update thread conversation history"""
        try:
            final_history = current_history + [
                {"role": "assistant", "content": json.dumps(processed_response)}
            ]
            await update_sidekick_thread(db, thread_id, final_history)
        except Exception as e:
            logger.error(f"Error updating thread history: {str(e)}")

    async def _process_entities(
        self, db: AsyncSession, user_id: str, processed_response: Dict[str, Any]
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, int]]:
        """Process and merge entities with detailed debug logging"""
        try:
            logger.info(
                f"Starting _process_entities with processed_response: {processed_response}"
            )

            context_updates, entity_updates = await self.update_entities(
                db, processed_response["data"], user_id
            )
            logger.info(f"After update_entities - entity_updates: {entity_updates}")

            affected_entities = processed_response["instructions"]["affected_entities"]
            logger.info(f"Processing affected_entities: {affected_entities}")

            fetched_entities = await self.fetch_entities_by_ids(db, affected_entities)
            logger.info(
                f"After fetch_entities_by_ids - fetched_entities: {fetched_entities}"
            )
            logger.info(f"Fetched people: {fetched_entities.get('people', [])}")

            inflated_entities = await self._merge_entities(
                entity_updates, fetched_entities
            )
            logger.info(
                f"After _merge_entities - inflated_entities: {inflated_entities}"
            )
            logger.info(f"Final people list: {inflated_entities.get('people', [])}")

            return inflated_entities, context_updates

        except Exception as e:
            logger.error(f"Error processing entities: {str(e)}")
            inflated_entities = entity_updates
            return inflated_entities, {"tasks": 0, "people": 0, "topics": 0, "notes": 0}

    async def _merge_entities(
        self,
        entity_updates: Dict[str, List[Dict[str, Any]]],
        fetched_entities: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Merge entities with corrected ID key handling"""
        logger.info("Starting _merge_entities")
        logger.info(f"Initial entity_updates: {entity_updates}")
        logger.info(f"Initial fetched_entities: {fetched_entities}")

        # Map of plural entity types to their ID field names
        id_field_map = {
            "tasks": "task_id",
            "people": "person_id",  # Fixed: "people" -> "person_id"
            "topics": "topic_id",
            "notes": "note_id",
        }

        merged = {
            entity_type: entity_updates.get(entity_type, [])
            + fetched_entities.get(entity_type, [])
            for entity_type in ["tasks", "people", "topics", "notes"]
        }
        logger.info(f"After initial merge: {merged}")

        for entity_type in merged:
            logger.info(f"Processing {entity_type}")
            seen_ids = set()
            unique_entities = []

            id_field = id_field_map[entity_type]  # Use the correct ID field name
            logger.info(f"Using ID field {id_field} for {entity_type}")

            for entity in merged[entity_type]:
                if not entity:
                    logger.warning(f"Found null entity in {entity_type}")
                    continue

                entity_id = entity.get(id_field)  # Use the mapped ID field
                logger.info(f"Processing {entity_type} entity with ID: {entity_id}")

                if entity_id and entity_id not in seen_ids:
                    seen_ids.add(entity_id)
                    unique_entities.append(entity)
                    logger.info(f"Added {entity_type} with ID {entity_id}")
                else:
                    logger.warning(
                        f"Skipped {entity_type} entity - invalid or duplicate ID: {entity_id}"
                    )

            merged[entity_type] = unique_entities
            logger.info(f"Final {entity_type} list: {merged[entity_type]}")

        return merged

    @dataclass
    class ThreadCompletionInfo:
        is_complete: bool
        new_thread_id: Optional[str]

    async def _handle_thread_completion(
        self,
        db: AsyncSession,
        user_id: str,
        current_thread_id: str,
        processed_response: Dict[str, Any],
    ) -> ThreadCompletionInfo:
        """Handle thread completion and new thread creation"""
        is_complete = processed_response["instructions"]["status"] == "complete"
        new_thread_id = None

        if is_complete:
            try:
                new_thread = await create_sidekick_thread(
                    db, SidekickThreadCreate(user_id=user_id)
                )
                new_thread_id = new_thread.id
            except Exception as e:
                logger.error(f"Error creating new thread: {str(e)}")
                is_complete = False
                new_thread_id = current_thread_id

        return self.ThreadCompletionInfo(
            is_complete=is_complete, new_thread_id=new_thread_id
        )

    async def get_user_context(
        self, db: AsyncSession, user_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get user context with improved error handling"""
        context: Dict[str, List[Dict[str, Any]]] = {
            "people": [],
            "tasks": [],
            "topics": [],
            "notes": [],
        }

        async def safe_fetch_entities(
            entity_type: str, fetch_func: Any, convert_func: Any
        ) -> List[Dict[str, Any]]:
            try:
                entities = await fetch_func(db, user_id)
                converted_entities = []
                for entity in entities:
                    try:
                        converted = convert_func(entity)
                        converted_entities.append(converted)
                    except Exception as e:
                        logger.error(f"Error converting {entity_type}: {str(e)}")
                        continue
                return converted_entities
            except SQLAlchemyError as e:
                logger.error(f"Database error fetching {entity_type}: {str(e)}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching {entity_type}: {str(e)}")
                return []

        # Fetch each type of entity independently
        context["people"] = await safe_fetch_entities(
            "people", get_people_for_user, self.person_to_dict
        )
        context["tasks"] = await safe_fetch_entities(
            "tasks", get_tasks_for_user, self.task_to_dict
        )
        context["topics"] = await safe_fetch_entities(
            "topics", get_topics_for_user, self.topic_to_dict
        )
        context["notes"] = await safe_fetch_entities(
            "notes", get_notes_for_user, self.note_to_dict
        )

        return context

    async def update_or_create_entity(
        self,
        db: AsyncSession,
        entity_data: Dict[str, Any],
        user_id: str,
        entity_type: str,
        create_schema: Any,
        get_func: Any,
        update_func: Any,
        create_func: Any,
        convert_func: Any,
    ) -> Optional[Dict[str, Any]]:
        """Generic function to safely update or create an entity with user ownership validation"""
        try:
            # Get the entity ID field name
            id_field = f"{entity_type}_id"
            entity_id = entity_data.get(id_field)

            # Check if entity exists
            if entity_id:
                existing_entity = await get_func(db, entity_id)

                if existing_entity:
                    # Check if the entity belongs to the current user
                    if (
                        hasattr(existing_entity, "user_id")
                        and existing_entity.user_id == user_id
                    ):
                        # User owns the entity - proceed with update
                        create_instance = create_schema(**entity_data)
                        updated_entity = await update_func(
                            db, entity_id, create_instance
                        )
                        if updated_entity:
                            return cast(Dict[str, Any], convert_func(updated_entity))
                    else:
                        # Entity exists but belongs to another user
                        # Generate new ID instead of removing it
                        entity_data[id_field] = generate(size=8)

            # Either entity doesn't exist or we removed conflicting ID
            # Create new entity with auto-generated ID if none provided
            create_instance = create_schema(**entity_data)
            new_entity = await create_func(db, create_instance, user_id)
            if new_entity:
                return cast(Dict[str, Any], convert_func(new_entity))

        except ValidationError as e:
            logger.error(f"Validation error for {entity_type}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error updating {entity_type}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing {entity_type}: {str(e)}")
            return None

        return None

    async def update_or_create_person(
        self, db: AsyncSession, person_data: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        # Set default importance if missing or empty
        if not person_data.get("importance", "").strip():
            person_data["importance"] = "medium"

        return await self.update_or_create_entity(
            db,
            person_data,
            user_id,
            "person",
            PersonCreate,
            get_person,
            update_person,
            create_person,
            self.person_to_dict,
        )

    async def update_or_create_task(
        self, db: AsyncSession, task_data: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.update_or_create_entity(
            db,
            task_data,
            user_id,
            "task",
            TaskCreate,
            get_task,
            update_task,
            create_task,
            self.task_to_dict,
        )

    async def update_or_create_topic(
        self, db: AsyncSession, topic_data: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        return await self.update_or_create_entity(
            db,
            topic_data,
            user_id,
            "topic",
            TopicCreate,
            get_topic,
            update_topic,
            create_topic,
            self.topic_to_dict,
        )

    async def update_or_create_note(
        self, db: AsyncSession, note_data: Dict[str, Any], user_id: str
    ) -> Optional[Dict[str, Any]]:
        # Ensure dates are in the correct format
        try:
            for date_field in ["created_at", "updated_at"]:
                if date_field in note_data:
                    # Convert to datetime if it's a string
                    if isinstance(note_data[date_field], str):
                        try:
                            datetime.fromisoformat(
                                note_data[date_field].replace("Z", "+00:00")
                            )
                        except ValueError:
                            # If parsing fails, use current UTC time
                            note_data[date_field] = datetime.now(UTC).isoformat()
        except Exception as e:
            logger.error(f"Error processing note dates: {str(e)}")
            # Set current time for both fields if there's an error
            current_time = datetime.now(UTC).isoformat()
            note_data["created_at"] = current_time
            note_data["updated_at"] = current_time

        return await self.update_or_create_entity(
            db,
            note_data,
            user_id,
            "note",
            NoteCreate,
            get_note,
            update_note,
            create_note,
            self.note_to_dict,
        )

    def person_to_dict(self, person: Person) -> Dict[str, Any]:
        """Convert person to dictionary with validation"""
        try:
            # First validate using Pydantic schema
            person_schema = PersonSchema(
                person_id=person.person_id,
                name=person.name,
                designation=person.designation,
                relation_type=person.relation_type,
                importance=cast(
                    Literal["high", "medium", "low"], person.importance or "medium"
                ),
                notes=person.notes or "",
                contact=PersonContact.model_validate(
                    person.contact or {"email": "", "phone": ""}
                ),
            )
            return cast(Dict[str, Any], person_schema.model_dump())
        except ValidationError as e:
            logger.error(
                f"Validation error converting person {person.person_id}: {str(e)}"
            )
            raise EntityProcessingError("person", person.person_id, str(e))

    def task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert task to dictionary with validation"""
        try:
            # First validate using Pydantic schema
            task_schema = TaskSchema(
                task_id=task.task_id,
                type=cast(Literal["1", "2", "3", "4"], task.type),
                description=task.description,
                status=cast(Literal["active", "pending", "completed"], task.status),
                actions=task.actions or [],
                people=TaskPeople.model_validate(
                    task.people
                    or {
                        "owner": "",
                        "final_beneficiary": "",
                        "stakeholders": [],
                    }
                ),
                dependencies=task.dependencies or [],
                schedule=task.schedule or "",
                priority=cast(
                    Literal["high", "medium", "low"], task.priority or "medium"
                ),
            )
            return cast(Dict[str, Any], task_schema.model_dump())
        except ValidationError as e:
            logger.error(f"Validation error converting task {task.task_id}: {str(e)}")
            raise EntityProcessingError("task", task.task_id, str(e))

    def topic_to_dict(self, topic: Topic) -> Dict[str, Any]:
        """Convert topic to dictionary with validation"""
        try:
            # First validate using Pydantic schema
            topic_schema = TopicSchema(
                topic_id=topic.topic_id,
                name=topic.name,
                description=topic.description or "",
                keywords=topic.keywords or [],
                related_people=topic.related_people or [],
                related_tasks=topic.related_tasks or [],
            )
            return cast(Dict[str, Any], topic_schema.model_dump())
        except ValidationError as e:
            logger.error(
                f"Validation error converting topic {topic.topic_id}: {str(e)}"
            )
            raise EntityProcessingError("topic", topic.topic_id, str(e))

    def note_to_dict(self, note: Note) -> Dict[str, Any]:
        """Convert note to dictionary with validation"""
        try:
            # Ensure dates are valid
            current_time = datetime.now(UTC).isoformat()
            created_at = note.created_at or current_time
            updated_at = note.updated_at or current_time

            # First validate using Pydantic schema
            note_schema = NoteSchema(
                note_id=note.note_id,
                content=note.content or "",
                created_at=created_at,
                updated_at=updated_at,
                related_people=note.related_people or [],
                related_tasks=note.related_tasks or [],
                related_topics=note.related_topics or [],
            )
            return cast(Dict[str, Any], note_schema.model_dump())
        except ValidationError as e:
            logger.error(f"Validation error converting note {note.note_id}: {str(e)}")
            raise EntityProcessingError("note", note.note_id, str(e))

    async def call_openai_api(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> tuple[LLMResponse, TokenUsage]:
        """Call OpenAI API with retry logic and improved error handling"""
        last_error = None
        for attempt in range(max_retries):
            try:
                # Sanitize messages
                sanitized_messages = []
                for msg in messages:
                    try:
                        if isinstance(msg["content"], str):
                            content = (
                                msg["content"]
                                .encode("utf-8", errors="replace")
                                .decode("utf-8")
                            )
                        else:
                            content = (
                                str(msg["content"])
                                .encode("utf-8", errors="replace")
                                .decode("utf-8")
                            )
                        sanitized_messages.append(
                            {"role": msg["role"], "content": content}
                        )
                    except Exception as e:
                        logger.error(f"Error sanitizing message: {str(e)}")
                        content = "Error processing message content"
                        sanitized_messages.append(
                            {"role": msg.get("role", "user"), "content": content}
                        )

                # Make API call using the synchronous create method but in an async context
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=settings.OPENAI_MODEL,
                        messages=sanitized_messages,
                        response_format={"type": "json_object"},
                        timeout=30.0,
                    ),
                )

                # Process response
                if not response.choices:
                    raise ValueError("No choices in OpenAI response")

                raw_response = response.choices[0].message.content
                if not raw_response:
                    raise ValueError("Empty response content from OpenAI")

                logger.debug(f"Raw OpenAI API response: {raw_response}")

                try:
                    api_response = LLMResponse.model_validate_json(raw_response)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {str(e)}")
                    logger.error(f"Raw response that caused the error: {raw_response}")
                    # Attempt to sanitize and retry JSON parsing
                    try:
                        sanitized_response = json.loads(raw_response)
                        api_response = LLMResponse.model_validate(sanitized_response)
                    except Exception as e2:
                        logger.error(f"Failed to sanitize response: {str(e2)}")
                        raise HTTPException(
                            status_code=500,
                            detail="Unable to parse OpenAI response as JSON",
                        )

                token_usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )
                return api_response, token_usage

            except Exception as e:
                last_error = e
                logger.error(
                    f"Error in OpenAI API call (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                continue

        # If all retries failed
        logger.error(f"All retries failed for OpenAI API call: {str(last_error)}")
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI API call failed after {max_retries} attempts: {str(last_error)}",
        )

    async def update_entities(
        self, db: AsyncSession, data: Dict[str, List[Dict[str, Any]]], user_id: str
    ) -> Tuple[Dict[str, int], Dict[str, List[Dict[str, Any]]]]:
        """Update entities with improved error handling"""
        context_updates = {"tasks": 0, "people": 0, "topics": 0, "notes": 0}
        updated_entities: Dict[str, List[Dict[str, Any]]] = {
            "tasks": [],
            "people": [],
            "topics": [],
            "notes": [],
        }

        # Process each entity type separately
        for entity_type, entities in data.items():
            if not isinstance(entities, list):
                logger.error(
                    f"Invalid data format for {entity_type}: expected list, got {type(entities)}"
                )
                continue

            for entity in entities:
                if not isinstance(entity, dict):
                    logger.error(
                        f"Invalid entity format for {entity_type}: expected dict, got {type(entity)}"
                    )
                    continue

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
                        logger.warning(f"Unknown entity type: {entity_type}")
                        continue

                    if updated_entity:
                        context_updates[entity_type] += 1
                        updated_entities[entity_type].append(updated_entity)

                except EntityProcessingError as e:
                    logger.error(f"Entity processing error for {entity_type}: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing {entity_type}: {str(e)}")
                    continue

        return context_updates, updated_entities

    def process_data(self, llm_response: LLMResponse) -> Dict[str, Any]:
        """Process LLM response with validation"""
        try:
            processed = llm_response.model_dump()
            # Ensure all required keys are present with defaults if missing
            processed.setdefault("instructions", {})
            processed["instructions"].setdefault("status", "complete")
            processed["instructions"].setdefault("followup", "")
            processed["instructions"].setdefault("new_prompt", "")
            processed["instructions"].setdefault("write", False)
            processed["instructions"].setdefault(
                "affected_entities",
                {"tasks": [], "people": [], "topics": [], "notes": []},
            )
            processed.setdefault(
                "data", {"tasks": [], "people": [], "topics": [], "notes": []}
            )

            logger.info(f"Processed LLM response: {processed}")
            return cast(Dict[str, Any], processed)
        except Exception as e:
            logger.error(f"Error processing LLM response: {str(e)}")
            # Return a safe default response
            return {
                "instructions": {
                    "status": "complete",
                    "followup": "Sorry, I encountered an error processing the response.",
                    "new_prompt": "",
                    "write": False,
                    "affected_entities": {
                        "tasks": [],
                        "people": [],
                        "topics": [],
                        "notes": [],
                    },
                },
                "data": {"tasks": [], "people": [], "topics": [], "notes": []},
            }

    async def get_or_create_thread(
        self, db: AsyncSession, user_id: str, thread_id: Optional[str]
    ) -> SidekickThread:
        """Get existing thread or create new one with error handling"""
        try:
            if thread_id:
                thread = await get_sidekick_thread(db, thread_id)
                if not thread or thread.user_id != user_id:
                    logger.error(
                        f"Thread {thread_id} not found or belongs to different user"
                    )
                    raise HTTPException(status_code=404, detail="Thread not found")
                return thread
            else:
                logger.info(f"Creating new thread for user {user_id}")
                try:
                    thread = await create_sidekick_thread(
                        db, SidekickThreadCreate(user_id=user_id)
                    )
                    return thread
                except SQLAlchemyError as e:
                    logger.error(f"Database error creating thread: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create new conversation thread",
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_or_create_thread: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error managing conversation thread: {str(e)}"
            )

    async def construct_prompt(
        self, db: AsyncSession, user_id: str, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Construct prompt with user context and error handling"""
        try:
            # Get user context with all entities
            context = await self.get_user_context(db, user_id)

            # Sanitize context before adding to prompt
            sanitized_context = json.dumps(context, ensure_ascii=False, default=str)

            # Construct messages array
            messages = [
                {"role": "system", "content": settings.SIDEKICK_SYSTEM_PROMPT},
                {"role": "user", "content": f"Current context: {sanitized_context}"},
            ]

            # Add conversation history with validation
            for msg in conversation_history:
                try:
                    # Ensure message has required fields
                    if "role" not in msg or "content" not in msg:
                        logger.warning(f"Skipping invalid message in history: {msg}")
                        continue

                    # Sanitize message content
                    content = msg["content"]
                    if not isinstance(content, str):
                        content = str(content)

                    # Add sanitized message
                    messages.append({"role": msg["role"], "content": content})
                except Exception as e:
                    logger.error(f"Error processing conversation message: {str(e)}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"Error constructing prompt: {str(e)}")
            # Return minimal prompt if context gathering fails
            return [
                {"role": "system", "content": settings.SIDEKICK_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "Error retrieving context. Please proceed with minimal context.",
                },
            ] + conversation_history  # Still include the conversation history
