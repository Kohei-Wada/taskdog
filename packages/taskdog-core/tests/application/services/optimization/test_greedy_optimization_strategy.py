"""Tests for GreedyOptimizationStrategy."""

from datetime import date, datetime

from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestGreedyOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for GreedyOptimizationStrategy."""

    algorithm_name = "greedy"

    def test_greedy_front_loads_single_task(self):
        """Test that greedy strategy front-loads a single task."""
        # Create task with 12h duration - should fill 2 days with 6h each
        task = self.create_task(
            "Greedy Task",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        # Start on Monday
        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify greedy front-loading
        assert len(result.successful_tasks) == 1

        # Should start on Monday, end on Tuesday (12h / 6h per day = 2 days)
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 20, 0, 0, 0),
            expected_end=datetime(2025, 10, 21, 23, 59, 59),
        )

        # Check daily allocations: greedy fills each day to max
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert len(updated_task.daily_allocations) == 2  # Mon-Tue
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 20), 0.0) - 6.0)
            < 1e-5
        )
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 21), 0.0) - 6.0)
            < 1e-5
        )

    def test_greedy_handles_partial_day(self):
        """Test that greedy strategy handles partial day allocation."""
        # Create task with 10h duration - should fill: 6h (day 1) + 4h (day 2)
        task = self.create_task(
            "Partial Day Task",
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Check daily allocations
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 20), 0.0) - 6.0)
            < 1e-5
        )
        assert (
            abs(updated_task.daily_allocations.get(date(2025, 10, 21), 0.0) - 4.0)
            < 1e-5
        )

    def test_greedy_skips_weekends(self):
        """Test that greedy strategy skips weekends."""
        # Create task that spans Friday to Monday
        task = self.create_task(
            "Weekend Task",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        # Start on Friday
        self.optimize_schedule(start_date=datetime(2025, 10, 24, 9, 0, 0))

        # Should start Friday, end Monday (skipping Saturday/Sunday)
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 24, 0, 0, 0),
            expected_end=datetime(2025, 10, 27, 23, 59, 59),
        )

        # Verify no weekend allocations
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert (
            updated_task.daily_allocations.get(date(2025, 10, 25)) is None
        )  # Saturday
        assert updated_task.daily_allocations.get(date(2025, 10, 26)) is None  # Sunday

    def test_greedy_respects_deadline(self):
        """Test that greedy strategy respects task deadlines."""
        # Create task with tight deadline (30h work but only 3 days * 6h/day = 18h available)
        self.create_task(
            "Tight Deadline",
            estimated_duration=30.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Should fail to schedule
        assert len(result.successful_tasks) == 0
        assert len(result.failed_tasks) == 1

    def test_greedy_respects_fixed_tasks_in_daily_limit(self):
        """Test that greedy strategy accounts for fixed tasks when calculating available hours."""
        # Create a fixed task with 4h/day allocation for 3 days (Mon-Wed)
        fixed_task = self.create_task(
            "Fixed Meeting",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 25, 18, 0, 0),
            is_fixed=True,
        )

        # Manually schedule the fixed task with specific daily allocations
        fixed_task.planned_start = datetime(2025, 10, 20, 9, 0, 0)
        fixed_task.planned_end = datetime(2025, 10, 22, 18, 0, 0)
        fixed_task.daily_allocations = {
            date(2025, 10, 20): 4.0,  # Monday: 4h
            date(2025, 10, 21): 4.0,  # Tuesday: 4h
            date(2025, 10, 22): 4.0,  # Wednesday: 4h
        }
        self.repository.save(fixed_task)

        # Create a regular task that needs 6h
        regular_task = self.create_task(
            "Regular Task",
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        # Optimize with max_hours_per_day=6.0
        # Available hours per day: 6.0 - 4.0 (fixed) = 2.0h
        # So 6h task should take 3 days (2h * 3 = 6h)
        result = self.optimize_schedule(
            start_date=datetime(2025, 10, 20, 9, 0, 0),
            force_override=True,
        )

        # Verify regular task was scheduled
        assert len(result.successful_tasks) == 1

        # Refetch regular task from repository to get updated state
        updated_regular = self.repository.get_by_id(regular_task.id)
        assert updated_regular is not None

        # Verify daily allocations respect fixed task hours
        # Each day should have max 2h for regular task (6.0 - 4.0 fixed)
        assert (
            abs(updated_regular.daily_allocations.get(date(2025, 10, 20), 0.0) - 2.0)
            < 1e-5
        )
        assert (
            abs(updated_regular.daily_allocations.get(date(2025, 10, 21), 0.0) - 2.0)
            < 1e-5
        )
        assert (
            abs(updated_regular.daily_allocations.get(date(2025, 10, 22), 0.0) - 2.0)
            < 1e-5
        )

        # Verify total daily allocations don't exceed max_hours_per_day
        for date_str, hours in result.daily_allocations.items():
            assert hours <= 6.0, (
                f"Total hours on {date_str} ({hours}h) exceeds max_hours_per_day (6.0h)"
            )

    def test_greedy_schedules_task_due_today_after_deadline_time(self):
        """Test that a task due today is scheduled regardless of wall-clock time.

        Allocation is day-granular, so a task with a deadline of today 18:00
        must still be schedulable when the optimizer runs later the same day
        (e.g. start_date defaulting to now() at 19:00). Regression test for #964.
        """
        task = self.create_task(
            "Due Today",
            estimated_duration=2.0,
            deadline=datetime(2025, 10, 20, 18, 0, 0),
        )

        # Optimizer runs at 19:00 on the deadline day
        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 19, 0, 0))

        assert len(result.successful_tasks) == 1
        assert len(result.failed_tasks) == 0

        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert date(2025, 10, 20) in updated_task.daily_allocations

    def test_greedy_exact_multiple_of_fractional_max_hours(self):
        """Fractional hours that divide evenly must not spill onto an extra day.

        20.1h at 6.7h/day is exactly 3 days, but 20.1 - 6.7 - 6.7 - 6.7 leaves
        ~1.8e-15 rather than 0.0, so a bare `remaining_hours > 0` check runs a
        fourth day and allocates the residue there.
        """
        task = self.create_task(
            "Fractional Task",
            estimated_duration=20.1,
            deadline=datetime(2025, 10, 31, 18, 0, 0),
        )

        result = self.optimize_schedule(
            start_date=datetime(2025, 10, 20, 9, 0, 0),
            max_hours_per_day=6.7,
        )

        assert len(result.successful_tasks) == 1
        assert len(result.failed_tasks) == 0

        # Mon-Wed, not Mon-Thu
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 20, 0, 0, 0),
            expected_end=datetime(2025, 10, 22, 23, 59, 59),
        )

        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert len(updated_task.daily_allocations) == 3
        assert date(2025, 10, 23) not in updated_task.daily_allocations

    def test_greedy_exact_fit_against_deadline_is_schedulable(self):
        """A task that exactly fills the days up to its deadline must schedule.

        20.1h at 6.7h/day needs Mon-Wed and the deadline is Wednesday. The float
        residue pushes allocation to Thursday, past the deadline, so the task is
        wrongly reported unschedulable.
        """
        self.create_task(
            "Exact Fit Task",
            estimated_duration=20.1,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(
            start_date=datetime(2025, 10, 20, 9, 0, 0),
            max_hours_per_day=6.7,
        )

        assert len(result.failed_tasks) == 0
        assert len(result.successful_tasks) == 1
