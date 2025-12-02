"""Tests for DateTimeValidator."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from taskdog_core.application.validators.datetime_validator import DateTimeValidator
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError


class TestDateTimeValidator:
    """Test cases for DateTimeValidator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize mock repository for each test."""
        self.mock_repository = Mock()

    @pytest.mark.parametrize(
        "field_name,task_status,actual_start_days_offset,value_days_offset,should_pass,error_fragment",
        [
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
        ],
        ids=[
            "valid_future_deadline",
            "valid_future_planned_start",
            "valid_future_planned_end",
            "valid_none_deadline",
            "valid_none_planned_start",
            "valid_none_planned_end",
            "valid_past_deadline_in_progress",
            "valid_past_planned_start_in_progress",
            "valid_past_planned_end_in_progress",
            "valid_past_deadline_completed",
            "valid_past_planned_start_completed",
            "valid_past_planned_end_completed",
            "valid_today_deadline",
            "valid_today_planned_start",
            "valid_today_planned_end",
            "invalid_past_deadline",
            "invalid_past_planned_start",
            "invalid_past_planned_end",
            "invalid_string_deadline",
            "invalid_string_planned_start",
            "invalid_int_deadline",
        ],
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
            with pytest.raises(TaskValidationError) as exc_info:
                validator.validate(value, task, self.mock_repository)
            assert error_fragment in str(exc_info.value)
