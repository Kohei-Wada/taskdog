"""Task table row builder for constructing table row data."""

from rich.text import Text

from taskdog.builders.table_cell_builder import TableCellBuilder
from taskdog.constants.colors import STATUS_STYLES
from taskdog.constants.symbols import EMOJI_NOTE
from taskdog.constants.table_dimensions import TASK_NAME_MAX_DISPLAY_LENGTH
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.formatters.duration_formatter import DurationFormatter
from taskdog.tui.constants.ui_settings import TAGS_MAX_DISPLAY_LENGTH
from taskdog.view_models.task_view_model import TaskRowViewModel


class TaskTableRowBuilder:
    """Builds table row data from TaskRowViewModel.

    Responsible for converting TaskRowViewModel objects into Rich Text objects
    suitable for display in the task table widget. Uses DateTimeFormatter,
    DurationFormatter, and TableCellBuilder for formatting logic.
    """

    def __init__(self):
        """Initialize the TaskTableRowBuilder with formatter dependencies."""
        self.date_formatter = DateTimeFormatter()
        self.duration_formatter = DurationFormatter()
        self.cell_builder = TableCellBuilder()

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

    def _build_id_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build ID cell.

        Args:
            task_vm: TaskRowViewModel to extract ID from

        Returns:
            Text object for ID column
        """
        return self.cell_builder.build_centered_cell(task_vm.id)

    def _build_name_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build name cell with truncation and strikethrough for completed, canceled, and archived tasks.

        Args:
            task_vm: TaskRowViewModel to extract name from

        Returns:
            Text object for name column
        """
        name_text = self._format_name(task_vm.name)
        name_style = "strike" if task_vm.is_finished else None
        return self.cell_builder.build_left_aligned_cell(name_text, style=name_style)

    def _build_priority_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build priority cell.

        Args:
            task_vm: TaskRowViewModel to extract priority from

        Returns:
            Text object for priority column
        """
        return self.cell_builder.build_centered_cell(task_vm.priority)

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
        return self.cell_builder.build_cell_from_formatter(
            self.duration_formatter.format_elapsed_time, task_vm
        )

    def _build_planned_start_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build planned start cell.

        Args:
            task_vm: TaskRowViewModel to extract planned start from

        Returns:
            Text object for planned start column
        """
        return self.cell_builder.build_cell_from_formatter(
            self.date_formatter.format_planned_start, task_vm.planned_start
        )

    def _build_planned_end_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build planned end cell.

        Args:
            task_vm: TaskRowViewModel to extract planned end from

        Returns:
            Text object for planned end column
        """
        return self.cell_builder.build_cell_from_formatter(
            self.date_formatter.format_planned_end, task_vm.planned_end
        )

    def _build_actual_start_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build actual start cell.

        Args:
            task_vm: TaskRowViewModel to extract actual start from

        Returns:
            Text object for actual start column
        """
        return self.cell_builder.build_cell_from_formatter(
            self.date_formatter.format_actual_start, task_vm.actual_start
        )

    def _build_actual_end_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build actual end cell.

        Args:
            task_vm: TaskRowViewModel to extract actual end from

        Returns:
            Text object for actual end column
        """
        return self.cell_builder.build_cell_from_formatter(
            self.date_formatter.format_actual_end, task_vm.actual_end
        )

    def _build_estimated_duration_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build estimated duration cell.

        Args:
            task_vm: TaskRowViewModel to extract estimated duration from

        Returns:
            Text object for estimated duration column
        """
        return self.cell_builder.build_cell_from_formatter(
            self.duration_formatter.format_estimated_duration, task_vm
        )

    def _build_actual_duration_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build actual duration cell.

        Args:
            task_vm: TaskRowViewModel to extract actual duration from

        Returns:
            Text object for actual duration column
        """
        return self.cell_builder.build_cell_from_formatter(
            self.duration_formatter.format_actual_duration, task_vm
        )

    def _build_deadline_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build deadline cell.

        Args:
            task_vm: TaskRowViewModel to extract deadline from

        Returns:
            Text object for deadline column
        """
        return self.cell_builder.build_cell_from_formatter(
            self.date_formatter.format_deadline, task_vm.deadline
        )

    def _build_dependencies_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build dependencies cell.

        Args:
            task_vm: TaskRowViewModel to extract dependencies from

        Returns:
            Text object for dependencies column
        """
        deps_text = self._format_dependencies(task_vm.depends_on)
        return self.cell_builder.build_centered_cell(deps_text)

    def _build_tags_cell(self, task_vm: TaskRowViewModel) -> Text:
        """Build tags cell with truncation.

        Args:
            task_vm: TaskRowViewModel to extract tags from

        Returns:
            Text object for tags column
        """
        tags_text = self._format_tags(task_vm.tags)
        return self.cell_builder.build_centered_cell(tags_text)

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
