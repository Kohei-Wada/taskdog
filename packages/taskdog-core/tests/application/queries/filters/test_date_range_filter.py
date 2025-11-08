"""Tests for DateRangeFilter."""

import unittest
from datetime import date, datetime

from parameterized import parameterized

from taskdog_core.application.queries.filters.date_range_filter import DateRangeFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestDateRangeFilter(unittest.TestCase):
    """Test cases for DateRangeFilter."""

    def setUp(self):
        """Create sample tasks for testing."""
        # Task with planned dates in January 2025
        self.task_jan = Task(
            id=1,
            name="January Task",
            status=TaskStatus.PENDING,
            priority=1,
            planned_start=datetime(2025, 1, 10),
            planned_end=datetime(2025, 1, 15),
        )

        # Task with planned dates in February 2025
        self.task_feb = Task(
            id=2,
            name="February Task",
            status=TaskStatus.PENDING,
            priority=1,
            planned_start=datetime(2025, 2, 5),
            planned_end=datetime(2025, 2, 10),
        )

        # Task with deadline in March 2025
        self.task_mar = Task(
            id=3,
            name="March Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=datetime(2025, 3, 20),
        )

        # Task with no dates
        self.task_no_dates = Task(
            id=4, name="No Dates", status=TaskStatus.PENDING, priority=1
        )

    @parameterized.expand(
        [
            # (scenario, start_date, end_date, expected_task_ids)
            ("start_date_only", date(2025, 2, 1), None, [2, 3]),
            ("end_date_only", None, date(2025, 2, 28), [1, 2]),
            ("both_dates", date(2025, 2, 1), date(2025, 2, 28), [2]),
        ]
    )
    def test_filter_with_date_ranges(
        self, scenario, start_date, end_date, expected_task_ids
    ):
        """Test filter with different date range configurations."""
        date_filter = DateRangeFilter(start_date=start_date, end_date=end_date)
        tasks = [self.task_jan, self.task_feb, self.task_mar]

        result = date_filter.filter(tasks)

        self.assertEqual(len(result), len(expected_task_ids))
        result_ids = [task.id for task in result]
        for expected_id in expected_task_ids:
            self.assertIn(expected_id, result_ids)

    def test_filter_includes_tasks_with_no_dates(self):
        """Test filter includes tasks with no date fields (unscheduled tasks)."""
        date_filter = DateRangeFilter(start_date=date(2025, 1, 1))
        tasks = [self.task_jan, self.task_no_dates]

        result = date_filter.filter(tasks)

        self.assertEqual(len(result), 2)
        self.assertIn(self.task_no_dates, result)

    def test_filter_checks_all_date_fields(self):
        """Test filter checks planned_start, planned_end, actual_start, actual_end, deadline."""
        # Task with multiple date fields
        task_multi = Task(
            id=5,
            name="Multi Date",
            status=TaskStatus.IN_PROGRESS,
            priority=1,
            planned_start=datetime(2025, 1, 5),
            planned_end=datetime(2025, 1, 10),
            actual_start=datetime(2025, 1, 6),
            deadline=datetime(2025, 1, 15),
        )

        # Filter for dates in January
        date_filter = DateRangeFilter(
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )

        result = date_filter.filter([task_multi])

        self.assertEqual(len(result), 1)

    def test_filter_with_boundary_dates(self):
        """Test filter includes tasks with dates on the boundaries."""
        date_filter = DateRangeFilter(
            start_date=date(2025, 1, 10), end_date=date(2025, 1, 15)
        )

        result = date_filter.filter([self.task_jan])

        # task_jan has planned_start=2025-01-10, planned_end=2025-01-15
        self.assertEqual(len(result), 1)

    def test_filter_with_no_matching_tasks(self):
        """Test filter returns empty list when no tasks match."""
        date_filter = DateRangeFilter(
            start_date=date(2025, 12, 1), end_date=date(2025, 12, 31)
        )
        tasks = [self.task_jan, self.task_feb, self.task_mar]

        result = date_filter.filter(tasks)

        self.assertEqual(len(result), 0)

    def test_filter_with_empty_task_list(self):
        """Test filter with empty task list."""
        date_filter = DateRangeFilter(start_date=date(2025, 1, 1))
        result = date_filter.filter([])

        self.assertEqual(len(result), 0)

    def test_init_requires_at_least_one_date(self):
        """Test __init__ raises ValueError when both dates are None."""
        with self.assertRaises(ValueError) as context:
            DateRangeFilter(start_date=None, end_date=None)

        self.assertIn(
            "At least one of start_date or end_date must be provided",
            str(context.exception),
        )

    def test_filter_includes_task_if_any_date_in_range(self):
        """Test filter includes task if any date field is in range."""
        # Task with deadline in March but planned dates in January
        task_mixed = Task(
            id=6,
            name="Mixed Dates",
            status=TaskStatus.PENDING,
            priority=1,
            planned_start=datetime(2025, 1, 5),
            planned_end=datetime(2025, 1, 10),
            deadline=datetime(2025, 3, 20),
        )

        # Filter for January only
        date_filter = DateRangeFilter(
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )

        result = date_filter.filter([task_mixed])

        # Should include because planned dates are in January
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
