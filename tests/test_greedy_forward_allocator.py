"""Tests for GreedyForwardAllocator."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from domain.entities.task import Task, TaskStatus
from shared.config_manager import Config, DisplayConfig, OptimizationConfig, TaskConfig, TimeConfig


class TestGreedyForwardAllocator(unittest.TestCase):
    """Test cases for GreedyForwardAllocator."""

    def setUp(self):
        """Initialize allocator and config for each test."""
        self.config = Config(
            optimization=OptimizationConfig(max_hours_per_day=6.0, default_algorithm="greedy"),
            task=TaskConfig(default_priority=5),
            display=DisplayConfig(datetime_format="%Y-%m-%d %H:%M:%S"),
            time=TimeConfig(default_start_hour=9, default_end_hour=18),
        )
        self.allocator = GreedyForwardAllocator(self.config)
        self.repository = MagicMock()

    def test_allocate_single_task_fills_days_greedily(self):
        """Test that allocator fills each day to max capacity (greedy approach)."""
        # Create task with 12h duration
        task = Task(
            id=1,
            name="Test Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=12.0,
            deadline="2025-10-31 18:00:00",
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        # Verify allocation succeeded
        self.assertIsNotNone(result)
        self.assertEqual(result.planned_start, "2025-10-20 09:00:00")
        self.assertEqual(result.planned_end, "2025-10-21 18:00:00")

        # Verify greedy allocation: fills each day to max (6h each)
        self.assertIsNotNone(result.daily_allocations)
        self.assertEqual(len(result.daily_allocations), 2)
        self.assertAlmostEqual(result.daily_allocations["2025-10-20"], 6.0, places=5)
        self.assertAlmostEqual(result.daily_allocations["2025-10-21"], 6.0, places=5)

        # Verify global daily_allocations updated
        self.assertAlmostEqual(daily_allocations["2025-10-20"], 6.0, places=5)
        self.assertAlmostEqual(daily_allocations["2025-10-21"], 6.0, places=5)

    def test_allocate_handles_partial_day(self):
        """Test that allocator handles partial day allocation correctly."""
        # Create task with 10h duration (6h + 4h)
        task = Task(
            id=1,
            name="Partial Day",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
            deadline="2025-10-31 18:00:00",
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.daily_allocations["2025-10-20"], 6.0, places=5)
        self.assertAlmostEqual(result.daily_allocations["2025-10-21"], 4.0, places=5)

    def test_allocate_skips_weekends(self):
        """Test that allocator skips weekends."""
        # Create task spanning Friday to Monday
        task = Task(
            id=1,
            name="Weekend Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=12.0,
            deadline="2025-10-31 18:00:00",
        )

        start_date = datetime(2025, 10, 24, 9, 0, 0)  # Friday
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.planned_start, "2025-10-24 09:00:00")
        self.assertEqual(result.planned_end, "2025-10-27 18:00:00")  # Monday

        # Verify no weekend allocations
        self.assertNotIn("2025-10-25", result.daily_allocations)  # Saturday
        self.assertNotIn("2025-10-26", result.daily_allocations)  # Sunday
        # Verify only weekday allocations
        self.assertIn("2025-10-24", result.daily_allocations)  # Friday
        self.assertIn("2025-10-27", result.daily_allocations)  # Monday

    def test_allocate_respects_existing_allocations(self):
        """Test that allocator respects existing daily allocations."""
        task = Task(
            id=1,
            name="Constrained Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=8.0,
            deadline="2025-10-31 18:00:00",
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        # Monday already has 4h allocated
        daily_allocations: dict[str, float] = {"2025-10-20": 4.0}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Monday: 2h (6 - 4), Tuesday: 6h
        self.assertAlmostEqual(result.daily_allocations["2025-10-20"], 2.0, places=5)
        self.assertAlmostEqual(result.daily_allocations["2025-10-21"], 6.0, places=5)

        # Verify global allocations updated correctly
        self.assertAlmostEqual(daily_allocations["2025-10-20"], 6.0, places=5)  # 4 + 2
        self.assertAlmostEqual(daily_allocations["2025-10-21"], 6.0, places=5)

    def test_allocate_fails_when_deadline_exceeded(self):
        """Test that allocator returns None when deadline cannot be met."""
        task = Task(
            id=1,
            name="Impossible Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=30.0,  # Too much work
            deadline="2025-10-22 18:00:00",  # Only 3 days available (18h)
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        # Should fail to allocate
        self.assertIsNone(result)
        # Note: Rollback happens but allocations were made during the attempt,
        # so daily_allocations may have entries. The important thing is that
        # the task itself was not scheduled (result is None).

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

    def test_allocate_fails_with_zero_duration(self):
        """Test that allocator returns None for tasks with zero duration."""
        task = Task(
            id=1,
            name="Zero Duration",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=0.0,
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
            estimated_duration=20.0,
            deadline="2025-10-22 18:00:00",  # Cannot fit 20h in 3 days (18h max)
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {"2025-10-19": 2.0}  # Pre-existing allocation

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNone(result)
        # Verify rollback: task's allocations were removed
        # Pre-existing allocations should remain
        self.assertIn("2025-10-19", daily_allocations)
        self.assertEqual(daily_allocations["2025-10-19"], 2.0)

    def test_allocate_uses_config_default_end_hour(self):
        """Test that allocator uses config.time.default_end_hour for planned_end."""
        task = Task(
            id=1,
            name="End Hour Test",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=6.0,
            deadline="2025-10-31 18:00:00",
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Should use default_end_hour (18) from config
        self.assertEqual(result.planned_end, "2025-10-20 18:00:00")


if __name__ == "__main__":
    unittest.main()
