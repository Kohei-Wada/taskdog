"""Tests for Task entity business logic methods."""

import unittest

from parameterized import parameterized

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotSchedulableError,
    TaskValidationError,
)


class TestTaskIsSchedulable(unittest.TestCase):
    """Test cases for Task.is_schedulable() method."""

    @parameterized.expand(
        [
            ("pending_with_duration", TaskStatus.PENDING, 4.0, True),
            ("completed_task", TaskStatus.COMPLETED, 4.0, False),
            ("in_progress_task", TaskStatus.IN_PROGRESS, 4.0, False),
            ("canceled_task", TaskStatus.CANCELED, 4.0, False),
            ("pending_no_duration", TaskStatus.PENDING, None, False),
        ]
    )
    def test_is_schedulable_by_status_and_duration(
        self, _scenario, status, duration, expected
    ):
        """Test schedulability based on status and estimated_duration."""
        task = Task(
            name="Test Task",
            priority=100,
            status=status,
            estimated_duration=duration,
        )
        result = task.is_schedulable(force_override=False)
        self.assertEqual(result, expected)

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

        self.assertFalse(result)

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

        self.assertTrue(result)

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
        self.assertFalse(task.is_schedulable(force_override=False))
        self.assertFalse(task.is_schedulable(force_override=True))


class TestTaskValidateSchedulable(unittest.TestCase):
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

        with self.assertRaises(TaskValidationError) as context:
            task.validate_schedulable(force_override=False)

        self.assertIn("Task ID must not be None", str(context.exception))

    @parameterized.expand(
        [
            (
                "archived_task",
                {"is_archived": True, "estimated_duration": 4.0},
                "archived",
            ),
            ("completed_task", {"status": TaskStatus.COMPLETED}, "COMPLETED"),
            ("canceled_task", {"status": TaskStatus.CANCELED}, "CANCELED"),
            (
                "in_progress_task",
                {"status": TaskStatus.IN_PROGRESS, "estimated_duration": 4.0},
                "in progress",
            ),
            ("no_duration", {"estimated_duration": None}, "duration"),
            (
                "fixed_task",
                {"is_fixed": True, "estimated_duration": 4.0},
                "fixed",
            ),
        ]
    )
    def test_validate_schedulable_raises_for_unschedulable_tasks(
        self, _scenario, task_kwargs, reason_keyword
    ):
        """Test that validation raises for various unschedulable tasks."""
        # Base task config
        base_config = {
            "id": 1,
            "name": "Test Task",
            "priority": 5,
            "status": TaskStatus.PENDING,
        }
        base_config.update(task_kwargs)

        task = Task(**base_config)

        with self.assertRaises(TaskNotSchedulableError) as context:
            task.validate_schedulable(force_override=False)

        self.assertEqual(context.exception.task_id, 1)
        self.assertIn(reason_keyword.lower(), context.exception.reason.lower())

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

        with self.assertRaises(TaskNotSchedulableError) as context:
            task.validate_schedulable(force_override=False)

        self.assertEqual(context.exception.task_id, 1)
        self.assertIn("schedule", context.exception.reason.lower())
        self.assertIn("force", context.exception.reason.lower())

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

        with self.assertRaises(TaskNotSchedulableError) as context:
            task.validate_schedulable(force_override=True)

        self.assertEqual(context.exception.task_id, 1)
        self.assertIn("fixed", context.exception.reason.lower())


class TestTaskGetUnschedulableReason(unittest.TestCase):
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
        self.assertIsNone(reason)

    @parameterized.expand(
        [
            ("archived_task", {"is_archived": True}, "archived"),
            ("completed_task", {"status": TaskStatus.COMPLETED}, "COMPLETED"),
            ("in_progress_task", {"status": TaskStatus.IN_PROGRESS}, "in progress"),
            ("no_duration", {"estimated_duration": None}, "duration"),
            ("fixed_task", {"is_fixed": True}, "fixed"),
        ]
    )
    def test_get_unschedulable_reason_returns_reason(
        self, _scenario, task_kwargs, expected_keyword
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
        self.assertIsNotNone(reason)
        self.assertIn(expected_keyword.lower(), reason.lower())


class TestTaskShouldCountInWorkload(unittest.TestCase):
    """Test cases for Task.should_count_in_workload() method."""

    @parameterized.expand(
        [
            ("pending_task", TaskStatus.PENDING, True),
            ("in_progress_task", TaskStatus.IN_PROGRESS, True),
            ("completed_task", TaskStatus.COMPLETED, False),
            ("canceled_task", TaskStatus.CANCELED, False),
        ]
    )
    def test_should_count_in_workload_by_status(self, _scenario, status, expected):
        """Test workload counting based on task status."""
        task = Task(name="Test task", priority=100, status=status)
        result = task.should_count_in_workload()
        self.assertEqual(result, expected)

    def test_should_count_in_workload_excludes_archived(self):
        """Test that archived tasks are not counted in workload."""
        # Archived task with PENDING status should not be counted
        task = Task(
            name="Test task", priority=100, status=TaskStatus.PENDING, is_archived=True
        )
        self.assertFalse(task.should_count_in_workload())

        # Archived task with IN_PROGRESS status should not be counted
        task = Task(
            name="Test task",
            priority=100,
            status=TaskStatus.IN_PROGRESS,
            is_archived=True,
        )
        self.assertFalse(task.should_count_in_workload())


if __name__ == "__main__":
    unittest.main()
