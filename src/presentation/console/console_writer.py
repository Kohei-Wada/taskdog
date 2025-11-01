"""Abstract interface for console output."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from application.dto.task_operation_output import TaskOperationOutput


class ConsoleWriter(ABC):
    """Abstract interface for console output.

    This interface abstracts away the specific console implementation (e.g., Rich)
    to improve testability and maintainability.
    """

    @abstractmethod
    def task_success(self, action: str, output: TaskOperationOutput) -> None:
        """Print success message with task info.

        Args:
            action: Action verb (e.g., "Added", "Started", "Completed", "Updated")
            output: Task operation output DTO
        """
        pass

    @abstractmethod
    def error(self, action: str, error: Exception) -> None:
        """Print general error message.

        Args:
            action: Action being performed (e.g., "adding task", "starting task")
            error: Exception object
        """
        pass

    @abstractmethod
    def validation_error(self, message: str) -> None:
        """Print validation error message.

        Args:
            message: Error message to display
        """
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """Print warning message.

        Args:
            message: Warning message to display
        """
        pass

    @abstractmethod
    def info(self, message: str) -> None:
        """Print informational message.

        Args:
            message: Information message to display
        """
        pass

    @abstractmethod
    def success(self, message: str) -> None:
        """Print generic success message.

        Args:
            message: Success message to display
        """
        pass

    @abstractmethod
    def update_success(
        self,
        output: TaskOperationOutput,
        field_name: str,
        value: Any,
        format_func: Callable[[Any], str] | None = None,
    ) -> None:
        """Print standardized update success message.

        Args:
            output: Task operation output of the updated task
            field_name: Name of the field that was updated
            value: New value of the field
            format_func: Optional function to format the value for display
        """
        pass

    @abstractmethod
    def print(self, message: Any = "", **kwargs: Any) -> None:
        """Print raw message.

        This method is used by formatters that need direct access to printing.
        Supports Rich objects like Table, Panel, etc.

        Args:
            message: Message to print (str or Rich renderable)
            **kwargs: Additional formatting options (implementation-specific)
        """
        pass

    @abstractmethod
    def empty_line(self) -> None:
        """Print an empty line."""
        pass

    @abstractmethod
    def get_width(self) -> int:
        """Get console width.

        Returns:
            Console width in characters
        """
        pass

    @abstractmethod
    def task_start_time(self, output: TaskOperationOutput, was_already_in_progress: bool) -> None:
        """Print task start time information.

        Args:
            output: Task operation output DTO
            was_already_in_progress: Whether the task was already in progress
        """
        pass

    @abstractmethod
    def task_completion_details(self, output: TaskOperationOutput) -> None:
        """Print task completion details (time, duration, comparison with estimate).

        This consolidates print_task_completion_time, print_task_duration,
        and print_duration_comparison into a single method.

        Args:
            output: Completed task output DTO
        """
        pass

    @abstractmethod
    def task_fields_updated(self, output: TaskOperationOutput, updated_fields: list[str]) -> None:
        """Print task fields update success message.

        Args:
            output: Task operation output of the updated task
            updated_fields: List of field names that were updated
        """
        pass
