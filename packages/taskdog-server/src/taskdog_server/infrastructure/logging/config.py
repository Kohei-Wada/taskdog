"""Logging configuration for the Taskdog API server."""

import logging
import os
import sys
from typing import Literal

LogFormat = Literal["text", "json"]


def configure_logging(
    level: str | None = None,
    format_type: LogFormat | None = None,
) -> None:
    """Configure application-wide logging.

    This function sets up logging for the entire application, including
    the taskdog_core and taskdog_server packages. It respects environment
    variables for configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to env var LOG_LEVEL or INFO.
        format_type: Log format ("text" or "json"). Defaults to env var LOG_FORMAT or "text".

    Environment Variables:
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FORMAT: Logging format - "text" or "json" (default: text)
    """
    # Determine log level
    log_level_str = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Determine format type
    format_str = (format_type or os.getenv("LOG_FORMAT") or "text").lower()

    # Configure format
    if format_str == "json":
        # JSON format for production (parseable by log aggregation tools)
        # Python 3.12+ supports JSON serialization natively
        log_format = '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s","context":%(context)s}'
    else:
        # Text format for development (human-readable)
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any existing configuration
    )

    # Set log level for taskdog packages
    logging.getLogger("taskdog_core").setLevel(log_level)
    logging.getLogger("taskdog_server").setLevel(log_level)

    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.info(f"Logging configured: level={log_level_str}, format={format_str}")
