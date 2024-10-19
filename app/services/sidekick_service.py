import json
from typing import List, Dict, Any, cast
import openai
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
)
from app.schemas.sidekick_schema import (
    SidekickThreadCreate,
    PersonCreate,
    TaskCreate,
    TopicCreate,
    NoteCreate,
)
from app.models import SidekickThread
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class SidekickService:
    def __init__(self) -> None:
        openai.api_key = settings.OPENAI_API_KEY

    async def process_input(
        self, db: AsyncSession, user_id: str, sidekick_input: SidekickInput
    ) -> SidekickOutput:
        try:
            thread = (
                await get_sidekick_thread(db, sidekick_input.thread_id)
                if sidekick_input.thread_id
                else await create_sidekick_thread(
                    db, SidekickThreadCreate(user_id=user_id)
                )
            )

            thread = cast(SidekickThread, thread)

            updated_history = thread.conversation_history + [
                {"role": "user", "content": sidekick_input.user_input}
            ]

            prompt = await self.construct_prompt(db, user_id, updated_history)
            llm_response, token_usage = await self.call_openai_api(prompt)
            processed_response = self.process_data(llm_response)

            final_history = updated_history + [
                {"role": "assistant", "content": json.dumps(llm_response)}
            ]
            await update_sidekick_thread(db, thread.id, final_history)

            context_updates = await self.update_entities(db, processed_response["data"])

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
                token_usage=token_usage,
            )
        except Exception as e:
            logger.error(f"Error in process_input: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def update_entities(
        self, db: AsyncSession, data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, int]:
        context_updates = {"tasks": 0, "people": 0, "topics": 0, "notes": 0}

        for entity_type, entities in data.items():
            for entity in entities:
                if entity_type == "people":
                    await self.update_or_create_person(db, entity)
                elif entity_type == "tasks":
                    await self.update_or_create_task(db, entity)
                elif entity_type == "topics":
                    await self.update_or_create_topic(db, entity)
                elif entity_type == "notes":
                    await self.update_or_create_note(db, entity)

                context_updates[entity_type] += 1

        return context_updates

    async def update_or_create_person(
        self, db: AsyncSession, person_data: Dict[str, Any]
    ) -> None:
        person_create = PersonCreate(**person_data)
        existing_person = await get_person(db, person_data["person_id"])
        if existing_person:
            await update_person(db, person_data["person_id"], person_create)
        else:
            await create_person(db, person_create)

    async def update_or_create_task(
        self, db: AsyncSession, task_data: Dict[str, Any]
    ) -> None:
        task_create = TaskCreate(**task_data)
        existing_task = await get_task(db, task_data["task_id"])
        if existing_task:
            await update_task(db, task_data["task_id"], task_create)
        else:
            await create_task(db, task_create)

    async def update_or_create_topic(
        self, db: AsyncSession, topic_data: Dict[str, Any]
    ) -> None:
        topic_create = TopicCreate(**topic_data)
        existing_topic = await get_topic(db, topic_data["topic_id"])
        if existing_topic:
            await update_topic(db, topic_data["topic_id"], topic_create)
        else:
            await create_topic(db, topic_create)

    async def update_or_create_note(
        self, db: AsyncSession, note_data: Dict[str, Any]
    ) -> None:
        note_create = NoteCreate(**note_data)
        existing_note = await get_note(db, note_data["note_id"])
        if existing_note:
            await update_note(db, note_data["note_id"], note_create)
        else:
            await create_note(db, note_create)

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
        # This method should be implemented to fetch all relevant user context
        # from the database (people, tasks, topics, notes)
        # For now, returning an empty context
        return {"people": [], "tasks": [], "topics": [], "notes": []}

    async def call_openai_api(
        self, messages: List[Dict[str, str]]
    ) -> tuple[LLMResponse, TokenUsage]:
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini-2024-07-18",
                messages=messages,
            )
            raw_response = response.choices[0].message.content
            logger.info(f"Raw OpenAI API response: {raw_response}")

            api_response = LLMResponse.parse_raw(raw_response)
            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            return api_response, token_usage
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Raw response that caused the error: {raw_response}")
            raise HTTPException(
                status_code=500, detail="Unable to parse OpenAI response as JSON"
            )
        except Exception as e:
            logger.error(f"Unexpected error in call_openai_api: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {str(e)}"
            )

    def process_data(self, llm_response: LLMResponse) -> Dict[str, Any]:
        return llm_response.model_dump()
