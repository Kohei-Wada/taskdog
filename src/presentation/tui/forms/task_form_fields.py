"""Common form field definitions for task dialogs."""

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Checkbox, Input, Label, Static

from domain.entities.task import Task
from shared.config_manager import Config


@dataclass
class TaskFormData:
    """Data structure for task form input.

    Attributes:
        name: Task name
        priority: Task priority (1-10)
        deadline: Optional deadline in format YYYY-MM-DD HH:MM:SS
        estimated_duration: Optional estimated duration in hours
        is_fixed: Whether task schedule is fixed (won't be rescheduled by optimizer)
        depends_on: List of task IDs this task depends on
    """

    name: str
    priority: int
    deadline: str | None = None
    estimated_duration: float | None = None
    is_fixed: bool = False
    depends_on: list[int] | None = None


class TaskFormFields:
    """Reusable form fields for task dialogs.

    This class provides methods to generate common form fields
    used in both Add Task and Edit Task dialogs.
    """

    @staticmethod
    def compose_form_fields(
        task: Task | None = None, config: Config | None = None
    ) -> ComposeResult:
        """Compose task form fields.

        Args:
            task: Existing task for editing (None for new task)
            config: Application configuration

        Yields:
            Form field widgets
        """
        # Error message area (hidden by default)
        yield Static("", id="error-message")

        # Get default priority from config
        default_priority = config.task.default_priority if config else 5

        with Vertical(id="form-container"):
            # Task name field
            yield Label("Task Name:", classes="field-label")
            yield Input(
                placeholder="Enter task name",
                id="task-name-input",
                value=task.name if task else "",
            )

            # Priority field
            yield Label("Priority:", classes="field-label")
            yield Input(
                placeholder=f"Enter priority (default: {default_priority}, higher = more important)",
                id="priority-input",
                type="integer",
                value=str(task.priority) if task else "",
            )

            # Deadline field
            yield Label("Deadline:", classes="field-label")
            yield Input(
                placeholder="Optional: 2025-12-31, tomorrow 6pm, next friday",
                id="deadline-input",
                value=task.deadline if task and task.deadline else "",
            )

            # Duration field
            yield Label("Duration (hours):", classes="field-label")
            yield Input(
                placeholder="Optional: 4, 2.5, 8",
                id="duration-input",
                value=str(task.estimated_duration) if task and task.estimated_duration else "",
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
            )

            # Fixed field (checkbox)
            yield Checkbox(
                "Fixed (won't be rescheduled by optimizer)",
                id="fixed-checkbox",
                value=task.is_fixed if task else False,
            )
