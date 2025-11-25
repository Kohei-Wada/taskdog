"""Confirmation dialog screen."""

from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label

from taskdog.tui.dialogs.base_dialog import BaseModalDialog


class ConfirmationDialog(BaseModalDialog[bool]):
    """Modal dialog for confirming actions with keyboard shortcuts."""

    BINDINGS: ClassVar = [
        Binding(
            "escape",
            "cancel",
            "Cancel",
            tooltip="Cancel the action and close the dialog",
        ),
        Binding("y", "confirm", "Yes", tooltip="Confirm the action"),
        Binding("n", "cancel", "No", tooltip="Cancel the action and close the dialog"),
    ]

    def __init__(self, title: str, message: str, *args: Any, **kwargs: Any):
        """Initialize the confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message
        """
        super().__init__(*args, **kwargs)
        self.title_text = title
        self.message_text = message

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Container(
            id="confirmation-dialog", classes="dialog-base dialog-compact"
        ) as container:
            container.border_title = self.title_text
            yield Label(
                "[dim]Y to confirm, N to cancel, Esc to cancel[/dim]",
                id="dialog-hint",
            )
            yield Label(self.message_text, id="dialog-message")

            with Horizontal(id="button-container"):
                yield Button("Yes (y)", variant="error", id="yes-button")
                yield Button("No (n)", variant="default", id="no-button")

    def on_mount(self) -> None:
        """Called when dialog is mounted."""
        # Focus on the "No" button by default (safer choice)
        no_button = self.query_one("#no-button", Button)
        no_button.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "yes-button":
            self.dismiss(True)
        elif event.button.id == "no-button":
            self.dismiss(False)

    def action_confirm(self) -> None:
        """Confirm action (y key)."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel action (n or escape key)."""
        self.dismiss(False)  # Override to return False instead of None
