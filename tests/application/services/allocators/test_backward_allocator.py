"""Tests for BackwardAllocator."""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock

from application.services.optimization.allocators.backward_allocator import BackwardAllocator
from domain.entities.task import Task, TaskStatus


class TestBackwardAllocator(unittest.TestCase):
    """Test cases for BackwardAllocator."""

    def setUp(self):
        """Initialize allocator for each test."""
        self.allocator = BackwardAllocator(default_start_hour=9, default_end_hour=18)
        self.repository = MagicMock()

    def test_allocate_schedules_backward_from_deadline(self):
        """Test that allocator schedules tasks backward from deadline."""
        # 12h task with deadline on Friday
        # Should fill: Thu 6h, Fri 6h (backward allocation)
        task = Task(
            id=1,
            name="Backward Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday (start constraint)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        # Verify allocation succeeded
        self.assertIsNotNone(result)
        # Should start on Thursday (last 2 days before deadline)
        self.assertEqual(result.planned_start, datetime(2025, 10, 23, 9, 0, 0))
        self.assertEqual(result.planned_end, datetime(2025, 10, 24, 18, 0, 0))

        # Verify backward allocation: fills last days first
        self.assertIsNotNone(result.daily_allocations)
        self.assertEqual(len(result.daily_allocations), 2)  # Thu-Fri
        self.assertAlmostEqual(
            result.daily_allocations[date(2025, 10, 23)], 6.0, places=5
        )  # Thursday
        self.assertAlmostEqual(
            result.daily_allocations[date(2025, 10, 24)], 6.0, places=5
        )  # Friday

    def test_allocate_handles_partial_day(self):
        """Test that allocator handles partial day allocation correctly."""
        # 10h task: should fill 6h + 4h backward from deadline
        task = Task(
            id=1,
            name="Partial Day",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Should start Thursday, end Friday
        self.assertEqual(result.planned_start, datetime(2025, 10, 23, 9, 0, 0))
        self.assertEqual(result.planned_end, datetime(2025, 10, 24, 18, 0, 0))

        # Verify backward allocation: 6h Friday, 4h Thursday
        self.assertAlmostEqual(result.daily_allocations[date(2025, 10, 24)], 6.0, places=5)
        self.assertAlmostEqual(result.daily_allocations[date(2025, 10, 23)], 4.0, places=5)

    def test_allocate_skips_weekends(self):
        """Test that allocator skips weekends when allocating backward."""
        # 12h task with deadline on Monday
        # Should skip weekend and allocate to Thu-Fri
        task = Task(
            id=1,
            name="Weekend Skip",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 27, 18, 0, 0),  # Monday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday start
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Should allocate to Friday and Monday (skipping weekend)
        self.assertNotIn("2025-10-25", result.daily_allocations)  # Saturday
        self.assertNotIn("2025-10-26", result.daily_allocations)  # Sunday
        # Should have allocations on Friday and Monday
        self.assertIn(date(2025, 10, 24), result.daily_allocations)  # Friday
        self.assertIn(date(2025, 10, 27), result.daily_allocations)  # Monday

    def test_allocate_respects_start_date_constraint(self):
        """Test that allocator doesn't schedule before start_date."""
        # 30h task with tight deadline
        # start_date Mon, deadline Fri = only 5 days (30h max)
        task = Task(
            id=1,
            name="Start Constraint",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=30.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        # Should succeed (exactly fits: 5 days * 6h = 30h)
        self.assertIsNotNone(result)
        self.assertEqual(result.planned_start, datetime(2025, 10, 20, 9, 0, 0))

    def test_allocate_fails_when_insufficient_time(self):
        """Test that allocator returns None when insufficient time before deadline."""
        # 40h task but only 30h available (5 days * 6h)
        task = Task(
            id=1,
            name="Impossible Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=40.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)  # Monday
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        # Should fail to allocate
        self.assertIsNone(result)

    def test_allocate_handles_no_deadline(self):
        """Test that allocator uses 1-week default when no deadline."""
        task = Task(
            id=1,
            name="No Deadline",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=12.0,
            deadline=None,
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Should schedule within 1 week from start
        self.assertTrue(result.planned_start >= datetime(2025, 10, 20, 9, 0, 0))
        self.assertTrue(result.planned_end <= datetime(2025, 10, 27, 18, 0, 0))

    def test_allocate_respects_existing_allocations(self):
        """Test that allocator respects existing daily allocations."""
        # 12h task, deadline Friday
        # Friday already has 4h allocated
        task = Task(
            id=1,
            name="Existing Allocation",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {
            date(2025, 10, 24): 4.0,  # Friday has 2h available
        }

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Should respect existing allocation
        self.assertLessEqual(daily_allocations[date(2025, 10, 24)], 6.0)

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

    def test_allocate_fills_days_backward_greedily(self):
        """Test that allocator fills each day to maximum capacity working backward."""
        # 18h task, deadline Friday
        # Should fill: Wed 6h, Thu 6h, Fri 6h (working backward)
        task = Task(
            id=1,
            name="Greedy Backward",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=18.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),  # Friday
        )

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        max_hours_per_day = 6.0
        daily_allocations: dict[str, float] = {}

        result = self.allocator.allocate(
            task, start_date, max_hours_per_day, daily_allocations, self.repository
        )

        self.assertIsNotNone(result)
        # Should start Wednesday
        self.assertEqual(result.planned_start, datetime(2025, 10, 22, 9, 0, 0))
        self.assertEqual(result.planned_end, datetime(2025, 10, 24, 18, 0, 0))

        # Verify each day is filled to max
        self.assertAlmostEqual(result.daily_allocations[date(2025, 10, 22)], 6.0, places=5)  # Wed
        self.assertAlmostEqual(result.daily_allocations[date(2025, 10, 23)], 6.0, places=5)  # Thu
        self.assertAlmostEqual(result.daily_allocations[date(2025, 10, 24)], 6.0, places=5)  # Fri


if __name__ == "__main__":
    unittest.main()
