from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.operations import get_sidekick_thread
from app.schemas.sidekick_schema import SidekickInput, SidekickOutput
from app.services.sidekick_service import SidekickService
from app.dependencies import get_current_user
from utils.database import get_db
from app.schemas.user_schema import UserInfo
from app.core.rate_limit import limiter
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/sidekick", response_model=SidekickOutput, tags=["sidekick"])
@limiter.limit(settings.rate_limits["default"])
async def process_sidekick_input(
    request: Request,
    sidekick_input: SidekickInput,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SidekickOutput:
    try:
        # Validate thread_id if provided
        if sidekick_input.thread_id:
            thread = await get_sidekick_thread(db, sidekick_input.thread_id)
            if not thread or thread.user_id != current_user.id:
                raise HTTPException(status_code=404, detail="Thread not found")

        sidekick_service = SidekickService()

        # Process the input using the updated SidekickService
        result = await sidekick_service.process_input(
            db, current_user.id, sidekick_input
        )

        # Log the successful processing
        logger.info(f"Processed sidekick input for user {current_user.id}")

        return result

    except HTTPException as http_ex:
        logger.error(
            f"HTTP exception processing sidekick input for user {current_user.id}: {http_ex.detail}"
        )
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log any unexpected errors
        logger.error(
            f"Error processing sidekick input for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
