"""Tests for BalancedAllocator."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from application.services.optimization.allocators.balanced_allocator import BalancedAllocator
from domain.entities.task import Task, TaskStatus
from shared.config_manager import Config, DisplayConfig, OptimizationConfig, TaskConfig, TimeConfig


class TestBalancedAllocator(unittest.TestCase):
    """Test cases for BalancedAllocator."""

    def setUp(self):
        """Initialize allocator and config for each test."""
        self.config = Config(
            optimization=OptimizationConfig(max_hours_per_day=6.0, default_algorithm="balanced"),
            task=TaskConfig(default_priority=5),
            display=DisplayConfig(datetime_format="%Y-%m-%d %H:%M:%S"),
            time=TimeConfig(default_start_hour=9, default_end_hour=18),
        )
        self.allocator = BalancedAllocator(self.config)
        self.repository = MagicMock()

    def test_allocate_distributes_evenly(self):
        """Test that allocator distributes hours evenly across available days."""
        # Create task with 10h duration over 5 weekdays (2h per day)
        task = Task(
            id=1,
            name="Balanced Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday (5 weekdays from Monday)
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        # Verify allocation succeeded
        self.assertIsNotNone(result)
        self.assertEqual(result.planned_start, datetime(2025, 10, 20, 9, 0, 0))
        self.assertEqual(result.planned_end, datetime(2025, 10, 24, 18, 0, 0))

        # Verify balanced distribution: 10h / 5 days = 2h per day
        self.assertIsNotNone(result.daily_allocations)
        self.assertEqual(len(result.daily_allocations), 5)  # Mon-Fri

        # All allocations should be exactly 2h (balanced)
        for allocation in result.daily_allocations.values():
            self.assertAlmostEqual(allocation, 2.0, places=5)

    def test_allocate_handles_no_deadline(self):
        """Test that allocator uses 2-week default period when no deadline."""
        task = Task(
            id=1,
            name="No Deadline Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=20.0,
            deadline=None,
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Should distribute evenly over ~10 weekdays (2 weeks)
        # 20h / 10 days = 2h per day
        allocations = list(result.daily_allocations.values())
        avg_allocation = sum(allocations) / len(allocations)
        self.assertAlmostEqual(avg_allocation, 2.0, delta=0.5)

    def test_allocate_skips_weekends(self):
        """Test that allocator skips weekends in distribution."""
        task = Task(
            id=1,
            name="Weekend Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 27, 18, 0, 0),  # Mon 10/20 to Mon 10/27
        )

        start_date = datetime(2025, 10, 24, 9, 0, 0)  # Friday
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Verify no weekend allocations
        self.assertNotIn("2025-10-25", result.daily_allocations)  # Saturday
        self.assertNotIn("2025-10-26", result.daily_allocations)  # Sunday

    def test_allocate_respects_max_hours_per_day(self):
        """Test that allocator respects max_hours_per_day constraint."""
        # 10h over 5 days with max 2h/day should work exactly
        task = Task(
            id=1,
            name="Constrained Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 2.0  # Exactly the target amount
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # All allocations should be <= max_hours_per_day
        for allocation in result.daily_allocations.values():
            self.assertLessEqual(allocation, max_hours_per_day + 0.01)  # Small tolerance

    def test_allocate_respects_existing_allocations(self):
        """Test that allocator respects existing daily allocations."""
        # 10h over 5 days (target 2h/day) but Monday has 4h already used
        task = Task(
            id=1,
            name="Existing Allocations Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        # Monday already has some allocation
        daily_allocations: dict[str, float] = {
            "2025-10-20": 4.0,  # 2h available (wants to allocate 2h)
        }

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Verify allocations respect existing capacity
        self.assertLessEqual(daily_allocations["2025-10-20"], 6.0)
        # Should have allocated 2h on Monday
        self.assertAlmostEqual(daily_allocations["2025-10-20"], 6.0, places=5)

    def test_allocate_fails_when_insufficient_capacity(self):
        """Test that allocator returns None when insufficient capacity."""
        task = Task(
            id=1,
            name="Impossible Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=30.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),  # Only 3 days (18h max)
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        # Should fail to allocate
        self.assertIsNone(result)

    def test_allocate_fails_without_estimated_duration(self):
        """Test that allocator returns None for tasks without estimated_duration."""
        task = Task(
            id=1,
            name="No Estimate",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=None,
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNone(result)

    def test_allocate_rollback_on_failure(self):
        """Test that allocator rolls back allocations on failure."""
        task = Task(
            id=1,
            name="Rollback Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=25.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),  # Cannot fit 25h in 3 days
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {"2025-10-19": 2.0}  # Pre-existing

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNone(result)
        # Pre-existing allocations should remain
        self.assertIn("2025-10-19", daily_allocations)
        self.assertEqual(daily_allocations["2025-10-19"], 2.0)

    def test_allocate_more_balanced_than_greedy(self):
        """Test that balanced allocator creates more even distribution than greedy."""
        task = Task(
            id=1,
            name="Comparison Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 27, 18, 0, 0),  # 5 weekdays available
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)

        # Calculate standard deviation to measure balance
        allocations = list(result.daily_allocations.values())
        mean = sum(allocations) / len(allocations)
        variance = sum((x - mean) ** 2 for x in allocations) / len(allocations)
        std_dev = variance**0.5

        # Balanced allocation should have low standard deviation
        # (all days roughly equal)
        self.assertLess(std_dev, 1.0)  # Should be fairly balanced


if __name__ == "__main__":
    unittest.main()
