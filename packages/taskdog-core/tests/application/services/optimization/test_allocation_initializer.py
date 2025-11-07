"""Tests for AllocationInitializer."""

import unittest
from datetime import date, datetime
from unittest.mock import Mock

from taskdog_core.application.services.optimization.allocation_initializer import (
    AllocationInitializer,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestAllocationInitializer(unittest.TestCase):
    """Test cases for AllocationInitializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.initializer = AllocationInitializer()

    def test_empty_task_list_returns_empty_allocations(self):
        """Test that empty task list returns empty allocations."""
        allocations = self.initializer.initialize_allocations([], force_override=False)
        self.assertEqual(allocations, {})

    def test_includes_task_with_planned_schedule(self):
        """Test that tasks with planned schedules are included."""
        task = Task(
            id=1,
            name="Scheduled Task",
            priority=5,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 18, 0, 0),
            estimated_duration=12.0,
            daily_allocations={
                date(2025, 10, 20): 6.0,
                date(2025, 10, 21): 6.0,
            },
        )

        allocations = self.initializer.initialize_allocations(
            [task], force_override=False
        )

        self.assertEqual(allocations[date(2025, 10, 20)], 6.0)
        self.assertEqual(allocations[date(2025, 10, 21)], 6.0)

    def test_skips_tasks_without_planned_start(self):
        """Test that tasks without planned_start are skipped."""
        task = Task(
            id=1,
            name="No Schedule",
            priority=5,
            estimated_duration=10.0,
            # No planned_start/planned_end
        )

        allocations = self.initializer.initialize_allocations(
            [task], force_override=False
        )
        self.assertEqual(allocations, {})

    def test_skips_tasks_without_estimated_duration(self):
        """Test that tasks without estimated_duration are skipped."""
        task = Task(
            id=1,
            name="No Duration",
            priority=5,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 18, 0, 0),
            # No estimated_duration
        )

        allocations = self.initializer.initialize_allocations(
            [task], force_override=False
        )
        self.assertEqual(allocations, {})

    def test_skips_completed_tasks(self):
        """Test that completed tasks are skipped (don't count in future workload)."""
        task = Task(
            id=1,
            name="Completed Task",
            priority=5,
            status=TaskStatus.COMPLETED,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 18, 0, 0),
            estimated_duration=12.0,
            daily_allocations={
                date(2025, 10, 20): 6.0,
                date(2025, 10, 21): 6.0,
            },
        )

        allocations = self.initializer.initialize_allocations(
            [task], force_override=False
        )
        self.assertEqual(allocations, {})

    def test_includes_fixed_tasks_even_with_force_override(self):
        """Test that fixed tasks are always included, even when force_override=True."""
        task = Task(
            id=1,
            name="Fixed Task",
            priority=5,
            status=TaskStatus.PENDING,
            is_fixed=True,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 18, 0, 0),
            estimated_duration=12.0,
            daily_allocations={
                date(2025, 10, 20): 6.0,
                date(2025, 10, 21): 6.0,
            },
        )

        allocations = self.initializer.initialize_allocations(
            [task], force_override=True
        )

        # Fixed task should be included even with force_override
        self.assertEqual(allocations[date(2025, 10, 20)], 6.0)
        self.assertEqual(allocations[date(2025, 10, 21)], 6.0)

    def test_includes_in_progress_tasks_even_with_force_override(self):
        """Test that IN_PROGRESS tasks are always included, even when force_override=True."""
        task = Task(
            id=1,
            name="In Progress Task",
            priority=5,
            status=TaskStatus.IN_PROGRESS,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 18, 0, 0),
            estimated_duration=12.0,
            actual_start=datetime(2025, 10, 20, 9, 0, 0),
            daily_allocations={
                date(2025, 10, 20): 6.0,
                date(2025, 10, 21): 6.0,
            },
        )

        allocations = self.initializer.initialize_allocations(
            [task], force_override=True
        )

        # IN_PROGRESS task should be included even with force_override
        self.assertEqual(allocations[date(2025, 10, 20)], 6.0)
        self.assertEqual(allocations[date(2025, 10, 21)], 6.0)

    def test_skips_pending_non_fixed_tasks_with_force_override(self):
        """Test that PENDING non-fixed tasks are skipped when force_override=True."""
        task = Task(
            id=1,
            name="Pending Task",
            priority=5,
            status=TaskStatus.PENDING,
            is_fixed=False,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 18, 0, 0),
            estimated_duration=12.0,
            daily_allocations={
                date(2025, 10, 20): 6.0,
                date(2025, 10, 21): 6.0,
            },
        )

        # With force_override=False, task should be included
        allocations_no_override = self.initializer.initialize_allocations(
            [task], force_override=False
        )
        self.assertEqual(allocations_no_override[date(2025, 10, 20)], 6.0)

        # With force_override=True, task should be skipped
        allocations_with_override = self.initializer.initialize_allocations(
            [task], force_override=True
        )
        self.assertEqual(allocations_with_override, {})

    def test_accumulates_hours_across_multiple_tasks(self):
        """Test that hours from multiple tasks are accumulated correctly."""
        task1 = Task(
            id=1,
            name="Task 1",
            priority=5,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 20, 18, 0, 0),
            estimated_duration=6.0,
            daily_allocations={
                date(2025, 10, 20): 6.0,
            },
        )

        task2 = Task(
            id=2,
            name="Task 2",
            priority=5,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 18, 0, 0),
            estimated_duration=10.0,
            daily_allocations={
                date(2025, 10, 20): 4.0,
                date(2025, 10, 21): 6.0,
            },
        )

        allocations = self.initializer.initialize_allocations(
            [task1, task2], force_override=False
        )

        # Oct 20: 6.0 (task1) + 4.0 (task2) = 10.0
        self.assertEqual(allocations[date(2025, 10, 20)], 10.0)
        # Oct 21: 6.0 (task2 only)
        self.assertEqual(allocations[date(2025, 10, 21)], 6.0)

    def test_uses_workload_calculator_when_daily_allocations_missing(self):
        """Test that WorkloadCalculator is used when task.daily_allocations is None."""
        task = Task(
            id=1,
            name="Task Without Allocations",
            priority=5,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 15, 0, 0),
            estimated_duration=12.0,
            # daily_allocations is None, should use WorkloadCalculator
        )

        # Mock WorkloadCalculator
        mock_calculator = Mock()
        mock_calculator.get_task_daily_hours.return_value = {
            date(2025, 10, 20): 6.0,
            date(2025, 10, 21): 6.0,
        }

        initializer = AllocationInitializer(workload_calculator=mock_calculator)
        allocations = initializer.initialize_allocations([task], force_override=False)

        # Should call WorkloadCalculator
        mock_calculator.get_task_daily_hours.assert_called_once_with(task)

        # Should return calculated allocations
        self.assertEqual(allocations[date(2025, 10, 20)], 6.0)
        self.assertEqual(allocations[date(2025, 10, 21)], 6.0)


if __name__ == "__main__":
    unittest.main()
