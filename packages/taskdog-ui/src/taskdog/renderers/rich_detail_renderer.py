"""Rich formatter for task detail view."""

from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from taskdog.console.console_writer import ConsoleWriter
from taskdog.constants.colors import STATUS_STYLES
from taskdog.constants.table_styles import (
    COLUMN_FIELD_LABEL_STYLE,
    PANEL_BORDER_STYLE_PRIMARY,
    PANEL_BORDER_STYLE_SECONDARY,
    TABLE_PADDING,
    format_table_title,
)
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto


class RichDetailRenderer:
    """Renderer for displaying task details with Rich.

    Handles rendering of task information and notes in a formatted panel.
    """

    def __init__(self, console_writer: ConsoleWriter):
        """Initialize renderer.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer

    def _add_basic_info(self, table: Table, task: TaskDetailDto) -> None:
        """Add basic task information to table."""
        table.add_row("ID", str(task.id))
        table.add_row("Name", task.name)
        table.add_row("Priority", str(task.priority))

        # Status with color
        status_style = STATUS_STYLES.get(task.status.value, "white")
        table.add_row("Status", f"[{status_style}]{task.status.value}[/{status_style}]")

        # Fixed flag
        if task.is_fixed:
            table.add_row("Fixed", "[yellow]Yes (won't be rescheduled)[/yellow]")

        # Dependencies
        if task.depends_on:
            deps_str = ", ".join(str(dep_id) for dep_id in task.depends_on)
            table.add_row("Depends On", f"[cyan]{deps_str}[/cyan]")

    def _add_time_fields(self, table: Table, task: TaskDetailDto) -> None:
        """Add time-related fields to table."""
        table.add_row("Created", DateTimeFormatter.format_created(task.created_at))
        table.add_row("Updated", DateTimeFormatter.format_updated(task.updated_at))

        if task.planned_start:
            table.add_row(
                "Planned Start",
                DateTimeFormatter.format_datetime_full(task.planned_start),
            )
        if task.planned_end:
            table.add_row(
                "Planned End", DateTimeFormatter.format_datetime_full(task.planned_end)
            )
        if task.deadline:
            table.add_row(
                "Deadline", DateTimeFormatter.format_datetime_full(task.deadline)
            )
        if task.actual_start:
            table.add_row(
                "Actual Start",
                DateTimeFormatter.format_datetime_full(task.actual_start),
            )
        if task.actual_end:
            table.add_row(
                "Actual End", DateTimeFormatter.format_datetime_full(task.actual_end)
            )
        if task.estimated_duration:
            table.add_row("Estimated Duration", f"{task.estimated_duration}h")
        if task.actual_duration_hours:
            table.add_row("Actual Duration", f"{task.actual_duration_hours}h")

    def _add_logged_hours(self, table: Table, task: TaskDetailDto) -> None:
        """Add logged daily hours to table."""
        if task.actual_daily_hours:
            total_logged = sum(task.actual_daily_hours.values())
            table.add_row("Total Logged Hours", f"[green]{total_logged}h[/green]")
            # Show daily breakdown
            daily_str = ", ".join(
                f"{date_obj.isoformat()}: {hours}h"
                for date_obj, hours in sorted(task.actual_daily_hours.items())
            )
            table.add_row("Daily Hours", f"[dim]{daily_str}[/dim]")

    def format_task_info(self, task: TaskDetailDto) -> Table:
        """Format task basic information as a Rich table.

        Args:
            task: Task entity to format

        Returns:
            Rich Table with task information
        """
        table = Table(show_header=False, box=None, padding=TABLE_PADDING)
        table.add_column("Field", style=COLUMN_FIELD_LABEL_STYLE, no_wrap=True)
        table.add_column("Value")

        self._add_basic_info(table, task)
        self._add_time_fields(table, task)
        self._add_logged_hours(table, task)

        return table

    def render(self, dto: TaskDetailOutput, raw: bool = False) -> None:
        """Render and display task detail.

        Args:
            dto: Task detail result containing task and notes
            raw: Whether to show raw markdown (default: False)
        """
        task = dto.task

        # Calculate appropriate width (max 100, but fit to console if smaller)
        max_width = min(100, self.console_writer.get_width())

        # Display task basic info
        task_info = self.format_task_info(task)
        panel = Panel(
            task_info,
            title=format_table_title(f"Task #{task.id}"),
            border_style=PANEL_BORDER_STYLE_PRIMARY,
            width=max_width,
            expand=False,
        )
        self.console_writer.print(panel)
        self.console_writer.empty_line()

        # Display notes if they exist
        if dto.has_notes and dto.notes_content:
            if raw:
                # Show raw markdown
                self.console_writer.print(format_table_title("Notes (raw):"))
                self.console_writer.print(dto.notes_content)
            else:
                # Render markdown with Rich
                self.console_writer.print(format_table_title("Notes:"))
                markdown = Markdown(dto.notes_content)
                notes_panel = Panel(
                    markdown,
                    border_style=PANEL_BORDER_STYLE_SECONDARY,
                    width=max_width,
                    expand=False,
                )
                self.console_writer.print(notes_panel)
        else:
            self.console_writer.print(
                f"[yellow]No notes found. Use 'taskdog note {task.id}' to create notes.[/yellow]"
            )
