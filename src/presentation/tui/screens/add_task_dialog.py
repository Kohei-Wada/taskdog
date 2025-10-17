"""Add task dialog screen."""

from typing import ClassVar

from dateutil import parser as dateutil_parser
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Input, Label, Static

from presentation.tui.screens.base_dialog import BaseModalDialog


class AddTaskDialog(BaseModalDialog[tuple[str, int, str | None] | None]):
    """Modal dialog for adding a new task with keyboard shortcuts."""

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Submit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Container(id="add-task-dialog"):
            yield Label("[bold cyan]Add New Task[/bold cyan]", id="dialog-title")
            yield Label(
                "[dim]Ctrl+S to submit, Esc to cancel, Tab to switch fields[/dim]",
                id="dialog-hint",
            )

            # Error message area
            yield Static("", id="error-message")

            with Vertical(id="form-container"):
                yield Label("Task Name:", classes="field-label")
                yield Input(placeholder="Enter task name", id="task-name-input")

                yield Label("Priority (1-10):", classes="field-label")
                yield Input(
                    placeholder="Enter priority (default: 5)",
                    id="priority-input",
                    type="integer",
                )

                yield Label("Deadline:", classes="field-label")
                yield Input(
                    placeholder="Optional: 2025-12-31, tomorrow 6pm, next friday",
                    id="deadline-input",
                )

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
        error_message = self.query_one("#error-message", Static)

        # Clear previous error
        error_message.update("")

        # Validate task name
        task_name = task_name_input.value.strip()
        if not task_name:
            error_message.update("[red]Error: Task name is required[/red]")
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
                    error_message.update("[red]Error: Priority must be between 1 and 10[/red]")
                    priority_input.focus()
                    return
            except ValueError:
                error_message.update("[red]Error: Priority must be a number[/red]")
                priority_input.focus()
                return

        # Validate deadline (optional)
        deadline_str = deadline_input.value.strip()
        deadline = None
        if deadline_str:
            try:
                # Parse flexible date formats using dateutil
                parsed_date = dateutil_parser.parse(deadline_str, fuzzy=True)
                # Convert to the standard format YYYY-MM-DD HH:MM:SS
                deadline = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                error_message.update(
                    "[red]Error: Invalid deadline format. Examples: 2025-12-31, tomorrow 6pm[/red]"
                )
                deadline_input.focus()
                return

        # Submit the form data
        self.dismiss((task_name, priority, deadline))
