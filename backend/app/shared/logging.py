"""
Structured Logging Configuration
Provides centralized logging setup for the application
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Dict, Any
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "endpoint"):
            log_entry["endpoint"] = record.endpoint
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class SimpleFormatter(logging.Formatter):
    """Simple formatter for development"""

    def format(self, record: logging.LogRecord) -> str:
        return f"[{record.levelname}] {record.name}: {record.getMessage()}"


def setup_logging() -> None:
    """Setup application logging configuration"""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    environment = os.getenv("ENVIRONMENT", "production")

    # Use structured JSON logging in production, simple logging in development
    if environment == "development":
        formatter_class = SimpleFormatter
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        formatter_class = StructuredFormatter
        log_format = None

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": formatter_class,
                "format": log_format,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name"""
    return logging.getLogger(name)


def log_endpoint_call(logger: logging.Logger, endpoint: str, method: str, **kwargs):
    """Log API endpoint call"""
    logger.info(
        f"API call: {method} {endpoint}",
        extra={"endpoint": endpoint, "method": method, **kwargs},
    )


def log_auth_event(logger: logging.Logger, event: str, user_id: str = None, **kwargs):
    """Log authentication events"""
    extra = {"auth_event": event, **kwargs}
    if user_id:
        extra["user_id"] = user_id

    logger.info(f"Authentication event: {event}", extra=extra)


def log_database_operation(
    logger: logging.Logger, operation: str, table: str, **kwargs
):
    """Log database operations"""
    logger.info(
        f"Database operation: {operation} on {table}",
        extra={"db_operation": operation, "table": table, **kwargs},
    )


def log_error(logger: logging.Logger, error: Exception, context: str = None, **kwargs):
    """Log errors with context"""
    extra = {"error_type": type(error).__name__, **kwargs}
    if context:
        extra["context"] = context

    logger.error(f"Error: {str(error)}", extra=extra, exc_info=True)
