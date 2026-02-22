"""Base class for form dialogs with standard navigation."""

from abc import abstractmethod
from typing import ClassVar, TypeVar

from textual.binding import Binding
from textual.widgets import Input

from taskdog.tui.dialogs.base_dialog import BaseModalDialog

T = TypeVar("T")


class FormDialogBase(BaseModalDialog[T]):
    """Base class for form dialogs with standard navigation.

    Provides:
    - Ctrl+S to submit
    - Ctrl+J/K for field navigation (same as Tab/Shift+Tab)
    - Escape to cancel

    Subclasses must:
    - Implement compose() to define the form layout
    - Implement _submit_form() to validate and submit form data
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
        Binding(
            "ctrl+n",
            "accept_suggestion",
            "Accept suggestion",
            show=False,
            priority=True,
            tooltip="Accept auto-completion suggestion",
        ),
    ]

    def action_submit(self) -> None:
        """Submit the form (Ctrl+S)."""
        self._submit_form()

    def action_focus_next(self) -> None:
        """Move focus to the next field (Ctrl+J)."""
        self.focus_next()

    def action_focus_previous(self) -> None:
        """Move focus to the previous field (Ctrl+K)."""
        self.focus_previous()

    def action_accept_suggestion(self) -> None:
        """Accept auto-completion suggestion on the focused input (Ctrl+N)."""
        focused = self.focused
        if isinstance(focused, Input):
            focused.action_cursor_right()

    @abstractmethod
    def _submit_form(self) -> None:
        """Validate and submit the form data.

        Subclasses should:
        1. Get widget values via query_one()
        2. Validate each field
        3. Call dismiss(result) on success
        """
        ...
