import logging
from logging.handlers import RotatingFileHandler
import os
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration with console and file handlers.
    Suppresses verbose logs from specific libraries.
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    file_handler = RotatingFileHandler("logs/app.log", maxBytes=10485760, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Suppress overly verbose logs from libraries that use the root logger
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger
