"""Tests for NumericFieldValidator."""

from unittest.mock import Mock

import pytest

from taskdog_core.application.validators.numeric_field_validator import (
    NumericFieldValidator,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


class TestNumericFieldValidator:
    """Test cases for NumericFieldValidator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize mock repository and task for each test."""
        self.mock_repository = Mock()
        self.task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=5)

    @pytest.mark.parametrize(
        "field_name,value,expected_error_fragment",
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
        ],
        ids=[
            "valid_duration_10",
            "valid_duration_100",
            "valid_duration_10.5",
            "valid_duration_0.5",
            "valid_duration_0.1",
            "valid_duration_none",
            "valid_duration_true",
            "valid_priority_100",
            "valid_priority_5.5",
            "valid_priority_1",
            "valid_priority_none",
            "valid_priority_true",
            "invalid_duration_zero_int",
            "invalid_duration_zero_float",
            "invalid_priority_zero_int",
            "invalid_priority_zero_float",
            "invalid_duration_false",
            "invalid_duration_negative_int",
            "invalid_duration_negative_float",
            "invalid_priority_negative_int",
            "invalid_priority_negative_float",
            "invalid_duration_string",
            "invalid_duration_list",
            "invalid_priority_string",
            "invalid_priority_dict",
        ],
    )
    def test_numeric_field_validation(self, field_name, value, expected_error_fragment):
        """Test validation of numeric fields with various inputs."""
        validator = NumericFieldValidator(field_name)

        if expected_error_fragment is None:
            # Should pass validation without raising
            validator.validate(value, self.task, self.mock_repository)
        else:
            # Should raise TaskValidationError with expected message
            with pytest.raises(TaskValidationError) as exc_info:
                validator.validate(value, self.task, self.mock_repository)
            assert expected_error_fragment in str(exc_info.value)
            # Also verify the value appears in error message for specific values
            if value not in (None, True, False) and not isinstance(
                value, list | dict | str
            ):
                assert str(value) in str(exc_info.value)

    def test_field_name_formatting_in_error_message(self):
        """Test that field names are properly formatted in error messages."""
        validator = NumericFieldValidator("estimated_duration")

        with pytest.raises(TaskValidationError) as exc_info:
            validator.validate(0, self.task, self.mock_repository)

        error_message = str(exc_info.value)
        # Should contain user-friendly "Estimated duration" (not "estimated_duration")
        assert "Estimated duration" in error_message
