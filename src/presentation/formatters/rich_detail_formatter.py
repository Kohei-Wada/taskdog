"""Rich formatter for task detail view."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from application.dto.task_detail_dto import TaskDetailDTO
from presentation.formatters.constants import STATUS_STYLES


class RichDetailFormatter:
    """Formatter for displaying task details with Rich.

    Handles rendering of task information and notes in a formatted panel.
    """

    def __init__(self, console: Console):
        """Initialize formatter.

        Args:
            console: Rich Console instance for output
        """
        self.console = console

    def format_task_info(self, task) -> Table:
        """Format task basic information as a Rich table.

        Args:
            task: Task entity to format

        Returns:
            Rich Table with task information
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan", no_wrap=True)
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

    def format(self, dto: TaskDetailDTO, raw: bool = False) -> None:
        """Format and display task detail.

        Args:
            dto: Task detail DTO containing task and notes
            raw: Whether to show raw markdown (default: False)
        """
        task = dto.task

        # Calculate appropriate width (max 100, but fit to console if smaller)
        max_width = min(100, self.console.width)

        # Display task basic info
        task_info = self.format_task_info(task)
        panel = Panel(
            task_info,
            title=f"[bold cyan]Task #{task.id}[/bold cyan]",
            border_style="cyan",
            width=max_width,
            expand=False,
        )
        self.console.print(panel)
        self.console.print()

        # Display notes if they exist
        if dto.has_notes and dto.notes_content:
            if raw:
                # Show raw markdown
                self.console.print("[bold cyan]Notes (raw):[/bold cyan]")
                self.console.print(dto.notes_content)
            else:
                # Render markdown with Rich
                self.console.print("[bold cyan]Notes:[/bold cyan]")
                markdown = Markdown(dto.notes_content)
                notes_panel = Panel(
                    markdown,
                    border_style="dim",
                    width=max_width,
                    expand=False,
                )
                self.console.print(notes_panel)
        else:
            self.console.print(
                f"[yellow]No notes found. Use 'taskdog note {task.id}' to create notes.[/yellow]"
            )
