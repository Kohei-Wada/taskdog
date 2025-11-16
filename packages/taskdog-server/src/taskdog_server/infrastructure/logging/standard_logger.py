"""Standard logging implementation using Python's logging module."""

import logging
from typing import Any


class StandardLogger:
    """Logger implementation using Python's standard logging module.

    This adapter implements the Logger protocol from taskdog_core.domain.services.logger,
    allowing the core package to log messages without depending on the logging library.
    """

    def __init__(self, name: str):
        """Initialize the logger with a specific name.

        Args:
            name: Logger name (typically __name__ of the module using it)
        """
        self._logger = logging.getLogger(name)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: The message to log
            **kwargs: Additional context information
        """
        extra = {"context": kwargs} if kwargs else {}
        self._logger.debug(message, extra=extra)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: The message to log
            **kwargs: Additional context information
        """
        extra = {"context": kwargs} if kwargs else {}
        self._logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: The message to log
            **kwargs: Additional context information
        """
        extra = {"context": kwargs} if kwargs else {}
        self._logger.warning(message, extra=extra)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: The message to log
            **kwargs: Additional context information
        """
        extra = {"context": kwargs} if kwargs else {}
        self._logger.error(message, extra=extra)
