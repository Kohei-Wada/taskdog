"""Form validation orchestration for TUI forms."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from textual.widgets import Input

from taskdog.tui.forms.validators import BaseValidator, ValidationResult

if TYPE_CHECKING:
    from taskdog.tui.screens.base_dialog import BaseModalDialog


@dataclass
class FormField:
    """Represents a form field with its validation rules.

    Attributes:
        name: Field name for the result dictionary
        widget_id: CSS selector ID for the input widget
        validator: Validator class to use for this field
        args: Arguments to pass to the validator
    """

    name: str
    widget_id: str
    validator: type[BaseValidator]
    args: list[Any]


class FormValidator:
    """Orchestrates validation of multiple form fields.

    This class provides a fluent API for building and executing
    a validation chain for form inputs. It handles error display
    and result collection.

    Example:
        validator = FormValidator(dialog)
        validator.add_field("task_name", "task-name-input", TaskNameValidator)
        validator.add_field("priority", "priority-input", PriorityValidator, default_priority)

        results = validator.validate_all()
        if results is None:
            return  # Validation failed, error already displayed

        # Use validated results
        form_data = TaskFormData(**results)
    """

    def __init__(
        self,
        screen: "BaseModalDialog[Any]",
        error_callback: Callable[[str, Input | None], None] | None = None,
    ):
        """Initialize the form validator.

        Args:
            screen: The modal dialog screen containing the form
            error_callback: Optional custom error display callback.
                           Defaults to screen._show_validation_error.
                           The widget parameter may be None if widget not found.
        """
        self.screen = screen
        self.fields: list[FormField] = []
        self.error_callback = error_callback or screen._show_validation_error

    def add_field(
        self,
        name: str,
        widget_id: str,
        validator: type[BaseValidator],
        *args: Any,
    ) -> "FormValidator":
        """Add a field to the validation chain.

        Args:
            name: Field name for the result dictionary
            widget_id: CSS selector ID for the input widget
            validator: Validator class to use
            *args: Arguments to pass to the validator's validate method

        Returns:
            Self for method chaining
        """
        self.fields.append(FormField(name, widget_id, validator, list(args)))
        return self

    def validate_all(self) -> dict[str, Any] | None:
        """Validate all registered fields in order.

        If any validation fails, the error is displayed via the error callback
        and validation stops.

        Returns:
            Dictionary mapping field names to validated values, or None if
            any validation failed
        """
        results: dict[str, Any] = {}

        for field in self.fields:
            # Query the input widget
            try:
                widget = self.screen.query_one(f"#{field.widget_id}", Input)
            except Exception:
                # Widget not found - this is a validation error
                error_msg = f"Required field '{field.name}' widget not found"
                self.error_callback(error_msg, None)
                return None

            # Run validation
            result: ValidationResult = field.validator.validate(
                widget.value, *field.args
            )

            # Handle validation failure
            if not result.is_valid:
                self.error_callback(result.error_message, widget)
                return None

            # Store validated value
            results[field.name] = result.value

        return results
