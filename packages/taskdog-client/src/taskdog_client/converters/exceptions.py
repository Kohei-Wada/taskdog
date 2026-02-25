"""Exception classes for converter errors."""

from typing import Any

from taskdog_core.domain.exceptions.task_exceptions import TaskError


class ConversionError(TaskError):
    """Error during API response to DTO conversion.

    This exception is raised when the converter encounters invalid or
    unexpected data in the API response that prevents proper DTO construction.
    It provides context about which field failed and what the problematic value was.

    Attributes:
        message: Description of the conversion error
        field: The field name that failed conversion (if applicable)
        value: The problematic value that caused the error (if applicable)
    """

    def __init__(
        self, message: str, field: str | None = None, value: Any | None = None
    ):
        """Initialize ConversionError with context.

        Args:
            message: Human-readable error description
            field: Optional field name that failed conversion
            value: Optional value that caused the error
        """
        self.field = field
        self.value = value
        super().__init__(message)
