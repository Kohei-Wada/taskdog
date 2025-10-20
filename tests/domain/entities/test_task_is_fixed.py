"""Tests for Task.is_schedulable() with is_fixed field."""

import unittest

from domain.entities.task import Task, TaskStatus


class TestTaskIsFixedScheduling(unittest.TestCase):
    """Test cases for Task.is_schedulable() with is_fixed field."""

    def test_is_not_schedulable_with_fixed_task_by_default(self):
        """Test that fixed task is not schedulable without force_override."""
        task = Task(
            name="Fixed task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=True,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_not_schedulable_with_fixed_task_even_when_forced(self):
        """Test that fixed task is NOT schedulable even with force_override.

        Fixed tasks are always protected to prevent accidental rescheduling
        of immovable constraints (meetings, deadlines, etc.).
        """
        task = Task(
            name="Fixed task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=True,
        )

        result = task.is_schedulable(force_override=True)

        self.assertFalse(result)

    def test_is_schedulable_with_non_fixed_task(self):
        """Test that non-fixed task is schedulable normally."""
        task = Task(
            name="Normal task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=False,
        )

        result = task.is_schedulable(force_override=False)

        self.assertTrue(result)

    def test_fixed_task_with_existing_schedule_not_schedulable(self):
        """Test that fixed task with existing schedule is not schedulable."""
        task = Task(
            name="Fixed scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=True,
            planned_start="2025-01-06 09:00:00",
        )

        result = task.is_schedulable(force_override=False)

        # Both is_fixed and planned_start prevent scheduling
        self.assertFalse(result)

    def test_fixed_task_with_existing_schedule_not_schedulable_even_when_forced(self):
        """Test that fixed task with schedule is NOT schedulable even with force_override.

        Fixed tasks are always protected, regardless of force_override flag.
        """
        task = Task(
            name="Fixed scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=True,
            planned_start="2025-01-06 09:00:00",
        )

        result = task.is_schedulable(force_override=True)

        # is_fixed always prevents scheduling, even with force_override
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
