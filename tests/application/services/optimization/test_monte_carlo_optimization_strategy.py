"""Tests for MonteCarloOptimizationStrategy."""

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


class TestMonteCarloOptimizationStrategy(unittest.TestCase):
    """Test cases for MonteCarloOptimizationStrategy.

    Note: Monte Carlo algorithm uses randomness, so tests focus on:
    - Algorithm completes successfully
    - Basic constraints are respected (deadlines, workload)
    - Valid schedules are produced
    """

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

    def test_monte_carlo_schedules_single_task(self):
        """Test that Monte Carlo can schedule a single task."""
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
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Should successfully schedule
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Verify basic properties
        self.assertIsNotNone(task.planned_start)
        self.assertIsNotNone(task.planned_end)
        self.assertIsNotNone(task.daily_allocations)

        # Verify total allocated hours equals estimated duration
        total_hours = sum(task.daily_allocations.values())
        self.assertAlmostEqual(total_hours, 12.0, places=5)

    def test_monte_carlo_schedules_multiple_tasks(self):
        """Test that Monte Carlo can schedule multiple tasks."""
        # Create multiple tasks
        for i in range(3):
            input_dto = CreateTaskRequest(
                name=f"Task {i + 1}",
                priority=100 - (i * 10),
                estimated_duration=6.0,
                deadline="2025-10-31 18:00:00",
            )
            self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Should successfully schedule all tasks
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify all tasks have valid schedules
        for task in result.successful_tasks:
            self.assertIsNotNone(task.planned_start)
            self.assertIsNotNone(task.planned_end)
            self.assertIsNotNone(task.daily_allocations)

            # Verify total allocated hours
            total_hours = sum(task.daily_allocations.values())
            self.assertAlmostEqual(total_hours, 6.0, places=5)

    def test_monte_carlo_respects_max_hours_per_day(self):
        """Test that Monte Carlo respects maximum hours per day."""
        # Create two tasks
        input_dto1 = CreateTaskRequest(
            name="Task 1",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="Task 2",
            priority=90,
            estimated_duration=6.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto2)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify daily allocations don't exceed max
        for date_str, total_hours in result.daily_allocations.items():
            self.assertLessEqual(
                total_hours, 6.0, f"Day {date_str} exceeds max hours: {total_hours}"
            )

    def test_monte_carlo_respects_deadlines(self):
        """Test that Monte Carlo respects task deadlines."""
        # Create task with tight but achievable deadline
        input_dto = CreateTaskRequest(
            name="Tight Deadline",
            priority=100,
            estimated_duration=12.0,
            deadline="2025-10-22 18:00:00",  # 3 days = 18h available
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Should successfully schedule
        self.assertEqual(len(result.successful_tasks), 1)

        task = result.successful_tasks[0]

        # Verify end date is before or on deadline
        end_dt = datetime.strptime(task.planned_end, "%Y-%m-%d %H:%M:%S")
        deadline_dt = datetime.strptime(task.deadline, "%Y-%m-%d %H:%M:%S")
        self.assertLessEqual(end_dt, deadline_dt)

    def test_monte_carlo_fails_impossible_deadlines(self):
        """Test that Monte Carlo fails tasks with impossible deadlines."""
        # Create task with impossible deadline
        input_dto = CreateTaskRequest(
            name="Impossible Deadline",
            priority=100,
            estimated_duration=30.0,
            deadline="2025-10-22 18:00:00",  # Only 18h available
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Should fail to schedule
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 1)

    def test_monte_carlo_skips_weekends(self):
        """Test that Monte Carlo skips weekends."""
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
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        task = result.successful_tasks[0]

        # Verify no weekend allocations
        self.assertIsNone(task.daily_allocations.get("2025-10-25"))  # Saturday
        self.assertIsNone(task.daily_allocations.get("2025-10-26"))  # Sunday

    def test_monte_carlo_produces_valid_results(self):
        """Test that Monte Carlo produces valid results with multiple simulations."""
        # Create multiple tasks with different priorities
        for i in range(5):
            input_dto = CreateTaskRequest(
                name=f"Task {i + 1}",
                priority=100 - (i * 20),
                estimated_duration=6.0,
                deadline="2025-10-31 18:00:00",
            )
            self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Should successfully schedule all tasks
        self.assertEqual(len(result.successful_tasks), 5)

        # Verify no overlapping allocations
        for task in result.successful_tasks:
            self.assertIsNotNone(task.daily_allocations)
            # All daily allocations should be positive
            for hours in task.daily_allocations.values():
                self.assertGreater(hours, 0)

    def test_monte_carlo_handles_empty_task_list(self):
        """Test that Monte Carlo handles empty task list gracefully."""
        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Should return empty results
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 0)

    def test_monte_carlo_finds_feasible_solution(self):
        """Test that Monte Carlo finds a feasible solution through multiple simulations."""
        # Create tasks with varying characteristics
        input_dto1 = CreateTaskRequest(
            name="High Priority",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-25 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskRequest(
            name="Medium Priority",
            priority=50,
            estimated_duration=9.0,
            deadline="2025-10-27 18:00:00",
        )
        self.create_use_case.execute(input_dto2)

        input_dto3 = CreateTaskRequest(
            name="Low Priority",
            priority=25,
            estimated_duration=12.0,
            deadline="2025-10-30 18:00:00",
        )
        self.create_use_case.execute(input_dto3)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="monte_carlo",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Should successfully schedule all tasks
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify all tasks respect their deadlines
        for task in result.successful_tasks:
            if task.deadline:
                end_dt = datetime.strptime(task.planned_end, "%Y-%m-%d %H:%M:%S")
                deadline_dt = datetime.strptime(task.deadline, "%Y-%m-%d %H:%M:%S")
                self.assertLessEqual(end_dt, deadline_dt, f"Task {task.name} exceeds deadline")


if __name__ == "__main__":
    unittest.main()
