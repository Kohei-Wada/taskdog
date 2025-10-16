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

    @abstractmethod
    def print_task_start_time(self, task: Task, was_already_in_progress: bool) -> None:
        """Print task start time information.

        Args:
            task: Task that was started
            was_already_in_progress: Whether the task was already in progress
        """
        pass

    @abstractmethod
    def print_cannot_start_finished_task_error(self, task_id: int, status: str) -> None:
        """Print error when trying to start a finished task.

        Args:
            task_id: ID of the task
            status: Current status of the task
        """
        pass

    @abstractmethod
    def print_task_completion_time(self, task: Task) -> None:
        """Print task completion time.

        Args:
            task: Completed task
        """
        pass

    @abstractmethod
    def print_task_duration(self, task: Task) -> None:
        """Print task duration.

        Args:
            task: Completed task with duration information
        """
        pass

    @abstractmethod
    def print_duration_comparison(self, actual_hours: float, estimated_hours: float) -> None:
        """Print comparison between actual and estimated duration.

        Args:
            actual_hours: Actual duration in hours
            estimated_hours: Estimated duration in hours
        """
        pass

    @abstractmethod
    def print_cannot_complete_finished_task_error(
        self, task_id: int, status: str
    ) -> None:
        """Print error when trying to complete an already finished task.

        Args:
            task_id: ID of the task
            status: Current status of the task
        """
        pass

    @abstractmethod
    def print_cannot_complete_pending_task_error(self, task_id: int) -> None:
        """Print error when trying to complete a pending task.

        Args:
            task_id: ID of the task
        """
        pass

    @abstractmethod
    def print_schedule_updated(
        self, task: Task, start: str | None, end: str | None
    ) -> None:
        """Print schedule update success message.

        Args:
            task: Task whose schedule was updated
            start: New start datetime string
            end: New end datetime string
        """
        pass

    @abstractmethod
    def print_no_fields_to_update_warning(self) -> None:
        """Print warning when no fields were specified for update."""
        pass

    @abstractmethod
    def print_task_fields_updated(self, task: Task, updated_fields: list[str]) -> None:
        """Print task fields update success message.

        Args:
            task: Updated task
            updated_fields: List of field names that were updated
        """
        pass

    @abstractmethod
    def print_notes_file_created(self, notes_path: Any) -> None:
        """Print notes file creation message.

        Args:
            notes_path: Path to the created notes file
        """
        pass

    @abstractmethod
    def print_opening_editor(self, editor: str) -> None:
        """Print editor opening message.

        Args:
            editor: Name of the editor being opened
        """
        pass

    @abstractmethod
    def print_notes_saved(self, task_id: int) -> None:
        """Print notes saved message.

        Args:
            task_id: ID of the task
        """
        pass

    @abstractmethod
    def print_task_removed(self, task_id: int) -> None:
        """Print task removed message.

        Args:
            task_id: ID of the removed task
        """
        pass

    @abstractmethod
    def print_task_archived(self, task_id: int) -> None:
        """Print task archived message.

        Args:
            task_id: ID of the archived task
        """
        pass

    @abstractmethod
    def print_optimization_result(self, task_count: int, is_dry_run: bool) -> None:
        """Print optimization result message.

        Args:
            task_count: Number of tasks optimized
            is_dry_run: Whether this was a dry run
        """
        pass

    @abstractmethod
    def print_optimization_heading(self) -> None:
        """Print optimization configuration heading."""
        pass

    @abstractmethod
    def print_export_success(self, task_count: int, output_path: str) -> None:
        """Print export success message.

        Args:
            task_count: Number of tasks exported
            output_path: Path where tasks were exported
        """
        pass
