"""Unified task form dialog for adding and editing tasks."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Input, Label, Static

from domain.entities.task import Task
from presentation.tui.forms.task_form_fields import TaskFormData, TaskFormFields
from presentation.tui.forms.validators import (
    DeadlineValidator,
    DurationValidator,
    PriorityValidator,
    TaskNameValidator,
)
from presentation.tui.screens.base_dialog import BaseModalDialog


class TaskFormDialog(BaseModalDialog[TaskFormData | None]):
    """Unified modal dialog for adding or editing tasks.

    This dialog can be used for both creating new tasks and editing existing ones.
    Pass a Task instance to edit mode, or None for add mode.
    """

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Submit"),
    ]

    def __init__(self, task: Task | None = None, *args, **kwargs):
        """Initialize the dialog.

        Args:
            task: Existing task for editing, or None for adding new task
        """
        super().__init__(*args, **kwargs)
        self.task_to_edit = task
        self.is_edit_mode = task is not None

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
            yield from TaskFormFields.compose_form_fields(self.task_to_edit)

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
        priority_result = PriorityValidator.validate(priority_input.value)
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

        # All validations passed - create form data
        form_data = TaskFormData(
            name=name_result.value,  # type: ignore
            priority=priority_result.value,  # type: ignore
            deadline=deadline_result.value,  # type: ignore
            estimated_duration=duration_result.value,  # type: ignore
        )

        # Submit the form data
        self.dismiss(form_data)
