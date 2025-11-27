"""Unified task form dialog for adding and editing tasks."""

from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Checkbox, Input, Label

from taskdog.tui.dialogs.base_dialog import BaseModalDialog
from taskdog.tui.forms.task_form_fields import TaskFormData, TaskFormFields
from taskdog.tui.forms.validators import DateTimeValidator
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
        # Get widget values directly (validated by Textual built-in validators)
        task_name_input = self.query_one("#task-name-input", Input)
        priority_input = self.query_one("#priority-input", Input)
        duration_input = self.query_one("#duration-input", Input)
        deadline_input = self.query_one("#deadline-input", Input)
        planned_start_input = self.query_one("#planned-start-input", Input)
        planned_end_input = self.query_one("#planned-end-input", Input)
        dependencies_input = self.query_one("#dependencies-input", Input)
        tags_input = self.query_one("#tags-input", Input)
        fixed_checkbox = self.query_one("#fixed-checkbox", Checkbox)

        # Clear previous error
        self._clear_validation_error()

        # Validate task name (required field)
        task_name = task_name_input.value.strip()
        if not task_name:
            self._show_validation_error("Task name is required", task_name_input)
            return

        # Parse priority (optional, defaults to config value)
        # Validation is handled by Textual's Number validator
        from taskdog.tui.constants.ui_settings import (
            DEFAULT_END_HOUR,
            DEFAULT_START_HOUR,
            DEFAULT_TASK_PRIORITY,
        )

        priority_str = priority_input.value.strip()
        priority = int(priority_str) if priority_str else DEFAULT_TASK_PRIORITY

        # Parse duration (optional, validated by Textual's Number validator)
        duration_str = duration_input.value.strip()
        duration = float(duration_str) if duration_str else None

        # Parse datetime fields using DateTimeValidator.parse()
        deadline_validator = DateTimeValidator("deadline", DEFAULT_END_HOUR)
        planned_start_validator = DateTimeValidator("planned start", DEFAULT_START_HOUR)
        planned_end_validator = DateTimeValidator("planned end", DEFAULT_END_HOUR)

        deadline = deadline_validator.parse(deadline_input.value)
        planned_start = planned_start_validator.parse(planned_start_input.value)
        planned_end = planned_end_validator.parse(planned_end_input.value)

        # Parse dependencies (optional, validated by Textual's Regex validator)
        dependencies_str = dependencies_input.value.strip()
        if dependencies_str:
            dependencies = [
                int(x.strip()) for x in dependencies_str.split(",") if x.strip()
            ]
        else:
            dependencies = []

        # Parse tags (optional, validated by Textual's Regex validator)
        tags_str = tags_input.value.strip()
        tags = [x.strip() for x in tags_str.split(",") if x.strip()] if tags_str else []

        # All validations passed - create form data
        form_data = TaskFormData(
            name=task_name,
            priority=priority,
            deadline=deadline,
            estimated_duration=duration,
            planned_start=planned_start,
            planned_end=planned_end,
            is_fixed=fixed_checkbox.value,
            depends_on=dependencies,
            tags=tags,
        )

        # Submit the form data
        self.dismiss(form_data)
