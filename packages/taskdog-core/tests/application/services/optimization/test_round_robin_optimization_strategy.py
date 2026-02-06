"""Tests for RoundRobinOptimizationStrategy."""

from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestRoundRobinOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for RoundRobinOptimizationStrategy."""

    algorithm_name = "round_robin"

    def test_round_robin_distributes_hours_equally(self):
        """Test that round-robin distributes hours equally among tasks."""
        # Create two tasks with same duration
        task1 = self.create_task(
            "Task 1",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        task2 = self.create_task(
            "Task 2",
            priority=50,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        assert len(result.successful_tasks) == 2

        # Each task should get 3h per day (6h / 2 tasks)
        for task in [task1, task2]:
            updated_task = self.repository.get_by_id(task.id)
            assert updated_task is not None
            assert updated_task.daily_allocations is not None
            # Check first day allocation
            first_day_allocation = updated_task.daily_allocations.get(
                date(2025, 10, 20), 0.0
            )
            assert abs(first_day_allocation - 3.0) < 1e-5

    def test_round_robin_makes_parallel_progress(self):
        """Test that round-robin makes progress on all tasks in parallel."""
        # Create three tasks with different durations
        tasks = []
        tasks.append(
            self.create_task(
                "Short Task",
                priority=100,
                estimated_duration=6.0,
                deadline=datetime(2025, 10, 31, 18, 0, 0),
            )
        )
        tasks.append(
            self.create_task(
                "Medium Task",
                priority=50,
                estimated_duration=12.0,
                deadline=datetime(2025, 10, 31, 18, 0, 0),
            )
        )
        tasks.append(
            self.create_task(
                "Long Task",
                priority=25,
                estimated_duration=18.0,
                deadline=datetime(2025, 10, 31, 18, 0, 0),
            )
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All tasks should be scheduled
        assert len(result.successful_tasks) == 3

        # All tasks should start on the same day (parallel progress)
        for task in tasks:
            updated_task = self.repository.get_by_id(task.id)
            assert updated_task is not None
            assert updated_task.planned_start == datetime(2025, 10, 20, 0, 0, 0)

    def test_round_robin_stops_allocating_after_task_completion(self):
        """Test that round-robin stops allocating to completed tasks."""
        # Create two tasks: one short, one long
        short_task = self.create_task(
            "Short Task",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        long_task = self.create_task(
            "Long Task",
            priority=50,
            estimated_duration=18.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        assert len(result.successful_tasks) == 2

        # Refetch tasks from repository to get updated state
        updated_short = self.repository.get_by_id(short_task.id)
        updated_long = self.repository.get_by_id(long_task.id)
        assert updated_short is not None and updated_long is not None

        # Short task should complete earlier than long task
        assert updated_short.planned_end < updated_long.planned_end

    def test_round_robin_respects_deadlines(self):
        """Test that round-robin respects task deadlines."""
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

    def test_round_robin_skips_weekends(self):
        """Test that round-robin skips weekends."""
        # Create task that spans over a weekend
        task = self.create_task(
            "Weekend Task",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        # Start on Friday
        self.optimize_schedule(start_date=datetime(2025, 10, 24, 9, 0, 0))

        # Refetch task from repository to get updated state
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None

        # Verify no weekend allocations
        assert (
            updated_task.daily_allocations.get(date(2025, 10, 25)) is None
        )  # Saturday
        assert updated_task.daily_allocations.get(date(2025, 10, 26)) is None  # Sunday

    def test_round_robin_with_single_task(self):
        """Test that round-robin works correctly with a single task."""
        # Single task should get all available hours each day
        task = self.create_task(
            "Single Task",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Refetch task from repository to get updated state
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None

        # Single task should get full 6h each day (not divided)
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 20), 0.0) - 6.0)
            < 1e-5
        )
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 21), 0.0) - 6.0)
            < 1e-5
        )

    def test_round_robin_adjusts_allocation_as_tasks_complete(self):
        """Test that round-robin adjusts allocation as tasks complete."""
        # Create three tasks with staggered durations
        quick_task = self.create_task(
            "Quick Task",
            priority=100,
            estimated_duration=4.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        medium_task = self.create_task(
            "Medium Task",
            priority=50,
            estimated_duration=8.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        long_task = self.create_task(
            "Long Task",
            priority=25,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # All tasks should be scheduled
        assert len(result.successful_tasks) == 3

        # Refetch tasks from repository to get updated state
        updated_quick = self.repository.get_by_id(quick_task.id)
        updated_medium = self.repository.get_by_id(medium_task.id)
        updated_long = self.repository.get_by_id(long_task.id)
        assert (
            updated_quick is not None
            and updated_medium is not None
            and updated_long is not None
        )

        # Verify that tasks complete at different times
        quick_end = updated_quick.planned_end
        medium_end = updated_medium.planned_end
        long_end = updated_long.planned_end

        assert quick_end < medium_end
        assert medium_end < long_end
