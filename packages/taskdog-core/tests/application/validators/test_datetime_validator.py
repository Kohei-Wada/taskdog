"""Tests for DateTimeValidator."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from parameterized import parameterized

from taskdog_core.application.validators.datetime_validator import DateTimeValidator
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


class TestDateTimeValidator(unittest.TestCase):
    """Test cases for DateTimeValidator."""

    def setUp(self):
        """Initialize mock repository for each test."""
        self.mock_repository = Mock()

    @parameterized.expand(
        [
            # (field_name, task_status, actual_start_days_offset, value_days_offset, should_pass, error_fragment)
            # Valid cases - future dates for new tasks
            ("deadline", TaskStatus.PENDING, None, 7, True, None),
            ("planned_start", TaskStatus.PENDING, None, 7, True, None),
            ("planned_end", TaskStatus.PENDING, None, 7, True, None),
            # Valid cases - None values (clearing field)
            ("deadline", TaskStatus.PENDING, None, None, True, None),
            ("planned_start", TaskStatus.PENDING, None, None, True, None),
            ("planned_end", TaskStatus.PENDING, None, None, True, None),
            # Valid cases - past dates for started tasks
            ("deadline", TaskStatus.IN_PROGRESS, -14, -7, True, None),
            ("planned_start", TaskStatus.IN_PROGRESS, -14, -7, True, None),
            ("planned_end", TaskStatus.IN_PROGRESS, -14, -7, True, None),
            # Valid cases - past dates for completed tasks with actual_start
            ("deadline", TaskStatus.COMPLETED, -30, -7, True, None),
            ("planned_start", TaskStatus.COMPLETED, -30, -7, True, None),
            ("planned_end", TaskStatus.COMPLETED, -30, -7, True, None),
            # Valid cases - today/near future (1 minute ahead to avoid race conditions)
            ("deadline", TaskStatus.PENDING, None, 0.0007, True, None),  # ~1 minute
            ("planned_start", TaskStatus.PENDING, None, 0.0007, True, None),
            ("planned_end", TaskStatus.PENDING, None, 0.0007, True, None),
            # Invalid cases - past dates for new tasks
            (
                "deadline",
                TaskStatus.PENDING,
                None,
                -7,
                False,
                "Cannot set deadline to past date",
            ),
            (
                "planned_start",
                TaskStatus.PENDING,
                None,
                -7,
                False,
                "Cannot set planned_start to past date",
            ),
            (
                "planned_end",
                TaskStatus.PENDING,
                None,
                -7,
                False,
                "Cannot set planned_end to past date",
            ),
            # Invalid cases - wrong types (string)
            (
                "deadline",
                TaskStatus.PENDING,
                None,
                "invalid_string",
                False,
                "Invalid datetime type",
            ),
            (
                "planned_start",
                TaskStatus.PENDING,
                None,
                "invalid_string",
                False,
                "Invalid datetime type",
            ),
            # Invalid cases - wrong types (int)
            (
                "deadline",
                TaskStatus.PENDING,
                None,
                "invalid_int",
                False,
                "Invalid datetime type",
            ),
        ]
    )
    def test_datetime_validation_scenarios(
        self,
        field_name,
        task_status,
        actual_start_days_offset,
        value_days_offset,
        should_pass,
        error_fragment,
    ):
        """Test validation of datetime fields with various scenarios."""
        # Build task with optional actual_start
        task_kwargs = {
            "id": 1,
            "name": "Test",
            "status": task_status,
            "priority": 1,
        }
        if actual_start_days_offset is not None:
            task_kwargs["actual_start"] = datetime.now() + timedelta(
                days=actual_start_days_offset
            )
        task = Task(**task_kwargs)

        # Build value based on offset or special markers
        if value_days_offset is None:
            value = None
        elif value_days_offset == "invalid_string":
            value = "2025-01-15 10:00:00"  # String instead of datetime
        elif value_days_offset == "invalid_int":
            value = 123456  # Int instead of datetime
        else:
            value = datetime.now() + timedelta(days=value_days_offset)

        validator = DateTimeValidator(field_name)

        if should_pass:
            # Should pass validation without raising
            validator.validate(value, task, self.mock_repository)
        else:
            # Should raise TaskValidationError with expected message
            with self.assertRaises(TaskValidationError) as context:
                validator.validate(value, task, self.mock_repository)
            self.assertIn(error_fragment, str(context.exception))


if __name__ == "__main__":
    unittest.main()
