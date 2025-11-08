"""Tests for ThisWeekFilter."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from taskdog_core.application.queries.filters.this_week_filter import ThisWeekFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestThisWeekFilter(unittest.TestCase):
    """Test cases for ThisWeekFilter."""

    def setUp(self):
        """Set up test with fixed "today" for predictable testing."""
        # Fix "today" to Wednesday, January 15, 2025
        self.today = datetime(2025, 1, 15).date()
        # Week: Monday Jan 13 - Sunday Jan 19
        self.week_start = datetime(2025, 1, 13).date()
        self.week_end = datetime(2025, 1, 19).date()

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_includes_task_with_deadline_this_week(self, mock_datetime):
        """Test filter includes task with deadline within this week."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        task = Task(
            id=1,
            name="Deadline This Week",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=datetime(2025, 1, 16),  # Thursday
        )

        this_week_filter = ThisWeekFilter()
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), 1)

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_excludes_task_with_deadline_next_week(self, mock_datetime):
        """Test filter excludes task with deadline in next week."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        task = Task(
            id=1,
            name="Deadline Next Week",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=datetime(2025, 1, 20),  # Monday next week
        )

        this_week_filter = ThisWeekFilter()
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), 0)

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_includes_task_with_planned_period_overlapping_this_week(
        self, mock_datetime
    ):
        """Test filter includes task with planned period overlapping this week."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        # Task planned from Monday to Friday
        task = Task(
            id=1,
            name="Planned This Week",
            status=TaskStatus.PENDING,
            priority=1,
            planned_start=datetime(2025, 1, 13),  # Monday
            planned_end=datetime(2025, 1, 17),  # Friday
        )

        this_week_filter = ThisWeekFilter()
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), 1)

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_includes_in_progress_tasks(self, mock_datetime):
        """Test filter includes IN_PROGRESS tasks regardless of dates."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        task = Task(
            id=1,
            name="In Progress",
            status=TaskStatus.IN_PROGRESS,
            priority=1,
            # No dates
        )

        this_week_filter = ThisWeekFilter()
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), 1)

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_excludes_completed_tasks_by_default(self, mock_datetime):
        """Test filter excludes COMPLETED tasks by default."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        task = Task(
            id=1,
            name="Completed",
            status=TaskStatus.COMPLETED,
            priority=1,
            deadline=datetime(2025, 1, 16),
        )

        this_week_filter = ThisWeekFilter()
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), 0)

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_includes_completed_tasks_when_enabled(self, mock_datetime):
        """Test filter includes COMPLETED tasks when include_completed=True."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        task = Task(
            id=1,
            name="Completed",
            status=TaskStatus.COMPLETED,
            priority=1,
            deadline=datetime(2025, 1, 16),
        )

        this_week_filter = ThisWeekFilter(include_completed=True)
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), 1)

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_excludes_pending_task_with_no_dates(self, mock_datetime):
        """Test filter excludes PENDING tasks with no dates."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        task = Task(id=1, name="No Dates", status=TaskStatus.PENDING, priority=1)

        this_week_filter = ThisWeekFilter()
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), 0)

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_with_empty_list(self, mock_datetime):
        """Test filter with empty task list."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        this_week_filter = ThisWeekFilter()
        result = this_week_filter.filter([])

        self.assertEqual(len(result), 0)

    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_calculates_week_correctly(self, mock_datetime):
        """Test filter calculates this week's Monday-Sunday range correctly."""
        # Test on different days of the week
        for day_offset in range(7):  # Monday=0 to Sunday=6
            current_day = datetime(2025, 1, 13) + timedelta(
                days=day_offset
            )  # Week starting Jan 13
            mock_datetime.now.return_value = current_day

            task = Task(
                id=1,
                name="Mid Week",
                status=TaskStatus.PENDING,
                priority=1,
                deadline=datetime(2025, 1, 16),  # Thursday
            )

            this_week_filter = ThisWeekFilter()
            result = this_week_filter.filter([task])

            # Should match regardless of which day "today" is within the week
            self.assertEqual(len(result), 1, f"Failed for {current_day.strftime('%A')}")


if __name__ == "__main__":
    unittest.main()
