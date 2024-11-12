import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import json
from typing import Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Generate unique request ID
        request_id = request.headers.get("X-Request-ID", "unknown")

        # Log request
        await self._log_request(request, request_id)

        # Process request and capture response
        response = await call_next(request)

        # Log response
        await self._log_response(response, request_id)

        return response

    async def _log_request(self, request: Request, request_id: str) -> None:
        logger = logging.getLogger("foxhole.api")

        # Get request body
        body = ""
        if request.method in ["POST", "PUT"]:
            try:
                body = await request.json()
            except Exception:
                body = "Could not parse request body"

        log_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "type": "request",
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "body": body,
        }

        logger.info(json.dumps(log_dict))

    async def _log_response(self, response: Response, request_id: str) -> None:
        logger = logging.getLogger("foxhole.api")

        log_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "type": "response",
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }

        # Try to parse response body if it exists
        try:
            body = json.loads(response.body.decode())
            log_dict["body"] = body
        except Exception:
            log_dict["body"] = "Could not parse response body"

        logger.info(json.dumps(log_dict))


def setup_logging() -> None:
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Set up the main logger
    logger = logging.getLogger("foxhole")
    logger.setLevel(settings.LOG_LEVEL)

    # Create formatters
    detailed_formatter = logging.Formatter(settings.LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.setFormatter(detailed_formatter)

    # File handler for general logs (10MB max size, 5 backup files)
    file_handler = RotatingFileHandler(
        "logs/foxhole.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # API specific handler
    api_handler = RotatingFileHandler(
        "logs/api.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(detailed_formatter)

    # Database specific handler
    db_handler = RotatingFileHandler(
        "logs/db.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    db_handler.setLevel(logging.DEBUG)
    db_handler.setFormatter(detailed_formatter)

    # Set up API logger
    api_logger = logging.getLogger("foxhole.api")
    api_logger.addHandler(api_handler)

    # Set up DB logger
    db_logger = logging.getLogger("foxhole.db")
    db_logger.addHandler(db_handler)

    # Add handlers to main logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Set up SQLAlchemy logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").addHandler(db_handler)

    # Set specific loggers to ERROR level only
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("fastapi").setLevel(logging.ERROR)

    # Clear any existing handlers from root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
