"""Tests for DependencyAwareOptimizationStrategy."""

import os
import tempfile
import unittest
from datetime import datetime

from application.dto.create_task_request import CreateTaskRequest
from application.dto.optimize_schedule_request import OptimizeScheduleRequest
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from shared.config_manager import ConfigManager


class TestDependencyAwareOptimizationStrategy(unittest.TestCase):
    """Test cases for DependencyAwareOptimizationStrategy."""

    def setUp(self):
        """Create temporary file and initialize use case for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.create_use_case = CreateTaskUseCase(self.repository)
        self.optimize_use_case = OptimizeScheduleUseCase(self.repository, ConfigManager.load())

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_dependency_aware_sorts_by_deadline_then_priority(self):
        """Test that dependency-aware strategy sorts by deadline, then priority."""
        # Create tasks with different deadlines and priorities
        input_dto1 = CreateTaskRequest(
            name="High Priority, Late Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-25 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="Low Priority, Early Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline="2025-10-22 18:00:00",
        )
        self.create_use_case.execute(input_dto2)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="dependency_aware",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Early deadline task should be scheduled first
        tasks_by_name = {t.name: t for t in result.successful_tasks}
        early_deadline = tasks_by_name["Low Priority, Early Deadline"]
        late_deadline = tasks_by_name["High Priority, Late Deadline"]

        self.assertEqual(early_deadline.planned_start, "2025-10-20 09:00:00")
        self.assertEqual(late_deadline.planned_start, "2025-10-21 09:00:00")

    def test_dependency_aware_uses_priority_as_tiebreaker(self):
        """Test that priority is used when deadlines are equal."""
        # Create tasks with same deadline but different priorities
        input_dto1 = CreateTaskRequest(
            name="Low Priority",
            priority=50,
            estimated_duration=6.0,
            deadline="2025-10-25 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="High Priority",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-25 18:00:00",  # Same deadline
        )
        self.create_use_case.execute(input_dto2)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="dependency_aware",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # High priority task should be scheduled first (same deadline)
        tasks_by_name = {t.name: t for t in result.successful_tasks}
        low_priority = tasks_by_name["Low Priority"]
        high_priority = tasks_by_name["High Priority"]

        self.assertEqual(high_priority.planned_start, "2025-10-20 09:00:00")
        self.assertEqual(low_priority.planned_start, "2025-10-21 09:00:00")

    def test_dependency_aware_schedules_no_deadline_tasks_last(self):
        """Test that tasks without deadlines are scheduled last."""
        # Create tasks with and without deadlines
        input_dto1 = CreateTaskRequest(
            name="With Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline="2025-10-25 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="No Deadline",
            priority=100,  # Higher priority but no deadline
            estimated_duration=6.0,
            deadline=None,
        )
        self.create_use_case.execute(input_dto2)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="dependency_aware",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task with deadline should be scheduled first
        tasks_by_name = {t.name: t for t in result.successful_tasks}
        with_deadline = tasks_by_name["With Deadline"]
        no_deadline = tasks_by_name["No Deadline"]

        self.assertEqual(with_deadline.planned_start, "2025-10-20 09:00:00")
        self.assertEqual(no_deadline.planned_start, "2025-10-21 09:00:00")

    def test_dependency_aware_uses_greedy_allocation(self):
        """Test that dependency-aware strategy uses greedy allocation."""
        # Create task that requires multiple days
        input_dto = CreateTaskRequest(
            name="Multi-day Task",
            priority=100,
            estimated_duration=15.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="dependency_aware",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        task = result.successful_tasks[0]

        # Verify greedy allocation: fills each day to maximum
        self.assertIsNotNone(task.daily_allocations)
        self.assertAlmostEqual(task.daily_allocations.get("2025-10-20", 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get("2025-10-21", 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get("2025-10-22", 0.0), 3.0, places=5)

    def test_dependency_aware_respects_deadlines(self):
        """Test that dependency-aware strategy respects deadlines."""
        # Create task with impossible deadline
        input_dto = CreateTaskRequest(
            name="Impossible Deadline",
            priority=100,
            estimated_duration=30.0,
            deadline="2025-10-22 18:00:00",  # Only 3 days available
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="dependency_aware",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Task should fail to schedule
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 1)

    def test_dependency_aware_handles_multiple_tasks(self):
        """Test that dependency-aware strategy handles multiple tasks correctly."""
        # Create multiple tasks with different characteristics
        input_dto1 = CreateTaskRequest(
            name="Urgent Low Priority",
            priority=30,
            estimated_duration=6.0,
            deadline="2025-10-21 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="Medium Priority Medium Deadline",
            priority=60,
            estimated_duration=6.0,
            deadline="2025-10-23 18:00:00",
        )
        self.create_use_case.execute(input_dto2)

        input_dto3 = CreateTaskRequest(
            name="High Priority Late Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-25 18:00:00",
        )
        self.create_use_case.execute(input_dto3)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="dependency_aware",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify scheduling order (deadline first, then priority)
        tasks_by_name = {t.name: t for t in result.successful_tasks}

        # Earliest deadline should be first
        self.assertEqual(tasks_by_name["Urgent Low Priority"].planned_start, "2025-10-20 09:00:00")
        # Middle deadline should be second
        self.assertEqual(
            tasks_by_name["Medium Priority Medium Deadline"].planned_start, "2025-10-21 09:00:00"
        )
        # Latest deadline should be last
        self.assertEqual(
            tasks_by_name["High Priority Late Deadline"].planned_start, "2025-10-22 09:00:00"
        )


if __name__ == "__main__":
    unittest.main()
