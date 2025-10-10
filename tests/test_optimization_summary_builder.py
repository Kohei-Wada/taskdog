"""Tests for OptimizationSummaryBuilder."""

import os
import tempfile
import unittest

from application.services.optimization_summary_builder import OptimizationSummaryBuilder
from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestOptimizationSummaryBuilder(unittest.TestCase):
    """Test cases for OptimizationSummaryBuilder."""

    def setUp(self):
        """Create temporary file and initialize builder for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.builder = OptimizationSummaryBuilder(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_build_with_new_tasks(self):
        """Test build calculates correct counts for newly scheduled tasks."""
        # Create tasks
        task1 = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start="2025-10-14 09:00:00",
            planned_end="2025-10-14 17:00:00",
            estimated_duration=8.0,
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start="2025-10-15 09:00:00",
            planned_end="2025-10-15 17:00:00",
            estimated_duration=8.0,
        )
        self.repository.save(task1)
        self.repository.save(task2)

        modified_tasks = [task1, task2]
        task_states_before = {1: None, 2: None}  # Both were unscheduled
        daily_allocations = {"2025-10-14": 8.0, "2025-10-15": 8.0}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        self.assertEqual(summary.new_count, 2)
        self.assertEqual(summary.rescheduled_count, 0)
        self.assertEqual(summary.total_hours, 16.0)
        self.assertEqual(summary.days_span, 2)
        self.assertEqual(len(summary.overloaded_days), 0)

    def test_build_with_rescheduled_tasks(self):
        """Test build calculates correct counts for rescheduled tasks."""
        task = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start="2025-10-15 09:00:00",
            planned_end="2025-10-15 17:00:00",
            estimated_duration=8.0,
        )
        self.repository.save(task)

        modified_tasks = [task]
        task_states_before = {1: "2025-10-14 09:00:00"}  # Was previously scheduled
        daily_allocations = {"2025-10-15": 8.0}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        self.assertEqual(summary.new_count, 0)
        self.assertEqual(summary.rescheduled_count, 1)

    def test_build_with_deadline_conflicts(self):
        """Test build detects deadline conflicts."""
        task = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start="2025-10-14 09:00:00",
            planned_end="2025-10-16 17:00:00",  # Ends after deadline
            deadline="2025-10-15 18:00:00",
            estimated_duration=16.0,
        )
        self.repository.save(task)

        modified_tasks = [task]
        task_states_before = {1: None}
        daily_allocations = {"2025-10-14": 8.0, "2025-10-15": 8.0}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        self.assertEqual(summary.deadline_conflicts, 1)

    def test_build_with_overloaded_days(self):
        """Test build detects overloaded days."""
        task = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start="2025-10-14 09:00:00",
            planned_end="2025-10-14 17:00:00",
            estimated_duration=10.0,
        )
        self.repository.save(task)

        modified_tasks = [task]
        task_states_before = {1: None}
        daily_allocations = {"2025-10-14": 10.0}  # Exceeds max
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        self.assertEqual(len(summary.overloaded_days), 1)
        self.assertEqual(summary.overloaded_days[0], ("2025-10-14", 10.0))

    def test_build_with_unscheduled_tasks(self):
        """Test build detects unscheduled tasks."""
        # Create scheduled task
        scheduled_task = Task(
            id=1,
            name="Scheduled",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start="2025-10-14 09:00:00",
            planned_end="2025-10-14 17:00:00",
            estimated_duration=8.0,
        )
        # Create unscheduled task
        unscheduled_task = Task(
            id=2,
            name="Unscheduled",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=8.0,
            # No planned_start/end
        )
        self.repository.save(scheduled_task)
        self.repository.save(unscheduled_task)

        modified_tasks = [scheduled_task]
        task_states_before = {1: None}
        daily_allocations = {"2025-10-14": 8.0}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        self.assertEqual(len(summary.unscheduled_tasks), 1)
        self.assertEqual(summary.unscheduled_tasks[0].id, 2)

    def test_build_ignores_completed_tasks(self):
        """Test build ignores completed tasks when checking unscheduled."""
        # Create completed task without schedule
        completed_task = Task(
            id=1,
            name="Completed",
            priority=1,
            status=TaskStatus.COMPLETED,
            estimated_duration=8.0,
            # No planned_start/end
        )
        self.repository.save(completed_task)

        modified_tasks = []
        task_states_before = {}
        daily_allocations = {}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        self.assertEqual(len(summary.unscheduled_tasks), 0)


if __name__ == "__main__":
    unittest.main()
