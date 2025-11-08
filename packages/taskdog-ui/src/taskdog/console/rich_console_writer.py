"""Rich Console implementation of ConsoleWriter."""

from collections.abc import Callable
from typing import Any

from rich.console import Console

from taskdog.console.console_writer import ConsoleWriter
from taskdog.constants.colors import (
    STYLE_ERROR,
    STYLE_INFO,
    STYLE_SUCCESS,
    STYLE_WARNING,
)
from taskdog.constants.icons import ICON_ERROR, ICON_INFO, ICON_SUCCESS, ICON_WARNING
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


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

    def task_success(self, action: str, output: TaskOperationOutput) -> None:
        """Print success message with task info.

        Args:
            action: Action verb (e.g., "Added", "Started", "Completed", "Updated")
            output: Task operation output DTO
        """
        self._console.print(
            f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] {action} task: "
            f"[bold]{output.name}[/bold] (ID: [cyan]{output.id}[/cyan])"
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
        self._console.print(
            f"[{STYLE_ERROR}]{ICON_ERROR}[/{STYLE_ERROR}] Error: {message}"
        )

    def warning(self, message: str) -> None:
        """Print warning message.

        Args:
            message: Warning message to display
        """
        self._console.print(
            f"[{STYLE_WARNING}]{ICON_WARNING}[/{STYLE_WARNING}] {message}"
        )

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
        self._console.print(
            f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] {message}"
        )

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
        formatted_value = format_func(value) if format_func else str(value)
        self._console.print(
            f"[{STYLE_SUCCESS}]{ICON_SUCCESS}[/{STYLE_SUCCESS}] Set {field_name} for "
            f"[bold]{output.name}[/bold] (ID: [cyan]{output.id}[/cyan]): "
            f"[magenta]{formatted_value}[/magenta]"
        )

    def print(self, message: Any = "", **kwargs: Any) -> None:
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

    def task_start_time(
        self, output: TaskOperationOutput, was_already_in_progress: bool
    ) -> None:
        """Print task start time information.

        Args:
            output: Task operation output DTO
            was_already_in_progress: Whether the task was already in progress
        """
        if was_already_in_progress:
            self._console.print(
                f"  [yellow]⚠[/yellow] Task was already IN_PROGRESS (started at [blue]{
                    output.actual_start
                }[/blue])"
            )
        elif output.actual_start:
            self._console.print(f"  Started at: [blue]{output.actual_start}[/blue]")

    def task_completion_details(self, output: TaskOperationOutput) -> None:
        """Print task completion details (time, duration, comparison with estimate).

        This consolidates print_task_completion_time, print_task_duration,
        and print_duration_comparison into a single method.

        Args:
            output: Completed task output DTO
        """
        # Show completion time if available
        if output.actual_end:
            self._console.print(f"  Completed at: [blue]{output.actual_end}[/blue]")

        # Show duration if available
        if output.actual_duration_hours:
            self._console.print(
                f"  Duration: [cyan]{output.actual_duration_hours}h[/cyan]"
            )

        # Show comparison with estimate if both available
        if output.actual_duration_hours and output.estimated_duration:
            actual_hours = output.actual_duration_hours
            estimated_hours = output.estimated_duration
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

    def task_fields_updated(
        self, output: TaskOperationOutput, updated_fields: list[str]
    ) -> None:
        """Print task fields update success message.

        Args:
            output: Task operation output of the updated task
            updated_fields: List of field names that were updated
        """
        self._console.print(
            f"[green]✓[/green] Updated task [bold]{output.name}[/bold] (ID: [cyan]{output.id}[/cyan]):"
        )
        for field in updated_fields:
            value = getattr(output, field)
            if field == "estimated_duration":
                self._console.print(f"  • {field}: [cyan]{value}h[/cyan]")
            else:
                self._console.print(f"  • {field}: [cyan]{value}[/cyan]")
