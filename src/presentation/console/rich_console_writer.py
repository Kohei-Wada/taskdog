"""Rich Console implementation of ConsoleWriter."""

from collections.abc import Callable
from typing import Any

from rich.console import Console

from domain.entities.task import Task
from presentation.console.console_writer import ConsoleWriter
from presentation.constants.colors import STYLE_ERROR, STYLE_INFO, STYLE_SUCCESS, STYLE_WARNING
from presentation.constants.icons import ICON_ERROR, ICON_INFO, ICON_SUCCESS, ICON_WARNING


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

    def task_success(self, action: str, task: Task) -> None:
        """Print success message with task info.

        Args:
            action: Action verb (e.g., "Added", "Started", "Completed", "Updated")
            task: Task object
        """
        self._console.print(
            f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] {action} task: "
            f"[bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan])"
        )

    def error(self, action: str, error: Exception) -> None:
        """Print general error message.

        Args:
            action: Action being performed (e.g., "adding task", "starting task")
            error: Exception object
        """
        self._console.print(
            f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error {action}: {error}",
            style="red",
        )

    def validation_error(self, message: str) -> None:
        """Print validation error message.

        Args:
            message: Error message to display
        """
        self._console.print(f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error: {message}")

    def warning(self, message: str) -> None:
        """Print warning message.

        Args:
            message: Warning message to display
        """
        self._console.print(f"[{STYLE_WARNING}]{ICON_WARNING}[/{STYLE_WARNING}] {message}")

    def info(self, message: str) -> None:
        """Print informational message.

        Args:
            message: Information message to display
        """
        self._console.print(f"[{STYLE_INFO}]{ICON_INFO}[/{STYLE_INFO}] {message}")

    def success(self, message: str) -> None:
        """Print generic success message.

        Args:
            message: Success message to display
        """
        self._console.print(f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] {message}")

    def update_success(
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

    def empty_line(self) -> None:
        """Print an empty line."""
        self._console.print()

    def get_width(self) -> int:
        """Get console width.

        Returns:
            Console width in characters
        """
        return self._console.width

    def task_start_time(self, task: Task, was_already_in_progress: bool) -> None:
        """Print task start time information.

        Args:
            task: Task that was started
            was_already_in_progress: Whether the task was already in progress
        """
        if was_already_in_progress:
            self._console.print(
                f"  [yellow]⚠[/yellow] Task was already IN_PROGRESS (started at [blue]{
                    task.actual_start
                }[/blue])"
            )
        elif task.actual_start:
            self._console.print(f"  Started at: [blue]{task.actual_start}[/blue]")

    def task_completion_details(self, task: Task) -> None:
        """Print task completion details (time, duration, comparison with estimate).

        This consolidates print_task_completion_time, print_task_duration,
        and print_duration_comparison into a single method.

        Args:
            task: Completed task with actual_end and duration information
        """
        # Show completion time if available
        if task.actual_end:
            self._console.print(f"  Completed at: [blue]{task.actual_end}[/blue]")

        # Show duration if available
        if task.actual_duration_hours:
            self._console.print(f"  Duration: [cyan]{task.actual_duration_hours}h[/cyan]")

        # Show comparison with estimate if both available
        if task.actual_duration_hours and task.estimated_duration:
            actual_hours = task.actual_duration_hours
            estimated_hours = task.estimated_duration
            diff = actual_hours - estimated_hours
            if diff > 0:
                self._console.print(
                    f"  [yellow]⚠[/yellow] Took [yellow]{diff}h longer[/yellow] than estimated"
                )
            elif diff < 0:
                self._console.print(
                    f"  [green]✓[/green] Finished [green]{abs(diff)}h faster[/green] than estimated"
                )
            else:
                self._console.print("  [green]✓[/green] Finished exactly on estimate!")

    def task_fields_updated(self, task: Task, updated_fields: list[str]) -> None:
        """Print task fields update success message.

        Args:
            task: Updated task
            updated_fields: List of field names that were updated
        """
        self._console.print(
            f"[green]✓[/green] Updated task [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]):"
        )
        for field in updated_fields:
            value = getattr(task, field)
            if field == "estimated_duration":
                self._console.print(f"  • {field}: [cyan]{value}h[/cyan]")
            else:
                self._console.print(f"  • {field}: [cyan]{value}[/cyan]")
