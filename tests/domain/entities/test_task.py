"""Tests for Task entity business logic methods."""

import unittest

from domain.entities.task import Task, TaskStatus


class TestTaskIsSchedulable(unittest.TestCase):
    """Test cases for Task.is_schedulable() method."""

    def test_is_schedulable_with_pending_task_and_duration(self):
        """Test that PENDING task with estimated_duration is schedulable."""
        task = Task(
            name="Test Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
        )

        result = task.is_schedulable(force_override=False)

        self.assertTrue(result)

    def test_is_not_schedulable_with_completed_task(self):
        """Test that COMPLETED tasks are not schedulable."""
        task = Task(
            name="Completed task",
            priority=100,
            status=TaskStatus.COMPLETED,
            estimated_duration=4.0,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_not_schedulable_with_deleted_task(self):
        """Test that deleted tasks are not schedulable."""
        task = Task(
            name="Deleted task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_deleted=True,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_not_schedulable_with_in_progress_task(self):
        """Test that IN_PROGRESS tasks are not reschedulable."""
        task = Task(
            name="In-progress task",
            priority=100,
            status=TaskStatus.IN_PROGRESS,
            estimated_duration=4.0,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_not_schedulable_without_duration(self):
        """Test that tasks without estimated_duration are not schedulable."""
        task = Task(
            name="Task without duration",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=None,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

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

    def test_is_not_schedulable_with_canceled_status(self):
        """Test that CANCELED tasks are not schedulable."""
        task = Task(
            name="Canceled task",
            priority=100,
            status=TaskStatus.CANCELED,
            estimated_duration=4.0,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)


class TestTaskShouldCountInWorkload(unittest.TestCase):
    """Test cases for Task.should_count_in_workload() method."""

    def test_pending_task_counts_in_workload(self):
        """Test that PENDING tasks count in workload."""
        task = Task(
            name="Pending task",
            priority=100,
            status=TaskStatus.PENDING,
        )

        result = task.should_count_in_workload()

        self.assertTrue(result)

    def test_in_progress_task_counts_in_workload(self):
        """Test that IN_PROGRESS tasks count in workload."""
        task = Task(
            name="In-progress task",
            priority=100,
            status=TaskStatus.IN_PROGRESS,
        )

        result = task.should_count_in_workload()

        self.assertTrue(result)

    def test_completed_task_does_not_count_in_workload(self):
        """Test that COMPLETED tasks do not count in workload."""
        task = Task(
            name="Completed task",
            priority=100,
            status=TaskStatus.COMPLETED,
        )

        result = task.should_count_in_workload()

        self.assertFalse(result)

    def test_canceled_task_does_not_count_in_workload(self):
        """Test that CANCELED tasks do not count in workload."""
        task = Task(
            name="Canceled task",
            priority=100,
            status=TaskStatus.CANCELED,
        )

        result = task.should_count_in_workload()

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
