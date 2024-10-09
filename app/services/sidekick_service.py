import json
from typing import List, Dict, Any, cast
import openai
from app.core.config import settings
from app.schemas.sidekick_schema import SidekickInput, SidekickOutput
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.operations import (
    get_sidekick_thread,
    update_sidekick_thread,
    create_sidekick_thread,
    get_sidekick_context,
    update_or_create_sidekick_context,
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
            # Get or create thread
            thread = (
                await get_sidekick_thread(db, sidekick_input.thread_id)
                if sidekick_input.thread_id
                else await create_sidekick_thread(
                    db, SidekickThreadCreate(user_id=user_id)
                )
            )

            thread = cast(SidekickThread, thread)

            # Add the current user input to the conversation history
            updated_history = thread.conversation_history + [
                {"role": "user", "content": sidekick_input.user_input}
            ]

            # Construct prompt with the updated history
            prompt = await self.construct_prompt(db, user_id, updated_history)

            # Call OpenAI API
            llm_response = await self.call_openai_api(prompt)

            # Process the response
            processed_response = self.process_data(llm_response)

            # Update thread with both user input and assistant response
            final_history = updated_history + [
                {"role": "assistant", "content": json.dumps(llm_response)}  # noqa E231
            ]
            await update_sidekick_thread(db, thread.id, final_history)

            # Update context if necessary
            context_updates: Dict[str, List[Dict[str, Any]]] = {}
            if processed_response.get("data"):
                for context_type, data in processed_response["data"].items():
                    if isinstance(data, dict):
                        context = await update_or_create_sidekick_context(
                            db,
                            SidekickContextCreate(
                                user_id=user_id, context_type=context_type, data=data
                            ),
                        )
                        context_updates[context_type] = [context.data]
                    else:
                        logger.error(
                            f"Error: data for {context_type} is not a dictionary: {data}"
                        )

            return SidekickOutput(
                response=processed_response["instructions"]["followup"],
                thread_id=thread.id,
                context_updates=context_updates if context_updates else None,
            )
        except Exception as e:
            logger.error(f"Error in process_input: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def construct_prompt(
        self, db: AsyncSession, user_id: str, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        try:
            # Load current context
            context = {}
            for context_type in ["people", "tasks", "knowledge"]:
                context_data = await get_sidekick_context(db, user_id, context_type)
                if context_data:
                    context[context_type] = context_data.data

            # Construct messages for the LLM
            messages = [
                {"role": "system", "content": settings.SIDEKICK_SYSTEM_PROMPT},
                {"role": "user", "content": f"Current context: {json.dumps(context)}"},
            ]

            # Add the conversation history, which now includes the current user input
            messages.extend(conversation_history)

            logger.debug(f"Constructed prompt: {messages}")
            return messages
        except Exception as e:
            logger.error(f"Error in construct_prompt: {str(e)}")
            raise

    async def call_openai_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini-2024-07-18",  # Use the appropriate model
                messages=messages,
            )
            api_response = json.loads(response.choices[0].message.content)
            logger.debug(f"OpenAI API response: {api_response}")
            return cast(Dict[str, Any], api_response)
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"OpenAI API error: {str(e)}"
            )  # noqa E231
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Unable to parse OpenAI response as JSON"
            )
        except Exception as e:
            logger.error(f"Unexpected error in call_openai_api: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {str(e)}"
            )

    def process_data(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Raw LLM response: {llm_response}")

        if "data" in llm_response:
            for context_type, data in llm_response["data"].items():
                logger.debug(
                    f"Context type: {context_type}, Data type: {type(data)}, Data: {data}"
                )

        # Ensure the response has the expected structure
        if (
            "instructions" not in llm_response
            or "followup" not in llm_response["instructions"]
        ):
            logger.error("LLM response is missing required fields")
            raise ValueError("Invalid LLM response structure")

        # Ensure data is a dictionary if present
        if "data" in llm_response and not isinstance(llm_response["data"], dict):
            logger.error(
                f"LLM response 'data' is not a dictionary: {llm_response['data']}"
            )
            llm_response["data"] = {}  # Set to empty dict to prevent further errors

        return llm_response
