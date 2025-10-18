"""Tests for EarliestDeadlineOptimizationStrategy."""

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


class TestEarliestDeadlineOptimizationStrategy(unittest.TestCase):
    """Test cases for EarliestDeadlineOptimizationStrategy."""

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

    def test_earliest_deadline_schedules_by_deadline_order(self):
        """Test that EDF schedules tasks by deadline, not priority."""
        # Create two tasks with opposite priority/deadline relationship
        # Task 1: Low priority, early deadline (should be scheduled first)
        input_dto1 = CreateTaskInput(
            name="Early Deadline Task",
            priority=50,
            estimated_duration=6.0,
            deadline="2025-10-22 18:00:00",  # 2 days away
        )
        self.create_use_case.execute(input_dto1)

        # Task 2: High priority, late deadline (should be scheduled second)
        input_dto2 = CreateTaskInput(
            name="Late Deadline Task",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-25 18:00:00",  # 5 days away
        )
        self.create_use_case.execute(input_dto2)

        # Start on Monday
        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="earliest_deadline"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task 1 (early deadline) should start first
        task1 = next(t for t in result.successful_tasks if t.name == "Early Deadline Task")
        task2 = next(t for t in result.successful_tasks if t.name == "Late Deadline Task")

        self.assertEqual(task1.planned_start, "2025-10-20 09:00:00")  # Monday
        self.assertEqual(task2.planned_start, "2025-10-21 09:00:00")  # Tuesday

    def test_earliest_deadline_handles_no_deadline(self):
        """Test that EDF schedules tasks without deadlines last."""
        # Task 1: Has deadline (should be scheduled first)
        input_dto1 = CreateTaskInput(
            name="With Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline="2025-10-25 18:00:00",
        )
        self.create_use_case.execute(input_dto1)

        # Task 2: No deadline (should be scheduled last)
        input_dto2 = CreateTaskInput(
            name="No Deadline",
            priority=100,  # Higher priority, but no deadline
            estimated_duration=6.0,
            deadline=None,
        )
        self.create_use_case.execute(input_dto2)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="earliest_deadline"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Task with deadline should start first
        task1 = next(t for t in result.successful_tasks if t.name == "With Deadline")
        task2 = next(t for t in result.successful_tasks if t.name == "No Deadline")

        self.assertEqual(task1.planned_start, "2025-10-20 09:00:00")  # Monday
        self.assertEqual(task2.planned_start, "2025-10-21 09:00:00")  # Tuesday

    def test_earliest_deadline_respects_deadline_constraints(self):
        """Test that EDF fails tasks that cannot meet their deadlines."""
        # Create task with impossible deadline
        input_dto = CreateTaskInput(
            name="Impossible Deadline",
            priority=100,
            estimated_duration=30.0,  # 30 hours
            deadline="2025-10-22 18:00:00",  # Only 3 days (18 hours max)
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="earliest_deadline"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Task should fail to schedule
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 1)

    def test_earliest_deadline_ignores_priority_completely(self):
        """Test that EDF ignores priority field when scheduling."""
        # Create three tasks with different priorities and deadlines
        # Priority should have NO effect on scheduling order
        input_dto1 = CreateTaskInput(
            name="Highest Priority, Latest Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline="2025-10-24 18:00:00",  # Day 5
        )
        self.create_use_case.execute(input_dto1)

        input_dto2 = CreateTaskInput(
            name="Medium Priority, Middle Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline="2025-10-22 18:00:00",  # Day 3
        )
        self.create_use_case.execute(input_dto2)

        input_dto3 = CreateTaskInput(
            name="Lowest Priority, Earliest Deadline",
            priority=10,
            estimated_duration=6.0,
            deadline="2025-10-21 18:00:00",  # Day 2
        )
        self.create_use_case.execute(input_dto3)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="earliest_deadline"
        )
        result = self.optimize_use_case.execute(optimize_input)

        # All tasks should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify scheduling order matches deadline order, not priority
        tasks_by_name = {t.name: t for t in result.successful_tasks}

        lowest_prio = tasks_by_name["Lowest Priority, Earliest Deadline"]
        medium_prio = tasks_by_name["Medium Priority, Middle Deadline"]
        highest_prio = tasks_by_name["Highest Priority, Latest Deadline"]

        # Earliest deadline should be scheduled first
        self.assertEqual(lowest_prio.planned_start, "2025-10-20 09:00:00")
        # Middle deadline should be scheduled second
        self.assertEqual(medium_prio.planned_start, "2025-10-21 09:00:00")
        # Latest deadline should be scheduled last
        self.assertEqual(highest_prio.planned_start, "2025-10-22 09:00:00")

    def test_earliest_deadline_uses_greedy_allocation(self):
        """Test that EDF uses greedy forward allocation strategy."""
        # Create task that requires multiple days
        input_dto = CreateTaskInput(
            name="Multi-day Task",
            priority=100,
            estimated_duration=15.0,
            deadline="2025-10-31 18:00:00",
        )
        self.create_use_case.execute(input_dto)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date, max_hours_per_day=6.0, algorithm_name="earliest_deadline"
        )
        result = self.optimize_use_case.execute(optimize_input)

        task = result.successful_tasks[0]

        # Verify greedy allocation: fills each day to maximum before moving to next
        self.assertIsNotNone(task.daily_allocations)
        self.assertAlmostEqual(task.daily_allocations.get("2025-10-20", 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get("2025-10-21", 0.0), 6.0, places=5)
        self.assertAlmostEqual(task.daily_allocations.get("2025-10-22", 0.0), 3.0, places=5)


if __name__ == "__main__":
    unittest.main()
