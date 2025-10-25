"""Tests for PriorityFirstOptimizationStrategy."""

import unittest
from datetime import datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestPriorityFirstOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for PriorityFirstOptimizationStrategy."""

    algorithm_name = "priority_first"

    def test_priority_first_schedules_by_priority_order(self):
        """Test that priority_first strategy schedules high priority tasks first."""
        # Create tasks with different priorities (in reverse order)
        self.create_task(
            "Low Priority",
            priority=10,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "Medium Priority",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "High Priority",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify scheduling order: high priority should start earliest
        tasks_by_name = {t.name: t for t in result.successful_tasks}

        # High priority starts first (Monday)
        self.assertEqual(
            tasks_by_name["High Priority"].planned_start, datetime(2025, 10, 20, 9, 0, 0)
        )
        # Medium priority starts second (Tuesday)
        self.assertEqual(
            tasks_by_name["Medium Priority"].planned_start, datetime(2025, 10, 21, 9, 0, 0)
        )
        # Low priority starts last (Wednesday)
        self.assertEqual(
            tasks_by_name["Low Priority"].planned_start, datetime(2025, 10, 22, 9, 0, 0)
        )

    def test_priority_first_ignores_deadlines(self):
        """Test that priority_first ignores deadlines and focuses only on priority."""
        # Create task with lower priority but urgent deadline
        self.create_task(
            "Low Priority Urgent",
            priority=10,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 21, 18, 0, 0),
        )
        # Create task with high priority but far deadline
        self.create_task(
            "High Priority Far",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 12, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

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
