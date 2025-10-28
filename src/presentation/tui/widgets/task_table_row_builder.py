"""Task table row builder for constructing table row data."""

from rich.text import Text

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.notes_repository import NotesRepository
from presentation.constants.colors import STATUS_STYLES
from presentation.constants.symbols import EMOJI_NOTE
from presentation.constants.table_dimensions import TASK_NAME_MAX_DISPLAY_LENGTH
from presentation.tui.formatters.task_table_formatter import TaskTableFormatter


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

        # Format status with color
        status_text = task.status.value
        status_color = STATUS_STYLES.get(task.status, "white")

        # Format duration
        duration = TaskTableFormatter.format_duration(task)

        # Format deadline
        deadline = TaskTableFormatter.format_deadline(task.deadline)

        # Format dependencies
        dependencies = TaskTableFormatter.format_dependencies(task)

        # Combine fixed and note indicators into flags
        fixed_indicator = "📌" if task.is_fixed else ""
        note_indicator = EMOJI_NOTE if self.notes_repository.has_notes(task.id) else ""
        flags = fixed_indicator + note_indicator

        # Format elapsed time
        elapsed_time = TaskTableFormatter.format_elapsed_time(task)

        # Format name with truncation
        name_text = self._format_name(task.name)

        # Apply strikethrough style for completed tasks
        name_style = "strike" if task.status == TaskStatus.COMPLETED else None

        # Format tags with truncation
        tags_text = self._format_tags(task.tags)

        # Build row with Text objects
        return (
            Text(str(task.id), justify="center"),
            Text(name_text, style=name_style, justify="left"),
            Text(str(task.priority), justify="center"),
            Text(status_text, style=status_color, justify="center"),
            Text(elapsed_time, justify="center"),
            Text(duration, justify="center"),
            Text(deadline, justify="center"),
            Text(dependencies, justify="center"),
            Text(tags_text, justify="center"),
            Text(flags, justify="center"),  # Combined Fixed + Note flags
        )

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
        if len(tags_text) > 18:
            return tags_text[:17] + "..."
        return tags_text
