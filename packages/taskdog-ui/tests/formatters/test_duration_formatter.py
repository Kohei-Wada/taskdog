"""Tests for DurationFormatter."""

from datetime import datetime
from unittest.mock import patch

import pytest

from taskdog.formatters.duration_formatter import DurationFormatter
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.domain.entities.task import TaskStatus


class TestDurationFormatter:
    """Test cases for DurationFormatter."""

    @pytest.mark.parametrize(
        "hours,expected",
        [
            (5.0, "5.0"),
            (None, "-"),
        ],
        ids=["with_value", "with_none"],
    )
    def test_format_hours(self, hours, expected):
        """Test format_hours with various input values."""
        result = DurationFormatter.format_hours(hours)
        assert result == expected

    @pytest.mark.parametrize(
        "estimated_duration,expected",
        [
            (10.0, "10.0"),
            (None, "-"),
        ],
        ids=["with_value", "without_value"],
    )
    def test_format_estimated_duration(self, estimated_duration, expected):
        """Test format_estimated_duration with and without duration value."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=estimated_duration,
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
        assert result == expected

    @pytest.mark.parametrize(
        "status,actual_duration_hours,is_finished,expected",
        [
            (TaskStatus.COMPLETED, 8.5, True, "8.5"),
            (TaskStatus.PENDING, None, False, "-"),
        ],
        ids=["with_value", "without_value"],
    )
    def test_format_actual_duration(
        self, status, actual_duration_hours, is_finished, expected
    ):
        """Test format_actual_duration with and without duration value."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=status,
            estimated_duration=None,
            actual_duration_hours=actual_duration_hours,
            deadline=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_finished=is_finished,
            has_notes=False,
            created_at=now,
            updated_at=now,
        )
        result = DurationFormatter.format_actual_duration(task_vm)
        assert result == expected

    @pytest.mark.parametrize(
        "status,actual_start",
        [
            (TaskStatus.PENDING, None),
            (TaskStatus.IN_PROGRESS, None),
        ],
        ids=["not_in_progress", "in_progress_without_actual_start"],
    )
    def test_format_elapsed_time_returns_dash(self, status, actual_start):
        """Test format_elapsed_time returns dash for non-elapsed cases."""
        now = datetime.now()
        task_vm = TaskRowViewModel(
            id=1,
            name="Test Task",
            priority=1,
            status=status,
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
            created_at=now,
            updated_at=now,
        )
        result = DurationFormatter.format_elapsed_time(task_vm)
        assert result == "-"

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
            assert result == "5:15:38"

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
            assert result == "3d 6:30:45"
