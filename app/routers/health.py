from fastapi import APIRouter, HTTPException, Depends, Request
import logging
from app.core.config import settings
from app.schemas.health_schema import HealthResponse
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from sqlalchemy import text
from app.core.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
@limiter.limit(settings.rate_limits["default"])
async def health_check(
    request: Request, db: AsyncSession = Depends(get_db)
) -> HealthResponse:
    """
    Comprehensive health check endpoint to verify the API and its dependencies are running.
    """
    logger.info("Health check endpoint was called.")

    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "error"

    # You can add more checks here, e.g., Redis connection, external services, etc.

    overall_status = "ok" if db_status == "ok" else "error"

    response = HealthResponse(
        status=overall_status, version=settings.APP_VERSION, database_status=db_status
    )

    if overall_status == "error":
        logger.error(f"Health check failed: {response.model_dump()}")
        raise HTTPException(status_code=503, detail="Service Unavailable")

    logger.info(f"Health check passed: {response.model_dump()}")
    return response
