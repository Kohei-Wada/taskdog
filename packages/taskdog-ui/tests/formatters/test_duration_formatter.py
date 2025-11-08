"""Tests for DurationFormatter."""

import unittest
from datetime import datetime
from unittest.mock import patch

from taskdog.formatters.duration_formatter import DurationFormatter
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.domain.entities.task import TaskStatus


class TestDurationFormatter(unittest.TestCase):
    """Test cases for DurationFormatter."""

    def test_format_hours_with_value(self):
        """Test format_hours with a valid hours value."""
        result = DurationFormatter.format_hours(5.0)
        self.assertEqual(result, "5.0h")

    def test_format_hours_with_none(self):
        """Test format_hours with None returns dash."""
        result = DurationFormatter.format_hours(None)
        self.assertEqual(result, "-")

    def test_format_estimated_duration_with_value(self):
        """Test format_estimated_duration with estimated duration."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
            actual_duration_hours=None,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=False,
            has_notes=False,
            created_at=now,
            updated_at=now,
        )
        result = DurationFormatter.format_estimated_duration(task_vm)
        self.assertEqual(result, "10.0h")

    def test_format_estimated_duration_without_value(self):
        """Test format_estimated_duration without estimated duration."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=None,
            actual_duration_hours=None,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=False,
            has_notes=False,
            created_at=now,
            updated_at=now,
        )
        result = DurationFormatter.format_estimated_duration(task_vm)
        self.assertEqual(result, "-")

    def test_format_actual_duration_with_value(self):
        """Test format_actual_duration with actual duration."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            estimated_duration=None,
            actual_duration_hours=8.5,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=True,
            has_notes=False,
            created_at=now,
            updated_at=now,
        )
        result = DurationFormatter.format_actual_duration(task_vm)
        self.assertEqual(result, "8.5h")

    def test_format_actual_duration_without_value(self):
        """Test format_actual_duration without actual duration."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=None,
            actual_duration_hours=None,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=False,
            has_notes=False,
            created_at=now,
            updated_at=now,
        )
        result = DurationFormatter.format_actual_duration(task_vm)
        self.assertEqual(result, "-")

    def test_format_elapsed_time_not_in_progress(self):
        """Test format_elapsed_time for non-IN_PROGRESS task."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=None,
            actual_duration_hours=None,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=False,
            has_notes=False,
            created_at=now,
            updated_at=now,
        )
        result = DurationFormatter.format_elapsed_time(task_vm)
        self.assertEqual(result, "-")

    def test_format_elapsed_time_in_progress_without_actual_start(self):
        """Test format_elapsed_time for IN_PROGRESS task without actual_start."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            estimated_duration=None,
            actual_duration_hours=None,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=False,
            has_notes=False,
            created_at=now,
            updated_at=now,
        )
        result = DurationFormatter.format_elapsed_time(task_vm)
        self.assertEqual(result, "-")

    def test_format_elapsed_time_hours_only(self):
        """Test format_elapsed_time with elapsed time less than 1 day."""
        actual_start = datetime(2025, 6, 15, 10, 30, 15)
        now_time = datetime(2025, 6, 15, 15, 45, 53)

        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            estimated_duration=None,
            actual_duration_hours=None,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=actual_start,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=False,
            has_notes=False,
            created_at=now_time,
            updated_at=now_time,
        )

        with patch("taskdog.formatters.duration_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = now_time
            result = DurationFormatter.format_elapsed_time(task_vm)
            # 5 hours, 15 minutes, 38 seconds
            self.assertEqual(result, "5:15:38")

    def test_format_elapsed_time_with_days(self):
        """Test format_elapsed_time with elapsed time more than 1 day."""
        actual_start = datetime(2025, 6, 10, 8, 0, 0)
        now_time = datetime(2025, 6, 13, 14, 30, 45)

        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            estimated_duration=None,
            actual_duration_hours=None,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=actual_start,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=False,
            has_notes=False,
            created_at=now_time,
            updated_at=now_time,
        )

        with patch("taskdog.formatters.duration_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = now_time
            result = DurationFormatter.format_elapsed_time(task_vm)
            # 3 days, 6 hours, 30 minutes, 45 seconds
            self.assertEqual(result, "3d 6:30:45")


if __name__ == "__main__":
    unittest.main()
