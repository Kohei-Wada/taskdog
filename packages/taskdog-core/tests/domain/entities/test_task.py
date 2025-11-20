"""Tests for Task entity business logic methods."""

import unittest

from parameterized import parameterized

from taskdog_core.domain.entities.task import Task, TaskStatus


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
