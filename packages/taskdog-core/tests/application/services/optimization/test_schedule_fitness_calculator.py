"""Tests for ScheduleFitnessCalculator."""

import unittest
from datetime import date, datetime

from taskdog_core.application.services.optimization.schedule_fitness_calculator import (
    DEADLINE_PENALTY_MULTIPLIER,
    SCHEDULED_TASK_BONUS,
    ScheduleFitnessCalculator,
)
from taskdog_core.domain.entities.task import Task


class TestScheduleFitnessCalculator(unittest.TestCase):
    """Test cases for ScheduleFitnessCalculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = ScheduleFitnessCalculator()

    def test_calculate_fitness_empty_schedule(self):
        """Test fitness calculation with no scheduled tasks."""
        fitness = self.calculator.calculate_fitness(
            [], {}, include_scheduling_bonus=False
        )
        self.assertEqual(fitness, 0.0)

    def test_calculate_fitness_with_scheduling_bonus(self):
        """Test that scheduling bonus is added when enabled."""
        tasks = [
            Task(
                id=1,
                name="Task 1",
                priority=5,
                planned_start=datetime(2025, 10, 20, 9, 0, 0),
                planned_end=datetime(2025, 10, 20, 18, 0, 0),
            ),
            Task(
                id=2,
                name="Task 2",
                priority=3,
                planned_start=datetime(2025, 10, 21, 9, 0, 0),
                planned_end=datetime(2025, 10, 21, 18, 0, 0),
            ),
        ]

        fitness_without_bonus = self.calculator.calculate_fitness(
            tasks, {}, include_scheduling_bonus=False
        )
        fitness_with_bonus = self.calculator.calculate_fitness(
            tasks, {}, include_scheduling_bonus=True
        )

        # Should add 2 * 50 = 100 points for 2 tasks
        expected_bonus = 2 * SCHEDULED_TASK_BONUS
        self.assertAlmostEqual(
            fitness_with_bonus, fitness_without_bonus + expected_bonus, places=5
        )

    def test_priority_score_higher_for_earlier_high_priority_tasks(self):
        """Test that priority score rewards scheduling high-priority tasks earlier."""
        # Task 1 (priority 10) scheduled first, Task 2 (priority 5) second
        tasks_good_order = [
            Task(
                id=1,
                name="High Priority",
                priority=10,
                planned_start=datetime(2025, 10, 20, 9, 0, 0),
                planned_end=datetime(2025, 10, 20, 18, 0, 0),
            ),
            Task(
                id=2,
                name="Low Priority",
                priority=5,
                planned_start=datetime(2025, 10, 21, 9, 0, 0),
                planned_end=datetime(2025, 10, 21, 18, 0, 0),
            ),
        ]

        # Task 2 (priority 5) scheduled first, Task 1 (priority 10) second
        tasks_bad_order = [tasks_good_order[1], tasks_good_order[0]]

        score_good = self.calculator._calculate_priority_score(tasks_good_order)
        score_bad = self.calculator._calculate_priority_score(tasks_bad_order)

        # Good order should have higher score
        self.assertGreater(score_good, score_bad)

        # Verify calculation: priority * (total_tasks - position)
        # Good: 10 * (2 - 0) + 5 * (2 - 1) = 20 + 5 = 25
        self.assertAlmostEqual(score_good, 25.0, places=5)
        # Bad: 5 * (2 - 0) + 10 * (2 - 1) = 10 + 10 = 20
        self.assertAlmostEqual(score_bad, 20.0, places=5)

    def test_priority_score_with_different_priorities(self):
        """Test priority score calculation with different priority values."""
        tasks = [
            Task(
                id=1,
                name="High Priority",
                priority=10,
                planned_start=datetime(2025, 10, 20, 9, 0, 0),
                planned_end=datetime(2025, 10, 20, 18, 0, 0),
            ),
            Task(
                id=2,
                name="Low Priority",
                priority=1,
                planned_start=datetime(2025, 10, 21, 9, 0, 0),
                planned_end=datetime(2025, 10, 21, 18, 0, 0),
            ),
        ]

        score = self.calculator._calculate_priority_score(tasks)
        # First task: 10 * (2 - 0) = 20
        # Second task: 1 * (2 - 1) = 1
        # Total: 20 + 1 = 21
        self.assertAlmostEqual(score, 21.0, places=5)

    def test_deadline_penalty_for_late_tasks(self):
        """Test that tasks finishing after deadline incur penalties."""
        # Task finishes 3 days late
        late_task = Task(
            id=1,
            name="Late Task",
            priority=5,
            deadline=datetime(2025, 10, 20, 18, 0, 0),
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 23, 18, 0, 0),  # 3 days late
        )

        penalty = self.calculator._calculate_deadline_penalty([late_task])
        # 3 days * DEADLINE_PENALTY_MULTIPLIER
        expected_penalty = 3 * DEADLINE_PENALTY_MULTIPLIER
        self.assertAlmostEqual(penalty, expected_penalty, places=5)

    def test_deadline_penalty_zero_for_on_time_tasks(self):
        """Test that tasks finishing on or before deadline have no penalty."""
        on_time_task = Task(
            id=1,
            name="On Time Task",
            priority=5,
            deadline=datetime(2025, 10, 23, 18, 0, 0),
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 23, 18, 0, 0),  # Exactly on deadline
        )

        early_task = Task(
            id=2,
            name="Early Task",
            priority=3,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 23, 18, 0, 0),  # 2 days early
        )

        penalty = self.calculator._calculate_deadline_penalty(
            [on_time_task, early_task]
        )
        self.assertEqual(penalty, 0.0)

    def test_deadline_penalty_ignores_tasks_without_deadline(self):
        """Test that tasks without deadline don't incur penalty."""
        tasks = [
            Task(
                id=1,
                name="No Deadline",
                priority=5,
                deadline=None,
                planned_start=datetime(2025, 10, 20, 9, 0, 0),
                planned_end=datetime(2025, 10, 23, 18, 0, 0),
            ),
            Task(
                id=2,
                name="No Planned End",
                priority=3,
                deadline=datetime(2025, 10, 20, 18, 0, 0),
                planned_start=datetime(2025, 10, 20, 9, 0, 0),
                planned_end=None,
            ),
        ]

        penalty = self.calculator._calculate_deadline_penalty(tasks)
        self.assertEqual(penalty, 0.0)

    def test_workload_penalty_for_unbalanced_schedule(self):
        """Test that unbalanced workload distribution incurs penalty."""
        # Highly unbalanced: 8h on one day, 2h on another
        unbalanced_allocations = {
            date(2025, 10, 20): 8.0,
            date(2025, 10, 21): 2.0,
        }

        # Balanced: 5h on each day
        balanced_allocations = {
            date(2025, 10, 20): 5.0,
            date(2025, 10, 21): 5.0,
        }

        penalty_unbalanced = self.calculator._calculate_workload_penalty(
            unbalanced_allocations
        )
        penalty_balanced = self.calculator._calculate_workload_penalty(
            balanced_allocations
        )

        # Unbalanced should have higher penalty
        self.assertGreater(penalty_unbalanced, penalty_balanced)

        # Balanced should have zero penalty (zero variance)
        self.assertEqual(penalty_balanced, 0.0)

        # Verify unbalanced calculation:
        # avg = (8 + 2) / 2 = 5
        # variance = ((8-5)^2 + (2-5)^2) / 2 = (9 + 9) / 2 = 9
        # penalty = 9 * 10 = 90
        self.assertAlmostEqual(penalty_unbalanced, 90.0, places=5)

    def test_workload_penalty_zero_for_empty_allocations(self):
        """Test that empty allocations have zero penalty."""
        penalty = self.calculator._calculate_workload_penalty({})
        self.assertEqual(penalty, 0.0)

    def test_calculate_fitness_combines_all_components(self):
        """Test that fitness combines priority score, deadline penalty, and workload penalty."""
        # Create 2 tasks: one on time with high priority, one late with low priority
        tasks = [
            Task(
                id=1,
                name="Good Task",
                priority=10,
                deadline=datetime(2025, 10, 25, 18, 0, 0),
                planned_start=datetime(2025, 10, 20, 9, 0, 0),
                planned_end=datetime(2025, 10, 21, 18, 0, 0),  # On time
            ),
            Task(
                id=2,
                name="Late Task",
                priority=5,
                deadline=datetime(2025, 10, 22, 18, 0, 0),
                planned_start=datetime(2025, 10, 22, 9, 0, 0),
                planned_end=datetime(2025, 10, 24, 18, 0, 0),  # 2 days late
            ),
        ]

        # Balanced allocations
        allocations = {
            date(2025, 10, 20): 5.0,
            date(2025, 10, 21): 5.0,
            date(2025, 10, 22): 5.0,
            date(2025, 10, 23): 5.0,
            date(2025, 10, 24): 5.0,
        }

        fitness = self.calculator.calculate_fitness(
            tasks, allocations, include_scheduling_bonus=False
        )

        # Manual calculation:
        # Priority score: 10 * (2 - 0) + 5 * (2 - 1) = 20 + 5 = 25
        # Deadline penalty: 2 days * 100 = 200
        # Workload penalty: 0 (balanced)
        # Fitness = 25 - 200 - 0 = -175
        self.assertAlmostEqual(fitness, -175.0, places=5)


if __name__ == "__main__":
    unittest.main()
