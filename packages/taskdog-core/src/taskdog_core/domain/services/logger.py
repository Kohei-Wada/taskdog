"""Logger protocol for dependency injection.

This module defines the Logger protocol that allows the domain and application
layers to log without depending on a specific logging implementation.
This follows the Dependency Inversion Principle of Clean Architecture.
"""

from typing import Any, Protocol


class Logger(Protocol):
    """Protocol for logging operations.

    This protocol allows controllers and use cases to log messages without
    depending on a specific logging library (e.g., Python's logging module).
    Implementations can provide different logging backends (console, file, etc.).
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: The message to log
            **kwargs: Additional context information (e.g., task_id=123)
        """
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: The message to log
            **kwargs: Additional context information (e.g., task_id=123)
        """
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: The message to log
            **kwargs: Additional context information (e.g., task_id=123)
        """
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: The message to log
            **kwargs: Additional context information (e.g., task_id=123)
        """
        ...
