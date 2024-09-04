from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Endpoint to check the health status of the application.
    Returns a simple JSON response indicating the status is OK.
    """
    return {"status": "ok"}