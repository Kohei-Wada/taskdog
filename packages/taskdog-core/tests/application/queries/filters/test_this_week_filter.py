"""Tests for ThisWeekFilter."""

from datetime import datetime, timedelta

import pytest
from tests.helpers.time_provider import FakeTimeProvider

from taskdog_core.application.queries.filters.this_week_filter import ThisWeekFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestThisWeekFilter:
    """Test cases for ThisWeekFilter."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test with fixed "today" for predictable testing."""
        # Fix "today" to Wednesday, January 15, 2025
        self.today = datetime(2025, 1, 15).date()
        # Week: Monday Jan 13 - Sunday Jan 19
        self.week_start = datetime(2025, 1, 13).date()
        self.week_end = datetime(2025, 1, 19).date()
        self.time_provider = FakeTimeProvider(datetime(2025, 1, 15, 12, 0, 0))

    @pytest.mark.parametrize(
        "status,deadline,planned_start,planned_end,expected_count",
        [
            (TaskStatus.PENDING, datetime(2025, 1, 16), None, None, 1),
            (TaskStatus.PENDING, datetime(2025, 1, 20), None, None, 0),
            (TaskStatus.PENDING, None, datetime(2025, 1, 13), datetime(2025, 1, 17), 1),
            (TaskStatus.IN_PROGRESS, None, None, None, 1),
            (TaskStatus.PENDING, None, None, None, 0),
        ],
        ids=[
            "deadline_this_week",
            "deadline_next_week",
            "planned_period_this_week",
            "in_progress_no_dates",
            "pending_no_dates",
        ],
    )
    def test_filter_task_scenarios(
        self,
        status,
        deadline,
        planned_start,
        planned_end,
        expected_count,
    ):
        """Test filter with various task scenarios."""
        task = Task(
            id=1,
            name="Test Task",
            status=status,
            priority=1,
            deadline=deadline,
            planned_start=planned_start,
            planned_end=planned_end,
        )

        this_week_filter = ThisWeekFilter(time_provider=self.time_provider)
        result = this_week_filter.filter([task])

        assert len(result) == expected_count

    @pytest.mark.parametrize(
        "include_completed,expected_count",
        [
            (False, 0),
            (True, 1),
        ],
        ids=["exclude_completed_by_default", "include_completed_when_enabled"],
    )
    def test_filter_completed_tasks(self, include_completed, expected_count):
        """Test filter behavior with COMPLETED tasks."""
        task = Task(
            id=1,
            name="Completed",
            status=TaskStatus.COMPLETED,
            priority=1,
            deadline=datetime(2025, 1, 16),
        )

        this_week_filter = ThisWeekFilter(
            include_completed=include_completed, time_provider=self.time_provider
        )
        result = this_week_filter.filter([task])

        assert len(result) == expected_count

    def test_filter_with_empty_list(self):
        """Test filter with empty task list."""
        this_week_filter = ThisWeekFilter(time_provider=self.time_provider)
        result = this_week_filter.filter([])

        assert len(result) == 0

    def test_filter_calculates_week_correctly(self):
        """Test filter calculates this week's Monday-Sunday range correctly."""
        # Test on different days of the week
        for day_offset in range(7):  # Monday=0 to Sunday=6
            current_day = datetime(2025, 1, 13) + timedelta(
                days=day_offset
            )  # Week starting Jan 13
            time_provider = FakeTimeProvider(current_day)

            task = Task(
                id=1,
                name="Mid Week",
                status=TaskStatus.PENDING,
                priority=1,
                deadline=datetime(2025, 1, 16),  # Thursday
            )

            this_week_filter = ThisWeekFilter(time_provider=time_provider)
            result = this_week_filter.filter([task])

            # Should match regardless of which day "today" is within the week
            assert len(result) == 1, f"Failed for {current_day.strftime('%A')}"
