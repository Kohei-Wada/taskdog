"""Tests for NumericFieldValidator."""

import unittest
from unittest.mock import Mock

from parameterized import parameterized

from taskdog_core.application.validators.numeric_field_validator import (
    NumericFieldValidator,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


class TestNumericFieldValidator(unittest.TestCase):
    """Test cases for NumericFieldValidator."""

    def setUp(self):
        """Initialize mock repository and task for each test."""
        self.mock_repository = Mock()
        self.task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=5)

    @parameterized.expand(
        [
            # Valid cases - (field_name, value, expected_error_fragment)
            ("estimated_duration", 10, None),
            ("estimated_duration", 100, None),
            ("estimated_duration", 10.5, None),
            ("estimated_duration", 0.5, None),
            ("estimated_duration", 0.1, None),
            ("estimated_duration", None, None),  # None is valid (clearing field)
            ("estimated_duration", True, None),  # True == 1 in Python
            ("priority", 100, None),
            ("priority", 5.5, None),
            ("priority", 1, None),
            ("priority", None, None),
            ("priority", True, None),
            # Invalid cases - zero values
            ("estimated_duration", 0, "Estimated duration must be greater than 0"),
            ("estimated_duration", 0.0, "Estimated duration must be greater than 0"),
            ("priority", 0, "Priority must be greater than 0"),
            ("priority", 0.0, "Priority must be greater than 0"),
            ("estimated_duration", False, "must be greater than 0"),  # False == 0
            # Invalid cases - negative values
            ("estimated_duration", -5, "Estimated duration must be greater than 0"),
            ("estimated_duration", -5.5, "Estimated duration must be greater than 0"),
            ("priority", -10, "Priority must be greater than 0"),
            ("priority", -1.5, "Priority must be greater than 0"),
            # Invalid cases - wrong types
            ("estimated_duration", "10", "Invalid type for estimated_duration"),
            ("estimated_duration", [10], "Invalid type for estimated_duration"),
            ("priority", "high", "Invalid type for priority"),
            ("priority", {"value": 10}, "Invalid type for priority"),
        ]
    )
    def test_numeric_field_validation(self, field_name, value, expected_error_fragment):
        """Test validation of numeric fields with various inputs."""
        validator = NumericFieldValidator(field_name)

        if expected_error_fragment is None:
            # Should pass validation without raising
            validator.validate(value, self.task, self.mock_repository)
        else:
            # Should raise TaskValidationError with expected message
            with self.assertRaises(TaskValidationError) as context:
                validator.validate(value, self.task, self.mock_repository)
            self.assertIn(expected_error_fragment, str(context.exception))
            # Also verify the value appears in error message for specific values
            if value not in (None, True, False) and not isinstance(
                value, list | dict | str
            ):
                self.assertIn(str(value), str(context.exception))

    def test_field_name_formatting_in_error_message(self):
        """Test that field names are properly formatted in error messages."""
        validator = NumericFieldValidator("estimated_duration")

        with self.assertRaises(TaskValidationError) as context:
            validator.validate(0, self.task, self.mock_repository)

        error_message = str(context.exception)
        # Should contain user-friendly "Estimated duration" (not "estimated_duration")
        self.assertIn("Estimated duration", error_message)


if __name__ == "__main__":
    unittest.main()
