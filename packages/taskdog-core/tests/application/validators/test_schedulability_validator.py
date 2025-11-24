"""Tests for SchedulabilityValidator."""

import unittest
from datetime import datetime

from parameterized import parameterized

from taskdog_core.application.validators.schedulability_validator import (
    SchedulabilityValidator,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    NoSchedulableTasksError,
    TaskNotFoundException,
)


class TestSchedulabilityValidator(unittest.TestCase):
    """Test cases for SchedulabilityValidator."""

    def setUp(self):
        """Set up test tasks."""
        # Schedulable task (PENDING with estimated_duration)
        self.task1 = Task(
            id=1,
            name="Schedulable Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=5.0,
        )

        # Already scheduled task
        self.task2 = Task(
            id=2,
            name="Scheduled Task",
            priority=3,
            status=TaskStatus.PENDING,
            estimated_duration=3.0,
            planned_start=datetime(2025, 1, 1, 9, 0),
        )

        # Fixed task
        self.task3 = Task(
            id=3,
            name="Fixed Task",
            priority=8,
            status=TaskStatus.PENDING,
            estimated_duration=2.0,
            is_fixed=True,
        )

        # Completed task
        self.task4 = Task(
            id=4,
            name="Completed Task",
            priority=5,
            status=TaskStatus.COMPLETED,
            estimated_duration=4.0,
        )

        # Task without estimated_duration
        self.task5 = Task(
            id=5,
            name="No Estimate Task",
            priority=5,
            status=TaskStatus.PENDING,
        )

        # In-progress task
        self.task6 = Task(
            id=6,
            name="In Progress Task",
            priority=5,
            status=TaskStatus.IN_PROGRESS,
            estimated_duration=3.0,
        )

        # Archived task
        self.task7 = Task(
            id=7,
            name="Archived Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=2.0,
            is_archived=True,
        )

        self.all_tasks = [
            self.task1,
            self.task2,
            self.task3,
            self.task4,
            self.task5,
            self.task6,
            self.task7,
        ]

    def test_validate_single_schedulable_task(self):
        """Test validating a single schedulable task."""
        result = SchedulabilityValidator.validate_and_filter_schedulable_tasks(
            task_ids=[1],
            all_tasks=self.all_tasks,
            force_override=False,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_validate_multiple_schedulable_tasks(self):
        """Test validating multiple schedulable tasks."""
        result = SchedulabilityValidator.validate_and_filter_schedulable_tasks(
            task_ids=[1, 5],  # task5 has no estimate, should fail
            all_tasks=self.all_tasks,
            force_override=False,
        )

        # Only task1 should be schedulable
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_validate_scheduled_task_with_force_override(self):
        """Test that scheduled task becomes schedulable with force_override."""
        result = SchedulabilityValidator.validate_and_filter_schedulable_tasks(
            task_ids=[2],
            all_tasks=self.all_tasks,
            force_override=True,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 2)

    def test_task_not_found_single(self):
        """Test that TaskNotFoundException is raised for non-existent task."""
        with self.assertRaises(TaskNotFoundException) as context:
            SchedulabilityValidator.validate_and_filter_schedulable_tasks(
                task_ids=[999],
                all_tasks=self.all_tasks,
                force_override=False,
            )

        self.assertEqual(context.exception.task_id, 999)

    def test_task_not_found_multiple(self):
        """Test that TaskNotFoundException is raised for multiple non-existent tasks."""
        with self.assertRaises(TaskNotFoundException) as context:
            SchedulabilityValidator.validate_and_filter_schedulable_tasks(
                task_ids=[998, 999],
                all_tasks=self.all_tasks,
                force_override=False,
            )

        # Should mention both IDs in message
        self.assertIn("998", str(context.exception))
        self.assertIn("999", str(context.exception))

    def test_no_schedulable_tasks_single(self):
        """Test NoSchedulableTasksError for single unschedulable task."""
        with self.assertRaises(NoSchedulableTasksError) as context:
            SchedulabilityValidator.validate_and_filter_schedulable_tasks(
                task_ids=[4],  # Completed task
                all_tasks=self.all_tasks,
                force_override=False,
            )

        self.assertEqual(context.exception.task_ids, [4])
        self.assertIn(4, context.exception.reasons)
        self.assertIn("COMPLETED", context.exception.reasons[4])

    def test_no_schedulable_tasks_multiple(self):
        """Test NoSchedulableTasksError for multiple unschedulable tasks."""
        with self.assertRaises(NoSchedulableTasksError) as context:
            SchedulabilityValidator.validate_and_filter_schedulable_tasks(
                task_ids=[3, 4, 5],  # Fixed, Completed, No estimate
                all_tasks=self.all_tasks,
                force_override=False,
            )

        self.assertEqual(context.exception.task_ids, [3, 4, 5])
        self.assertEqual(len(context.exception.reasons), 3)
        self.assertIn("fixed", context.exception.reasons[3].lower())
        self.assertIn("COMPLETED", context.exception.reasons[4])
        self.assertIn("duration", context.exception.reasons[5].lower())

    @parameterized.expand(
        [
            # (task_id, force_override, should_be_schedulable, reason_keyword)
            (1, False, True, None),  # Schedulable task
            (2, False, False, "schedule"),  # Already scheduled
            (2, True, True, None),  # Scheduled but force_override
            (3, False, False, "fixed"),  # Fixed task
            (3, True, False, "fixed"),  # Fixed even with force_override
            (4, False, False, "COMPLETED"),  # Completed task
            (5, False, False, "duration"),  # No estimated_duration
            (6, False, False, "progress"),  # In progress
            (7, False, False, "archived"),  # Archived task
        ]
    )
    def test_schedulability_scenarios(
        self, task_id, force_override, should_be_schedulable, reason_keyword
    ):
        """Test various schedulability scenarios."""
        if should_be_schedulable:
            result = SchedulabilityValidator.validate_and_filter_schedulable_tasks(
                task_ids=[task_id],
                all_tasks=self.all_tasks,
                force_override=force_override,
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, task_id)
        else:
            with self.assertRaises(NoSchedulableTasksError) as context:
                SchedulabilityValidator.validate_and_filter_schedulable_tasks(
                    task_ids=[task_id],
                    all_tasks=self.all_tasks,
                    force_override=force_override,
                )

            self.assertIn(task_id, context.exception.reasons)
            if reason_keyword:
                self.assertIn(
                    reason_keyword.lower(),
                    context.exception.reasons[task_id].lower(),
                )

    def test_mixed_schedulable_and_unschedulable(self):
        """Test filtering when some tasks are schedulable and others are not."""
        result = SchedulabilityValidator.validate_and_filter_schedulable_tasks(
            task_ids=[1, 3, 4],  # Schedulable, Fixed, Completed
            all_tasks=self.all_tasks,
            force_override=False,
        )

        # Only task1 should be returned
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_empty_all_tasks_list(self):
        """Test with empty all_tasks list."""
        with self.assertRaises(TaskNotFoundException):
            SchedulabilityValidator.validate_and_filter_schedulable_tasks(
                task_ids=[1],
                all_tasks=[],
                force_override=False,
            )


if __name__ == "__main__":
    unittest.main()
