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

    def test_is_schedulable_with_fixed_task_when_forced(self):
        """Test that fixed task is schedulable with force_override."""
        task = Task(
            name="Fixed task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=True,
        )

        result = task.is_schedulable(force_override=True)

        self.assertTrue(result)

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

    def test_fixed_task_with_existing_schedule_schedulable_when_forced(self):
        """Test that fixed task with schedule is schedulable with force_override."""
        task = Task(
            name="Fixed scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_fixed=True,
            planned_start="2025-01-06 09:00:00",
        )

        result = task.is_schedulable(force_override=True)

        # force_override bypasses both is_fixed and existing schedule checks
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
