"""Console message formatting utilities for taskdog commands."""

from collections.abc import Callable
from typing import Any

from domain.entities.task import Task

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


def print_success(console, action: str, task: Task) -> None:
    """Print success message with task info.

    Args:
        console: Rich Console instance
        action: Action verb (e.g., "Added", "Started", "Completed", "Updated")
        task: Task object
    """
    console.print(
        f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] {action} task: [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan])"
    )


def print_task_not_found_error(console, task_id: int, is_parent: bool = False) -> None:
    """Print task not found error.

    Args:
        console: Rich Console instance
        task_id: ID of the task that was not found
        is_parent: Whether this is a parent task error
    """
    prefix = "Parent task" if is_parent else "Task"
    console.print(
        f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error: {prefix} {task_id} not found",
        style="red",
    )


def print_error(console, action: str, error: Exception) -> None:
    """Print general error message.

    Args:
        console: Rich Console instance
        action: Action being performed (e.g., "adding task", "starting task")
        error: Exception object
    """
    console.print(
        f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error {action}: {error}", style="red"
    )


def print_update_success(
    console,
    task: Task,
    field_name: str,
    value: Any,
    format_func: Callable[[Any], str] | None = None,
) -> None:
    """Print standardized update success message.

    Args:
        console: Rich Console instance
        task: Task that was updated
        field_name: Name of the field that was updated
        value: New value of the field
        format_func: Optional function to format the value for display
    """
    formatted_value = format_func(value) if format_func else str(value)
    console.print(
        f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] Set {field_name} for [bold]{task.name}[/bold] "
        f"(ID: [cyan]{task.id}[/cyan]): [magenta]{formatted_value}[/magenta]"
    )


def print_info(console, message: str) -> None:
    """Print informational message.

    Args:
        console: Rich Console instance
        message: Information message to display
    """
    console.print(f"[{STYLE_INFO}]{ICON_INFO}[/{STYLE_INFO}] {message}")


def print_warning(console, message: str) -> None:
    """Print warning message.

    Args:
        console: Rich Console instance
        message: Warning message to display
    """
    console.print(f"[{STYLE_WARNING}]{ICON_WARNING}[/{STYLE_WARNING}] {message}")


def print_validation_error(console, message: str) -> None:
    """Print validation error message.

    Args:
        console: Rich Console instance
        message: Error message to display
    """
    console.print(f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error: {message}")
