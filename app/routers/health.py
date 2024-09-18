from fastapi import APIRouter
from typing import Dict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Simple health check endpoint to verify the API is running.
    """
    logger.info("Health check endpoint was called.")
    return {"status": "ok"}
