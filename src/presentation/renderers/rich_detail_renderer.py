"""Rich formatter for task detail view."""

from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from application.dto.task_detail_dto import TaskDetailDTO
from presentation.console.console_writer import ConsoleWriter
from presentation.constants.colors import STATUS_STYLES
from presentation.constants.table_styles import (
    COLUMN_FIELD_LABEL_STYLE,
    PANEL_BORDER_STYLE_PRIMARY,
    PANEL_BORDER_STYLE_SECONDARY,
    TABLE_PADDING,
    format_table_title,
)


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

    def format_task_info(self, task) -> Table:
        """Format task basic information as a Rich table.

        Args:
            task: Task entity to format

        Returns:
            Rich Table with task information
        """
        table = Table(show_header=False, box=None, padding=TABLE_PADDING)
        table.add_column("Field", style=COLUMN_FIELD_LABEL_STYLE, no_wrap=True)
        table.add_column("Value")

        # Basic info
        table.add_row("ID", str(task.id))
        table.add_row("Name", task.name)
        table.add_row("Priority", str(task.priority))

        # Status with color
        status_style = STATUS_STYLES.get(task.status, "white")
        table.add_row("Status", f"[{status_style}]{task.status.value}[/{status_style}]")

        # Timestamps
        table.add_row("Created", task.created_at_str)

        # Time management fields
        if task.planned_start:
            table.add_row("Planned Start", task.planned_start)
        if task.planned_end:
            table.add_row("Planned End", task.planned_end)
        if task.deadline:
            table.add_row("Deadline", task.deadline)
        if task.actual_start:
            table.add_row("Actual Start", task.actual_start)
        if task.actual_end:
            table.add_row("Actual End", task.actual_end)
        if task.estimated_duration:
            table.add_row("Estimated Duration", f"{task.estimated_duration}h")
        if task.actual_duration_hours:
            table.add_row("Actual Duration", f"{task.actual_duration_hours}h")

        return table

    def render(self, dto: TaskDetailDTO, raw: bool = False) -> None:
        """Render and display task detail.

        Args:
            dto: Task detail DTO containing task and notes
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
