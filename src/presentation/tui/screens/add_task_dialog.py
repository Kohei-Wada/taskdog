"""Add task dialog screen."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class AddTaskDialog(ModalScreen[tuple[str, int] | None]):
    """Modal dialog for adding a new task with Vi-style navigation."""

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Submit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Container(id="add-task-dialog"):
            yield Label("[bold cyan]Add New Task[/bold cyan]", id="dialog-title")

            with Vertical(id="form-container"):
                yield Label("Task Name:", classes="field-label")
                yield Input(placeholder="Enter task name", id="task-name-input")

                yield Label("Priority (1-10):", classes="field-label")
                yield Input(
                    placeholder="Enter priority (default: 5)",
                    id="priority-input",
                    type="integer",
                )

            with Vertical(id="button-container"):
                yield Button("Submit (Ctrl+S)", variant="primary", id="submit-button")
                yield Button("Cancel (Esc)", variant="default", id="cancel-button")

    def on_mount(self) -> None:
        """Called when dialog is mounted."""
        # Focus on task name input
        task_input = self.query_one("#task-name-input", Input)
        task_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "submit-button":
            self._submit_form()
        elif event.button.id == "cancel-button":
            self.dismiss(None)

    def action_submit(self) -> None:
        """Submit the form (Ctrl+S)."""
        self._submit_form()

    def action_cancel(self) -> None:
        """Cancel and close the dialog (Escape)."""
        self.dismiss(None)

    def _submit_form(self) -> None:
        """Validate and submit the form data."""
        task_name_input = self.query_one("#task-name-input", Input)
        priority_input = self.query_one("#priority-input", Input)

        # Validate task name
        task_name = task_name_input.value.strip()
        if not task_name:
            task_name_input.focus()
            return

        # Validate and parse priority
        priority_str = priority_input.value.strip()
        if not priority_str:
            priority = 5  # Default priority
        else:
            try:
                priority = int(priority_str)
                if priority < 1 or priority > 10:
                    priority_input.focus()
                    return
            except ValueError:
                priority_input.focus()
                return

        # Submit the form data
        self.dismiss((task_name, priority))
