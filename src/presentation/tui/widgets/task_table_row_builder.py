"""Task table row builder for constructing table row data."""

from collections.abc import Callable
from datetime import datetime

from rich.text import Text

from presentation.constants.colors import STATUS_STYLES
from presentation.constants.symbols import EMOJI_NOTE
from presentation.constants.table_dimensions import TASK_NAME_MAX_DISPLAY_LENGTH
from presentation.enums.task_status import TaskStatus
from presentation.view_models.task_view_model import TaskRowViewModel

# Constants for text truncation
TAGS_MAX_DISPLAY_LENGTH = 18


class TaskTableRowBuilder:
    """Builds table row data from TaskRowViewModel.

    Responsible for converting TaskRowViewModel objects into Rich Text objects
    suitable for display in the task table widget.
    """

    def build_row(self, task_vm: TaskRowViewModel) -> tuple[Text, ...]:
        """Build a table row from a task view model.

        Args:
            task_vm: TaskRowViewModel to build row for

        Returns:
            Tuple of Text objects representing the table row columns
        """
        return (
            self._build_id_cell(task_vm),
            self._build_name_cell(task_vm),
            self._build_status_cell(task_vm),
            self._build_priority_cell(task_vm),
            self._build_flags_cell(task_vm),
            self._build_estimated_duration_cell(task_vm),
            self._build_actual_duration_cell(task_vm),
            self._build_deadline_cell(task_vm),
            self._build_planned_start_cell(task_vm),
            self._build_planned_end_cell(task_vm),
            self._build_actual_start_cell(task_vm),
            self._build_actual_end_cell(task_vm),
            self._build_elapsed_cell(task_vm),
            self._build_dependencies_cell(task_vm),
            self._build_tags_cell(task_vm),
        )

    @staticmethod
    def _create_centered_cell(value: str | int) -> Text:
        """Create a centered text cell.

        Args:
            value: Value to display in the cell

        Returns:
            Text object with centered justification
        """
        return Text(str(value), justify="center")

    @staticmethod
    def _create_cell_from_formatter(formatter_func: Callable, *args: object) -> Text:
        """Create a cell using a formatter function.

        Args:
            formatter_func: Formatter function to call
            *args: Arguments to pass to the formatter

        Returns:
            Text object with centered justification
        """
        return Text(formatter_func(*args), justify="center")

    def _build_id_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build ID cell.

        Args:
            task_vm: TaskRowViewModel to extract ID from

        Returns:
            Text object for ID column
        """
        return self._create_centered_cell(task_vm.id)

    def _build_name_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build name cell with truncation and strikethrough for completed, canceled, and archived tasks.

        Args:
            task_vm: TaskRowViewModel to extract name from

        Returns:
            Text object for name column
        """
        name_text = self._format_name(task_vm.name)
        name_style = "strike" if task_vm.is_finished else None
        return Text(name_text, style=name_style, justify="left")

    def _build_priority_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build priority cell.

        Args:
            task_vm: TaskRowViewModel to extract priority from

        Returns:
            Text object for priority column
        """
        return self._create_centered_cell(task_vm.priority)

    def _build_status_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build status cell with color coding.

        Args:
            task_vm: TaskRowViewModel to extract status from

        Returns:
            Text object for status column
        """
        status_text = task_vm.status.value
        status_color = STATUS_STYLES.get(task_vm.status.value, "white")
        return Text(status_text, style=status_color, justify="center")

    def _build_elapsed_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build elapsed time cell.

        Args:
            task_vm: TaskRowViewModel to calculate elapsed time for

        Returns:
            Text object for elapsed time column
        """
        return self._create_cell_from_formatter(TaskTableRowBuilder.format_elapsed_time, task_vm)

    def _build_planned_start_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build planned start cell.

        Args:
            task_vm: TaskRowViewModel to extract planned start from

        Returns:
            Text object for planned start column
        """
        return self._create_cell_from_formatter(
            TaskTableRowBuilder.format_planned_start, task_vm.planned_start
        )

    def _build_planned_end_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build planned end cell.

        Args:
            task_vm: TaskRowViewModel to extract planned end from

        Returns:
            Text object for planned end column
        """
        return self._create_cell_from_formatter(
            TaskTableRowBuilder.format_planned_end, task_vm.planned_end
        )

    def _build_actual_start_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build actual start cell.

        Args:
            task_vm: TaskRowViewModel to extract actual start from

        Returns:
            Text object for actual start column
        """
        return self._create_cell_from_formatter(
            TaskTableRowBuilder.format_actual_start, task_vm.actual_start
        )

    def _build_actual_end_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build actual end cell.

        Args:
            task_vm: TaskRowViewModel to extract actual end from

        Returns:
            Text object for actual end column
        """
        return self._create_cell_from_formatter(
            TaskTableRowBuilder.format_actual_end, task_vm.actual_end
        )

    def _build_estimated_duration_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build estimated duration cell.

        Args:
            task_vm: TaskRowViewModel to extract estimated duration from

        Returns:
            Text object for estimated duration column
        """
        return self._create_cell_from_formatter(
            TaskTableRowBuilder.format_estimated_duration, task_vm
        )

    def _build_actual_duration_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build actual duration cell.

        Args:
            task_vm: TaskRowViewModel to extract actual duration from

        Returns:
            Text object for actual duration column
        """
        return self._create_cell_from_formatter(TaskTableRowBuilder.format_actual_duration, task_vm)

    def _build_deadline_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build deadline cell.

        Args:
            task_vm: TaskRowViewModel to extract deadline from

        Returns:
            Text object for deadline column
        """
        return self._create_cell_from_formatter(
            TaskTableRowBuilder.format_deadline, task_vm.deadline
        )

    def _build_dependencies_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build dependencies cell.

        Args:
            task_vm: TaskRowViewModel to extract dependencies from

        Returns:
            Text object for dependencies column
        """
        return self._create_cell_from_formatter(TaskTableRowBuilder.format_dependencies, task_vm)

    def _build_tags_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build tags cell with truncation.

        Args:
            task_vm: TaskRowViewModel to extract tags from

        Returns:
            Text object for tags column
        """
        tags_text = self._format_tags(task_vm.tags)
        return Text(tags_text, justify="center")

    def _build_flags_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build flags cell (fixed indicator + note indicator).

        Args:
            task_vm: TaskRowViewModel to build flags for

        Returns:
            Text object for flags column
        """
        fixed_indicator = "📌" if task_vm.is_fixed else ""
        note_indicator = EMOJI_NOTE if task_vm.has_notes else ""
        flags = fixed_indicator + note_indicator
        return Text(flags, justify="center")

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
        """Format task tags with truncation if needed.

        Args:
            tags: List of tags to format

        Returns:
            Formatted tags string
        """
        if not tags:
            return ""

        tags_text = ", ".join(tags)
        if len(tags_text) > TAGS_MAX_DISPLAY_LENGTH:
            return tags_text[: TAGS_MAX_DISPLAY_LENGTH - 1] + "..."
        return tags_text

    # ============================================================================
    # Static Formatting Methods (formerly from TaskTableFormatter)
    # ============================================================================

    @staticmethod
    def format_duration(task_vm: TaskRowViewModel) -> str:
        """Format duration information for display.

        Args:
            task_vm: TaskRowViewModel to format duration for

        Returns:
            Formatted duration string
        """
        if not task_vm.estimated_duration and not task_vm.actual_duration_hours:
            return "-"

        parts = []
        if task_vm.estimated_duration:
            parts.append(f"E:{task_vm.estimated_duration}h")
        if task_vm.actual_duration_hours:
            parts.append(f"A:{task_vm.actual_duration_hours}h")

        return " ".join(parts)

    @staticmethod
    def format_dependencies(task_vm: TaskRowViewModel) -> str:
        """Format task dependencies for display.

        Args:
            task_vm: TaskRowViewModel to extract dependencies from

        Returns:
            Formatted dependencies string (e.g., "1,2,3" or "-")
        """
        if not task_vm.depends_on:
            return "-"
        return ",".join(str(dep_id) for dep_id in task_vm.depends_on)

    @staticmethod
    def _format_datetime(dt: datetime | None) -> str:
        """Format datetime for display with year-aware formatting.

        Shows MM-DD HH:MM for current year, 'YY MM-DD HH:MM otherwise.

        Args:
            dt: Datetime to format, or None

        Returns:
            Formatted string, or "-" if dt is None
        """
        if not dt:
            return "-"

        current_year = datetime.now().year
        if dt.year == current_year:
            return dt.strftime("%m-%d %H:%M")
        return dt.strftime("'%y %m-%d %H:%M")

    @staticmethod
    def format_deadline(deadline: datetime | None) -> str:
        """Format deadline for display.

        Args:
            deadline: Deadline datetime object or None

        Returns:
            Formatted deadline string
        """
        return TaskTableRowBuilder._format_datetime(deadline)

    @staticmethod
    def format_estimated_duration(task_vm: TaskRowViewModel) -> str:
        """Format estimated duration for display.

        Args:
            task_vm: TaskRowViewModel to format estimated duration for

        Returns:
            Formatted estimated duration string (e.g., "5h" or "-")
        """
        if not task_vm.estimated_duration:
            return "-"
        return f"{task_vm.estimated_duration}h"

    @staticmethod
    def format_actual_duration(task_vm: TaskRowViewModel) -> str:
        """Format actual duration for display.

        Args:
            task_vm: TaskRowViewModel to format actual duration for

        Returns:
            Formatted actual duration string (e.g., "3h" or "-")
        """
        if not task_vm.actual_duration_hours:
            return "-"
        return f"{task_vm.actual_duration_hours}h"

    @staticmethod
    def format_planned_start(planned_start: datetime | None) -> str:
        """Format planned start datetime for display.

        Args:
            planned_start: Planned start datetime object or None

        Returns:
            Formatted planned start string
        """
        return TaskTableRowBuilder._format_datetime(planned_start)

    @staticmethod
    def format_planned_end(planned_end: datetime | None) -> str:
        """Format planned end datetime for display.

        Args:
            planned_end: Planned end datetime object or None

        Returns:
            Formatted planned end string
        """
        return TaskTableRowBuilder._format_datetime(planned_end)

    @staticmethod
    def format_actual_start(actual_start: datetime | None) -> str:
        """Format actual start datetime for display.

        Args:
            actual_start: Actual start datetime object or None

        Returns:
            Formatted actual start string
        """
        return TaskTableRowBuilder._format_datetime(actual_start)

    @staticmethod
    def format_actual_end(actual_end: datetime | None) -> str:
        """Format actual end datetime for display.

        Args:
            actual_end: Actual end datetime object or None

        Returns:
            Formatted actual end string
        """
        return TaskTableRowBuilder._format_datetime(actual_end)

    @staticmethod
    def format_elapsed_time(task_vm: TaskRowViewModel) -> str:
        """Format elapsed time for IN_PROGRESS tasks.

        Args:
            task_vm: TaskRowViewModel to format elapsed time for

        Returns:
            Formatted elapsed time string (e.g., "15:04:38" or "3d 15:04:38")
        """
        if task_vm.status != TaskStatus.IN_PROGRESS or not task_vm.actual_start:
            return "-"

        # Calculate elapsed time
        elapsed_seconds = int((datetime.now() - task_vm.actual_start).total_seconds())

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
