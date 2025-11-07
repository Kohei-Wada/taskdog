"""Tests for Task.is_schedulable() with is_fixed field."""

import unittest

from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskIsFixedScheduling(unittest.TestCase):
    """Test cases for Task.is_schedulable() with is_fixed field."""

    def test_is_schedulable_with_is_fixed_combinations(self):
        """Test schedulability with various is_fixed, force_override, and schedule combinations.

        Fixed tasks are always protected to prevent accidental rescheduling
        of immovable constraints (meetings, deadlines, etc.).
        """
        test_cases = [
            (True, False, None, False, "fixed task, no force, no schedule"),
            (True, True, None, False, "fixed task, forced, no schedule"),
            (False, False, None, True, "non-fixed task, no force, no schedule"),
            (
                True,
                False,
                "2025-01-06 09:00:00",
                False,
                "fixed task, no force, with schedule",
            ),
            (
                True,
                True,
                "2025-01-06 09:00:00",
                False,
                "fixed task, forced, with schedule (still protected)",
            ),
        ]
        for (
            is_fixed,
            force_override,
            planned_start,
            expected,
            description,
        ) in test_cases:
            with self.subTest(description=description):
                task = Task(
                    name="Test task",
                    priority=100,
                    status=TaskStatus.PENDING,
                    estimated_duration=4.0,
                    is_fixed=is_fixed,
                    planned_start=planned_start,
                )
                result = task.is_schedulable(force_override=force_override)
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
