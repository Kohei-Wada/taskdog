"""Task table row builder for constructing table row data."""

from rich.text import Text

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.notes_repository import NotesRepository
from presentation.constants.colors import STATUS_STYLES
from presentation.constants.symbols import EMOJI_NOTE
from presentation.constants.table_dimensions import TASK_NAME_MAX_DISPLAY_LENGTH
from presentation.tui.formatters.task_table_formatter import TaskTableFormatter

# Constants for text truncation
TAGS_MAX_DISPLAY_LENGTH = 18


class TaskTableRowBuilder:
    """Builds table row data from Task entities.

    Responsible for converting Task domain objects into Rich Text objects
    suitable for display in the task table widget.
    """

    def __init__(self, notes_repository: NotesRepository):
        """Initialize the row builder.

        Args:
            notes_repository: Repository for checking note existence
        """
        self.notes_repository = notes_repository

    def build_row(self, task: Task) -> tuple[Text, ...]:
        """Build a table row from a task.

        Args:
            task: Task to build row for

        Returns:
            Tuple of Text objects representing the table row columns
        """
        return (
            self._build_id_cell(task),
            self._build_name_cell(task),
            self._build_priority_cell(task),
            self._build_status_cell(task),
            self._build_planned_start_cell(task),
            self._build_planned_end_cell(task),
            self._build_actual_start_cell(task),
            self._build_actual_end_cell(task),
            self._build_elapsed_cell(task),
            self._build_estimated_duration_cell(task),
            self._build_actual_duration_cell(task),
            self._build_deadline_cell(task),
            self._build_dependencies_cell(task),
            self._build_tags_cell(task),
            self._build_flags_cell(task),
        )

    def _build_id_cell(self, task: Task) -> Text:
        """Build ID cell.

        Args:
            task: Task to extract ID from

        Returns:
            Text object for ID column
        """
        return Text(str(task.id), justify="center")

    def _build_name_cell(self, task: Task) -> Text:
        """Build name cell with truncation and strikethrough for completed tasks.

        Args:
            task: Task to extract name from

        Returns:
            Text object for name column
        """
        name_text = self._format_name(task.name)
        name_style = "strike" if task.status == TaskStatus.COMPLETED else None
        return Text(name_text, style=name_style, justify="left")

    def _build_priority_cell(self, task: Task) -> Text:
        """Build priority cell.

        Args:
            task: Task to extract priority from

        Returns:
            Text object for priority column
        """
        return Text(str(task.priority), justify="center")

    def _build_status_cell(self, task: Task) -> Text:
        """Build status cell with color coding.

        Args:
            task: Task to extract status from

        Returns:
            Text object for status column
        """
        status_text = task.status.value
        status_color = STATUS_STYLES.get(task.status, "white")
        return Text(status_text, style=status_color, justify="center")

    def _build_elapsed_cell(self, task: Task) -> Text:
        """Build elapsed time cell.

        Args:
            task: Task to calculate elapsed time for

        Returns:
            Text object for elapsed time column
        """
        elapsed_time = TaskTableFormatter.format_elapsed_time(task)
        return Text(elapsed_time, justify="center")

    def _build_planned_start_cell(self, task: Task) -> Text:
        """Build planned start cell.

        Args:
            task: Task to extract planned start from

        Returns:
            Text object for planned start column
        """
        planned_start = TaskTableFormatter.format_planned_start(task.planned_start)
        return Text(planned_start, justify="center")

    def _build_planned_end_cell(self, task: Task) -> Text:
        """Build planned end cell.

        Args:
            task: Task to extract planned end from

        Returns:
            Text object for planned end column
        """
        planned_end = TaskTableFormatter.format_planned_end(task.planned_end)
        return Text(planned_end, justify="center")

    def _build_actual_start_cell(self, task: Task) -> Text:
        """Build actual start cell.

        Args:
            task: Task to extract actual start from

        Returns:
            Text object for actual start column
        """
        actual_start = TaskTableFormatter.format_actual_start(task.actual_start)
        return Text(actual_start, justify="center")

    def _build_actual_end_cell(self, task: Task) -> Text:
        """Build actual end cell.

        Args:
            task: Task to extract actual end from

        Returns:
            Text object for actual end column
        """
        actual_end = TaskTableFormatter.format_actual_end(task.actual_end)
        return Text(actual_end, justify="center")

    def _build_estimated_duration_cell(self, task: Task) -> Text:
        """Build estimated duration cell.

        Args:
            task: Task to extract estimated duration from

        Returns:
            Text object for estimated duration column
        """
        est_duration = TaskTableFormatter.format_estimated_duration(task)
        return Text(est_duration, justify="center")

    def _build_actual_duration_cell(self, task: Task) -> Text:
        """Build actual duration cell.

        Args:
            task: Task to extract actual duration from

        Returns:
            Text object for actual duration column
        """
        actual_duration = TaskTableFormatter.format_actual_duration(task)
        return Text(actual_duration, justify="center")

    def _build_deadline_cell(self, task: Task) -> Text:
        """Build deadline cell.

        Args:
            task: Task to extract deadline from

        Returns:
            Text object for deadline column
        """
        deadline = TaskTableFormatter.format_deadline(task.deadline)
        return Text(deadline, justify="center")

    def _build_dependencies_cell(self, task: Task) -> Text:
        """Build dependencies cell.

        Args:
            task: Task to extract dependencies from

        Returns:
            Text object for dependencies column
        """
        dependencies = TaskTableFormatter.format_dependencies(task)
        return Text(dependencies, justify="center")

    def _build_tags_cell(self, task: Task) -> Text:
        """Build tags cell with truncation.

        Args:
            task: Task to extract tags from

        Returns:
            Text object for tags column
        """
        tags_text = self._format_tags(task.tags)
        return Text(tags_text, justify="center")

    def _build_flags_cell(self, task: Task) -> Text:
        """Build flags cell (fixed indicator + note indicator).

        Args:
            task: Task to build flags for

        Returns:
            Text object for flags column
        """
        fixed_indicator = "📌" if task.is_fixed else ""
        note_indicator = EMOJI_NOTE if self.notes_repository.has_notes(task.id) else ""
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
