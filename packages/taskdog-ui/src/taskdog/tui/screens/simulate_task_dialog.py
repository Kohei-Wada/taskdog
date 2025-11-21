"""Dialog for simulating task scheduling - extends TaskFormDialog."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Checkbox, Input, Label, Static

from taskdog.tui.forms import FormValidator
from taskdog.tui.forms.validators import (
    DateTimeValidator,
    DependenciesValidator,
    DurationValidator,
    PriorityValidator,
    TagsValidator,
    TaskNameValidator,
)
from taskdog.tui.screens.task_form_dialog import TaskFormDialog
from taskdog_core.shared.config_manager import Config
from taskdog_core.shared.constants.formats import DATETIME_FORMAT


@dataclass
class SimulateTaskFormData:
    """Data structure for simulate task form input.

    Attributes:
        name: Task name
        estimated_duration: Estimated duration in hours (required)
        priority: Task priority (1-10)
        deadline: Optional deadline in format YYYY-MM-DD HH:MM:SS
        is_fixed: Whether task schedule is fixed
        depends_on: List of task IDs this task depends on
        tags: List of tags for categorization
        max_hours_per_day: Maximum work hours per day
    """

    name: str
    estimated_duration: float
    priority: int
    deadline: str | None = None
    is_fixed: bool = False
    depends_on: list[int] | None = None
    tags: list[str] | None = None
    max_hours_per_day: float = 6.0

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


class SimulateTaskDialog(TaskFormDialog):
    """Modal dialog for simulating task scheduling.

    Extends TaskFormDialog to provide simulation-specific fields:
    - Requires estimated_duration (optional in base class)
    - Adds max_hours_per_day field (simulation parameter)
    - Removes planned_start/end fields (not needed for simulation)
    """

    BINDINGS: ClassVar = [
        Binding(
            "escape",
            "cancel",
            "Cancel",
            tooltip="Cancel and close the form without simulating",
        ),
        Binding(
            "ctrl+s",
            "submit",
            "Simulate",
            tooltip="Run simulation with these parameters",
        ),
        Binding(
            "ctrl+j",
            "focus_next",
            "Next field",
            priority=True,
            tooltip="Move to next form field",
        ),
        Binding(
            "ctrl+k",
            "focus_previous",
            "Previous field",
            priority=True,
            tooltip="Move to previous form field",
        ),
    ]

    def __init__(
        self,
        config: Config | None = None,
        **kwargs: Any,
    ):
        """Initialize the simulate dialog.

        Args:
            config: Application configuration
        """
        # Always initialize with task=None (simulate is always new)
        super().__init__(task=None, config=config, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the dialog layout for simulation.

        Overrides parent to provide simulation-specific fields.
        """
        with Container(
            id="simulate-task-dialog", classes="dialog-base dialog-standard"
        ) as container:
            container.border_title = "Simulate Task"
            yield Label(
                "[dim]Ctrl+S: simulate | Esc: cancel | Tab/Ctrl-j: next | Shift+Tab/Ctrl-k: previous[/dim]",
                id="dialog-hint",
            )

            # Error message area (hidden by default)
            yield Static("", id="error-message")

            # Get defaults from config
            default_priority = self.config.task.default_priority
            default_max_hours = self.config.optimization.max_hours_per_day

            with Vertical(id="form-container"):
                # Task name field
                yield Label("Task Name:", classes="field-label")
                yield Input(
                    placeholder="Enter task name",
                    id="task-name-input",
                    value="",
                )

                # Duration field (REQUIRED for simulation)
                yield Label("Duration (hours):", classes="field-label")
                yield Input(
                    placeholder="Required: 4, 2.5, 8",
                    id="duration-input",
                    value="",
                )

                # Deadline field
                yield Label("Deadline:", classes="field-label")
                yield Input(
                    placeholder="Optional: 2025-12-31, tomorrow 6pm, next friday",
                    id="deadline-input",
                    value="",
                )

                # Priority field
                yield Label("Priority:", classes="field-label")
                yield Input(
                    placeholder=f"Enter priority (default: {default_priority}, higher = more important)",
                    id="priority-input",
                    type="integer",
                    value="",
                )

                # Dependencies field
                yield Label("Dependencies:", classes="field-label")
                yield Input(
                    placeholder="Optional: 1,2,3 (comma-separated task IDs)",
                    id="depends-on-input",
                    value="",
                )

                # Tags field
                yield Label("Tags:", classes="field-label")
                yield Input(
                    placeholder="Optional: work,urgent,client-a (comma-separated tags)",
                    id="tags-input",
                    value="",
                )

                # Fixed field (checkbox)
                yield Label(
                    "Fixed (won't be rescheduled by optimizer):", classes="field-label"
                )
                yield Checkbox(
                    id="fixed-checkbox",
                    value=False,
                )

                # Max hours per day field (simulation-specific, at the end)
                yield Label("Max Hours Per Day:", classes="field-label")
                yield Input(
                    placeholder=f"Maximum work hours per day (default: {default_max_hours})",
                    id="max-hours-input",
                    value="",
                )

    def _submit_form(self) -> None:
        """Validate and submit the form data for simulation.

        Overrides parent to return SimulateTaskFormData instead of TaskFormData.
        """
        # Get fixed checkbox value
        fixed_checkbox = self.query_one("#fixed-checkbox", Checkbox)

        # Clear previous error
        self._clear_validation_error()

        # Build validation chain using FormValidator
        default_priority = self.config.task.default_priority
        default_end_hour = self.config.time.default_end_hour
        default_max_hours = self.config.optimization.max_hours_per_day

        validator = FormValidator(self)
        validator.add_field("task_name", "task-name-input", TaskNameValidator)
        validator.add_field("duration", "duration-input", DurationValidator)
        validator.add_field(
            "deadline",
            "deadline-input",
            DateTimeValidator,
            "deadline",
            default_end_hour,
        )
        validator.add_field(
            "priority", "priority-input", PriorityValidator, default_priority
        )
        validator.add_field("depends_on", "depends-on-input", DependenciesValidator)
        validator.add_field("tags", "tags-input", TagsValidator)

        # Validate all fields
        results = validator.validate_all()
        if results is None:
            return  # Validation failed, error already displayed

        # Check that duration is provided (REQUIRED for simulation)
        if results["duration"] is None:
            duration_input = self.query_one("#duration-input", Input)
            self._show_validation_error(
                "Duration is required for simulation", duration_input
            )
            return

        # Get and validate max hours per day (last field)
        max_hours_input = self.query_one("#max-hours-input", Input)
        max_hours_str = max_hours_input.value.strip()

        try:
            max_hours_per_day = (
                float(max_hours_str) if max_hours_str else default_max_hours
            )
            if max_hours_per_day <= 0 or max_hours_per_day > 24:
                self._show_validation_error(
                    "Max hours per day must be between 0 and 24", max_hours_input
                )
                return
        except ValueError:
            self._show_validation_error("Invalid max hours per day", max_hours_input)
            return

        # Build SimulateTaskFormData (not TaskFormData)
        form_data = SimulateTaskFormData(
            name=results["task_name"],
            estimated_duration=results["duration"],
            priority=results["priority"],
            deadline=results.get("deadline"),
            is_fixed=fixed_checkbox.value,
            depends_on=results.get("depends_on"),
            tags=results.get("tags"),
            max_hours_per_day=max_hours_per_day,
        )

        # Close dialog and return simulate-specific form data
        self.dismiss(form_data)  # type: ignore[arg-type]
