"""Tests for ThisWeekFilter."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from parameterized import parameterized

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

    @parameterized.expand(
        [
            # (scenario, status, deadline, planned_start, planned_end, expected_count)
            (
                "deadline_this_week",
                TaskStatus.PENDING,
                datetime(2025, 1, 16),
                None,
                None,
                1,
            ),
            (
                "deadline_next_week",
                TaskStatus.PENDING,
                datetime(2025, 1, 20),
                None,
                None,
                0,
            ),
            (
                "planned_period_this_week",
                TaskStatus.PENDING,
                None,
                datetime(2025, 1, 13),
                datetime(2025, 1, 17),
                1,
            ),
            ("in_progress_no_dates", TaskStatus.IN_PROGRESS, None, None, None, 1),
            ("pending_no_dates", TaskStatus.PENDING, None, None, None, 0),
        ]
    )
    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_task_scenarios(
        self,
        scenario,
        status,
        deadline,
        planned_start,
        planned_end,
        expected_count,
        mock_datetime,
    ):
        """Test filter with various task scenarios."""
        mock_datetime.now.return_value = datetime.combine(
            self.today, datetime.min.time()
        )

        task = Task(
            id=1,
            name=scenario,
            status=status,
            priority=1,
            deadline=deadline,
            planned_start=planned_start,
            planned_end=planned_end,
        )

        this_week_filter = ThisWeekFilter()
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), expected_count)

    @parameterized.expand(
        [
            ("exclude_completed_by_default", False, 0),
            ("include_completed_when_enabled", True, 1),
        ]
    )
    @patch("taskdog_core.application.queries.filters.this_week_filter.datetime")
    def test_filter_completed_tasks(
        self, scenario, include_completed, expected_count, mock_datetime
    ):
        """Test filter behavior with COMPLETED tasks."""
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

        this_week_filter = ThisWeekFilter(include_completed=include_completed)
        result = this_week_filter.filter([task])

        self.assertEqual(len(result), expected_count)

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
