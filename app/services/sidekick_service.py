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


class SidekickService:
    def __init__(self) -> None:
        openai.api_key = settings.OPENAI_API_KEY

    async def process_input(
        self, db: AsyncSession, user_id: str, sidekick_input: SidekickInput
    ) -> SidekickOutput:
        # Get or create thread
        thread = (
            await get_sidekick_thread(db, sidekick_input.thread_id)
            if sidekick_input.thread_id
            else await create_sidekick_thread(db, SidekickThreadCreate(user_id=user_id))
        )

        thread = cast(
            SidekickThread, thread
        )  # Add this line to cast thread to SidekickThread

        # Construct prompt
        prompt = await self.construct_prompt(db, user_id, thread.conversation_history)

        # Call OpenAI API
        llm_response = await self.call_openai_api(prompt)

        # Process the response
        processed_response = self.process_data(llm_response)

        # Update thread
        updated_history = thread.conversation_history + [
            {"role": "user", "content": sidekick_input.user_input},
            {"role": "assistant", "content": json.dumps(llm_response)},
        ]
        await update_sidekick_thread(db, thread.id, updated_history)

        # Update context if necessary
        context_updates: Dict[str, List[Dict[str, Any]]] = {}
        if processed_response.get("data"):
            for context_type, data in processed_response["data"].items():
                context = await update_or_create_sidekick_context(
                    db,
                    SidekickContextCreate(
                        user_id=user_id, context_type=context_type, data=data
                    ),
                )
                context_updates[context_type] = [context.data]

        return SidekickOutput(
            response=processed_response["instructions"]["followup"],
            thread_id=thread.id,
            context_updates=context_updates if context_updates else None,
        )

    async def construct_prompt(
        self, db: AsyncSession, user_id: str, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
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

        messages.extend(conversation_history)

        return messages

    async def call_openai_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini-2024-07-18",  # Use the appropriate model
                messages=messages,
            )
            return cast(Dict[str, Any], json.loads(response.choices[0].message.content))
        except openai.error.OpenAIError as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, detail="Unable to parse OpenAI response as JSON"
            )

    def process_data(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        # Process the LLM response
        # This method can be expanded based on specific requirements
        return llm_response
