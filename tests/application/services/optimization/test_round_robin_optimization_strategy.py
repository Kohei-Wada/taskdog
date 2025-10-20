"""Tests for RoundRobinOptimizationStrategy."""

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


class TestRoundRobinOptimizationStrategy(unittest.TestCase):
    """Test cases for RoundRobinOptimizationStrategy."""

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

    def test_round_robin_distributes_hours_equally(self):
        """Test that round-robin distributes hours equally among tasks."""
        # Create two tasks with same duration
        input_dto1 = CreateTaskRequest(
            name="Task 1",
            priority=100,
            estimated_duration=12.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="Task 2",
            priority=50,
            estimated_duration=12.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto2)

        # Start on Monday with 6h/day capacity
        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="round_robin",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Each task should get 3h per day (6h / 2 tasks)
        for task in result.successful_tasks:
            self.assertIsNotNone(task.daily_allocations)
            # Check first day allocation
            first_day_allocation = task.daily_allocations.get("2025-10-20", 0.0)
            self.assertAlmostEqual(first_day_allocation, 3.0, places=5)

    def test_round_robin_makes_parallel_progress(self):
        """Test that round-robin makes progress on all tasks in parallel."""
        # Create three tasks with different durations
        input_dto1 = CreateTaskRequest(
            name="Short Task",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="Medium Task",
            priority=50,
            estimated_duration=12.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto2)

        input_dto3 = CreateTaskRequest(
            name="Long Task",
            priority=25,
            estimated_duration=18.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto3)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="round_robin",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # All tasks should start on the same day (parallel progress)
        for task in result.successful_tasks:
            self.assertEqual(task.planned_start, "2025-10-20 09:00:00")

    def test_round_robin_stops_allocating_after_task_completion(self):
        """Test that round-robin stops allocating to completed tasks."""
        # Create two tasks: one short, one long
        input_dto1 = CreateTaskRequest(
            name="Short Task",
            priority=100,
            estimated_duration=6.0,  # Completes after 3 days
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="Long Task",
            priority=50,
            estimated_duration=18.0,  # Takes longer
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto2)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="round_robin",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        tasks_by_name = {t.name: t for t in result.successful_tasks}
        short_task = tasks_by_name["Short Task"]
        long_task = tasks_by_name["Long Task"]

        # Short task should complete earlier than long task
        short_end = datetime.strptime(short_task.planned_end, "%Y-%m-%d %H:%M:%S")
        long_end = datetime.strptime(long_task.planned_end, "%Y-%m-%d %H:%M:%S")
        self.assertLess(short_end, long_end)

    def test_round_robin_respects_deadlines(self):
        """Test that round-robin respects task deadlines."""
        # Create task with impossible deadline
        input_dto = CreateTaskRequest(
            name="Impossible Deadline",
            priority=100,
            estimated_duration=30.0,  # 30 hours
            deadline="2025-10-22 18:00:00",  # Only 3 days (18h max with round-robin)
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="round_robin",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Task should fail to schedule
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 1)

    def test_round_robin_skips_weekends(self):
        """Test that round-robin skips weekends."""
        # Create task that spans over a weekend
        input_dto = CreateTaskRequest(
            name="Weekend Task",
            priority=100,
            estimated_duration=12.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto)

        # Start on Friday
        start_date = datetime(2025, 10, 24, 9, 0, 0)  # Friday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="round_robin",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        task = result.successful_tasks[0]

        # Verify no weekend allocations
        self.assertIsNone(task.daily_allocations.get("2025-10-25"))  # Saturday
        self.assertIsNone(task.daily_allocations.get("2025-10-26"))  # Sunday

    def test_round_robin_with_single_task(self):
        """Test that round-robin works correctly with a single task."""
        # Single task should get all available hours each day
        input_dto = CreateTaskRequest(
            name="Single Task",
            priority=100,
            estimated_duration=12.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="round_robin",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        task = result.successful_tasks[0]

        # Single task should get full 6h each day (not divided)
        self.assertAlmostEqual(task.daily_allocations.get("2025-10-20", 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get("2025-10-21", 0.0), 6.0, places=5)

    def test_round_robin_adjusts_allocation_as_tasks_complete(self):
        """Test that round-robin adjusts allocation as tasks complete."""
        # Create three tasks with staggered durations
        input_dto1 = CreateTaskRequest(
            name="Quick Task",
            priority=100,
            estimated_duration=4.0,  # Completes in 2 days
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="Medium Task",
            priority=50,
            estimated_duration=8.0,  # Completes in 4-5 days
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto2)

        input_dto3 = CreateTaskRequest(
            name="Long Task",
            priority=25,
            estimated_duration=12.0,  # Takes longest
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto3)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="round_robin",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        tasks_by_name = {t.name: t for t in result.successful_tasks}

        # Verify that tasks complete at different times
        quick_end = datetime.strptime(tasks_by_name["Quick Task"].planned_end, "%Y-%m-%d %H:%M:%S")
        medium_end = datetime.strptime(
            tasks_by_name["Medium Task"].planned_end, "%Y-%m-%d %H:%M:%S"
        )
        long_end = datetime.strptime(tasks_by_name["Long Task"].planned_end, "%Y-%m-%d %H:%M:%S")

        self.assertLess(quick_end, medium_end)
        self.assertLess(medium_end, long_end)


if __name__ == "__main__":
    unittest.main()
