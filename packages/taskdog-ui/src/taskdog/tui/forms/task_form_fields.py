"""Common form field definitions for task dialogs."""

from dataclasses import dataclass
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.validation import Length, Number, Regex
from textual.widgets import Checkbox, Input, Label, Static

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.constants.ui_settings import (
    DEFAULT_END_HOUR,
    DEFAULT_START_HOUR,
)
from taskdog.tui.forms.validators import DateTimeValidator
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.shared.constants.formats import DATETIME_FORMAT


@dataclass
class TaskFormData:
    """Data structure for task form input.

    Attributes:
        name: Task name
        priority: Task priority (higher = more important), or None if not set
        deadline: Optional deadline in format YYYY-MM-DD HH:MM:SS
        estimated_duration: Optional estimated duration in hours
        planned_start: Optional planned start date in format YYYY-MM-DD HH:MM:SS
        planned_end: Optional planned end date in format YYYY-MM-DD HH:MM:SS
        is_fixed: Whether task schedule is fixed (won't be rescheduled by optimizer)
        depends_on: List of task IDs this task depends on
        tags: List of tags for categorization and filtering
    """

    name: str
    priority: int | None = None
    deadline: str | None = None
    estimated_duration: float | None = None
    planned_start: str | None = None
    planned_end: str | None = None
    is_fixed: bool = False
    depends_on: list[int] | None = None
    tags: list[str] | None = None

    @staticmethod
    def parse_datetime(datetime_str: str | None) -> datetime | None:
        """Parse datetime string to datetime object.

        Args:
            datetime_str: Datetime string in YYYY-MM-DD HH:MM:SS format or None

        Returns:
            datetime object or None if datetime_str is None
        """
        if datetime_str is None:
            return None
        return datetime.strptime(datetime_str, DATETIME_FORMAT)

    def get_deadline(self) -> datetime | None:
        """Get deadline as datetime object."""
        return self.parse_datetime(self.deadline)

    def get_planned_start(self) -> datetime | None:
        """Get planned start as datetime object."""
        return self.parse_datetime(self.planned_start)

    def get_planned_end(self) -> datetime | None:
        """Get planned end as datetime object."""
        return self.parse_datetime(self.planned_end)


class TaskFormFields:
    """Reusable form fields for task dialogs.

    This class provides methods to generate common form fields
    used in both Add Task and Edit Task dialogs.
    """

    @staticmethod
    def compose_form_fields(task: TaskDetailDto | None = None) -> ComposeResult:
        """Compose task form fields.

        Args:
            task: Existing task for editing (None for new task)

        Yields:
            Form field widgets
        """
        # Error message area (hidden by default)
        yield Static("", id="error-message")

        with Vertical(id="form-container"):
            # Task name field (required)
            yield Label("Task Name [red]*[/red]:", classes="field-label", markup=True)
            yield Input(
                placeholder="Enter task name",
                id="task-name-input",
                value=task.name if task else "",
                validators=[Length(minimum=1)],
            )

            # Duration field
            yield Label("Duration (hours):", classes="field-label")
            yield Input(
                placeholder="Optional: 4, 2.5, 8",
                id="duration-input",
                value=str(task.estimated_duration)
                if task and task.estimated_duration
                else "",
                valid_empty=True,
                validators=[Number(minimum=0.1)],
            )

            # Deadline field
            yield Label("Deadline:", classes="field-label")
            yield Input(
                placeholder="Optional: 2025-12-31, tomorrow 6pm, next friday",
                id="deadline-input",
                value=DateTimeFormatter.format_datetime_for_export(task.deadline)
                if task and task.deadline
                else "",
                valid_empty=True,
                validators=[DateTimeValidator("deadline", DEFAULT_END_HOUR)],
            )

            # Planned Start field
            yield Label("Planned Start:", classes="field-label")
            yield Input(
                placeholder="Optional: 2025-11-01, tomorrow 9am, next monday",
                id="planned-start-input",
                value=DateTimeFormatter.format_datetime_for_export(task.planned_start)
                if task and task.planned_start
                else "",
                valid_empty=True,
                validators=[DateTimeValidator("planned start", DEFAULT_START_HOUR)],
            )

            # Planned End field
            yield Label("Planned End:", classes="field-label")
            yield Input(
                placeholder="Optional: 2025-11-15, in 2 weeks, friday 5pm",
                id="planned-end-input",
                value=DateTimeFormatter.format_datetime_for_export(task.planned_end)
                if task and task.planned_end
                else "",
                valid_empty=True,
                validators=[DateTimeValidator("planned end", DEFAULT_END_HOUR)],
            )

            # Priority field
            yield Label("Priority:", classes="field-label")
            yield Input(
                placeholder="Optional: 1, 5, 10 (higher = more important)",
                id="priority-input",
                value=str(task.priority) if task and task.priority is not None else "",
                valid_empty=True,
                validators=[Number(minimum=1)],
            )

            # Dependencies field
            yield Label("Dependencies:", classes="field-label")
            # Format current dependencies as comma-separated string
            depends_on_str = ""
            if task and task.depends_on:
                depends_on_str = ",".join(str(dep_id) for dep_id in task.depends_on)
            yield Input(
                placeholder="Optional: 1,2,3 (comma-separated task IDs)",
                id="dependencies-input",
                value=depends_on_str,
                valid_empty=True,
                validators=[Regex(r"^(\d+\s*,\s*)*\d+$")],
            )

            # Tags field
            yield Label("Tags:", classes="field-label")
            # Format current tags as comma-separated string
            tags_str = ""
            if task and task.tags:
                tags_str = ",".join(task.tags)
            yield Input(
                placeholder="Optional: work,urgent,client-a (comma-separated tags)",
                id="tags-input",
                value=tags_str,
                valid_empty=True,
                validators=[Regex(r"^([a-zA-Z0-9_-]+\s*,\s*)*[a-zA-Z0-9_-]+$")],
            )

            # Fixed field (checkbox)
            yield Label(
                "Fixed (won't be rescheduled by optimizer):", classes="field-label"
            )
            yield Checkbox(
                id="fixed-checkbox",
                value=task.is_fixed if task else False,
            )
