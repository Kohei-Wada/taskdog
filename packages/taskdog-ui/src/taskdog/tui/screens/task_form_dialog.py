"""Unified task form dialog for adding and editing tasks."""

from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Checkbox, Input, Label

from taskdog.tui.forms import FormValidator
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


class TaskFormDialog(BaseModalDialog[TaskFormData | None]):
    """Unified modal dialog for adding or editing tasks.

    This dialog can be used for both creating new tasks and editing existing ones.
    Pass a TaskDetailDto instance to edit mode, or None for add mode.
    """

    BINDINGS: ClassVar = [
        Binding(
            "escape",
            "cancel",
            "Cancel",
            tooltip="Cancel and close the form without saving",
        ),
        Binding(
            "ctrl+s", "submit", "Submit", tooltip="Submit the form and save changes"
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
        task: TaskDetailDto | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the dialog.

        Args:
            task: Existing task DTO for editing, or None for adding new task
        """
        super().__init__(*args, **kwargs)
        self.task_to_edit = task
        self.is_edit_mode = task is not None

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
            yield from TaskFormFields.compose_form_fields(self.task_to_edit)

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
        # Get fixed checkbox value
        fixed_checkbox = self.query_one("#fixed-checkbox", Checkbox)

        # Clear previous error
        self._clear_validation_error()

        # Build validation chain using FormValidator
        # Use centralized UI defaults for form validation
        # Server will apply actual config defaults when creating/updating tasks
        from taskdog.tui.constants.ui_settings import (
            DEFAULT_BUSINESS_END_HOUR,
            DEFAULT_BUSINESS_START_HOUR,
            DEFAULT_TASK_PRIORITY,
        )

        validator = FormValidator(self)
        validator.add_field("task_name", "task-name-input", TaskNameValidator)
        validator.add_field(
            "priority", "priority-input", PriorityValidator, DEFAULT_TASK_PRIORITY
        )
        validator.add_field(
            "deadline",
            "deadline-input",
            DateTimeValidator,
            "deadline",
            DEFAULT_BUSINESS_END_HOUR,
        )
        validator.add_field("duration", "duration-input", DurationValidator)
        validator.add_field(
            "planned_start",
            "planned-start-input",
            DateTimeValidator,
            "planned start",
            DEFAULT_BUSINESS_START_HOUR,
        )
        validator.add_field(
            "planned_end",
            "planned-end-input",
            DateTimeValidator,
            "planned end",
            DEFAULT_BUSINESS_END_HOUR,
        )
        validator.add_field("dependencies", "dependencies-input", DependenciesValidator)
        validator.add_field("tags", "tags-input", TagsValidator)

        # Run validations
        results = validator.validate_all()
        if results is None:
            return  # Validation failed, error already displayed

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
