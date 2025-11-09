"""Validators for collection fields (dependencies and tags)."""

from taskdog.constants.validation_messages import ValidationMessages
from taskdog.tui.forms.validators.base import BaseValidator, ValidationResult


class DependenciesValidator(BaseValidator):
    """Validator for task dependencies (comma-separated task IDs)."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate comma-separated task IDs.

        Args:
            value: Comma-separated task IDs (e.g., "1,2,3")

        Returns:
            ValidationResult with validation status, error message, and list of task IDs
        """
        dependencies_str = value.strip()

        # Empty string means no dependencies
        if not dependencies_str:
            return DependenciesValidator._success([])

        # Split by comma and parse each ID
        parts = [p.strip() for p in dependencies_str.split(",")]
        task_ids = []

        for part in parts:
            if not part:  # Skip empty parts
                continue

            try:
                task_id = int(part)
            except ValueError:
                return DependenciesValidator._error(
                    ValidationMessages.invalid_task_id(part)
                )

            if task_id <= 0:
                return DependenciesValidator._error(
                    ValidationMessages.invalid_task_id(part)
                )

            task_ids.append(task_id)

        # Remove duplicates while preserving order
        unique_ids = list(dict.fromkeys(task_ids))

        return DependenciesValidator._success(unique_ids)


class TagsValidator(BaseValidator):
    """Validator for task tags (comma-separated strings)."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate comma-separated tags.

        Args:
            value: Comma-separated tags (e.g., "work,urgent,client-a")

        Returns:
            ValidationResult with validation status, error message, and list of tags
        """
        tags_str = value.strip()

        # Empty string means no tags
        if not tags_str:
            return TagsValidator._success([])

        # Split by comma and parse each tag
        parts = [p.strip() for p in tags_str.split(",")]
        tags = []

        for part in parts:
            if not part:  # Skip empty parts
                continue

            # Check for empty tag
            if not part.strip():
                return TagsValidator._error(ValidationMessages.TAG_CANNOT_BE_EMPTY)

            tags.append(part)

        # Check for duplicates
        if len(tags) != len(set(tags)):
            return TagsValidator._error(ValidationMessages.TAGS_MUST_BE_UNIQUE)

        return TagsValidator._success(tags)
