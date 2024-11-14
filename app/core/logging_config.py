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
    async def dispatch(self, request: Request, call_next: Any) -> Response | Any:
        # Generate unique request ID
        request_id = request.headers.get("X-Request-ID", "unknown")

        # Log request
        await self._log_request(request, request_id)

        # Process request and capture response
        response = await call_next(request)

        # Create a response copy to read the body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Create a new response with the same body
        new_response = Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

        # Log response with the captured body
        await self._log_response(new_response, response_body, request_id)

        return new_response

    def _mask_auth_header(self, headers: dict) -> dict:
        masked_headers = headers.copy()
        if "authorization" in masked_headers:
            auth_value = masked_headers["authorization"]
            if auth_value.lower().startswith("bearer "):
                masked_headers["authorization"] = "Bearer ********"
        return masked_headers

    async def _log_request(self, request: Request, request_id: str) -> None:
        logger = logging.getLogger("foxhole.api")

        # Get request body
        body = ""
        if request.method in ["POST", "PUT"]:
            try:
                body = await request.json()
            except Exception:
                body = "Could not parse request body"

        headers = self._mask_auth_header(dict(request.headers))

        log_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "type": "request",
            "method": request.method,
            "url": str(request.url),
            "headers": headers,
            "body": body,
        }

        formatted_log = (
            f"\n{'='*50} INCOMING REQUEST {'='*50}\n"  # noqa: E226
            f"{json.dumps(log_dict, indent=2)}\n"
            f"{'='*120}\n"  # noqa: E226
        )
        logger.info(formatted_log)

    async def _log_response(
        self, response: Response, raw_body: bytes, request_id: str
    ) -> None:
        logger = logging.getLogger("foxhole.api")

        # Try to parse response body
        try:
            body = json.loads(raw_body.decode())
        except Exception:
            body = raw_body.decode() if raw_body else "Empty body"

        log_dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "type": "response",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body,
        }

        formatted_log = (
            f"\n{'='*50} OUTGOING RESPONSE {'='*50}\n"  # noqa: E226
            f"{json.dumps(log_dict, indent=2)}\n"
            f"{'='*120}\n"  # noqa: E226
        )
        logger.info(formatted_log)


def setup_logging() -> None:
    # Create logs directory if it doesn't exist
    log_dir = "data/logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Set up the main logger
    logger = logging.getLogger("foxhole")
    logger.setLevel(settings.LOG_LEVEL)
    logger.propagate = False

    # Create formatters
    detailed_formatter = logging.Formatter(settings.LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.setFormatter(detailed_formatter)

    # File handler for general logs
    file_handler = RotatingFileHandler(
        "data/logs/foxhole.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # API specific handler
    api_handler = RotatingFileHandler(
        "data/logs/api.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(detailed_formatter)

    # Database specific handler
    db_handler = RotatingFileHandler(
        "data/logs/db.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    db_handler.setLevel(logging.DEBUG)
    db_handler.setFormatter(detailed_formatter)

    # Set up API logger
    api_logger = logging.getLogger("foxhole.api")
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = False
    api_logger.addHandler(api_handler)

    # Set up DB logger
    db_logger = logging.getLogger("foxhole.db")
    db_logger.setLevel(logging.DEBUG)
    db_logger.propagate = False
    db_logger.addHandler(db_handler)

    # Add handlers to main logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Set up SQLAlchemy logging
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.INFO)
    sqlalchemy_logger.addHandler(db_handler)

    # Set specific loggers to ERROR level only
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("fastapi").setLevel(logging.ERROR)

    # Clear any existing handlers from root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
