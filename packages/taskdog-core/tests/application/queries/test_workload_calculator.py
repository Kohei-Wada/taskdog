"""Tests for WorkloadCalculator query service."""

import unittest
from datetime import date, datetime, timedelta

from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
from taskdog_core.domain.entities.task import Task, TaskStatus


class WorkloadCalculatorTest(unittest.TestCase):
    """Test cases for WorkloadCalculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = WorkloadCalculator()

    def test_calculate_daily_workload_single_task(self):
        """Test workload calculation with a single task."""
        # Task from Monday to Friday (5 weekdays), 10 hours estimated
        # Expected with equal distribution: 10h / 5 days = 2h per day
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 10, 18, 0, 0),  # Friday
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Equal distribution: 2h per day on all weekdays
        self.assertAlmostEqual(result[date(2025, 1, 6)], 2.0, places=2)  # Monday
        self.assertAlmostEqual(result[date(2025, 1, 7)], 2.0, places=2)  # Tuesday
        self.assertAlmostEqual(result[date(2025, 1, 8)], 2.0, places=2)  # Wednesday
        self.assertAlmostEqual(result[date(2025, 1, 9)], 2.0, places=2)  # Thursday
        self.assertAlmostEqual(result[date(2025, 1, 10)], 2.0, places=2)  # Friday

    def test_calculate_daily_workload_excludes_weekends(self):
        """Test that weekends are excluded from workload calculation."""
        # Task spanning a weekend (Friday to Tuesday)
        # Expected with equal distribution: 6h / 3 weekdays (Fri, Mon, Tue) = 2h per day
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 10, 9, 0, 0),  # Friday
            planned_end=datetime(2025, 1, 14, 18, 0, 0),  # Tuesday (next week)
            estimated_duration=6.0,  # 3 weekdays: Fri, Mon, Tue
        )

        start_date = date(2025, 1, 10)  # Friday
        end_date = date(2025, 1, 14)  # Tuesday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Equal distribution: 2h per weekday, weekends excluded
        self.assertAlmostEqual(result[date(2025, 1, 10)], 2.0, places=2)  # Friday
        self.assertAlmostEqual(result[date(2025, 1, 11)], 0.0, places=2)  # Saturday
        self.assertAlmostEqual(result[date(2025, 1, 12)], 0.0, places=2)  # Sunday
        self.assertAlmostEqual(result[date(2025, 1, 13)], 2.0, places=2)  # Monday
        self.assertAlmostEqual(result[date(2025, 1, 14)], 2.0, places=2)  # Tuesday

    def test_calculate_daily_workload_multiple_tasks(self):
        """Test workload calculation with multiple overlapping tasks."""
        # With equal distribution:
        # Task 1 (6h, Mon-Wed, 3 weekdays): 2h per day
        # Task 2 (9h, Wed-Fri, 3 weekdays): 3h per day
        task1 = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
        )

        # Task 2: Wednesday to Friday, 9 hours
        task2 = Task(
            id=2,
            name="Task 2",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 8, 9, 0, 0),  # Wednesday
            planned_end=datetime(2025, 1, 10, 18, 0, 0),  # Friday
            estimated_duration=9.0,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload(
            [task1, task2], start_date, end_date
        )

        # Task 1: 2h on Mon, Tue, Wed
        # Task 2: 3h on Wed, Thu, Fri
        # Wednesday has both: 2h + 3h = 5h
        self.assertAlmostEqual(
            result[date(2025, 1, 6)], 2.0, places=2
        )  # Monday (task1)
        self.assertAlmostEqual(
            result[date(2025, 1, 7)], 2.0, places=2
        )  # Tuesday (task1)
        self.assertAlmostEqual(
            result[date(2025, 1, 8)], 5.0, places=2
        )  # Wednesday (task1 + task2)
        self.assertAlmostEqual(
            result[date(2025, 1, 9)], 3.0, places=2
        )  # Thursday (task2)
        self.assertAlmostEqual(
            result[date(2025, 1, 10)], 3.0, places=2
        )  # Friday (task2)

    def test_calculate_daily_workload_no_estimated_duration(self):
        """Test that tasks without estimated duration are skipped."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),
            planned_end=datetime(2025, 1, 10, 18, 0, 0),
            estimated_duration=None,  # No estimate
        )

        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # All days should have 0 hours
        for day_offset in range(5):
            current_date = start_date + timedelta(days=day_offset)
            self.assertEqual(result[current_date], 0.0)

    def test_calculate_daily_workload_no_planned_dates(self):
        """Test that tasks without planned dates are skipped."""
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=None,
            planned_end=None,
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # All days should have 0 hours
        for day_offset in range(5):
            current_date = start_date + timedelta(days=day_offset)
            self.assertEqual(result[current_date], 0.0)

    def test_calculate_daily_workload_task_outside_range(self):
        """Test that tasks outside the date range are handled correctly."""
        # Task from Feb 1-5, but we're looking at Jan 6-10
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 2, 1, 9, 0, 0),
            planned_end=datetime(2025, 2, 5, 18, 0, 0),
            estimated_duration=10.0,
        )

        start_date = date(2025, 1, 6)
        end_date = date(2025, 1, 10)

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # All days should have 0 hours (task is outside range)
        for day_offset in range(5):
            current_date = start_date + timedelta(days=day_offset)
            self.assertEqual(result[current_date], 0.0)

    def test_calculate_daily_workload_excludes_completed_tasks(self):
        """Test that completed tasks are excluded from workload calculation."""
        # Task 1: PENDING task (Monday to Wednesday, 6 hours, 3 weekdays)
        # With equal distribution: 2h per day
        task1 = Task(
            id=1,
            name="Pending Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
        )

        # Task 2: COMPLETED task (Wednesday to Friday, 9 hours) - should be excluded
        task2 = Task(
            id=2,
            name="Completed Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 8, 9, 0, 0),  # Wednesday
            planned_end=datetime(2025, 1, 10, 18, 0, 0),  # Friday
            estimated_duration=9.0,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload(
            [task1, task2], start_date, end_date
        )

        # Only task1 (PENDING) should be counted with equal distribution
        # Task2 (COMPLETED) is excluded entirely
        self.assertAlmostEqual(
            result[date(2025, 1, 6)], 2.0, places=2
        )  # Monday (task1)
        self.assertAlmostEqual(
            result[date(2025, 1, 7)], 2.0, places=2
        )  # Tuesday (task1)
        self.assertAlmostEqual(
            result[date(2025, 1, 8)], 2.0, places=2
        )  # Wednesday (task1)
        self.assertAlmostEqual(
            result[date(2025, 1, 9)], 0.0, places=2
        )  # Thursday (task2 excluded)
        self.assertAlmostEqual(
            result[date(2025, 1, 10)], 0.0, places=2
        )  # Friday (task2 excluded)

    def test_calculate_daily_workload_with_daily_allocations(self):
        """Test workload calculation using daily_allocations from optimization."""
        # Task with daily_allocations (from optimization)
        # Monday: 5h, Tuesday: 1h
        task = Task(
            id=1,
            name="Optimized Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 7, 18, 0, 0),  # Tuesday
            estimated_duration=6.0,
            daily_allocations={
                date(2025, 1, 6): 5.0,  # Monday
                date(2025, 1, 7): 1.0,  # Tuesday
            },
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Should use daily_allocations instead of equal distribution
        self.assertAlmostEqual(result[date(2025, 1, 6)], 5.0, places=2)  # Monday
        self.assertAlmostEqual(result[date(2025, 1, 7)], 1.0, places=2)  # Tuesday
        self.assertAlmostEqual(result[date(2025, 1, 8)], 0.0, places=2)  # Wednesday
        self.assertAlmostEqual(result[date(2025, 1, 9)], 0.0, places=2)  # Thursday
        self.assertAlmostEqual(result[date(2025, 1, 10)], 0.0, places=2)  # Friday

    def test_calculate_daily_workload_fallback_to_equal_distribution(self):
        """Test that calculator falls back to equal distribution when daily_allocations is empty."""
        # Task without daily_allocations (backward compatibility)
        task = Task(
            id=1,
            name="Legacy Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
            daily_allocations={},  # Empty dict (no optimizer data)
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload([task], start_date, end_date)

        # Should fall back to equal distribution: 6h / 3 weekdays = 2h per day
        self.assertAlmostEqual(result[date(2025, 1, 6)], 2.0, places=2)  # Monday
        self.assertAlmostEqual(result[date(2025, 1, 7)], 2.0, places=2)  # Tuesday
        self.assertAlmostEqual(result[date(2025, 1, 8)], 2.0, places=2)  # Wednesday
        self.assertAlmostEqual(result[date(2025, 1, 9)], 0.0, places=2)  # Thursday
        self.assertAlmostEqual(result[date(2025, 1, 10)], 0.0, places=2)  # Friday

    def test_calculate_daily_workload_excludes_archived_tasks(self):
        """Test that archived tasks are excluded from workload calculation."""
        # Task 1: PENDING task (Monday to Wednesday, 6 hours, 3 weekdays)
        # With equal distribution: 2h per day
        task1 = Task(
            id=1,
            name="Active Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 6, 9, 0, 0),  # Monday
            planned_end=datetime(2025, 1, 8, 18, 0, 0),  # Wednesday
            estimated_duration=6.0,
        )

        # Task 2: PENDING but archived task (Wednesday to Friday, 9 hours) - should be excluded
        task2 = Task(
            id=2,
            name="Archived Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.fromtimestamp(1234567890.0),
            planned_start=datetime(2025, 1, 8, 9, 0, 0),  # Wednesday
            planned_end=datetime(2025, 1, 10, 18, 0, 0),  # Friday
            estimated_duration=9.0,
            is_archived=True,
        )

        start_date = date(2025, 1, 6)  # Monday
        end_date = date(2025, 1, 10)  # Friday

        result = self.calculator.calculate_daily_workload(
            [task1, task2], start_date, end_date
        )

        # Only task1 (active) should be counted with equal distribution
        # Task2 (archived) is excluded entirely
        self.assertAlmostEqual(
            result[date(2025, 1, 6)], 2.0, places=2
        )  # Monday (task1)
        self.assertAlmostEqual(
            result[date(2025, 1, 7)], 2.0, places=2
        )  # Tuesday (task1)
        self.assertAlmostEqual(
            result[date(2025, 1, 8)], 2.0, places=2
        )  # Wednesday (task1)
        self.assertAlmostEqual(
            result[date(2025, 1, 9)], 0.0, places=2
        )  # Thursday (task2 excluded)
        self.assertAlmostEqual(
            result[date(2025, 1, 10)], 0.0, places=2
        )  # Friday (task2 excluded)


if __name__ == "__main__":
    unittest.main()
