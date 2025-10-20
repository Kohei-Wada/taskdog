"""Unified task form dialog for adding and editing tasks."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Checkbox, Input, Label, Static

from domain.entities.task import Task
from presentation.tui.forms.task_form_fields import TaskFormData, TaskFormFields
from presentation.tui.forms.validators import (
    DeadlineValidator,
    DependenciesValidator,
    DurationValidator,
    PlannedEndValidator,
    PlannedStartValidator,
    PriorityValidator,
    TaskNameValidator,
)
from presentation.tui.screens.base_dialog import BaseModalDialog
from shared.config_manager import Config


class TaskFormDialog(BaseModalDialog[TaskFormData | None]):
    """Unified modal dialog for adding or editing tasks.

    This dialog can be used for both creating new tasks and editing existing ones.
    Pass a Task instance to edit mode, or None for add mode.
    """

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Submit"),
    ]

    def __init__(self, task: Task | None = None, config: Config | None = None, *args, **kwargs):
        """Initialize the dialog.

        Args:
            task: Existing task for editing, or None for adding new task
            config: Application configuration
        """
        super().__init__(*args, **kwargs)
        self.task_to_edit = task
        self.is_edit_mode = task is not None
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        dialog_id = "edit-task-dialog" if self.is_edit_mode else "add-task-dialog"
        dialog_title = "Edit Task" if self.is_edit_mode else "Add New Task"

        with Container(id=dialog_id):
            yield Label(f"[bold cyan]{dialog_title}[/bold cyan]", id="dialog-title")
            yield Label(
                "[dim]Ctrl+S to submit, Esc to cancel, Tab to switch fields[/dim]",
                id="dialog-hint",
            )

            # Compose form fields using the common helper
            yield from TaskFormFields.compose_form_fields(self.task_to_edit, self.config)

    def on_mount(self) -> None:
        """Called when dialog is mounted."""
        # Focus on task name input
        task_input = self.query_one("#task-name-input", Input)
        task_input.focus()

    def action_submit(self) -> None:
        """Submit the form (Ctrl+S)."""
        self._submit_form()

    def _submit_form(self) -> None:
        """Validate and submit the form data."""
        task_name_input = self.query_one("#task-name-input", Input)
        priority_input = self.query_one("#priority-input", Input)
        deadline_input = self.query_one("#deadline-input", Input)
        duration_input = self.query_one("#duration-input", Input)
        planned_start_input = self.query_one("#planned-start-input", Input)
        planned_end_input = self.query_one("#planned-end-input", Input)
        dependencies_input = self.query_one("#dependencies-input", Input)
        fixed_checkbox = self.query_one("#fixed-checkbox", Checkbox)
        error_message = self.query_one("#error-message", Static)

        # Clear previous error
        error_message.update("")

        # Validate task name
        name_result = TaskNameValidator.validate(task_name_input.value)
        if not name_result.is_valid:
            error_message.update(f"[red]Error: {name_result.error_message}[/red]")
            task_name_input.focus()
            return

        # Validate priority
        default_priority = self.config.task.default_priority if self.config else 5
        priority_result = PriorityValidator.validate(priority_input.value, default_priority)
        if not priority_result.is_valid:
            error_message.update(f"[red]Error: {priority_result.error_message}[/red]")
            priority_input.focus()
            return

        # Validate deadline
        deadline_result = DeadlineValidator.validate(deadline_input.value)
        if not deadline_result.is_valid:
            error_message.update(f"[red]Error: {deadline_result.error_message}[/red]")
            deadline_input.focus()
            return

        # Validate duration
        duration_result = DurationValidator.validate(duration_input.value)
        if not duration_result.is_valid:
            error_message.update(f"[red]Error: {duration_result.error_message}[/red]")
            duration_input.focus()
            return

        # Validate planned start
        planned_start_result = PlannedStartValidator.validate(planned_start_input.value)
        if not planned_start_result.is_valid:
            error_message.update(f"[red]Error: {planned_start_result.error_message}[/red]")
            planned_start_input.focus()
            return

        # Validate planned end
        planned_end_result = PlannedEndValidator.validate(planned_end_input.value)
        if not planned_end_result.is_valid:
            error_message.update(f"[red]Error: {planned_end_result.error_message}[/red]")
            planned_end_input.focus()
            return

        # Validate dependencies
        dependencies_result = DependenciesValidator.validate(dependencies_input.value)
        if not dependencies_result.is_valid:
            error_message.update(f"[red]Error: {dependencies_result.error_message}[/red]")
            dependencies_input.focus()
            return

        # All validations passed - create form data
        form_data = TaskFormData(
            name=name_result.value,  # type: ignore
            priority=priority_result.value,  # type: ignore
            deadline=deadline_result.value,  # type: ignore
            estimated_duration=duration_result.value,  # type: ignore
            planned_start=planned_start_result.value,  # type: ignore
            planned_end=planned_end_result.value,  # type: ignore
            is_fixed=fixed_checkbox.value,
            depends_on=dependencies_result.value,  # type: ignore
        )

        # Submit the form data
        self.dismiss(form_data)
