"""Tests for Task entity business logic methods."""

from datetime import datetime

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotSchedulableError,
    TaskValidationError,
)


class TestTaskIsSchedulable:
    """Test cases for Task.is_schedulable() method."""

    @pytest.mark.parametrize(
        "status,duration,expected",
        [
            (TaskStatus.PENDING, 4.0, True),
            (TaskStatus.COMPLETED, 4.0, False),
            (TaskStatus.IN_PROGRESS, 4.0, False),
            (TaskStatus.CANCELED, 4.0, False),
            (TaskStatus.PENDING, None, False),
        ],
        ids=[
            "pending_with_duration",
            "completed_task",
            "in_progress_task",
            "canceled_task",
            "pending_no_duration",
        ],
    )
    def test_is_schedulable_by_status_and_duration(self, status, duration, expected):
        """Test schedulability based on status and estimated_duration."""
        task = Task(
            name="Test Task",
            priority=100,
            status=status,
            estimated_duration=duration,
        )
        result = task.is_schedulable(force_override=False)
        assert result == expected

    def test_is_not_schedulable_with_existing_schedule_by_default(self):
        """Test that tasks with existing schedules are not schedulable by default."""
        task = Task(
            name="Scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            planned_start="2025-01-06 09:00:00",
        )

        result = task.is_schedulable(force_override=False)

        assert result is False

    def test_is_schedulable_with_existing_schedule_when_forced(self):
        """Test that tasks with existing schedules are schedulable with force_override."""
        task = Task(
            name="Scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            planned_start="2025-01-06 09:00:00",
        )

        result = task.is_schedulable(force_override=True)

        assert result is True

    def test_is_not_schedulable_when_archived(self):
        """Test that archived tasks are never schedulable."""
        task = Task(
            name="Archived task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_archived=True,
        )

        # Archived tasks should not be schedulable, even with force_override
        assert task.is_schedulable(force_override=False) is False
        assert task.is_schedulable(force_override=True) is False


class TestTaskValidateSchedulable:
    """Test cases for Task.validate_schedulable() method."""

    def test_validate_schedulable_success(self):
        """Test that valid schedulable task passes validation."""
        task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
        )

        # Should not raise
        task.validate_schedulable(force_override=False)

    def test_validate_schedulable_raises_for_none_id(self):
        """Test that validation raises for task with None ID."""
        task = Task(
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
        )

        with pytest.raises(TaskValidationError) as exc_info:
            task.validate_schedulable(force_override=False)

        assert "Task ID must not be None" in str(exc_info.value)

    @pytest.mark.parametrize(
        "task_kwargs,reason_keyword",
        [
            ({"is_archived": True, "estimated_duration": 4.0}, "archived"),
            ({"status": TaskStatus.COMPLETED}, "COMPLETED"),
            ({"status": TaskStatus.CANCELED}, "CANCELED"),
            (
                {"status": TaskStatus.IN_PROGRESS, "estimated_duration": 4.0},
                "in progress",
            ),
            ({"estimated_duration": None}, "duration"),
            ({"is_fixed": True, "estimated_duration": 4.0}, "fixed"),
        ],
        ids=[
            "archived_task",
            "completed_task",
            "canceled_task",
            "in_progress_task",
            "no_duration",
            "fixed_task",
        ],
    )
    def test_validate_schedulable_raises_for_unschedulable_tasks(
        self, task_kwargs, reason_keyword
    ):
        """Test that validation raises for various unschedulable tasks."""
        base_config = {
            "id": 1,
            "name": "Test Task",
            "priority": 5,
            "status": TaskStatus.PENDING,
        }
        base_config.update(task_kwargs)

        task = Task(**base_config)

        with pytest.raises(TaskNotSchedulableError) as exc_info:
            task.validate_schedulable(force_override=False)

        assert exc_info.value.task_id == 1
        assert reason_keyword.lower() in exc_info.value.reason.lower()

    def test_validate_schedulable_raises_for_scheduled_task_without_force(self):
        """Test that validation raises for already-scheduled task without force_override."""
        task = Task(
            id=1,
            name="Scheduled Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            planned_start="2025-01-06 09:00:00",
        )

        with pytest.raises(TaskNotSchedulableError) as exc_info:
            task.validate_schedulable(force_override=False)

        assert exc_info.value.task_id == 1
        assert "schedule" in exc_info.value.reason.lower()
        assert "force" in exc_info.value.reason.lower()

    def test_validate_schedulable_passes_for_scheduled_task_with_force(self):
        """Test that validation passes for already-scheduled task with force_override."""
        task = Task(
            id=1,
            name="Scheduled Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            planned_start="2025-01-06 09:00:00",
        )

        # Should not raise with force_override=True
        task.validate_schedulable(force_override=True)

    def test_validate_schedulable_raises_for_fixed_task_even_with_force(self):
        """Test that validation raises for fixed task even with force_override."""
        task = Task(
            id=1,
            name="Fixed Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=True,
        )

        with pytest.raises(TaskNotSchedulableError) as exc_info:
            task.validate_schedulable(force_override=True)

        assert exc_info.value.task_id == 1
        assert "fixed" in exc_info.value.reason.lower()


