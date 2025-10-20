"""Tests for BackwardOptimizationStrategy."""

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


class TestBackwardOptimizationStrategy(unittest.TestCase):
    """Test cases for BackwardOptimizationStrategy."""

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

    def test_backward_schedules_close_to_deadline(self):
        """Test that backward strategy schedules tasks close to deadline."""
        # Create task with 6h duration and deadline on Friday
        # Should be scheduled on Friday (as late as possible)
        input_dto = CreateTaskRequest(
            name="JIT Task",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-24 18:00:00",  # Friday
        )
        self.create_use_case.execute(input_dto)

        # Start on Monday
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="backward",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should be scheduled on Friday (closest to deadline)
        self.assertEqual(task.planned_start, "2025-10-24 09:00:00")
        self.assertEqual(task.planned_end, "2025-10-24 18:00:00")

        # All 6h allocated on Friday
        self.assertEqual(task.daily_allocations["2025-10-24"], 6.0)

    def test_backward_spans_backward_from_deadline(self):
        """Test that backward strategy fills backwards when task doesn't fit in one day."""
        # Create task with 12h duration and deadline on Friday
        # With 6h/day max, needs 2 days: Thursday and Friday
        input_dto = CreateTaskRequest(
            name="Multi-day JIT",
            priority=100,
            estimated_duration=12.0,
            deadline="2025-10-24 18:00:00",  # Friday
        )
        self.create_use_case.execute(input_dto)

        # Start on Monday
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="backward",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should start on Thursday
        self.assertEqual(task.planned_start, "2025-10-23 09:00:00")
        # Should end on Friday
        self.assertEqual(task.planned_end, "2025-10-24 18:00:00")

        # 6h on Thursday, 6h on Friday
        self.assertEqual(task.daily_allocations["2025-10-23"], 6.0)
        self.assertEqual(task.daily_allocations["2025-10-24"], 6.0)

    def test_backward_without_deadline_schedules_near_future(self):
        """Test that tasks without deadline are scheduled in near future (1 week)."""
        # Create task without deadline
        input_dto = CreateTaskRequest(name="No Deadline Task", priority=100, estimated_duration=6.0)
        self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="backward",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should be scheduled (using default 1-week period)
        self.assertIsNotNone(task.planned_start)
        self.assertIsNotNone(task.planned_end)
        self.assertIsNotNone(task.daily_allocations)

        # Should be 6h total
        total_allocated = sum(task.daily_allocations.values())
        self.assertEqual(total_allocated, 6.0)

    def test_backward_respects_max_hours_per_day(self):
        """Test that backward strategy respects max_hours_per_day constraint."""
        # Create task with 18h duration and deadline 3 weekdays away
        # With 6h/day max, should use all 3 days
        input_dto = CreateTaskRequest(
            name="Max Hours Task",
            priority=100,
            estimated_duration=18.0,
            deadline="2025-10-22 18:00:00",  # Wednesday
        )
        self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="backward",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should respect max_hours_per_day
        for _date_str, hours in task.daily_allocations.items():
            self.assertLessEqual(hours, 6.0)

        # Total should be 18h
        total_allocated = sum(task.daily_allocations.values())
        self.assertEqual(total_allocated, 18.0)

        # Should use Mon, Tue, Wed (backwards from Wed)
        self.assertEqual(len(task.daily_allocations), 3)

    def test_backward_handles_multiple_tasks(self):
        """Test backward strategy with multiple tasks (furthest deadline first)."""
        # Create two tasks with different deadlines
        input1 = CreateTaskRequest(
            name="Task 1",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-24 18:00:00",  # Friday (further)
        )
        input2 = CreateTaskRequest(
            name="Task 2",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-22 18:00:00",  # Wednesday (closer)
        )
        self.create_use_case.execute(input1)
        self.create_use_case.execute(input2)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="backward",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task 1 (further deadline) is processed first, scheduled on Friday
        task1 = [t for t in result.successful_tasks if t.deadline == "2025-10-24 18:00:00"][0]
        self.assertEqual(task1.planned_start, "2025-10-24 09:00:00")

        # Task 2 (closer deadline) is processed second, scheduled on Wednesday
        task2 = [t for t in result.successful_tasks if t.deadline == "2025-10-22 18:00:00"][0]
        self.assertEqual(task2.planned_start, "2025-10-22 09:00:00")

    def test_backward_fails_when_deadline_before_start(self):
        """Test that backward strategy fails when deadline is before start date."""
        # Create task with deadline before start date
        input_dto = CreateTaskRequest(
            name="Past Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-19 18:00:00",  # Sunday (before Monday start)
        )
        self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="backward",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Task should not be scheduled
        self.assertEqual(len(result.successful_tasks), 0)

    def test_backward_skips_weekends(self):
        """Test that backward strategy skips weekends when allocating."""
        # Create task with 6h duration and deadline on Monday
        # Should skip weekend and allocate on Friday
        input_dto = CreateTaskRequest(
            name="Weekend Skip",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-27 18:00:00",  # Monday
        )
        self.create_use_case.execute(input_dto)

        # Start on Monday (week before)
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="backward",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify
        self.assertEqual(len(result.successful_tasks), 1)
        task = result.successful_tasks[0]

        # Should be scheduled on Monday (deadline day)
        self.assertEqual(task.planned_start, "2025-10-27 09:00:00")
        self.assertEqual(task.planned_end, "2025-10-27 18:00:00")

        # Only Monday in allocations (no weekend days)
        self.assertEqual(len(task.daily_allocations), 1)
        self.assertIn("2025-10-27", task.daily_allocations)


if __name__ == "__main__":
    unittest.main()
