from typing import TYPE_CHECKING, ClassVar, Literal, cast

from rich.table import Table

from taskdog.console.console_writer import ConsoleWriter
from taskdog.constants.common import (
    COLUMN_DATETIME_NO_WRAP,
    COLUMN_FINISHED_STYLE,
    COLUMN_ID_STYLE,
    COLUMN_NAME_STYLE,
    HEADER_ESTIMATED,
    HEADER_ID,
    HEADER_NAME,
    JUSTIFY_ESTIMATED,
    JUSTIFY_ID,
    JUSTIFY_NAME,
    TABLE_BORDER_STYLE,
    TABLE_HEADER_STYLE,
    TABLE_PADDING,
)
from taskdog.constants.formatting import format_table_title
from taskdog.constants.symbols import EMOJI_NOTE
from taskdog.constants.task_table import (
    COLUMN_CREATED_AT_STYLE,
    COLUMN_DATETIME_STYLE,
    COLUMN_DEADLINE_STYLE,
    COLUMN_DEPENDENCIES_STYLE,
    COLUMN_DURATION_STYLE,
    COLUMN_ELAPSED_STYLE,
    COLUMN_FIXED_STYLE,
    COLUMN_PRIORITY_STYLE,
    COLUMN_TAGS_STYLE,
    COLUMN_UPDATED_AT_STYLE,
    HEADER_ACTUAL,
    HEADER_ACTUAL_END,
    HEADER_ACTUAL_START,
    HEADER_CREATED_AT,
    HEADER_DEADLINE,
    HEADER_DEPENDENCIES,
    HEADER_DURATION,
    HEADER_ELAPSED,
    HEADER_FIXED,
    HEADER_FLAGS,
    HEADER_NOTE,
    HEADER_PLANNED_END,
    HEADER_PLANNED_START,
    HEADER_PRIORITY,
    HEADER_STATUS,
    HEADER_TAGS,
    HEADER_UPDATED_AT,
    JUSTIFY_ACTUAL,
    JUSTIFY_ACTUAL_END,
    JUSTIFY_ACTUAL_START,
    JUSTIFY_CREATED_AT,
    JUSTIFY_DEADLINE,
    JUSTIFY_DEPENDENCIES,
    JUSTIFY_DURATION,
    JUSTIFY_ELAPSED,
    JUSTIFY_FIXED,
    JUSTIFY_FLAGS,
    JUSTIFY_NOTE,
    JUSTIFY_PLANNED_END,
    JUSTIFY_PLANNED_START,
    JUSTIFY_PRIORITY,
    JUSTIFY_STATUS,
    JUSTIFY_TAGS,
    JUSTIFY_UPDATED_AT,
)
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.formatters.duration_formatter import DurationFormatter
from taskdog.renderers.rich_renderer_base import RichRendererBase
from taskdog.view_models.task_view_model import TaskRowViewModel

if TYPE_CHECKING:
    from collections.abc import Callable

# Type alias for Rich table justify method
JustifyMethod = Literal["default", "left", "center", "right", "full"]