class TestTaskGetUnschedulableReason:
    """Test cases for Task.get_unschedulable_reason() method."""

    def test_get_unschedulable_reason_returns_none_for_schedulable(self):
        """Test that schedulable task returns None."""
        task = Task(
            id=1,
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
        )

        reason = task.get_unschedulable_reason(force_override=False)
        assert reason is None

    @pytest.mark.parametrize(
        "task_kwargs,expected_keyword",
        [
            ({"is_archived": True}, "archived"),
            ({"status": TaskStatus.COMPLETED}, "COMPLETED"),
            ({"status": TaskStatus.IN_PROGRESS}, "in progress"),
            ({"estimated_duration": None}, "duration"),
            ({"is_fixed": True}, "fixed"),
        ],
        ids=[
            "archived_task",
            "completed_task",
            "in_progress_task",
            "no_duration",
            "fixed_task",
        ],
    )
    def test_get_unschedulable_reason_returns_reason(
        self, task_kwargs, expected_keyword
    ):
        """Test that unschedulable task returns appropriate reason."""
        base_config = {
            "id": 1,
            "name": "Test Task",
            "priority": 5,
            "status": TaskStatus.PENDING,
            "estimated_duration": 4.0,
        }
        base_config.update(task_kwargs)

        task = Task(**base_config)

        reason = task.get_unschedulable_reason(force_override=False)
        assert reason is not None
        assert expected_keyword.lower() in reason.lower()


class TestTaskShouldCountInWorkload:
    """Test cases for Task.should_count_in_workload() method."""

    @pytest.mark.parametrize(
        "status,expected",
        [
            (TaskStatus.PENDING, True),
            (TaskStatus.IN_PROGRESS, True),
            (TaskStatus.COMPLETED, False),
            (TaskStatus.CANCELED, False),
        ],
        ids=[
            "pending_task",
            "in_progress_task",
            "completed_task",
            "canceled_task",
        ],
    )
    def test_should_count_in_workload_by_status(self, status, expected):
        """Test workload counting based on task status."""
        task = Task(name="Test task", priority=100, status=status)
        result = task.should_count_in_workload()
        assert result == expected

    def test_should_count_in_workload_excludes_archived(self):
        """Test that archived tasks are not counted in workload."""
        # Archived task with PENDING status should not be counted
        task = Task(
            name="Test task", priority=100, status=TaskStatus.PENDING, is_archived=True
        )
        assert task.should_count_in_workload() is False

        # Archived task with IN_PROGRESS status should not be counted
        task = Task(
            name="Test task",
            priority=100,
            status=TaskStatus.IN_PROGRESS,
            is_archived=True,
        )
        assert task.should_count_in_workload() is False


