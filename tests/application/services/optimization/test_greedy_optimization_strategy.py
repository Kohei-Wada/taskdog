"""Tests for GreedyOptimizationStrategy."""

import os
import tempfile
import unittest
from datetime import date, datetime

from application.dto.create_task_request import CreateTaskRequest
from application.dto.optimize_schedule_request import OptimizeScheduleRequest
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from shared.config_manager import ConfigManager


class TestGreedyOptimizationStrategy(unittest.TestCase):
    """Test cases for GreedyOptimizationStrategy."""

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

    def test_greedy_front_loads_single_task(self):
        """Test that greedy strategy front-loads a single task."""
        # Create task with 12h duration
        # Should fill 2 days with 6h each
        input_dto = CreateTaskRequest(
            name="Greedy Task",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_use_case.execute(input_dto)

        # Start on Monday
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday 9:00
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="greedy",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify greedy front-loading
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should start on Monday
        self.assertEqual(task.planned_start, datetime(2025, 10, 20, 9, 0, 0))
        # Should end on Tuesday (12h / 6h per day = 2 days)
        self.assertEqual(task.planned_end, datetime(2025, 10, 21, 18, 0, 0))

        # Check daily allocations: greedy fills each day to max
        self.assertIsNotNone(task.daily_allocations)
        self.assertEqual(len(task.daily_allocations), 2)  # Mon-Tue
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 20), 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 21), 0.0), 6.0, places=5)

    def test_greedy_handles_partial_day(self):
        """Test that greedy strategy handles partial day allocation."""
        # Create task with 10h duration
        # Should fill: 6h (day 1) + 4h (day 2)
        input_dto = CreateTaskRequest(
            name="Partial Day Task",
            priority=100,
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="greedy",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        task = result.successful_tasks[0]

        # Check daily allocations
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 20), 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get(date(2025, 10, 21), 0.0), 4.0, places=5)

    def test_greedy_skips_weekends(self):
        """Test that greedy strategy skips weekends."""
        # Create task that spans Friday to Monday
        input_dto = CreateTaskRequest(
            name="Weekend Task",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_use_case.execute(input_dto)

        # Start on Friday
        start_date = datetime(2025, 10, 24, 9, 0, 0)  # Friday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="greedy",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        task = result.successful_tasks[0]

        # Should start Friday
        self.assertEqual(task.planned_start, datetime(2025, 10, 24, 9, 0, 0))
        # Should end Monday (skipping Saturday/Sunday)
        self.assertEqual(task.planned_end, datetime(2025, 10, 27, 18, 0, 0))

        # Verify no weekend allocations
        self.assertIsNone(task.daily_allocations.get(date(2025, 10, 25)))  # Saturday
        self.assertIsNone(task.daily_allocations.get(date(2025, 10, 26)))  # Sunday

    def test_greedy_respects_deadline(self):
        """Test that greedy strategy respects task deadlines."""
        # Create task with tight deadline
        input_dto = CreateTaskRequest(
            name="Tight Deadline",
            priority=100,
            estimated_duration=30.0,  # Too much work
            deadline=datetime(2025, 10, 22, 18, 0, 0),  # Only 3 days available
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="greedy",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Should fail to schedule (30h > 3 days * 6h/day = 18h)
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 1)

    def test_greedy_respects_fixed_tasks_in_daily_limit(self):
        """Test that greedy strategy accounts for fixed tasks when calculating available hours."""
        # Create a fixed task with 4h/day allocation for 3 days (Mon-Wed)
        fixed_task_input = CreateTaskRequest(
            name="Fixed Meeting",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
            is_fixed=True,
        )
        fixed_task = self.create_use_case.execute(fixed_task_input)

        # Manually schedule the fixed task with specific daily allocations
        fixed_task.planned_start = datetime(2025, 10, 20, 9, 0, 0)
        fixed_task.planned_end = datetime(2025, 10, 22, 18, 0, 0)
        fixed_task.daily_allocations = {
            date(2025, 10, 20): 4.0,  # Monday: 4h
            date(2025, 10, 21): 4.0,  # Tuesday: 4h
            date(2025, 10, 22): 4.0,  # Wednesday: 4h
        }
        self.repository.save(fixed_task)

        # Create a regular task that needs 6h
        regular_task_input = CreateTaskRequest(
            name="Regular Task",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_use_case.execute(regular_task_input)

        # Optimize with max_hours_per_day=6.0
        # Available hours per day: 6.0 - 4.0 (fixed) = 2.0h
        # So 6h task should take 3 days (2h * 3 = 6h)
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="greedy",
            force_override=True,  # Force to reschedule regular task
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify regular task was scheduled
        self.assertEqual(len(result.successful_tasks), 1)
        regular_task = result.successful_tasks[0]

        # Verify daily allocations respect fixed task hours
        # Each day should have max 2h for regular task (6.0 - 4.0 fixed)
        self.assertIsNotNone(regular_task.daily_allocations)
        self.assertAlmostEqual(
            regular_task.daily_allocations.get(date(2025, 10, 20), 0.0), 2.0, places=5
        )
        self.assertAlmostEqual(
            regular_task.daily_allocations.get(date(2025, 10, 21), 0.0), 2.0, places=5
        )
        self.assertAlmostEqual(
            regular_task.daily_allocations.get(date(2025, 10, 22), 0.0), 2.0, places=5
        )

        # Verify total daily allocations don't exceed max_hours_per_day
        for date_str, hours in result.daily_allocations.items():
            self.assertLessEqual(
                hours, 6.0, f"Total hours on {date_str} ({hours}h) exceeds max_hours_per_day (6.0h)"
            )


if __name__ == "__main__":
    unittest.main()
