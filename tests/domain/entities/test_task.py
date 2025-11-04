"""Tests for Task entity business logic methods."""

import unittest

from domain.entities.task import Task, TaskStatus


class TestTaskIsSchedulable(unittest.TestCase):
    """Test cases for Task.is_schedulable() method."""

    def test_is_schedulable_by_status_and_duration(self):
        """Test schedulability based on status and estimated_duration."""
        test_cases = [
            (TaskStatus.PENDING, 4.0, True, "PENDING with duration"),
            (TaskStatus.COMPLETED, 4.0, False, "COMPLETED task"),
            (TaskStatus.IN_PROGRESS, 4.0, False, "IN_PROGRESS task"),
            (TaskStatus.CANCELED, 4.0, False, "CANCELED task"),
            (TaskStatus.PENDING, None, False, "PENDING without duration"),
        ]
        for status, duration, expected, description in test_cases:
            with self.subTest(description=description):
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

    def test_should_count_in_workload_by_status(self):
        """Test workload counting based on task status."""
        test_cases = [
            (TaskStatus.PENDING, True, "PENDING task"),
            (TaskStatus.IN_PROGRESS, True, "IN_PROGRESS task"),
            (TaskStatus.COMPLETED, False, "COMPLETED task"),
            (TaskStatus.CANCELED, False, "CANCELED task"),
        ]
        for status, expected, description in test_cases:
            with self.subTest(description=description):
                task = Task(name="Test task", priority=100, status=status)
                result = task.should_count_in_workload()
                self.assertEqual(result, expected)

    def test_should_count_in_workload_excludes_archived(self):
        """Test that archived tasks are not counted in workload."""
        # Archived task with PENDING status should not be counted
        task = Task(name="Test task", priority=100, status=TaskStatus.PENDING, is_archived=True)
        self.assertFalse(task.should_count_in_workload())

        # Archived task with IN_PROGRESS status should not be counted
        task = Task(name="Test task", priority=100, status=TaskStatus.IN_PROGRESS, is_archived=True)
        self.assertFalse(task.should_count_in_workload())


if __name__ == "__main__":
    unittest.main()
