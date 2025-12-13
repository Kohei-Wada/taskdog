"""Base dialog class for TUI modal screens."""

from abc import abstractmethod
from typing import Any, ClassVar, TypeVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.validation import Validator
from textual.widgets import Input, Static

T = TypeVar("T")
V = TypeVar("V", bound=Validator)


class BaseModalDialog(ModalScreen[T]):
    """Base class for modal dialog screens.

    Provides common functionality:
    - Escape key to cancel (dismiss with None)
    - Centered alignment (applied via CSS)
    - Standard dialog structure

    Subclasses should:
    - Implement compose() to define the dialog layout
    - Override on_mount() if custom initialization is needed
    - Call dismiss(result) when ready to close
    """

    BINDINGS: ClassVar = [
        Binding("escape", "cancel", "Cancel", tooltip="Cancel and close the dialog"),
    ]

    def action_cancel(self) -> None:
        """Cancel and close the dialog (Escape key).

        By default, dismisses with None. Override if different behavior is needed.
        """
        self.dismiss(None)

    def _show_validation_error(self, message: str, widget_to_focus: Any) -> None:
        """Show validation error and focus the relevant widget.

        This method expects the dialog to have a Static widget with id="error-message".
        If the widget is not found, only the focus operation will be performed.

        Args:
            message: Error message to display (will be formatted in red)
            widget_to_focus: Widget to focus after showing error
        """
        try:
            error_message = self.query_one("#error-message", Static)
            error_message.update(f"[red]Error: {message}[/red]")
        except Exception:
            # If error-message widget doesn't exist, skip error display
            # This allows dialogs without validation to not require the widget
            pass
        widget_to_focus.focus()

    def _clear_validation_error(self) -> None:
        """Clear validation error message.

        This method expects the dialog to have a Static widget with id="error-message".
        If the widget is not found, the operation will be silently ignored.
        """
        try:
            error_message = self.query_one("#error-message", Static)
            error_message.update("")
        except Exception:
            # If error-message widget doesn't exist, skip error clearing
            pass

    def _get_validator(self, input_widget: Input, validator_type: type[V]) -> V:
        """Get a validator of a specific type from an Input widget.

        Args:
            input_widget: Input widget to get validator from
            validator_type: Type of validator to find

        Returns:
            The validator instance of the specified type

        Raises:
            ValueError: If no validator of the specified type is found
        """
        for validator in input_widget.validators:
            if isinstance(validator, validator_type):
                return validator
        raise ValueError(f"Validator {validator_type.__name__} not found")

    def _is_input_valid(self, input_widget: Input) -> bool:
        """Check if an Input widget's value is valid.

        This method properly handles the valid_empty attribute:
        - If valid_empty=True and value is empty, returns True (bypasses validators)
        - Otherwise, returns the result of input_widget.is_valid

        Note: Textual validators may fail on empty strings even when valid_empty=True.
        This method provides the expected behavior where empty values are considered
        valid when the field is marked as optional (valid_empty=True).

        Args:
            input_widget: Input widget to validate

        Returns:
            True if the input is valid, False otherwise
        """
        if input_widget.valid_empty and not input_widget.value.strip():
            return True  # Empty is valid when valid_empty=True
        return bool(input_widget.is_valid)

    @abstractmethod
    def compose(self) -> ComposeResult:
        """Compose the dialog layout.

        Must be implemented by subclasses.
        """
        ...
