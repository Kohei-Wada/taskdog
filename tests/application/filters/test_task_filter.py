"""Unit tests for TaskFilter service."""

import unittest

from application.services.task_filter import TaskFilter
from domain.entities.task import Task, TaskStatus


class TestTaskFilter(unittest.TestCase):
    """Test cases for TaskFilter."""

    def setUp(self):
        """Set up test fixtures."""
        self.filter = TaskFilter()

    def test_should_schedule_pending_task_with_duration(self):
        """Test that PENDING task with estimated_duration should be scheduled."""
        task = Task(
            id=1,
            name="Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
        )

        result = self.filter.should_schedule_task(task, force_override=False)

        self.assertTrue(result)

    def test_should_not_schedule_completed_task(self):
        """Test that COMPLETED tasks should not be scheduled."""
        task = Task(
            id=1,
            name="Completed task",
            priority=100,
            status=TaskStatus.COMPLETED,
            estimated_duration=4.0,
        )

        result = self.filter.should_schedule_task(task, force_override=False)

        self.assertFalse(result)

    def test_should_not_schedule_in_progress_task(self):
        """Test that IN_PROGRESS tasks should not be rescheduled."""
        task = Task(
            id=1,
            name="In-progress task",
            priority=100,
            status=TaskStatus.IN_PROGRESS,
            estimated_duration=4.0,
        )

        result = self.filter.should_schedule_task(task, force_override=False)

        self.assertFalse(result)

    def test_should_not_schedule_task_without_duration(self):
        """Test that tasks without estimated_duration should not be scheduled."""
        task = Task(
            id=1,
            name="Task without duration",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=None,
        )

        result = self.filter.should_schedule_task(task, force_override=False)

        self.assertFalse(result)

    def test_should_not_schedule_task_with_existing_schedule_by_default(self):
        """Test that tasks with existing schedules are skipped by default."""
        task = Task(
            id=1,
            name="Scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            planned_start="2025-01-06 09:00:00",
        )

        result = self.filter.should_schedule_task(task, force_override=False)

        self.assertFalse(result)

    def test_should_schedule_task_with_existing_schedule_when_forced(self):
        """Test that tasks with existing schedules are included with force_override."""
        task = Task(
            id=1,
            name="Scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            planned_start="2025-01-06 09:00:00",
        )

        result = self.filter.should_schedule_task(task, force_override=True)

        self.assertTrue(result)

    def test_get_schedulable_tasks_filters_correctly(self):
        """Test that get_schedulable_tasks filters tasks correctly."""
        tasks = [
            Task(
                id=1,
                name="Schedulable task",
                priority=100,
                status=TaskStatus.PENDING,
                estimated_duration=4.0,
            ),
            Task(
                id=2,
                name="Completed task",
                priority=100,
                status=TaskStatus.COMPLETED,
                estimated_duration=3.0,
            ),
            Task(
                id=3,
                name="In-progress task",
                priority=100,
                status=TaskStatus.IN_PROGRESS,
                estimated_duration=5.0,
            ),
            Task(
                id=4,
                name="Task without duration",
                priority=100,
                status=TaskStatus.PENDING,
                estimated_duration=None,
            ),
            Task(
                id=5,
                name="Task with schedule",
                priority=100,
                status=TaskStatus.PENDING,
                estimated_duration=2.0,
                planned_start="2025-01-06 09:00:00",
            ),
        ]

        result = self.filter.get_schedulable_tasks(tasks, force_override=False)

        # Only task 1 should be schedulable
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_get_schedulable_tasks_with_force_override(self):
        """Test that get_schedulable_tasks includes existing schedules with force_override."""
        tasks = [
            Task(
                id=1,
                name="Schedulable task",
                priority=100,
                status=TaskStatus.PENDING,
                estimated_duration=4.0,
            ),
            Task(
                id=2,
                name="Task with schedule",
                priority=100,
                status=TaskStatus.PENDING,
                estimated_duration=2.0,
                planned_start="2025-01-06 09:00:00",
            ),
            Task(
                id=3,
                name="In-progress task",
                priority=100,
                status=TaskStatus.IN_PROGRESS,
                estimated_duration=5.0,
                planned_start="2025-01-07 09:00:00",
            ),
        ]

        result = self.filter.get_schedulable_tasks(tasks, force_override=True)

        # Tasks 1 and 2 should be schedulable (not task 3 which is IN_PROGRESS)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)

    def test_get_schedulable_tasks_returns_empty_list_when_none_match(self):
        """Test that get_schedulable_tasks returns empty list when no tasks match."""
        tasks = [
            Task(
                id=1,
                name="Completed task",
                priority=100,
                status=TaskStatus.COMPLETED,
                estimated_duration=4.0,
            ),
        ]

        result = self.filter.get_schedulable_tasks(tasks, force_override=False)

        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
