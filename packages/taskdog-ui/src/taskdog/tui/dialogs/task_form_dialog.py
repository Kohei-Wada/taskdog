"""Unified task form dialog for adding and editing tasks."""

from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Checkbox, Input, Label

from taskdog.tui.dialogs.form_dialog import FormDialogBase
from taskdog.tui.forms.task_form_fields import TaskFormData, TaskFormFields
from taskdog.tui.forms.validators import DateTimeValidator
from taskdog_core.application.dto.task_dto import TaskDetailDto

if TYPE_CHECKING:
    from taskdog.infrastructure.cli_config_manager import InputDefaultsConfig


class TaskFormDialog(FormDialogBase[TaskFormData | None]):
    """Unified modal dialog for adding or editing tasks.

    This dialog can be used for both creating new tasks and editing existing ones.
    Pass a TaskDetailDto instance to edit mode, or None for add mode.
    """

    def __init__(
        self,
        task: TaskDetailDto | None = None,
        input_defaults: "InputDefaultsConfig | None" = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the dialog.

        Args:
            task: Existing task DTO for editing, or None for adding new task
            input_defaults: UI input completion defaults (uses hardcoded defaults if None)
        """
        super().__init__(*args, **kwargs)
        self.task_to_edit = task
        self.is_edit_mode = task is not None
        self._input_defaults = input_defaults

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
                self.task_to_edit, self._input_defaults
            )

    def on_mount(self) -> None:
        """Called when dialog is mounted."""
        # Focus on task name input
        task_input = self.query_one("#task-name-input", Input)
        task_input.focus()

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

        # Parse priority (optional, can be None)
        # Validate numeric fields before parsing
        if not self._is_input_valid(priority_input):
            priority_input.focus()
            return

        if not self._is_input_valid(duration_input):
            duration_input.focus()
            return

        priority_str = priority_input.value.strip()
        priority = int(priority_str) if priority_str else None

        # Parse duration (optional)
        duration_str = duration_input.value.strip()
        duration = float(duration_str) if duration_str else None

        # Validate datetime fields before parsing
        if not self._is_input_valid(deadline_input):
            deadline_input.focus()
            return

        if not self._is_input_valid(planned_start_input):
            planned_start_input.focus()
            return

        if not self._is_input_valid(planned_end_input):
            planned_end_input.focus()
            return

        # Parse datetime fields using validators registered on Input widgets
        deadline = self._get_validator(deadline_input, DateTimeValidator).parse(
            deadline_input.value
        )
        planned_start = self._get_validator(
            planned_start_input, DateTimeValidator
        ).parse(planned_start_input.value)
        planned_end = self._get_validator(planned_end_input, DateTimeValidator).parse(
            planned_end_input.value
        )

        # Validate dependencies and tags before parsing
        if not self._is_input_valid(dependencies_input):
            dependencies_input.focus()
            return

        if not self._is_input_valid(tags_input):
            tags_input.focus()
            return

        # Parse dependencies (optional)
        dependencies_str = dependencies_input.value.strip()
        if dependencies_str:
            dependencies = [
                int(x.strip()) for x in dependencies_str.split(",") if x.strip()
            ]
        else:
            dependencies = []

        # Parse tags (optional)
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