class RichTableRenderer(RichRendererBase):
    """Renders tasks as a table using Rich."""

    # Field definitions: field_name -> column configuration
    FIELD_DEFINITIONS: ClassVar[dict[str, dict[str, str | bool]]] = {
        "id": {
            "header": HEADER_ID,
            "justify": JUSTIFY_ID,
            "style": COLUMN_ID_STYLE,
            "no_wrap": True,
        },
        "name": {
            "header": HEADER_NAME,
            "justify": JUSTIFY_NAME,
            "style": COLUMN_NAME_STYLE,
        },
        "note": {
            "header": HEADER_NOTE,
            "justify": JUSTIFY_NOTE,
            "no_wrap": True,
        },
        "priority": {
            "header": HEADER_PRIORITY,
            "justify": JUSTIFY_PRIORITY,
            "style": COLUMN_PRIORITY_STYLE,
            "no_wrap": True,
        },
        "flags": {
            "header": HEADER_FLAGS,
            "justify": JUSTIFY_FLAGS,
            "no_wrap": True,
        },
        "status": {
            "header": HEADER_STATUS,
            "justify": JUSTIFY_STATUS,
        },
        "planned_start": {
            "header": HEADER_PLANNED_START,
            "justify": JUSTIFY_PLANNED_START,
            "style": COLUMN_DATETIME_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "planned_end": {
            "header": HEADER_PLANNED_END,
            "justify": JUSTIFY_PLANNED_END,
            "style": COLUMN_DATETIME_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "actual_start": {
            "header": HEADER_ACTUAL_START,
            "justify": JUSTIFY_ACTUAL_START,
            "style": COLUMN_DATETIME_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "actual_end": {
            "header": HEADER_ACTUAL_END,
            "justify": JUSTIFY_ACTUAL_END,
            "style": COLUMN_DATETIME_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "deadline": {
            "header": HEADER_DEADLINE,
            "justify": JUSTIFY_DEADLINE,
            "style": COLUMN_DEADLINE_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "duration": {
            "header": HEADER_DURATION,
            "justify": JUSTIFY_DURATION,
            "style": COLUMN_DURATION_STYLE,
            "no_wrap": True,
        },
        "estimated_duration": {
            "header": HEADER_ESTIMATED,
            "justify": JUSTIFY_ESTIMATED,
            "style": COLUMN_DURATION_STYLE,
            "no_wrap": True,
        },
        "actual_duration": {
            "header": HEADER_ACTUAL,
            "justify": JUSTIFY_ACTUAL,
            "style": COLUMN_DURATION_STYLE,
            "no_wrap": True,
        },
        "elapsed": {
            "header": HEADER_ELAPSED,
            "justify": JUSTIFY_ELAPSED,
            "style": COLUMN_ELAPSED_STYLE,
            "no_wrap": True,
        },
        "created_at": {
            "header": HEADER_CREATED_AT,
            "justify": JUSTIFY_CREATED_AT,
            "style": COLUMN_CREATED_AT_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "updated_at": {
            "header": HEADER_UPDATED_AT,
            "justify": JUSTIFY_UPDATED_AT,
            "style": COLUMN_UPDATED_AT_STYLE,
            "no_wrap": COLUMN_DATETIME_NO_WRAP,
        },
        "depends_on": {
            "header": HEADER_DEPENDENCIES,
            "justify": JUSTIFY_DEPENDENCIES,
            "style": COLUMN_DEPENDENCIES_STYLE,
            "no_wrap": True,
        },
        "is_fixed": {
            "header": HEADER_FIXED,
            "justify": JUSTIFY_FIXED,
            "style": COLUMN_FIXED_STYLE,
            "no_wrap": True,
        },
        "tags": {
            "header": HEADER_TAGS,
            "justify": JUSTIFY_TAGS,
            "style": COLUMN_TAGS_STYLE,
            "no_wrap": False,
        },
    }

    # Default fields to display when none specified (matches TUI column order)
    DEFAULT_FIELDS: ClassVar[list[str]] = [
        "id",
        "name",
        "status",
        "priority",
        "flags",
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

    def __init__(self, console_writer: ConsoleWriter):
        """Initialize the renderer.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer

    def render(
        self, tasks: list[TaskRowViewModel], fields: list[str] | None = None
    ) -> None:
        """Render and print tasks as a table with Rich.

        Args:
            tasks: List of TaskRowViewModel for display
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
            # Escape '[' for Rich markup (e.g. "Estimated[h]" → "Estimated\[h]")
            header = str(field_config["header"]).replace("[", "\\[")
            justify_val = field_config.get("justify")
            valid_justify = {"default", "left", "center", "right", "full"}
            justify: JustifyMethod = (
                cast("JustifyMethod", justify_val)
                if isinstance(justify_val, str) and justify_val in valid_justify
                else "left"
            )
            style_val = field_config.get("style")
            style = str(style_val) if style_val else None
            no_wrap = bool(field_config.get("no_wrap", False))
            table.add_column(header, justify=justify, style=style, no_wrap=no_wrap)

        # Add rows
        for task in tasks:
            row_values = [
                self._get_field_value(task, field_name) for field_name in fields
            ]
            table.add_row(*row_values)

        # Print table using console writer
        self.console_writer.print(table)

    def _get_field_value(self, task: TaskRowViewModel, field_name: str) -> str:
        """Get the formatted value for a specific field.

        Args:
            task: TaskRowViewModel to extract value from
            field_name: Name of the field

        Returns:
            Formatted string value for display
        """
        # Field value extractors mapping
        field_extractors: dict[str, Callable[[TaskRowViewModel], str]] = {
            "id": lambda t: str(t.id),
            "name": lambda t: (
                f"[{COLUMN_FINISHED_STYLE}]{t.name}[/{COLUMN_FINISHED_STYLE}]"
                if t.is_finished
                else t.name
            ),
            "note": lambda t: EMOJI_NOTE if t.has_notes else "",
            "priority": lambda t: str(t.priority),
            "flags": lambda t: self._format_flags(t),
            "status": lambda t: self._format_status(t),
            "is_fixed": lambda t: "📌" if t.is_fixed else "",
            "depends_on": lambda t: self._format_dependencies(t),
            "tags": lambda t: self._format_tags(t),
            "planned_start": lambda t: DateTimeFormatter.format_datetime(
                t.planned_start
            ),
            "planned_end": lambda t: DateTimeFormatter.format_datetime(t.planned_end),
            "actual_start": lambda t: DateTimeFormatter.format_datetime(t.actual_start),
            "actual_end": lambda t: DateTimeFormatter.format_datetime(t.actual_end),
            "deadline": lambda t: DateTimeFormatter.format_datetime(t.deadline),
            "duration": lambda t: self._format_duration_info(t),
            "estimated_duration": lambda t: DurationFormatter.format_estimated_duration(
                t
            ),
            "actual_duration": lambda t: DurationFormatter.format_actual_duration(t),
            "elapsed": lambda t: DurationFormatter.format_elapsed_time(t),
            "created_at": lambda t: DateTimeFormatter.format_datetime(t.created_at),
            "updated_at": lambda t: DateTimeFormatter.format_datetime(t.updated_at),
        }

        extractor = field_extractors.get(field_name)
        return extractor(task) if extractor else "-"

    @staticmethod
    def _format_flags(task: TaskRowViewModel) -> str:
        """Format task flags (fixed indicator + note indicator).

        Args:
            task: TaskRowViewModel to extract flags from

        Returns:
            Formatted flags string
        """
        fixed_indicator = "📌" if task.is_fixed else ""
        note_indicator = EMOJI_NOTE if task.has_notes else ""
        return fixed_indicator + note_indicator

    def _format_tags(self, task: TaskRowViewModel) -> str:
        """Format task tags for display.

        Args:
            task: TaskRowViewModel to extract tags from

        Returns:
            Formatted tags string (e.g., "work, urgent" or "")
        """
        if not task.tags:
            return ""
        return ", ".join(task.tags)

    def _format_status(self, task: TaskRowViewModel) -> str:
        """Format status with color styling.

        Args:
            task: TaskRowViewModel to extract status from

        Returns:
            Formatted status string with Rich markup
        """
        status_style = self._get_status_style(task.status)
        return f"[{status_style}]{task.status.value}[/{status_style}]"

    def _format_dependencies(self, task: TaskRowViewModel) -> str:
        """Format task dependencies for display.

        Args:
            task: TaskRowViewModel to extract dependencies from

        Returns:
            Formatted dependencies string (e.g., "1,2,3" or "-")
        """
        if not task.depends_on:
            return "-"
        return ",".join(str(dep_id) for dep_id in task.depends_on)

    def _format_duration_info(self, task: TaskRowViewModel) -> str:
        """Format duration information for a task.

        Args:
            task: TaskRowViewModel to format

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
