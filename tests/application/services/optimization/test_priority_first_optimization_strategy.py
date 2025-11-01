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
        low_priority = self.create_task(
            "Low Priority",
            priority=10,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        medium_priority = self.create_task(
            "Medium Priority",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        high_priority = self.create_task(
            "High Priority",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All should be scheduled
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify scheduling order: high priority should start earliest
        # Refetch tasks from repository to get updated state
        updated_high = self.repository.get_by_id(high_priority.id)
        updated_medium = self.repository.get_by_id(medium_priority.id)
        updated_low = self.repository.get_by_id(low_priority.id)
        assert updated_high is not None and updated_medium is not None and updated_low is not None

        # High priority starts first (Monday)
        self.assertEqual(updated_high.planned_start, datetime(2025, 10, 20, 9, 0, 0))
        # Medium priority starts second (Tuesday)
        self.assertEqual(updated_medium.planned_start, datetime(2025, 10, 21, 9, 0, 0))
        # Low priority starts last (Wednesday)
        self.assertEqual(updated_low.planned_start, datetime(2025, 10, 22, 9, 0, 0))

    def test_priority_first_ignores_deadlines(self):
        """Test that priority_first ignores deadlines and focuses only on priority."""
        # Create task with lower priority but urgent deadline
        low_priority_urgent = self.create_task(
            "Low Priority Urgent",
            priority=10,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 21, 18, 0, 0),
        )
        # Create task with high priority but far deadline
        high_priority_far = self.create_task(
            "High Priority Far",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 12, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both should be scheduled
        self.assertEqual(len(result.successful_tasks), 2)

        # Refetch tasks from repository to get updated state
        updated_high_far = self.repository.get_by_id(high_priority_far.id)
        updated_low_urgent = self.repository.get_by_id(low_priority_urgent.id)
        assert updated_high_far is not None and updated_low_urgent is not None

        # High priority task scheduled first despite far deadline
        self.assertEqual(updated_high_far.planned_start, datetime(2025, 10, 20, 9, 0, 0))
        # Urgent task scheduled second despite earlier deadline
        self.assertEqual(updated_low_urgent.planned_start, datetime(2025, 10, 21, 9, 0, 0))


if __name__ == "__main__":
    unittest.main()
