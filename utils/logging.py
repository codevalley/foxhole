import logging
from logging.handlers import RotatingFileHandler
import os
from app.core.config import settings

def setup_logging():
    """
    Set up logging configuration for the application.
    """
    # Create logs directory if it doesn't exist and a log file is specified
    if settings.LOG_FILE:
        log_dir = os.path.dirname(settings.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)

    # Create handlers
    console_handler = logging.StreamHandler()
    handlers = [console_handler]

    if settings.LOG_FILE:
        file_handler = RotatingFileHandler(settings.LOG_FILE, maxBytes=10485760, backupCount=5)
        handlers.append(file_handler)

    # Create formatters
    console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Set formatters for handlers
    console_handler.setFormatter(console_format)
    if settings.LOG_FILE:
        file_handler.setFormatter(file_format)

    # Add handlers to the logger
    for handler in handlers:
        logger.addHandler(handler)

def get_logger(name):
    """
    Get a logger with the specified name.
    """
    return logging.getLogger(name)