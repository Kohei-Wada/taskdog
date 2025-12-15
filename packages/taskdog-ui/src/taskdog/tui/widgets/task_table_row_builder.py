"""Task table row builder for constructing table row data."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from rich.text import Text

from taskdog.constants.colors import STATUS_STYLES
from taskdog.constants.symbols import EMOJI_NOTE
from taskdog.constants.table_dimensions import TASK_NAME_MAX_DISPLAY_LENGTH
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.formatters.duration_formatter import DurationFormatter
from taskdog.view_models.task_view_model import TaskRowViewModel


@dataclass(frozen=True)
class ColumnConfig:
    """Configuration for a single table column.

    Attributes:
        formatter: Function to extract/format value from TaskRowViewModel
        justification: Text alignment (left/center/right)
        style_func: Optional function to determine cell style based on TaskRowViewModel
    """

    formatter: Callable[[TaskRowViewModel], str]
    justification: Literal["left", "center", "right"] = "center"
    style_func: Callable[[TaskRowViewModel], str | None] | None = None


class TaskTableRowBuilder:
    """Builds table row data from TaskRowViewModel.

    Responsible for converting TaskRowViewModel objects into Rich Text objects
    suitable for display in the task table widget. Uses DateTimeFormatter
    and DurationFormatter for formatting logic.
    """

    def __init__(self):
        """Initialize the TaskTableRowBuilder with formatter dependencies."""
        self.date_formatter = DateTimeFormatter()
        self.duration_formatter = DurationFormatter()
        self._columns = self._initialize_column_config()

    def _initialize_column_config(self) -> list[ColumnConfig]:
        """Initialize column configuration for table building.

        Returns:
            List of ColumnConfig defining each table column's formatting
        """
        return [
            # ID column
            ColumnConfig(formatter=lambda vm: str(vm.id)),
            # Name column (left-aligned, strikethrough for finished)
            ColumnConfig(
                formatter=lambda vm: self._format_name(vm.name),
                justification="left",
                style_func=lambda vm: "strike" if vm.is_finished else None,
            ),
            # Status column (color-coded)
            ColumnConfig(
                formatter=lambda vm: vm.status.value,
                style_func=lambda vm: STATUS_STYLES.get(vm.status.value, "white"),
            ),
            # Priority column
            ColumnConfig(formatter=lambda vm: str(vm.priority)),
            # Flags column (fixed indicator + note indicator)
            ColumnConfig(formatter=lambda vm: self._format_flags(vm)),
            # Estimated duration column
            ColumnConfig(
                formatter=lambda vm: self.duration_formatter.format_estimated_duration(
                    vm
                )
            ),
            # Actual duration column
            ColumnConfig(
                formatter=lambda vm: self.duration_formatter.format_actual_duration(vm)
            ),
            # Deadline column
            ColumnConfig(
                formatter=lambda vm: self.date_formatter.format_deadline(vm.deadline)
            ),
            # Planned start column
            ColumnConfig(
                formatter=lambda vm: self.date_formatter.format_planned_start(
                    vm.planned_start
                )
            ),
            # Planned end column
            ColumnConfig(
                formatter=lambda vm: self.date_formatter.format_planned_end(
                    vm.planned_end
                )
            ),
            # Actual start column
            ColumnConfig(
                formatter=lambda vm: self.date_formatter.format_actual_start(
                    vm.actual_start
                )
            ),
            # Actual end column
            ColumnConfig(
                formatter=lambda vm: self.date_formatter.format_actual_end(
                    vm.actual_end
                )
            ),
            # Elapsed time column
            ColumnConfig(
                formatter=lambda vm: self.duration_formatter.format_elapsed_time(vm)
            ),
            # Dependencies column
            ColumnConfig(formatter=lambda vm: self._format_dependencies(vm.depends_on)),
            # Tags column
            ColumnConfig(formatter=lambda vm: self._format_tags(vm.tags)),
        ]

    def build_row(self, task_vm: TaskRowViewModel) -> tuple[Text, ...]:
        """Build a table row from a task view model.

        Args:
            task_vm: TaskRowViewModel to build row for

        Returns:
            Tuple of Text objects representing the table row columns
        """
        return tuple(self._build_cell(task_vm, col) for col in self._columns)

    def _build_cell(self, task_vm: TaskRowViewModel, col: ColumnConfig) -> Text:
        """Build a single cell based on column configuration.

        Args:
            task_vm: TaskRowViewModel to extract data from
            col: ColumnConfig defining cell formatting

        Returns:
            Text object for the cell
        """
        value = col.formatter(task_vm)
        style = col.style_func(task_vm) if col.style_func else None
        text = Text(value, justify=col.justification)
        if style:
            text.stylize(style)
        return text

    @staticmethod
    def _format_flags(task_vm: TaskRowViewModel) -> str:
        """Format task flags (fixed indicator + note indicator).

        Args:
            task_vm: TaskRowViewModel to extract flags from

        Returns:
            Formatted flags string
        """
        fixed_indicator = "📌" if task_vm.is_fixed else ""
        note_indicator = EMOJI_NOTE if task_vm.has_notes else ""
        return fixed_indicator + note_indicator

    @staticmethod
    def _format_name(name: str) -> str:
        """Format task name with truncation if needed.

        Args:
            name: Task name to format

        Returns:
            Formatted task name
        """
        if len(name) > TASK_NAME_MAX_DISPLAY_LENGTH:
            return name[:TASK_NAME_MAX_DISPLAY_LENGTH] + "..."
        return name

    @staticmethod
    def _format_tags(tags: list[str] | None) -> str:
        """Format task tags.

        Args:
            tags: List of tags to format

        Returns:
            Formatted tags string
        """
        if not tags:
            return ""
        return ", ".join(tags)

    @staticmethod
    def _format_dependencies(depends_on: list[int] | None) -> str:
        """Format task dependencies for display.

        Args:
            depends_on: List of dependency task IDs

        Returns:
            Formatted dependencies string (e.g., "1,2,3" or "-")
        """
        if not depends_on:
            return "-"
        return ",".join(str(dep_id) for dep_id in depends_on)
