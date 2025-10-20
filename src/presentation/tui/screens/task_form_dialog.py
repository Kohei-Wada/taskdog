"""Unified task form dialog for adding and editing tasks."""

from typing import Any, ClassVar

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
        # Get all form inputs
        inputs = {
            "task_name": self.query_one("#task-name-input", Input),
            "priority": self.query_one("#priority-input", Input),
            "deadline": self.query_one("#deadline-input", Input),
            "duration": self.query_one("#duration-input", Input),
            "planned_start": self.query_one("#planned-start-input", Input),
            "planned_end": self.query_one("#planned-end-input", Input),
            "dependencies": self.query_one("#dependencies-input", Input),
        }
        fixed_checkbox = self.query_one("#fixed-checkbox", Checkbox)
        error_message = self.query_one("#error-message", Static)

        # Clear previous error
        error_message.update("")

        # Define validation chain with (field_name, input_widget, validator, validator_args)
        default_priority = self.config.task.default_priority if self.config else 5
        validations: list[tuple[str, Input, Any, list[Any]]] = [
            ("task_name", inputs["task_name"], TaskNameValidator, []),
            ("priority", inputs["priority"], PriorityValidator, [default_priority]),
            ("deadline", inputs["deadline"], DeadlineValidator, []),
            ("duration", inputs["duration"], DurationValidator, []),
            ("planned_start", inputs["planned_start"], PlannedStartValidator, []),
            ("planned_end", inputs["planned_end"], PlannedEndValidator, []),
            ("dependencies", inputs["dependencies"], DependenciesValidator, []),
        ]

        # Run validations
        results: dict[str, Any] = {}
        for field_name, input_widget, validator, args in validations:
            result = validator.validate(input_widget.value, *args)
            if not result.is_valid:
                error_message.update(f"[red]Error: {result.error_message}[/red]")
                input_widget.focus()
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
        )

        # Submit the form data
        self.dismiss(form_data)
