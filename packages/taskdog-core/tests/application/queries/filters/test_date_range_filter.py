"""Tests for DateRangeFilter."""

from datetime import date, datetime

import pytest

from taskdog_core.application.queries.filters.date_range_filter import DateRangeFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestDateRangeFilter:
    """Test cases for DateRangeFilter."""

    @pytest.fixture(autouse=True)
    def setup(self):
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

    @pytest.mark.parametrize(
        "start_date,end_date,expected_task_ids",
        [
            (date(2025, 2, 1), None, [2, 3]),
            (None, date(2025, 2, 28), [1, 2]),
            (date(2025, 2, 1), date(2025, 2, 28), [2]),
        ],
        ids=["start_date_only", "end_date_only", "both_dates"],
    )
    def test_filter_with_date_ranges(self, start_date, end_date, expected_task_ids):
        """Test filter with different date range configurations."""
        date_filter = DateRangeFilter(start_date=start_date, end_date=end_date)
        tasks = [self.task_jan, self.task_feb, self.task_mar]

        result = date_filter.filter(tasks)

        assert len(result) == len(expected_task_ids)
        result_ids = [task.id for task in result]
        for expected_id in expected_task_ids:
            assert expected_id in result_ids

    def test_filter_includes_tasks_with_no_dates(self):
        """Test filter includes tasks with no date fields (unscheduled tasks)."""
        date_filter = DateRangeFilter(start_date=date(2025, 1, 1))
        tasks = [self.task_jan, self.task_no_dates]

        result = date_filter.filter(tasks)

        assert len(result) == 2
        assert self.task_no_dates in result

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

        assert len(result) == 1

    def test_filter_with_boundary_dates(self):
        """Test filter includes tasks with dates on the boundaries."""
        date_filter = DateRangeFilter(
            start_date=date(2025, 1, 10), end_date=date(2025, 1, 15)
        )

        result = date_filter.filter([self.task_jan])

        # task_jan has planned_start=2025-01-10, planned_end=2025-01-15
        assert len(result) == 1

    def test_filter_with_no_matching_tasks(self):
        """Test filter returns empty list when no tasks match."""
        date_filter = DateRangeFilter(
            start_date=date(2025, 12, 1), end_date=date(2025, 12, 31)
        )
        tasks = [self.task_jan, self.task_feb, self.task_mar]

        result = date_filter.filter(tasks)

        assert len(result) == 0

    def test_filter_with_empty_task_list(self):
        """Test filter with empty task list."""
        date_filter = DateRangeFilter(start_date=date(2025, 1, 1))
        result = date_filter.filter([])

        assert len(result) == 0

    def test_init_requires_at_least_one_date(self):
        """Test __init__ raises ValueError when both dates are None."""
        with pytest.raises(ValueError) as exc_info:
            DateRangeFilter(start_date=None, end_date=None)

        assert "At least one of start_date or end_date must be provided" in str(
            exc_info.value
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
        assert len(result) == 1
