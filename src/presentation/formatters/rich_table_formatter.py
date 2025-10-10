from typing import List
from rich.table import Table
from rich.console import Console
from domain.entities.task import Task
from presentation.formatters.rich_formatter_base import RichFormatterBase


class RichTableFormatter(RichFormatterBase):
    """Formats tasks as a table using Rich."""

    def format_tasks(self, tasks: List[Task], repository) -> str:
        """Format tasks into a table with Rich.

        Args:
            tasks: List of all tasks
            repository: Repository instance (not used for table format)

        Returns:
            Formatted string with table structure
        """
        if not tasks:
            return "No tasks found."

        # Create Rich table
        table = Table(
            title="[bold cyan]Tasks[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_blue",
        )

        # Add columns
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Priority", justify="center", style="yellow", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Parent", justify="center", style="dim", no_wrap=True)
        table.add_column("Plan Start", style="green", no_wrap=True)
        table.add_column("Plan End", style="green", no_wrap=True)
        table.add_column("Actual Start", style="blue", no_wrap=True)
        table.add_column("Actual End", style="blue", no_wrap=True)
        table.add_column("Deadline", style="magenta", no_wrap=True)
        table.add_column("Duration", justify="right", style="cyan", no_wrap=True)

        # Add rows
        for task in tasks:
            parent_str = str(task.parent_id) if task.parent_id else "-"

            # Status with color
            status_style = self._get_status_style(task.status)

            # Planned times
            planned_start_str = self._format_datetime(task.planned_start)
            planned_end_str = self._format_datetime(task.planned_end)

            # Actual times
            actual_start_str = self._format_datetime(task.actual_start)
            actual_end_str = self._format_datetime(task.actual_end)

            # Deadline
            deadline_str = self._format_datetime(task.deadline)

            # Duration info
            duration_str = self._format_duration_info(task)

            table.add_row(
                str(task.id),
                task.name,
                str(task.priority),
                f"[{status_style}]{task.status.value}[/{status_style}]",
                parent_str,
                planned_start_str,
                planned_end_str,
                actual_start_str,
                actual_end_str,
                deadline_str,
                duration_str,
            )

        # Render to string
        from io import StringIO

        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        console.print(table)
        return string_io.getvalue().rstrip()

    def _format_datetime(self, datetime_str: str) -> str:
        """Format datetime string for display.

        Args:
            datetime_str: Datetime string or None

        Returns:
            Formatted datetime string or "-"
        """
        if not datetime_str:
            return "-"
        # Show only date and time (YYYY-MM-DD HH:MM)
        # Remove seconds to save space
        if len(datetime_str) >= 16:
            return datetime_str[:16]
        return datetime_str

    def _format_duration_info(self, task: Task) -> str:
        """Format duration information for a task.

        Args:
            task: The task to format

        Returns:
            Formatted duration string
        """
        if not task.estimated_duration and not task.actual_duration_hours:
            return "-"

        duration_parts = []

        if task.estimated_duration:
            duration_parts.append(f"E:{task.estimated_duration}h")

        if task.actual_duration_hours:
            duration_parts.append(f"A:{task.actual_duration_hours}h")

        return " / ".join(duration_parts)
