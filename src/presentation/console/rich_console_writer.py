"""Rich Console implementation of ConsoleWriter."""

from collections.abc import Callable
from typing import Any

from rich.console import Console

from domain.entities.task import Task
from presentation.console.console_writer import ConsoleWriter

# Message icons
ICON_SUCCESS = "✓"
ICON_ERROR = "✗"
ICON_WARNING = "⚠"
ICON_INFO = "ℹ"  # noqa: RUF001

# Message styles (colors)
STYLE_SUCCESS = "green"
STYLE_ERROR = "red"
STYLE_WARNING = "yellow"
STYLE_INFO = "cyan"


class RichConsoleWriter(ConsoleWriter):
    """Rich Console implementation of ConsoleWriter.

    This class wraps Rich Console and provides a unified interface for
    console output across the application.
    """

    def __init__(self, console: Console):
        """Initialize RichConsoleWriter.

        Args:
            console: Rich Console instance
        """
        self._console = console

    def print_success(self, action: str, task: Task) -> None:
        """Print success message with task info.

        Args:
            action: Action verb (e.g., "Added", "Started", "Completed", "Updated")
            task: Task object
        """
        self._console.print(
            f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] {action} task: "
            f"[bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan])"
        )

    def print_error(self, action: str, error: Exception) -> None:
        """Print general error message.

        Args:
            action: Action being performed (e.g., "adding task", "starting task")
            error: Exception object
        """
        self._console.print(
            f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error {action}: {error}",
            style="red",
        )

    def print_validation_error(self, message: str) -> None:
        """Print validation error message.

        Args:
            message: Error message to display
        """
        self._console.print(
            f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error: {message}"
        )

    def print_warning(self, message: str) -> None:
        """Print warning message.

        Args:
            message: Warning message to display
        """
        self._console.print(
            f"[{STYLE_WARNING}]{ICON_WARNING}[/{STYLE_WARNING}] {message}"
        )

    def print_info(self, message: str) -> None:
        """Print informational message.

        Args:
            message: Information message to display
        """
        self._console.print(f"[{STYLE_INFO}]{ICON_INFO}[/{STYLE_INFO}] {message}")

    def print_task_not_found_error(self, task_id: int, is_parent: bool = False) -> None:
        """Print task not found error.

        Args:
            task_id: ID of the task that was not found
            is_parent: Whether this is a parent task error
        """
        prefix = "Parent task" if is_parent else "Task"
        self._console.print(
            f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error: {prefix} {task_id} not found",
            style="red",
        )

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
        formatted_value = format_func(value) if format_func else str(value)
        self._console.print(
            f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] Set {field_name} for "
            f"[bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]): "
            f"[magenta]{formatted_value}[/magenta]"
        )

    def print(self, message: Any = "", **kwargs) -> None:
        """Print raw message.

        This method is used by formatters that need direct access to printing.
        Supports Rich objects like Table, Panel, etc.

        Args:
            message: Message to print (str or Rich renderable)
            **kwargs: Additional formatting options passed to Rich Console
        """
        self._console.print(message, **kwargs)

    def print_empty_line(self) -> None:
        """Print an empty line."""
        self._console.print()

    def get_width(self) -> int:
        """Get console width.

        Returns:
            Console width in characters
        """
        return self._console.width
