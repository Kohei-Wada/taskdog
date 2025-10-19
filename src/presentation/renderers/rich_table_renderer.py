from typing import ClassVar

from rich.table import Table

from domain.entities.task import Task
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
        "created_at": {
            "header": "Created At",
            "style": "dim",
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
    }

    # Default fields to display when none specified
    DEFAULT_FIELDS: ClassVar[list[str]] = [
        "id",
        "name",
        "note",
        "priority",
        "status",
        "planned_start",
        "planned_end",
        "actual_start",
        "actual_end",
        "deadline",
        "duration",
    ]

    def __init__(self, console_writer: ConsoleWriter):
        """Initialize the renderer.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer

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
            "name": lambda t: t.name,
            "note": lambda t: "📝" if t.has_note else "",
            "priority": lambda t: str(t.priority),
            "status": lambda t: self._format_status(t),
            "planned_start": lambda t: self._format_datetime(t.planned_start),
            "planned_end": lambda t: self._format_datetime(t.planned_end),
            "actual_start": lambda t: self._format_datetime(t.actual_start),
            "actual_end": lambda t: self._format_datetime(t.actual_end),
            "deadline": lambda t: self._format_datetime(t.deadline),
            "duration": lambda t: self._format_duration_info(t),
            "created_at": lambda t: self._format_datetime(t.created_at_str),
        }

        extractor = field_extractors.get(field_name)
        return extractor(task) if extractor else "-"

    def _format_status(self, task: Task) -> str:
        """Format status with color styling.

        Args:
            task: Task to extract status from

        Returns:
            Formatted status string with Rich markup
        """
        status_style = self._get_status_style(task.status)
        return f"[{status_style}]{task.status.value}[/{status_style}]"

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
