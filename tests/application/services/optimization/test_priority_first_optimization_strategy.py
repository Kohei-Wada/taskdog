"""Tests for PriorityFirstOptimizationStrategy."""

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


class TestPriorityFirstOptimizationStrategy(unittest.TestCase):
    """Test cases for PriorityFirstOptimizationStrategy."""

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

    def test_priority_first_schedules_by_priority_order(self):
        """Test that priority_first strategy schedules high priority tasks first."""
        # Create tasks with different priorities
        high_priority = CreateTaskRequest(
            name="High Priority",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        medium_priority = CreateTaskRequest(
            name="Medium Priority",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        low_priority = CreateTaskRequest(
            name="Low Priority",
            priority=10,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        self.create_use_case.execute(low_priority)  # Create in reverse order
        self.create_use_case.execute(medium_priority)
        self.create_use_case.execute(high_priority)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="priority_first",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # All should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify scheduling order: high priority should start earliest
        tasks_by_name = {t.name: t for t in result.successful_tasks}

        high_start = tasks_by_name["High Priority"].planned_start
        medium_start = tasks_by_name["Medium Priority"].planned_start
        low_start = tasks_by_name["Low Priority"].planned_start

        # High priority starts first (Monday)
        self.assertEqual(high_start, datetime(2025, 10, 20, 9, 0, 0))
        # Medium priority starts second (Tuesday)
        self.assertEqual(medium_start, datetime(2025, 10, 21, 9, 0, 0))
        # Low priority starts last (Wednesday)
        self.assertEqual(low_start, datetime(2025, 10, 22, 9, 0, 0))

    def test_priority_first_ignores_deadlines(self):
        """Test that priority_first ignores deadlines and focuses only on priority."""
        # Create task with high priority but far deadline
        high_priority_far_deadline = CreateTaskRequest(
            name="High Priority Far",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 12, 31, 18, 0, 0),
        )
        # Create task with lower priority but urgent deadline
        low_priority_urgent = CreateTaskRequest(
            name="Low Priority Urgent",
            priority=10,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 21, 18, 0, 0),
        )

        self.create_use_case.execute(low_priority_urgent)
        self.create_use_case.execute(high_priority_far_deadline)

        # Optimize
        start_date = datetime(2025, 10, 20, 9, 0, 0)
        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=6.0,
            algorithm_name="priority_first",
            force_override=False,
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        tasks_by_name = {t.name: t for t in result.successful_tasks}

        # High priority task scheduled first despite far deadline
        self.assertEqual(
            tasks_by_name["High Priority Far"].planned_start, datetime(2025, 10, 20, 9, 0, 0)
        )
        # Urgent task scheduled second despite earlier deadline
        self.assertEqual(
            tasks_by_name["Low Priority Urgent"].planned_start, datetime(2025, 10, 21, 9, 0, 0)
        )


if __name__ == "__main__":
    unittest.main()
