"""Tests for DateTimeValidator."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from application.validators.datetime_validator import DateTimeValidator
from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskValidationError


class TestDateTimeValidator(unittest.TestCase):
    """Test cases for DateTimeValidator."""

    def setUp(self):
        """Initialize validator and mock repository for each test."""
        self.deadline_validator = DateTimeValidator("deadline")
        self.planned_start_validator = DateTimeValidator("planned_start")
        self.planned_end_validator = DateTimeValidator("planned_end")
        self.mock_repository = Mock()

    def test_validate_future_date_success(self):
        """Test that future dates are accepted for new tasks."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)
        future_date = (datetime.now() + timedelta(days=7)).strftime(DATETIME_FORMAT)

        # Should not raise for all validators
        self.deadline_validator.validate(future_date, task, self.mock_repository)
        self.planned_start_validator.validate(future_date, task, self.mock_repository)
        self.planned_end_validator.validate(future_date, task, self.mock_repository)

    def test_validate_past_date_for_new_task_raises_error(self):
        """Test that past dates are rejected for tasks that haven't started."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)
        past_date = (datetime.now() - timedelta(days=7)).strftime(DATETIME_FORMAT)

        # Test deadline
        with self.assertRaises(TaskValidationError) as context:
            self.deadline_validator.validate(past_date, task, self.mock_repository)
        self.assertIn("Cannot set deadline to past date", str(context.exception))
        self.assertIn("haven't started", str(context.exception))

        # Test planned_start
        with self.assertRaises(TaskValidationError) as context:
            self.planned_start_validator.validate(past_date, task, self.mock_repository)
        self.assertIn("Cannot set planned_start to past date", str(context.exception))

        # Test planned_end
        with self.assertRaises(TaskValidationError) as context:
            self.planned_end_validator.validate(past_date, task, self.mock_repository)
        self.assertIn("Cannot set planned_end to past date", str(context.exception))

    def test_validate_past_date_for_started_task_success(self):
        """Test that past dates are allowed for tasks that have started."""
        actual_start = (datetime.now() - timedelta(days=14)).strftime(DATETIME_FORMAT)
        task = Task(
            id=1,
            name="Test",
            status=TaskStatus.IN_PROGRESS,
            priority=1,
            actual_start=actual_start,
        )
        past_date = (datetime.now() - timedelta(days=7)).strftime(DATETIME_FORMAT)

        # Should not raise - task has already started
        self.deadline_validator.validate(past_date, task, self.mock_repository)
        self.planned_start_validator.validate(past_date, task, self.mock_repository)
        self.planned_end_validator.validate(past_date, task, self.mock_repository)

    def test_validate_none_value_success(self):
        """Test that None values (clearing the field) are accepted."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        # Should not raise for None values
        self.deadline_validator.validate(None, task, self.mock_repository)
        self.planned_start_validator.validate(None, task, self.mock_repository)
        self.planned_end_validator.validate(None, task, self.mock_repository)

    def test_validate_invalid_format_raises_error(self):
        """Test that invalid datetime formats are rejected."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)
        invalid_date = "2025-13-45"  # Invalid month/day

        with self.assertRaises(TaskValidationError) as context:
            self.deadline_validator.validate(invalid_date, task, self.mock_repository)
        self.assertIn("Invalid datetime format", str(context.exception))
        self.assertIn("deadline", str(context.exception))

    def test_validate_wrong_format_string_raises_error(self):
        """Test that wrong format strings are rejected."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)
        wrong_format = "10/20/2025"  # MM/DD/YYYY instead of YYYY-MM-DD HH:MM:SS

        with self.assertRaises(TaskValidationError) as context:
            self.deadline_validator.validate(wrong_format, task, self.mock_repository)
        self.assertIn("Invalid datetime format", str(context.exception))

    def test_validate_completed_task_with_actual_start_allows_past_dates(self):
        """Test that completed tasks with actual_start can have past dates."""
        actual_start = (datetime.now() - timedelta(days=30)).strftime(DATETIME_FORMAT)
        task = Task(
            id=1,
            name="Test",
            status=TaskStatus.COMPLETED,
            priority=1,
            actual_start=actual_start,
        )
        past_date = (datetime.now() - timedelta(days=7)).strftime(DATETIME_FORMAT)

        # Should not raise - task has actual_start
        self.deadline_validator.validate(past_date, task, self.mock_repository)
        self.planned_start_validator.validate(past_date, task, self.mock_repository)
        self.planned_end_validator.validate(past_date, task, self.mock_repository)

    def test_validate_today_is_allowed(self):
        """Test that today's date (current time) is allowed."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)
        # Use a time slightly in the future to avoid race conditions
        today_plus_1min = (datetime.now() + timedelta(minutes=1)).strftime(DATETIME_FORMAT)

        # Should not raise
        self.deadline_validator.validate(today_plus_1min, task, self.mock_repository)
        self.planned_start_validator.validate(today_plus_1min, task, self.mock_repository)
        self.planned_end_validator.validate(today_plus_1min, task, self.mock_repository)


if __name__ == "__main__":
    unittest.main()
