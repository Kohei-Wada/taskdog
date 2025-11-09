"""Base validation classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether the validation passed
        error_message: Error message if validation failed (empty if valid)
        value: The validated/parsed value (None if validation failed)
    """

    is_valid: bool
    error_message: str = ""
    value: object = None


class BaseValidator(ABC):
    """Base class for all validators.

    This provides a common interface and helper methods for validation.
    """

    @staticmethod
    @abstractmethod
    def validate(*args: Any, **kwargs: Any) -> ValidationResult:
        """Validate the input value.

        Args:
            *args: Positional arguments for validation
            **kwargs: Keyword arguments for validation

        Returns:
            ValidationResult with validation status and error message
        """
        pass

    @staticmethod
    def _success(value: Any) -> ValidationResult:
        """Create a successful validation result.

        Args:
            value: The validated value

        Returns:
            ValidationResult indicating success
        """
        return ValidationResult(is_valid=True, error_message="", value=value)

    @staticmethod
    def _error(message: str) -> ValidationResult:
        """Create a failed validation result.

        Args:
            message: Error message

        Returns:
            ValidationResult indicating failure
        """
        return ValidationResult(is_valid=False, error_message=message, value=None)