class TestTaskFixActualTimes:
    """Test cases for Task.fix_actual_times() method."""

    def test_fix_actual_times_sets_start(self):
        """Test setting actual_start only."""
        task = Task(name="Test Task", priority=100)
        start_time = datetime(2025, 12, 13, 9, 0, 0)

        task.fix_actual_times(actual_start=start_time)

        assert task.actual_start == start_time
        assert task.actual_end is None

    def test_fix_actual_times_sets_end(self):
        """Test setting actual_end only."""
        task = Task(name="Test Task", priority=100)
        task.actual_start = datetime(2025, 12, 13, 9, 0, 0)
        end_time = datetime(2025, 12, 13, 17, 0, 0)

        task.fix_actual_times(actual_end=end_time)

        assert task.actual_start == datetime(2025, 12, 13, 9, 0, 0)
        assert task.actual_end == end_time

    def test_fix_actual_times_sets_both(self):
        """Test setting both actual_start and actual_end."""
        task = Task(name="Test Task", priority=100)
        start_time = datetime(2025, 12, 13, 9, 0, 0)
        end_time = datetime(2025, 12, 13, 17, 0, 0)

        task.fix_actual_times(actual_start=start_time, actual_end=end_time)

        assert task.actual_start == start_time
        assert task.actual_end == end_time

    def test_fix_actual_times_clears_start(self):
        """Test clearing actual_start by setting to None."""
        task = Task(name="Test Task", priority=100)
        task.actual_start = datetime(2025, 12, 13, 9, 0, 0)
        task.actual_end = datetime(2025, 12, 13, 17, 0, 0)

        task.fix_actual_times(actual_start=None)

        assert task.actual_start is None
        assert task.actual_end == datetime(2025, 12, 13, 17, 0, 0)

    def test_fix_actual_times_clears_end(self):
        """Test clearing actual_end by setting to None."""
        task = Task(name="Test Task", priority=100)
        task.actual_start = datetime(2025, 12, 13, 9, 0, 0)
        task.actual_end = datetime(2025, 12, 13, 17, 0, 0)

        task.fix_actual_times(actual_end=None)

        assert task.actual_start == datetime(2025, 12, 13, 9, 0, 0)
        assert task.actual_end is None

    def test_fix_actual_times_keeps_current_with_ellipsis(self):
        """Test that Ellipsis (default) keeps current values."""
        task = Task(name="Test Task", priority=100)
        original_start = datetime(2025, 12, 13, 9, 0, 0)
        original_end = datetime(2025, 12, 13, 17, 0, 0)
        task.actual_start = original_start
        task.actual_end = original_end

        # Call with no arguments (uses Ellipsis defaults)
        task.fix_actual_times()

        assert task.actual_start == original_start
        assert task.actual_end == original_end

    def test_fix_actual_times_validation_end_before_start_raises(self):
        """Test that validation fails when actual_end < actual_start."""
        task = Task(name="Test Task", priority=100)
        start_time = datetime(2025, 12, 13, 17, 0, 0)  # Later time
        end_time = datetime(2025, 12, 13, 9, 0, 0)  # Earlier time

        with pytest.raises(TaskValidationError) as exc_info:
            task.fix_actual_times(actual_start=start_time, actual_end=end_time)

        assert "actual_end" in str(exc_info.value)
        assert "actual_start" in str(exc_info.value)

    def test_fix_actual_times_validation_with_existing_start(self):
        """Test validation when setting only end with existing start."""
        task = Task(name="Test Task", priority=100)
        task.actual_start = datetime(2025, 12, 13, 17, 0, 0)  # Later time
        end_time = datetime(2025, 12, 13, 9, 0, 0)  # Earlier time

        with pytest.raises(TaskValidationError) as exc_info:
            task.fix_actual_times(actual_end=end_time)

        assert "actual_end" in str(exc_info.value)

    def test_fix_actual_times_past_dates_allowed(self):
        """Test that past dates are allowed (historical records)."""
        task = Task(name="Test Task", priority=100)
        past_start = datetime(2020, 1, 1, 9, 0, 0)
        past_end = datetime(2020, 1, 1, 17, 0, 0)

        # Should not raise
        task.fix_actual_times(actual_start=past_start, actual_end=past_end)

        assert task.actual_start == past_start
        assert task.actual_end == past_end

    def test_fix_actual_times_same_start_and_end_allowed(self):
        """Test that same start and end times are allowed."""
        task = Task(name="Test Task", priority=100)
        same_time = datetime(2025, 12, 13, 12, 0, 0)

        # Should not raise (edge case: zero duration)
        task.fix_actual_times(actual_start=same_time, actual_end=same_time)

        assert task.actual_start == same_time
        assert task.actual_end == same_time
