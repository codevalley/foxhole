from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from app.schemas.error_schema import ErrorResponse, ErrorDetail  # Import ErrorResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.error(f"Validation error for request {request.url}: {exc}")
    error_details = [
        ErrorDetail(loc=error["loc"], msg=error["msg"], type=error["type"])
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(detail=error_details).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled error for request {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
