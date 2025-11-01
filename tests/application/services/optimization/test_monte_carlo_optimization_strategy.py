"""Tests for MonteCarloOptimizationStrategy."""

import unittest
from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestMonteCarloOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for MonteCarloOptimizationStrategy.

    Note: Monte Carlo algorithm uses randomness, so tests focus on:
    - Algorithm completes successfully
    - Basic constraints are respected (deadlines, workload)
    - Valid schedules are produced
    """

    algorithm_name = "monte_carlo"

    def test_monte_carlo_schedules_single_task(self):
        """Test that Monte Carlo can schedule a single task."""
        task = self.create_task(
            "Single Task",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should successfully schedule
        self.assertEqual(len(result.successful_tasks), 1)

        # Verify basic properties
        self.assert_task_scheduled(task)

        # Verify total allocated hours equals estimated duration
        self.assert_total_allocated_hours(task, 12.0)

    def test_monte_carlo_schedules_multiple_tasks(self):
        """Test that Monte Carlo can schedule multiple tasks."""
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = self.create_task(
                f"Task {i + 1}",
                priority=100 - (i * 10),
                estimated_duration=6.0,
                deadline=datetime(2025, 10, 31, 18, 0, 0),
            )
            tasks.append(task)

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should successfully schedule all tasks
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify all tasks have valid schedules
        for task in tasks:
            self.assert_task_scheduled(task)
            self.assert_total_allocated_hours(task, 6.0)

    def test_monte_carlo_respects_max_hours_per_day(self):
        """Test that Monte Carlo respects maximum hours per day."""
        # Create two tasks
        self.create_task(
            "Task 1",
            priority=100,
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )
        self.create_task(
            "Task 2", priority=90, estimated_duration=6.0, deadline=datetime(2025, 10, 31, 18, 0, 0)
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify daily allocations don't exceed max
        for date_str, total_hours in result.daily_allocations.items():
            self.assertLessEqual(
                total_hours, 6.0, f"Day {date_str} exceeds max hours: {total_hours}"
            )

    def test_monte_carlo_respects_deadlines(self):
        """Test that Monte Carlo respects task deadlines."""
        # Create task with tight but achievable deadline
        task = self.create_task(
            "Tight Deadline",
            priority=100,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should successfully schedule
        self.assertEqual(len(result.successful_tasks), 1)

        # Refetch task from repository to get updated state
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None

        # Verify end date is before or on deadline
        self.assertLessEqual(updated_task.planned_end, updated_task.deadline)

    def test_monte_carlo_fails_impossible_deadlines(self):
        """Test that Monte Carlo fails tasks with impossible deadlines."""
        # Create task with impossible deadline
        self.create_task(
            "Impossible Deadline",
            priority=100,
            estimated_duration=30.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should fail to schedule
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 1)

    def test_monte_carlo_skips_weekends(self):
        """Test that Monte Carlo skips weekends."""
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
        self.assertIsNone(updated_task.daily_allocations.get(date(2025, 10, 25)))  # Saturday
        self.assertIsNone(updated_task.daily_allocations.get(date(2025, 10, 26)))  # Sunday

    def test_monte_carlo_produces_valid_results(self):
        """Test that Monte Carlo produces valid results with multiple simulations."""
        # Create multiple tasks with different priorities
        tasks = []
        for i in range(5):
            task = self.create_task(
                f"Task {i + 1}",
                priority=100 - (i * 20),
                estimated_duration=6.0,
                deadline=datetime(2025, 10, 31, 18, 0, 0),
            )
            tasks.append(task)

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should successfully schedule all tasks
        self.assertEqual(len(result.successful_tasks), 5)

        # Verify no overlapping allocations
        for task in tasks:
            updated_task = self.repository.get_by_id(task.id)
            assert updated_task is not None
            self.assertIsNotNone(updated_task.daily_allocations)
            # All daily allocations should be positive
            for hours in updated_task.daily_allocations.values():
                self.assertGreater(hours, 0)

    def test_monte_carlo_handles_empty_task_list(self):
        """Test that Monte Carlo handles empty task list gracefully."""
        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should return empty results
        self.assertEqual(len(result.successful_tasks), 0)
        self.assertEqual(len(result.failed_tasks), 0)

    def test_monte_carlo_finds_feasible_solution(self):
        """Test that Monte Carlo finds a feasible solution through multiple simulations."""
        # Create tasks with varying characteristics
        tasks = []
        tasks.append(
            self.create_task(
                "High Priority",
                priority=100,
                estimated_duration=6.0,
                deadline=datetime(2025, 10, 25, 18, 0, 0),
            )
        )
        tasks.append(
            self.create_task(
                "Medium Priority",
                priority=50,
                estimated_duration=9.0,
                deadline=datetime(2025, 10, 27, 18, 0, 0),
            )
        )
        tasks.append(
            self.create_task(
                "Low Priority",
                priority=25,
                estimated_duration=12.0,
                deadline=datetime(2025, 10, 30, 18, 0, 0),
            )
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should successfully schedule all tasks
        self.assertEqual(len(result.successful_tasks), 3)

        # Verify all tasks respect their deadlines
        for task in tasks:
            updated_task = self.repository.get_by_id(task.id)
            assert updated_task is not None
            if updated_task.deadline:
                self.assertLessEqual(
                    updated_task.planned_end,
                    updated_task.deadline,
                    f"Task {updated_task.name} exceeds deadline",
                )


if __name__ == "__main__":
    unittest.main()
