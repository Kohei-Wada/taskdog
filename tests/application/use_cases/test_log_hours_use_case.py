"""Tests for LogHoursUseCase."""

import os
import tempfile
import unittest

from application.dto.log_hours_input import LogHoursInput
from application.use_cases.log_hours import LogHoursUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestLogHoursUseCase(unittest.TestCase):
    """Test cases for LogHoursUseCase."""

    def setUp(self):
        """Create temporary file and initialize use case for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.use_case = LogHoursUseCase(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_logs_hours(self):
        """Test execute logs hours for a date."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = LogHoursInput(task_id=task.id, date="2025-01-15", hours=4.5)
        result = self.use_case.execute(input_dto)

        self.assertIn("2025-01-15", result.actual_daily_hours)
        self.assertEqual(result.actual_daily_hours["2025-01-15"], 4.5)

    def test_execute_persists_changes(self):
        """Test execute saves hours to repository."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = LogHoursInput(task_id=task.id, date="2025-01-15", hours=3.0)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        self.assertIn("2025-01-15", retrieved.actual_daily_hours)
        self.assertEqual(retrieved.actual_daily_hours["2025-01-15"], 3.0)

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = LogHoursInput(task_id=999, date="2025-01-15", hours=4.0)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_with_invalid_date_format_raises_error(self):
        """Test execute with invalid date format raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1)

        # Invalid date formats
        invalid_dates = ["2025/01/15", "15-01-2025", "invalid", "2025-13-01"]

        for invalid_date in invalid_dates:
            input_dto = LogHoursInput(task_id=task.id, date=invalid_date, hours=4.0)

            with self.assertRaises(TaskValidationError) as context:
                self.use_case.execute(input_dto)

            self.assertIn("Invalid date format", str(context.exception))

    def test_execute_with_zero_hours_raises_error(self):
        """Test execute with zero hours raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = LogHoursInput(task_id=task.id, date="2025-01-15", hours=0.0)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("must be greater than 0", str(context.exception))

    def test_execute_with_negative_hours_raises_error(self):
        """Test execute with negative hours raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = LogHoursInput(task_id=task.id, date="2025-01-15", hours=-2.5)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("must be greater than 0", str(context.exception))

    def test_execute_overwrites_existing_hours(self):
        """Test execute overwrites hours for same date."""
        task = self.repository.create(name="Test Task", priority=1)

        # Log hours first time
        input_dto1 = LogHoursInput(task_id=task.id, date="2025-01-15", hours=3.0)
        self.use_case.execute(input_dto1)

        # Log hours again for same date
        input_dto2 = LogHoursInput(task_id=task.id, date="2025-01-15", hours=5.0)
        result = self.use_case.execute(input_dto2)

        # Should have new value, not sum
        self.assertEqual(result.actual_daily_hours["2025-01-15"], 5.0)

    def test_execute_allows_multiple_dates(self):
        """Test execute allows logging hours for multiple dates."""
        task = self.repository.create(name="Test Task", priority=1)

        # Log hours for different dates
        dates_hours = [
            ("2025-01-15", 4.0),
            ("2025-01-16", 3.5),
            ("2025-01-17", 2.0),
        ]

        for date, hours in dates_hours:
            input_dto = LogHoursInput(task_id=task.id, date=date, hours=hours)
            self.use_case.execute(input_dto)

        # Verify all dates logged
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(len(retrieved.actual_daily_hours), 3)
        for date, hours in dates_hours:
            self.assertEqual(retrieved.actual_daily_hours[date], hours)

    def test_execute_with_decimal_hours(self):
        """Test execute accepts decimal hours."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = LogHoursInput(task_id=task.id, date="2025-01-15", hours=2.75)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.actual_daily_hours["2025-01-15"], 2.75)


if __name__ == "__main__":
    unittest.main()
