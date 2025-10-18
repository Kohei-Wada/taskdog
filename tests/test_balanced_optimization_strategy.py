"""Tests for BalancedOptimizationStrategy."""

import os
import tempfile
import unittest
from datetime import datetime

from application.dto.create_task_input import CreateTaskInput
from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from shared.config_manager import ConfigManager


class TestBalancedOptimizationStrategy(unittest.TestCase):
    """Test cases for BalancedOptimizationStrategy."""

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

    def test_balanced_distributes_evenly_with_deadline(self):
        """Test that balanced strategy distributes hours evenly across available period."""
        # Create task with 10h duration and deadline 5 weekdays away
        # Monday to Friday = 5 weekdays, should allocate 2h/day
        input_dto = CreateTaskInput(
            name="Balanced Task",
            priority=100,
            estimated_duration=10.0,
            deadline="2025-10-24 18:00:00",  # Friday (5 weekdays from Monday start)
        )
        self.create_use_case.execute(input_dto)

        # Start on Monday
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday 9:00
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="balanced"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify balanced distribution
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should start on Monday
        self.assertEqual(task.planned_start, "2025-10-20 09:00:00")
        # Should end on Friday
        self.assertEqual(task.planned_end, "2025-10-24 18:00:00")

        # Check daily allocations: 10h / 5 days = 2h/day
        self.assertIsNotNone(task.daily_allocations)
        self.assertEqual(len(task.daily_allocations), 5)  # Mon-Fri
        for _date_str, hours in task.daily_allocations.items():
            self.assertAlmostEqual(hours, 2.0, places=5)

    def test_balanced_without_deadline_uses_default_period(self):
        """Test that tasks without deadline use a default period (2 weeks)."""
        # Create task without deadline
        input_dto = CreateTaskInput(name="No Deadline Task", priority=100, estimated_duration=20.0)
        self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="balanced"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should be scheduled (using default 2-week period)
        self.assertIsNotNone(task.planned_start)
        self.assertIsNotNone(task.planned_end)
        self.assertIsNotNone(task.daily_allocations)

        # With 20h over 2 weeks (10 weekdays), should allocate 2h/day
        total_allocated = sum(task.daily_allocations.values())
        self.assertAlmostEqual(total_allocated, 20.0, places=5)

    def test_balanced_respects_max_hours_per_day(self):
        """Test that balanced strategy respects max_hours_per_day constraint."""
        # Create task that would need more days due to max_hours_per_day
        # 12h over 5 weekdays = 2.4h/day, but we set max to 6h/day (plenty)
        input_dto = CreateTaskInput(
            name="Constrained Task",
            priority=100,
            estimated_duration=12.0,
            deadline="2025-10-24 18:00:00",  # Friday (5 weekdays from Monday)
        )
        self.create_use_case.execute(input_dto)

        # Optimize with 6h/day max
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="balanced"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should respect max_hours_per_day
        for _date_str, hours in task.daily_allocations.items():
            self.assertLessEqual(hours, 6.0)

        # Total should still be 12h
        total_allocated = sum(task.daily_allocations.values())
        self.assertAlmostEqual(total_allocated, 12.0, places=5)

    def test_balanced_handles_multiple_tasks(self):
        """Test balanced strategy with multiple tasks."""
        # Create two tasks with deadlines
        input1 = CreateTaskInput(
            name="Task 1",
            priority=200,
            estimated_duration=6.0,
            deadline="2025-10-22 18:00:00",  # Wednesday
        )
        input2 = CreateTaskInput(
            name="Task 2",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-24 18:00:00",  # Friday
        )
        self.create_use_case.execute(input1)
        self.create_use_case.execute(input2)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="balanced"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Each task should have daily allocations
        for task in result.successful_tasks:
            self.assertIsNotNone(task.daily_allocations)
            total = sum(task.daily_allocations.values())
            self.assertAlmostEqual(total, 6.0, places=5)

    def test_balanced_fails_when_deadline_too_tight(self):
        """Test that balanced strategy returns None when deadline cannot be met."""
        # Create task with 10h duration but only 1 weekday until deadline
        # Even with 6h/day max, cannot fit 10h in 1 day
        input_dto = CreateTaskInput(
            name="Impossible Task",
            priority=100,
            estimated_duration=10.0,
            deadline="2025-10-20 18:00:00",  # Same day as start
        )
        self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="balanced"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Task should not be scheduled
        self.assertEqual(len(result.successful_tasks), 0)


if __name__ == "__main__":
    unittest.main()
