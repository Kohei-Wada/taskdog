"""Tests for NumericFieldValidator."""

import unittest
from unittest.mock import Mock

from taskdog_core.application.validators.numeric_field_validator import (
    NumericFieldValidator,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


class TestNumericFieldValidator(unittest.TestCase):
    """Test cases for NumericFieldValidator."""

    def setUp(self):
        """Initialize validators and mock repository for each test."""
        self.estimated_duration_validator = NumericFieldValidator("estimated_duration")
        self.priority_validator = NumericFieldValidator("priority")
        self.mock_repository = Mock()
        self.task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=5)

    def test_validate_positive_integer_success(self):
        """Test that positive integer values are accepted."""
        # estimated_duration
        self.estimated_duration_validator.validate(10, self.task, self.mock_repository)

        # priority
        self.priority_validator.validate(100, self.task, self.mock_repository)

    def test_validate_positive_float_success(self):
        """Test that positive float values are accepted."""
        # estimated_duration
        self.estimated_duration_validator.validate(
            10.5, self.task, self.mock_repository
        )
        self.estimated_duration_validator.validate(0.5, self.task, self.mock_repository)

        # priority (although typically int, should accept float)
        self.priority_validator.validate(5.5, self.task, self.mock_repository)

    def test_validate_zero_raises_error(self):
        """Test that zero values are rejected."""
        # estimated_duration
        with self.assertRaises(TaskValidationError) as context:
            self.estimated_duration_validator.validate(
                0, self.task, self.mock_repository
            )
        self.assertIn(
            "Estimated duration must be greater than 0", str(context.exception)
        )
        self.assertIn("got 0", str(context.exception))

        # priority
        with self.assertRaises(TaskValidationError) as context:
            self.priority_validator.validate(0, self.task, self.mock_repository)
        self.assertIn("Priority must be greater than 0", str(context.exception))
        self.assertIn("got 0", str(context.exception))

    def test_validate_zero_float_raises_error(self):
        """Test that zero float values are rejected."""
        # estimated_duration
        with self.assertRaises(TaskValidationError) as context:
            self.estimated_duration_validator.validate(
                0.0, self.task, self.mock_repository
            )
        self.assertIn(
            "Estimated duration must be greater than 0", str(context.exception)
        )

        # priority
        with self.assertRaises(TaskValidationError) as context:
            self.priority_validator.validate(0.0, self.task, self.mock_repository)
        self.assertIn("Priority must be greater than 0", str(context.exception))

    def test_validate_negative_raises_error(self):
        """Test that negative values are rejected."""
        # estimated_duration
        with self.assertRaises(TaskValidationError) as context:
            self.estimated_duration_validator.validate(
                -5, self.task, self.mock_repository
            )
        self.assertIn(
            "Estimated duration must be greater than 0", str(context.exception)
        )
        self.assertIn("got -5", str(context.exception))

        # priority
        with self.assertRaises(TaskValidationError) as context:
            self.priority_validator.validate(-10, self.task, self.mock_repository)
        self.assertIn("Priority must be greater than 0", str(context.exception))
        self.assertIn("got -10", str(context.exception))

    def test_validate_negative_float_raises_error(self):
        """Test that negative float values are rejected."""
        # estimated_duration
        with self.assertRaises(TaskValidationError) as context:
            self.estimated_duration_validator.validate(
                -5.5, self.task, self.mock_repository
            )
        self.assertIn(
            "Estimated duration must be greater than 0", str(context.exception)
        )

        # priority
        with self.assertRaises(TaskValidationError) as context:
            self.priority_validator.validate(-1.5, self.task, self.mock_repository)
        self.assertIn("Priority must be greater than 0", str(context.exception))

    def test_validate_none_value_success(self):
        """Test that None values (clearing the field) are accepted."""
        # Should not raise for None values
        self.estimated_duration_validator.validate(
            None, self.task, self.mock_repository
        )
        self.priority_validator.validate(None, self.task, self.mock_repository)

    def test_validate_invalid_type_raises_error(self):
        """Test that invalid types are rejected (expects int or float)."""
        # String values
        with self.assertRaises(TaskValidationError) as context:
            self.estimated_duration_validator.validate(
                "10", self.task, self.mock_repository
            )
        self.assertIn("Invalid type for estimated_duration", str(context.exception))
        self.assertIn("Expected int or float", str(context.exception))

        with self.assertRaises(TaskValidationError) as context:
            self.priority_validator.validate("high", self.task, self.mock_repository)
        self.assertIn("Invalid type for priority", str(context.exception))
        self.assertIn("Expected int or float", str(context.exception))

    def test_validate_boolean_behavior(self):
        """Test boolean value behavior (bool is subclass of int in Python)."""
        # Note: In Python, bool is a subclass of int, so True == 1 and False == 0
        # True should pass validation (treated as 1)
        self.estimated_duration_validator.validate(
            True, self.task, self.mock_repository
        )

        # False should fail validation (treated as 0)
        with self.assertRaises(TaskValidationError) as context:
            self.estimated_duration_validator.validate(
                False, self.task, self.mock_repository
            )
        self.assertIn("must be greater than 0", str(context.exception))

    def test_validate_list_raises_error(self):
        """Test that list values are rejected."""
        with self.assertRaises(TaskValidationError) as context:
            self.estimated_duration_validator.validate(
                [10], self.task, self.mock_repository
            )
        self.assertIn("Invalid type for estimated_duration", str(context.exception))

    def test_validate_dict_raises_error(self):
        """Test that dict values are rejected."""
        with self.assertRaises(TaskValidationError) as context:
            self.priority_validator.validate(
                {"value": 10}, self.task, self.mock_repository
            )
        self.assertIn("Invalid type for priority", str(context.exception))

    def test_field_name_formatting_in_error_message(self):
        """Test that field names are properly formatted in error messages."""
        # estimated_duration should be formatted as "Estimated duration"
        with self.assertRaises(TaskValidationError) as context:
            self.estimated_duration_validator.validate(
                0, self.task, self.mock_repository
            )
        error_message = str(context.exception)
        self.assertIn("Estimated duration", error_message)
        # Should not contain underscores in the user-facing message
        self.assertTrue(
            "Estimated duration" in error_message
            or "estimated_duration" in error_message
        )


if __name__ == "__main__":
    unittest.main()
