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

    def print_task_start_time(self, task: Task, was_already_in_progress: bool) -> None:
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

    def print_cannot_start_finished_task_error(self, task_id: int, status: str) -> None:
        """Print error when trying to start a finished task.

        Args:
            task_id: ID of the task
            status: Current status of the task
        """
        self._console.print(f"[red]✗[/red] Cannot start task {task_id}")
        self._console.print(f"  [yellow]⚠[/yellow] Task is already {status}")
        self._console.print("  [dim]Finished tasks cannot be restarted.[/dim]")

    def print_task_completion_time(self, task: Task) -> None:
        """Print task completion time.

        Args:
            task: Completed task
        """
        if task.actual_end:
            self._console.print(f"  Completed at: [blue]{task.actual_end}[/blue]")

    def print_task_duration(self, task: Task) -> None:
        """Print task duration.

        Args:
            task: Completed task with duration information
        """
        if task.actual_duration_hours:
            self._console.print(f"  Duration: [cyan]{task.actual_duration_hours}h[/cyan]")

    def print_duration_comparison(self, actual_hours: float, estimated_hours: float) -> None:
        """Print comparison between actual and estimated duration.

        Args:
            actual_hours: Actual duration in hours
            estimated_hours: Estimated duration in hours
        """
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

    def print_cannot_complete_finished_task_error(
        self, task_id: int, status: str
    ) -> None:
        """Print error when trying to complete an already finished task.

        Args:
            task_id: ID of the task
            status: Current status of the task
        """
        self._console.print(f"[red]✗[/red] Cannot complete task {task_id}")
        self._console.print(f"  [yellow]⚠[/yellow] Task is already {status}")
        self._console.print("  [dim]Task has already been completed.[/dim]")

    def print_cannot_complete_pending_task_error(self, task_id: int) -> None:
        """Print error when trying to complete a pending task.

        Args:
            task_id: ID of the task
        """
        self._console.print(f"[red]✗[/red] Cannot complete task {task_id}")
        self._console.print(
            f"  [yellow]⚠[/yellow] Task is still PENDING. Start the task first with [blue]taskdog start {
                task_id
            }[/blue]"
        )

    def print_schedule_updated(
        self, task: Task, start: str | None, end: str | None
    ) -> None:
        """Print schedule update success message.

        Args:
            task: Task whose schedule was updated
            start: New start datetime string
            end: New end datetime string
        """
        self._console.print(
            f"[green]✓[/green] Set schedule for [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]):"
        )
        if start:
            self._console.print(f"  Start: [green]{start}[/green]")
        if end:
            self._console.print(f"  End: [green]{end}[/green]")

    def print_no_fields_to_update_warning(self) -> None:
        """Print warning when no fields were specified for update."""
        self._console.print(
            "[yellow]No fields to update.[/yellow] Use --priority, --status, --planned-start, --planned-end, --deadline, or --estimated-duration"
        )

    def print_task_fields_updated(self, task: Task, updated_fields: list[str]) -> None:
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

    def print_notes_file_created(self, notes_path: Any) -> None:
        """Print notes file creation message.

        Args:
            notes_path: Path to the created notes file
        """
        self._console.print(f"[green]✓[/green] Created notes file: {notes_path}")

    def print_opening_editor(self, editor: str) -> None:
        """Print editor opening message.

        Args:
            editor: Name of the editor being opened
        """
        self._console.print(f"[blue]Opening {editor}...[/blue]")

    def print_notes_saved(self, task_id: int) -> None:
        """Print notes saved message.

        Args:
            task_id: ID of the task
        """
        self._console.print(f"[green]✓[/green] Notes saved for task #{task_id}")

    def print_task_removed(self, task_id: int) -> None:
        """Print task removed message.

        Args:
            task_id: ID of the removed task
        """
        self._console.print(f"[green]✓[/green] Removed task with ID: [cyan]{task_id}[/cyan]")

    def print_task_archived(self, task_id: int) -> None:
        """Print task archived message.

        Args:
            task_id: ID of the archived task
        """
        self._console.print(f"[green]✓[/green] Archived task with ID: [cyan]{task_id}[/cyan]")

    def print_optimization_result(self, task_count: int, is_dry_run: bool) -> None:
        """Print optimization result message.

        Args:
            task_count: Number of tasks optimized
            is_dry_run: Whether this was a dry run
        """
        if is_dry_run:
            self._console.print(
                f"[cyan]DRY RUN:[/cyan] Preview of {task_count} task(s) to be optimized\n"
            )
        else:
            self._console.print(f"[green]✓[/green] Optimized schedules for {task_count} task(s)\n")

    def print_optimization_heading(self) -> None:
        """Print optimization configuration heading."""
        self._console.print("\n[bold]Configuration:[/bold]")

    def print_export_success(self, task_count: int, output_path: str) -> None:
        """Print export success message.

        Args:
            task_count: Number of tasks exported
            output_path: Path where tasks were exported
        """
        self._console.print(f"[green]✓[/green] Exported {task_count} tasks to [cyan]{output_path}[/cyan]")
