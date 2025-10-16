"""Unit tests for WorkloadAllocator service."""

import unittest
from datetime import datetime
from unittest.mock import Mock

from application.services.workload_allocator import WorkloadAllocator
from domain.entities.task import Task, TaskStatus
from domain.services.deadline_calculator import DeadlineCalculator


class TestWorkloadAllocator(unittest.TestCase):
    """Test cases for WorkloadAllocator."""

    def setUp(self):
        """Set up test fixtures."""
        self.start_date = datetime(2025, 1, 6, 9, 0, 0)  # Monday 9:00 AM
        self.allocator = WorkloadAllocator(max_hours_per_day=6.0, start_date=self.start_date)

    def test_allocate_single_day_task(self):
        """Test allocating a task that fits in a single day."""
        task = Task(
            id=1,
            name="Short task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
        )

        result = self.allocator.allocate_timeblock(task)

        self.assertIsNotNone(result)
        self.assertEqual(result.planned_start, "2025-01-06 09:00:00")
        self.assertEqual(result.planned_end, "2025-01-06 18:00:00")
        self.assertEqual(result.daily_allocations, {"2025-01-06": 4.0})
        self.assertEqual(self.allocator.daily_allocations, {"2025-01-06": 4.0})

    def test_allocate_multi_day_task(self):
        """Test allocating a task that spans multiple days."""
        task = Task(
            id=1,
            name="Long task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=15.0,
        )

        result = self.allocator.allocate_timeblock(task)

        self.assertIsNotNone(result)
        self.assertEqual(result.planned_start, "2025-01-06 09:00:00")  # Monday
        self.assertEqual(result.planned_end, "2025-01-08 18:00:00")  # Wednesday
        self.assertEqual(
            result.daily_allocations,
            {
                "2025-01-06": 6.0,  # Monday
                "2025-01-07": 6.0,  # Tuesday
                "2025-01-08": 3.0,  # Wednesday
            },
        )

    def test_allocate_skips_weekends(self):
        """Test that allocation skips weekends."""
        # Start on Friday
        friday_allocator = WorkloadAllocator(
            max_hours_per_day=6.0, start_date=datetime(2025, 1, 10, 9, 0, 0)
        )
        task = Task(
            id=1,
            name="Task spanning weekend",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
        )

        result = friday_allocator.allocate_timeblock(task)

        self.assertIsNotNone(result)
        self.assertEqual(result.planned_start, "2025-01-10 09:00:00")  # Friday
        self.assertEqual(result.planned_end, "2025-01-13 18:00:00")  # Monday
        # Should skip Saturday (1/11) and Sunday (1/12)
        self.assertEqual(
            result.daily_allocations,
            {
                "2025-01-10": 6.0,  # Friday
                "2025-01-13": 4.0,  # Monday
            },
        )

    def test_allocate_respects_max_hours_per_day(self):
        """Test that allocation respects max_hours_per_day constraint."""
        # Pre-allocate 4 hours on Monday
        self.allocator.daily_allocations["2025-01-06"] = 4.0

        task = Task(
            id=1,
            name="Task with constraint",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=5.0,
        )

        result = self.allocator.allocate_timeblock(task)

        self.assertIsNotNone(result)
        self.assertEqual(result.planned_start, "2025-01-06 09:00:00")  # Monday
        self.assertEqual(result.planned_end, "2025-01-07 18:00:00")  # Tuesday
        # Monday has 4 hours pre-allocated, so only 2 hours available
        # Remaining 3 hours go to Tuesday
        self.assertEqual(
            result.daily_allocations,
            {
                "2025-01-06": 2.0,  # Monday (only 2 hours available)
                "2025-01-07": 3.0,  # Tuesday
            },
        )
        # Check total allocations updated
        self.assertEqual(self.allocator.daily_allocations["2025-01-06"], 6.0)
        self.assertEqual(self.allocator.daily_allocations["2025-01-07"], 3.0)

    def test_allocate_fails_if_deadline_exceeded(self):
        """Test that allocation fails if deadline cannot be met."""
        task = Task(
            id=1,
            name="Task with tight deadline",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=20.0,
            deadline="2025-01-07 18:00:00",  # Tuesday (only 2 days available)
        )

        result = self.allocator.allocate_timeblock(task)

        # Should fail because 20 hours cannot fit in 2 days (max 12 hours)
        self.assertIsNone(result)

    def test_allocate_without_estimated_duration(self):
        """Test that allocation fails for tasks without estimated duration."""
        task = Task(
            id=1,
            name="Task without duration",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=None,
        )

        result = self.allocator.allocate_timeblock(task)

        self.assertIsNone(result)

    def test_initialize_allocations_with_existing_schedules(self):
        """Test initialization with tasks that have existing schedules."""
        tasks = [
            Task(
                id=1,
                name="Existing task",
                priority=100,
                status=TaskStatus.PENDING,
                planned_start="2025-01-06 09:00:00",
                estimated_duration=4.0,
                daily_allocations={"2025-01-06": 4.0},
            ),
            Task(
                id=2,
                name="Another task",
                priority=100,
                status=TaskStatus.IN_PROGRESS,
                planned_start="2025-01-07 09:00:00",
                estimated_duration=3.0,
                daily_allocations={"2025-01-07": 3.0},
            ),
        ]

        self.allocator.initialize_allocations(tasks, force_override=False)

        self.assertEqual(
            self.allocator.daily_allocations,
            {
                "2025-01-06": 4.0,
                "2025-01-07": 3.0,
            },
        )

    def test_initialize_allocations_skips_completed_tasks(self):
        """Test that initialization skips completed tasks."""
        tasks = [
            Task(
                id=1,
                name="Completed task",
                priority=100,
                status=TaskStatus.COMPLETED,
                planned_start="2025-01-06 09:00:00",
                estimated_duration=4.0,
                daily_allocations={"2025-01-06": 4.0},
            ),
        ]

        self.allocator.initialize_allocations(tasks, force_override=False)

        self.assertEqual(self.allocator.daily_allocations, {})

    def test_initialize_allocations_with_force_override_skips_pending(self):
        """Test that initialization with force_override skips PENDING tasks."""
        tasks = [
            Task(
                id=1,
                name="Pending task",
                priority=100,
                status=TaskStatus.PENDING,
                planned_start="2025-01-06 09:00:00",
                estimated_duration=4.0,
                daily_allocations={"2025-01-06": 4.0},
            ),
            Task(
                id=2,
                name="In-progress task",
                priority=100,
                status=TaskStatus.IN_PROGRESS,
                planned_start="2025-01-07 09:00:00",
                estimated_duration=3.0,
                daily_allocations={"2025-01-07": 3.0},
            ),
        ]

        self.allocator.initialize_allocations(tasks, force_override=True)

        # With force_override=True, only IN_PROGRESS tasks are counted
        self.assertEqual(self.allocator.daily_allocations, {"2025-01-07": 3.0})

    def test_allocate_multiple_tasks_sequentially(self):
        """Test allocating multiple tasks in sequence."""
        task1 = Task(
            id=1,
            name="First task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
        )
        task2 = Task(
            id=2,
            name="Second task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=5.0,
        )

        result1 = self.allocator.allocate_timeblock(task1)
        result2 = self.allocator.allocate_timeblock(task2)

        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)

        # First task should take 4 hours on Monday
        self.assertEqual(result1.daily_allocations, {"2025-01-06": 4.0})

        # Second task should take remaining 2 hours on Monday + 3 hours on Tuesday
        self.assertEqual(result2.daily_allocations, {"2025-01-06": 2.0, "2025-01-07": 3.0})

    def test_get_effective_deadline_uses_own_deadline(self):
        """Test that get_effective_deadline returns task's own deadline when no parent exists."""
        mock_repo = Mock()

        task = Task(
            id=1,
            name="Task with deadline",
            priority=100,
            status=TaskStatus.PENDING,
            deadline="2025-01-10 18:00:00",
        )

        effective_deadline = DeadlineCalculator.get_effective_deadline(task, mock_repo)
        self.assertEqual(effective_deadline, "2025-01-10 18:00:00")

    def test_allocate_multiple_tasks_with_same_tight_deadline(self):
        """Test that multiple tasks with same tight deadline respect max_hours_per_day constraint.

        This test reproduces issue #53: When multiple tasks have the same tight deadline,
        the allocator should fail to schedule tasks that would exceed the max hours constraint,
        rather than violating the constraint.
        """
        # Start on Thursday 10/16, deadline on Friday 10/17
        # Max 5 hours per day, so 2 days = 10 hours max capacity
        thursday = datetime(2025, 10, 16, 9, 0, 0)
        allocator = WorkloadAllocator(max_hours_per_day=5.0, start_date=thursday)

        # Create 6 tasks with same deadline, totaling 11 hours (exceeds 10h capacity)
        tasks = [
            Task(id=7, name="Task 7", priority=100, status=TaskStatus.PENDING,
                 estimated_duration=3.0, deadline="2025-10-17 18:00:00"),
            Task(id=10, name="Task 10", priority=100, status=TaskStatus.PENDING,
                 estimated_duration=1.0, deadline="2025-10-17 18:00:00"),
            Task(id=11, name="Task 11", priority=100, status=TaskStatus.PENDING,
                 estimated_duration=1.0, deadline="2025-10-17 18:00:00"),
            Task(id=17, name="Task 17", priority=100, status=TaskStatus.PENDING,
                 estimated_duration=3.0, deadline="2025-10-17 18:00:00"),
            Task(id=22, name="Task 22", priority=100, status=TaskStatus.PENDING,
                 estimated_duration=1.0, deadline="2025-10-17 18:00:00"),
            Task(id=26, name="Task 26", priority=100, status=TaskStatus.PENDING,
                 estimated_duration=2.0, deadline="2025-10-17 18:00:00"),
        ]

        # Schedule tasks sequentially
        scheduled_tasks = []
        failed_tasks = []

        for task in tasks:
            result = allocator.allocate_timeblock(task)
            if result:
                scheduled_tasks.append(result)
            else:
                failed_tasks.append(task)

        # Calculate hours from successfully scheduled tasks
        actual_daily_hours = {}
        for task in scheduled_tasks:
            if task.daily_allocations:
                for date_str, hours in task.daily_allocations.items():
                    actual_daily_hours[date_str] = actual_daily_hours.get(date_str, 0.0) + hours

        # Check for phantom allocations: allocator.daily_allocations should match actual task allocations
        for date_str in allocator.daily_allocations:
            allocator_hours = allocator.daily_allocations[date_str]
            actual_hours = actual_daily_hours.get(date_str, 0.0)
            self.assertAlmostEqual(
                allocator_hours, actual_hours,
                places=5,
                msg=f"Phantom allocation detected on {date_str}: allocator has {allocator_hours}h "
                    f"but actual tasks only have {actual_hours}h"
            )

        # Verify that max_hours_per_day is never exceeded
        for date_str, hours in allocator.daily_allocations.items():
            self.assertLessEqual(
                hours, 5.0,
                f"Day {date_str} has {hours}h scheduled, exceeding max 5.0h"
            )

        # Verify that some tasks failed to schedule (can't fit 11h in 10h capacity)
        self.assertGreater(
            len(failed_tasks), 0,
            "Expected some tasks to fail scheduling when capacity exceeded"
        )

        # Calculate total scheduled hours
        total_scheduled = sum(t.estimated_duration for t in scheduled_tasks)
        self.assertLessEqual(
            total_scheduled, 10.0,
            f"Total scheduled {total_scheduled}h exceeds capacity 10.0h"
        )


if __name__ == "__main__":
    unittest.main()
