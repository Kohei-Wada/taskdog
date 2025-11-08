"""Validation error message constants for TUI forms.

Centralizes all validation error messages for:
- Consistency across validators
- Easy maintenance and updates
- Future internationalization support
"""


class ValidationMessages:
    """Validation error messages used across form validators."""

    # Task name validation
    TASK_NAME_REQUIRED = "Task name is required"

    # Priority validation
    PRIORITY_MUST_BE_NUMBER = "Priority must be a number"
    PRIORITY_MUST_BE_POSITIVE = "Priority must be greater than 0"

    # Duration validation
    DURATION_MUST_BE_NUMBER = "Duration must be a number"
    DURATION_MUST_BE_POSITIVE = "Duration must be greater than 0"
    DURATION_MAX_EXCEEDED = "Duration must be 999 hours or less"

    # Tag validation
    TAG_CANNOT_BE_EMPTY = "Tag cannot be empty"
    TAGS_MUST_BE_UNIQUE = "Tags must be unique"

    @staticmethod
    def invalid_date_format(field_name: str, examples: str) -> str:
        """Generate invalid date format error message.

        Args:
            field_name: Name of the date field (e.g., "deadline", "planned start")
            examples: Examples of valid formats

        Returns:
            Formatted error message
        """
        return f"Invalid {field_name} format. Examples: {examples}"

    @staticmethod
    def invalid_task_id(value: str) -> str:
        """Generate invalid task ID error message.

        Args:
            value: The invalid task ID value

        Returns:
            Formatted error message
        """
        return f"Invalid task ID: '{value}'. Must be a number."

    @staticmethod
    def task_not_found(task_id: int) -> str:
        """Generate task not found error message.

        Args:
            task_id: The task ID that was not found

        Returns:
            Formatted error message
        """
        return f"Task #{task_id} not found"
