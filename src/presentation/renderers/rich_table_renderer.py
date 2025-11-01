from typing import ClassVar

from rich.table import Table

from domain.entities.task import Task
from domain.repositories.notes_repository import NotesRepository
from presentation.console.console_writer import ConsoleWriter
from presentation.constants.table_styles import (
    COLUMN_DATETIME_NO_WRAP,
    COLUMN_DATETIME_STYLE,
    COLUMN_DEADLINE_STYLE,
    COLUMN_DURATION_STYLE,
    COLUMN_ID_STYLE,
    COLUMN_NAME_STYLE,
    COLUMN_NOTE_JUSTIFY,
    COLUMN_PRIORITY_STYLE,
    COLUMN_STATUS_JUSTIFY,
    TABLE_BORDER_STYLE,
    TABLE_HEADER_STYLE,
    TABLE_PADDING,
    format_table_title,
)
from presentation.renderers.rich_renderer_base import RichRendererBase


class RichTableRenderer(RichRendererBase):
    """Renders tasks as a table using Rich."""

    # Field definitions: field_name -> column configuration
    FIELD_DEFINITIONS: ClassVar[dict[str, dict[str, str | bool]]] = {
        "id": {
            "header": "ID",
            "justify": "right",
            "style": COLUMN_ID_STYLE,
            "no_wrap": True,
        },
        "name": {
            "header": "Name",
            "style": COLUMN_NAME_STYLE,
        },
        "note": {
            "header": "Note",
            "justify": COLUMN_NOTE_JUSTIFY,
            "no_wrap": True,
        },
        "priority": {
            "header": "Priority",
            "justify": "center",
            "style": COLUMN_PRIORITY_STYLE,
            "no_wrap": True,
        },
        "status": {
            "header": "Status",
            "justify": COLUMN_STATUS_JUSTIFY,
        },
        "planned_start": {
            "header": "Plan Start",
            "style": COLUMN_DATETIME_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "planned_end": {
            "header": "Plan End",
            "style": COLUMN_DATETIME_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "actual_start": {
            "header": "Actual Start",
            "style": COLUMN_DATETIME_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "actual_end": {
            "header": "Actual End",
            "style": COLUMN_DATETIME_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "deadline": {
            "header": "Deadline",
            "style": COLUMN_DEADLINE_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "duration": {
            "header": "Duration",
            "justify": "right",
            "style": COLUMN_DURATION_STYLE,
            "no_wrap": True,
        },
        "estimated_duration": {
            "header": "Est",
            "justify": "center",
            "style": COLUMN_DURATION_STYLE,
            "no_wrap": True,
        },
        "actual_duration": {
            "header": "Actual",
            "justify": "center",
            "style": COLUMN_DURATION_STYLE,
            "no_wrap": True,
        },
        "elapsed": {
            "header": "Elapsed",
            "justify": "center",
            "style": "cyan",
            "no_wrap": True,
        },
        "created_at": {
            "header": "Created At",
            "style": "dim",
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "updated_at": {
            "header": "Updated At",
            "style": "dim",
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "depends_on": {
            "header": "Dependencies",
            "justify": "center",
            "style": "cyan",
            "no_wrap": True,
        },
        "is_fixed": {
            "header": "Fixed",
            "justify": "center",
            "style": "yellow",
            "no_wrap": True,
        },
        "tags": {
            "header": "Tags",
            "justify": "left",
            "style": "magenta",
            "no_wrap": False,
        },
    }

    # Default fields to display when none specified (matches TUI column order)
    DEFAULT_FIELDS: ClassVar[list[str]] = [
        "id",
        "name",
        "status",
        "priority",
        "note",
        "is_fixed",
        "estimated_duration",
        "actual_duration",
        "deadline",
        "planned_start",
        "planned_end",
        "actual_start",
        "actual_end",
        "elapsed",
        "depends_on",
        "tags",
    ]

    def __init__(self, console_writer: ConsoleWriter, notes_repository: NotesRepository):
        """Initialize the renderer.

        Args:
            console_writer: Console writer for output
            notes_repository: Notes repository for checking note existence
        """
        self.console_writer = console_writer
        self.notes_repository = notes_repository

    def render(self, tasks: list[Task], fields: list[str] | None = None) -> None:
        """Render and print tasks as a table with Rich.

        Args:
            tasks: List of all tasks
            fields: List of field names to display (None = all default fields)

        Raises:
            ValueError: If an invalid field name is provided
        """
        if not tasks:
            self.console_writer.warning("No tasks found.")
            return

        # Use default fields if none specified
        if fields is None:
            fields = self.DEFAULT_FIELDS

        # Validate field names
        invalid_fields = [f for f in fields if f not in self.FIELD_DEFINITIONS]
        if invalid_fields:
            valid_fields = ", ".join(self.FIELD_DEFINITIONS.keys())
            raise ValueError(
                f"Invalid field(s): {', '.join(invalid_fields)}. Valid fields are: {valid_fields}"
            )

        # Create Rich table
        table = Table(
            title=format_table_title("Tasks"),
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            padding=TABLE_PADDING,
        )

        # Add columns dynamically based on selected fields
        for field_name in fields:
            field_config = self.FIELD_DEFINITIONS[field_name]
            table.add_column(
                field_config["header"],
                justify=field_config.get("justify"),
                style=field_config.get("style"),
                no_wrap=field_config.get("no_wrap", False),
            )

        # Add rows
        for task in tasks:
            row_values = [self._get_field_value(task, field_name) for field_name in fields]
            table.add_row(*row_values)

        # Print table using console writer
        self.console_writer.print(table)

    def _get_field_value(self, task: Task, field_name: str) -> str:
        """Get the formatted value for a specific field.

        Args:
            task: Task to extract value from
            field_name: Name of the field

        Returns:
            Formatted string value for display
        """
        # Field value extractors mapping
        field_extractors = {
            "id": lambda t: str(t.id),
            "name": lambda t: f"[strike]{t.name}[/strike]" if t.is_finished else t.name,
            "note": lambda t: "📝" if self.notes_repository.has_notes(t.id) else "",
            "priority": lambda t: str(t.priority),
            "status": lambda t: self._format_status(t),
            "is_fixed": lambda t: "📌" if t.is_fixed else "",
            "depends_on": lambda t: self._format_dependencies(t),
            "tags": lambda t: self._format_tags(t),
            "planned_start": lambda t: self._format_datetime(t.planned_start),
            "planned_end": lambda t: self._format_datetime(t.planned_end),
            "actual_start": lambda t: self._format_datetime(t.actual_start),
            "actual_end": lambda t: self._format_datetime(t.actual_end),
            "deadline": lambda t: self._format_datetime(t.deadline),
            "duration": lambda t: self._format_duration_info(t),
            "estimated_duration": lambda t: self._format_estimated_duration(t),
            "actual_duration": lambda t: self._format_actual_duration(t),
            "elapsed": lambda t: self._format_elapsed(t),
            "created_at": lambda t: self._format_datetime(t.created_at),
            "updated_at": lambda t: self._format_datetime(t.updated_at),
        }

        extractor = field_extractors.get(field_name)
        return extractor(task) if extractor else "-"

    def _format_tags(self, task: Task) -> str:
        """Format task tags for display.

        Args:
            task: Task to extract tags from

        Returns:
            Formatted tags string (e.g., "work, urgent" or "-")
        """
        if not task.tags:
            return "-"
        return ", ".join(task.tags)

    def _format_status(self, task: Task) -> str:
        """Format status with color styling.

        Args:
            task: Task to extract status from

        Returns:
            Formatted status string with Rich markup
        """
        status_style = self._get_status_style(task.status)
        return f"[{status_style}]{task.status.value}[/{status_style}]"

    def _format_datetime(self, dt) -> str:
        """Format datetime for display.

        Args:
            dt: datetime object or None

        Returns:
            Formatted datetime string or "-"
        """
        if not dt:
            return "-"
        from datetime import datetime

        if isinstance(dt, datetime):
            # Show only date and time (YYYY-MM-DD HH:MM)
            return dt.strftime("%Y-%m-%d %H:%M")
        return str(dt)

    def _format_dependencies(self, task: Task) -> str:
        """Format task dependencies for display.

        Args:
            task: Task to extract dependencies from

        Returns:
            Formatted dependencies string (e.g., "1,2,3" or "-")
        """
        if not task.depends_on:
            return "-"
        return ",".join(str(dep_id) for dep_id in task.depends_on)

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

    def _format_estimated_duration(self, task: Task) -> str:
        """Format estimated duration for display.

        Args:
            task: Task to format estimated duration for

        Returns:
            Formatted estimated duration string (e.g., "5h" or "-")
        """
        if not task.estimated_duration:
            return "-"
        return f"{task.estimated_duration}h"

    def _format_actual_duration(self, task: Task) -> str:
        """Format actual duration for display.

        Args:
            task: Task to format actual duration for

        Returns:
            Formatted actual duration string (e.g., "3h" or "-")
        """
        if not task.actual_duration_hours:
            return "-"
        return f"{task.actual_duration_hours}h"

    def _format_elapsed(self, task: Task) -> str:
        """Format elapsed time for IN_PROGRESS tasks.

        Args:
            task: Task to format elapsed time for

        Returns:
            Formatted elapsed time string (e.g., "15:04:38" or "3d 15:04:38")
        """
        from datetime import datetime

        from domain.entities.task import TaskStatus

        if task.status != TaskStatus.IN_PROGRESS or not task.actual_start:
            return "-"

        # Calculate elapsed time
        elapsed_seconds = int((datetime.now() - task.actual_start).total_seconds())

        # Convert to days, hours, minutes, seconds
        days = elapsed_seconds // 86400
        remaining_seconds = elapsed_seconds % 86400
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60

        # Format based on duration
        if days > 0:
            return f"{days}d {hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
