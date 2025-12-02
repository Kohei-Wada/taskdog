"""Tests for Task.is_schedulable() with is_fixed field."""

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskIsFixedScheduling:
    """Test cases for Task.is_schedulable() with is_fixed field."""

    @pytest.mark.parametrize(
        "is_fixed,force_override,planned_start,expected",
        [
            (True, False, None, False),
            (True, True, None, False),
            (False, False, None, True),
            (True, False, "2025-01-06 09:00:00", False),
            (True, True, "2025-01-06 09:00:00", False),
        ],
        ids=[
            "fixed_task_no_force_no_schedule",
            "fixed_task_forced_no_schedule",
            "non_fixed_task_no_force_no_schedule",
            "fixed_task_no_force_with_schedule",
            "fixed_task_forced_with_schedule_still_protected",
        ],
    )
    def test_is_schedulable_with_is_fixed_combinations(
        self, is_fixed, force_override, planned_start, expected
    ):
        """Test schedulability with various is_fixed, force_override, and schedule combinations.

        Fixed tasks are always protected to prevent accidental rescheduling
        of immovable constraints (meetings, deadlines, etc.).
        """
        task = Task(
            name="Test task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=is_fixed,
            planned_start=planned_start,
        )
        result = task.is_schedulable(force_override=force_override)
        assert result == expected
