"""Tests for EarliestDeadlineOptimizationStrategy."""

from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestEarliestDeadlineOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for EarliestDeadlineOptimizationStrategy."""

    algorithm_name = "earliest_deadline"

    def test_earliest_deadline_schedules_by_deadline_order(self):
        """Test that EDF schedules tasks by deadline, not priority."""
        # Create two tasks with opposite priority/deadline relationship
        # Task 1: Low priority, early deadline (should be scheduled first)
        task1 = self.create_task(
            "Early Deadline Task",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )
        # Task 2: High priority, late deadline (should be scheduled second)
        task2 = self.create_task(
            "Late Deadline Task",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        assert len(result.successful_tasks) == 2

        # Task 1 (early deadline) should start first
        updated_task1 = self.repository.get_by_id(task1.id)
        updated_task2 = self.repository.get_by_id(task2.id)
        assert updated_task1 is not None and updated_task2 is not None

        assert updated_task1.planned_start == datetime(2025, 10, 20, 0, 0, 0)  # Monday
        assert updated_task2.planned_start == datetime(2025, 10, 21, 0, 0, 0)  # Tuesday

    def test_earliest_deadline_handles_no_deadline(self):
        """Test that EDF schedules tasks without deadlines last."""
        # Task 1: Has deadline (should be scheduled first)
        task1 = self.create_task(
            "With Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
        )
        # Task 2: No deadline (should be scheduled last)
        task2 = self.create_task(
            "No Deadline", priority=100, estimated_duration=6.0, deadline=None
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        assert len(result.successful_tasks) == 2

        # Task with deadline should start first
        updated_task1 = self.repository.get_by_id(task1.id)
        updated_task2 = self.repository.get_by_id(task2.id)
        assert updated_task1 is not None and updated_task2 is not None

        assert updated_task1.planned_start == datetime(2025, 10, 20, 0, 0, 0)  # Monday
        assert updated_task2.planned_start == datetime(2025, 10, 21, 0, 0, 0)  # Tuesday

    def test_earliest_deadline_respects_deadline_constraints(self):
        """Test that EDF fails tasks that cannot meet their deadlines."""
        # Create task with impossible deadline
        self.create_task(
            "Impossible Deadline",
            priority=100,
            estimated_duration=30.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Task should fail to schedule
        assert len(result.successful_tasks) == 0
        assert len(result.failed_tasks) == 1

    def test_earliest_deadline_ignores_priority_completely(self):
        """Test that EDF ignores priority field when scheduling."""
        # Create three tasks with different priorities and deadlines
        # Priority should have NO effect on scheduling order
        high_late = self.create_task(
            "Highest Priority, Latest Deadline",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),
        )
        medium_middle = self.create_task(
            "Medium Priority, Middle Deadline",
            priority=50,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )
        low_early = self.create_task(
            "Lowest Priority, Earliest Deadline",
            priority=10,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 21, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All tasks should be scheduled
        assert len(result.successful_tasks) == 3

        # Verify scheduling order matches deadline order, not priority
        updated_low = self.repository.get_by_id(low_early.id)
        updated_medium = self.repository.get_by_id(medium_middle.id)
        updated_high = self.repository.get_by_id(high_late.id)
        assert (
            updated_low is not None
            and updated_medium is not None
            and updated_high is not None
        )

        # Earliest deadline should be scheduled first
        assert updated_low.planned_start == datetime(2025, 10, 20, 0, 0, 0)
        # Middle deadline should be scheduled second
        assert updated_medium.planned_start == datetime(2025, 10, 21, 0, 0, 0)
        # Latest deadline should be scheduled last
        assert updated_high.planned_start == datetime(2025, 10, 22, 0, 0, 0)

    def test_earliest_deadline_uses_greedy_allocation(self):
        """Test that EDF uses greedy forward allocation strategy."""
        # Create task that requires multiple days
        task = self.create_task(
            "Multi-day Task",
            priority=100,
            estimated_duration=15.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Refetch task from repository to get updated state
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None

        # Verify greedy allocation: fills each day to maximum before moving to next
        assert updated_task.daily_allocations is not None
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 20), 0.0) - 6.0)
            < 1e-5
        )
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 21), 0.0) - 6.0)
            < 1e-5
        )
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 22), 0.0) - 3.0)
            < 1e-5
        )
