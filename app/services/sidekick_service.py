import json
from typing import List, Dict, Any, cast
import openai
from app.core.config import settings
from app.schemas.sidekick_schema import SidekickInput, SidekickOutput
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.operations import (
    get_sidekick_context,
    update_or_create_sidekick_context,
    get_sidekick_thread,
    update_sidekick_thread,
    create_sidekick_thread,
)
from app.schemas.sidekick_schema import SidekickThreadCreate, SidekickContextCreate
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
            llm_response = await self.call_openai_api(prompt)
            processed_response = self.process_data(llm_response)

            final_history = updated_history + [
                {"role": "assistant", "content": json.dumps(llm_response)}
            ]
            await update_sidekick_thread(db, thread.id, final_history)

            context_updates: Dict[str, int] = {"tasks": 0, "people": 0, "knowledge": 0}
            if processed_response.get("data"):
                for context_type in ["tasks", "people", "knowledge"]:
                    new_data = processed_response["data"].get(context_type, [])
                    if new_data:
                        existing_context = await get_sidekick_context(
                            db, user_id, context_type
                        )
                        existing_data = (
                            existing_context.data if existing_context else []
                        )

                        updated_data = existing_data + new_data

                        await update_or_create_sidekick_context(
                            db,
                            SidekickContextCreate(
                                user_id=user_id,
                                context_type=context_type,
                                data=updated_data,
                            ),
                        )
                        context_updates[context_type] = len(new_data)

            instructions = processed_response["instructions"]
            is_thread_complete = instructions["status"] == "complete"
            new_thread_id = ""
            if is_thread_complete:
                new_thread = await create_sidekick_thread(
                    db, SidekickThreadCreate(user_id=user_id)
                )
                new_thread_id = new_thread.id

            return SidekickOutput(
                response=instructions["followup"],
                thread_id=new_thread_id if is_thread_complete else thread.id,
                status=instructions["status"],
                primary_type=instructions["primary_type"],
                new_prompt=instructions.get("new_prompt"),
                is_thread_complete=is_thread_complete,
                updated_entities=context_updates,
            )
        except Exception as e:
            logger.error(f"Error in process_input: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def construct_prompt(
        self, db: AsyncSession, user_id: str, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        try:
            context = {}
            for context_type in ["tasks", "people", "knowledge"]:
                context_data = await get_sidekick_context(db, user_id, context_type)
                if context_data:
                    context[context_type] = context_data.data

            messages = [
                {"role": "system", "content": settings.SIDEKICK_SYSTEM_PROMPT},
                {"role": "user", "content": f"Current context: {json.dumps(context)}"},
            ]

            messages.extend(conversation_history)
            return messages
        except Exception as e:
            logger.error(f"Error in construct_prompt: {str(e)}")
            raise

    async def call_openai_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini-2024-07-18",
                messages=messages,
            )
            raw_response = response.choices[0].message.content
            logger.info(f"Raw OpenAI API response: {raw_response}")

            api_response = json.loads(raw_response)
            return cast(Dict[str, Any], api_response)
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

    def process_data(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        if "instructions" not in llm_response or "data" not in llm_response:
            raise ValueError("Invalid LLM response structure")

        instructions = llm_response["instructions"]
        required_instruction_fields = ["status", "followup", "primary_type"]
        for field in required_instruction_fields:
            if field not in instructions:
                raise ValueError(f"Invalid LLM response structure: missing {field}")

        data = llm_response["data"]
        for context_type in ["tasks", "people", "knowledge"]:
            if context_type in data and not isinstance(data[context_type], list):
                data[context_type] = []

        return llm_response
