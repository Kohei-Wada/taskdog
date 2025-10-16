"""Abstract interface for console output."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from domain.entities.task import Task


class ConsoleWriter(ABC):
    """Abstract interface for console output.

    This interface abstracts away the specific console implementation (e.g., Rich)
    to improve testability and maintainability.
    """

    @abstractmethod
    def print_success(self, action: str, task: Task) -> None:
        """Print success message with task info.

        Args:
            action: Action verb (e.g., "Added", "Started", "Completed", "Updated")
            task: Task object
        """
        pass

    @abstractmethod
    def print_error(self, action: str, error: Exception) -> None:
        """Print general error message.

        Args:
            action: Action being performed (e.g., "adding task", "starting task")
            error: Exception object
        """
        pass

    @abstractmethod
    def print_validation_error(self, message: str) -> None:
        """Print validation error message.

        Args:
            message: Error message to display
        """
        pass

    @abstractmethod
    def print_warning(self, message: str) -> None:
        """Print warning message.

        Args:
            message: Warning message to display
        """
        pass

    @abstractmethod
    def print_info(self, message: str) -> None:
        """Print informational message.

        Args:
            message: Information message to display
        """
        pass

    @abstractmethod
    def print_task_not_found_error(self, task_id: int, is_parent: bool = False) -> None:
        """Print task not found error.

        Args:
            task_id: ID of the task that was not found
            is_parent: Whether this is a parent task error
        """
        pass

    @abstractmethod
    def print_update_success(
        self,
        task: Task,
        field_name: str,
        value: Any,
        format_func: Callable[[Any], str] | None = None,
    ) -> None:
        """Print standardized update success message.

        Args:
            task: Task that was updated
            field_name: Name of the field that was updated
            value: New value of the field
            format_func: Optional function to format the value for display
        """
        pass

    @abstractmethod
    def print(self, message: Any = "", **kwargs) -> None:
        """Print raw message.

        This method is used by formatters that need direct access to printing.
        Supports Rich objects like Table, Panel, etc.

        Args:
            message: Message to print (str or Rich renderable)
            **kwargs: Additional formatting options (implementation-specific)
        """
        pass

    @abstractmethod
    def print_empty_line(self) -> None:
        """Print an empty line."""
        pass

    @abstractmethod
    def get_width(self) -> int:
        """Get console width.

        Returns:
            Console width in characters
        """
        pass
