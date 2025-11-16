"""Unified task form dialog for adding and editing tasks."""

from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Checkbox, Input, Label

from taskdog.tui.forms.task_form_fields import TaskFormData, TaskFormFields
from taskdog.tui.forms.validators import (
    DateTimeValidator,
    DependenciesValidator,
    DurationValidator,
    PriorityValidator,
    TagsValidator,
    TaskNameValidator,
)
from taskdog.tui.screens.base_dialog import BaseModalDialog
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.shared.config_manager import Config


class TaskFormDialog(BaseModalDialog[TaskFormData | None]):
    """Unified modal dialog for adding or editing tasks.

    This dialog can be used for both creating new tasks and editing existing ones.
    Pass a TaskDetailDto instance to edit mode, or None for add mode.
    """

    BINDINGS: ClassVar = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Submit"),
        Binding("ctrl+j", "focus_next", "Next field", priority=True),
        Binding("ctrl+k", "focus_previous", "Previous field", priority=True),
    ]

    def __init__(
        self,
        task: TaskDetailDto | None = None,
        config: Config | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the dialog.

        Args:
            task: Existing task DTO for editing, or None for adding new task
            config: Application configuration
        """
        super().__init__(*args, **kwargs)
        self.task_to_edit = task
        self.is_edit_mode = task is not None
        if config is None:
            raise ValueError("config parameter is required")
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        dialog_id = "edit-task-dialog" if self.is_edit_mode else "add-task-dialog"
        dialog_title = "Edit Task" if self.is_edit_mode else "Add New Task"

        with Container(
            id=dialog_id, classes="dialog-base dialog-standard"
        ) as container:
            container.border_title = dialog_title
            yield Label(
                "[dim]Ctrl+S: submit | Esc: cancel | Tab/Ctrl-j: next | Shift+Tab/Ctrl-k: previous[/dim]",
                id="dialog-hint",
            )

            # Compose form fields using the common helper
            yield from TaskFormFields.compose_form_fields(
                self.task_to_edit, self.config
            )

    def on_mount(self) -> None:
        """Called when dialog is mounted."""
        # Focus on task name input
        task_input = self.query_one("#task-name-input", Input)
        task_input.focus()

    def action_submit(self) -> None:
        """Submit the form (Ctrl+S)."""
        self._submit_form()

    def action_focus_next(self) -> None:
        """Move focus to the next field (Ctrl+J)."""
        self.focus_next()

    def action_focus_previous(self) -> None:
        """Move focus to the previous field (Ctrl+K)."""
        self.focus_previous()

    def _submit_form(self) -> None:
        """Validate and submit the form data."""
        # Get all form inputs
        inputs = {
            "task_name": self.query_one("#task-name-input", Input),
            "priority": self.query_one("#priority-input", Input),
            "deadline": self.query_one("#deadline-input", Input),
            "duration": self.query_one("#duration-input", Input),
            "planned_start": self.query_one("#planned-start-input", Input),
            "planned_end": self.query_one("#planned-end-input", Input),
            "dependencies": self.query_one("#dependencies-input", Input),
            "tags": self.query_one("#tags-input", Input),
        }
        fixed_checkbox = self.query_one("#fixed-checkbox", Checkbox)

        # Clear previous error
        self._clear_validation_error()

        # Define validation chain with (field_name, input_widget, validator, validator_args)
        # Config is always available (loaded in __init__ if None)
        default_priority = self.config.task.default_priority
        default_start_hour = self.config.time.default_start_hour
        default_end_hour = self.config.time.default_end_hour
        validations: list[tuple[str, Input, Any, list[Any]]] = [
            ("task_name", inputs["task_name"], TaskNameValidator, []),
            ("priority", inputs["priority"], PriorityValidator, [default_priority]),
            (
                "deadline",
                inputs["deadline"],
                DateTimeValidator,
                ["deadline", default_end_hour],
            ),
            ("duration", inputs["duration"], DurationValidator, []),
            (
                "planned_start",
                inputs["planned_start"],
                DateTimeValidator,
                ["planned start", default_start_hour],
            ),
            (
                "planned_end",
                inputs["planned_end"],
                DateTimeValidator,
                ["planned end", default_end_hour],
            ),
            ("dependencies", inputs["dependencies"], DependenciesValidator, []),
            ("tags", inputs["tags"], TagsValidator, []),
        ]

        # Run validations
        results: dict[str, Any] = {}
        for field_name, input_widget, validator, args in validations:
            result = validator.validate(input_widget.value, *args)
            if not result.is_valid:
                self._show_validation_error(result.error_message, input_widget)
                return
            results[field_name] = result.value

        # All validations passed - create form data
        form_data = TaskFormData(
            name=results["task_name"],
            priority=results["priority"],
            deadline=results["deadline"],
            estimated_duration=results["duration"],
            planned_start=results["planned_start"],
            planned_end=results["planned_end"],
            is_fixed=fixed_checkbox.value,
            depends_on=results["dependencies"],
            tags=results["tags"],
        )

        # Submit the form data
        self.dismiss(form_data)
