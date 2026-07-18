"""Tests for BackwardOptimizationStrategy."""

from datetime import date, datetime, timedelta

from taskdog_core.shared.constants import DEFAULT_SCHEDULE_DAYS
from tests.application.services.optimization.optimization_strategy_test_base import (
    BaseOptimizationStrategyTest,
)


class TestBackwardOptimizationStrategy(BaseOptimizationStrategyTest):
    """Test cases for BackwardOptimizationStrategy."""

    algorithm_name = "backward"

    def test_backward_schedules_close_to_deadline(self):
        """Test that backward strategy schedules tasks close to deadline."""
        # Create task with 6h duration and deadline on Friday
        # Should be scheduled on Friday (as late as possible)
        task = self.create_task(
            "JIT Task",
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        assert len(result.successful_tasks) == 1

        # Should be scheduled on Friday (closest to deadline)
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 24, 0, 0, 0),
            expected_end=datetime(2025, 10, 24, 23, 59, 59),
        )

        # Re-fetch task from repository to verify allocations
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        # All 6h allocated on Friday
        assert updated_task.daily_allocations[date(2025, 10, 24)] == 6.0

    def test_backward_spans_backward_from_deadline(self):
        """Test that backward strategy fills backwards when task doesn't fit in one day."""
        # Create task with 12h duration and deadline on Friday
        # With 6h/day max, needs 2 days: Thursday and Friday
        task = self.create_task(
            "Multi-day JIT",
            estimated_duration=12.0,
            deadline=datetime(2025, 10, 24, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        assert len(result.successful_tasks) == 1

        # Should start on Thursday, end on Friday
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 23, 0, 0, 0),
            expected_end=datetime(2025, 10, 24, 23, 59, 59),
        )

        # 6h on Thursday, 6h on Friday
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert updated_task.daily_allocations[date(2025, 10, 23)] == 6.0
        assert updated_task.daily_allocations[date(2025, 10, 24)] == 6.0

    def test_backward_without_deadline_uses_default_schedule_horizon(self):
        """A deadline-less task falls back to the shared DEFAULT_SCHEDULE_DAYS horizon.

        Regression for #1096: backward previously hardcoded a 7-day fallback while
        balanced used DEFAULT_SCHEDULE_DAYS, so identical input scheduled differently
        by strategy.
        """
        # Create task without deadline
        task = self.create_task("No Deadline Task", estimated_duration=6.0)

        start_date = datetime(2025, 10, 20, 9, 0, 0)
        result = self.optimize_schedule(start_date=start_date)

        # Verify
        assert len(result.successful_tasks) == 1

        # Should be 6h total
        self.assert_total_allocated_hours(task, 6.0)

        # Backward places the task at the fallback horizon; its allocation must fall
        # on the last workday on/before start_date + DEFAULT_SCHEDULE_DAYS.
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        horizon = (start_date + timedelta(days=DEFAULT_SCHEDULE_DAYS)).date()
        latest_allocated = max(updated_task.daily_allocations)
        assert latest_allocated <= horizon
        assert (horizon - latest_allocated).days <= 2  # skip weekend at most

    def test_backward_respects_max_hours_per_day(self):
        """Test that backward strategy respects max_hours_per_day constraint."""
        # Create task with 18h duration and deadline 3 weekdays away
        # With 6h/day max, should use all 3 days
        task = self.create_task(
            "Max Hours Task",
            estimated_duration=18.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        assert len(result.successful_tasks) == 1

        # Should respect max_hours_per_day
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        for hours in updated_task.daily_allocations.values():
            assert hours <= 6.0

        # Total should be 18h
        self.assert_total_allocated_hours(task, 18.0)

        # Should use Mon, Tue, Wed (backwards from Wed)
        assert len(updated_task.daily_allocations) == 3

    def test_backward_handles_multiple_tasks(self):
        """Test backward strategy with multiple tasks (furthest deadline first)."""
        # Create two tasks with different deadlines
        task1 = self.create_task(
            "Task 1", estimated_duration=6.0, deadline=datetime(2025, 10, 24, 18, 0, 0)
        )
        task2 = self.create_task(
            "Task 2", estimated_duration=6.0, deadline=datetime(2025, 10, 22, 18, 0, 0)
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Both tasks should be scheduled
        assert len(result.successful_tasks) == 2

        # Task 1 (further deadline) is processed first, scheduled on Friday
        updated_task1 = self.repository.get_by_id(task1.id)
        assert updated_task1 is not None
        assert updated_task1.planned_start == datetime(2025, 10, 24, 0, 0, 0)

        # Task 2 (closer deadline) is processed second, scheduled on Wednesday
        updated_task2 = self.repository.get_by_id(task2.id)
        assert updated_task2 is not None
        assert updated_task2.planned_start == datetime(2025, 10, 22, 0, 0, 0)

    def test_backward_fails_when_deadline_before_start(self):
        """Test that backward strategy fails when deadline is before start date."""
        # Create task with deadline before start date
        self.create_task(
            "Past Deadline",
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 19, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Task should not be scheduled
        assert len(result.successful_tasks) == 0

    def test_backward_skips_weekends(self):
        """Test that backward strategy skips weekends when allocating."""
        # Create task with 6h duration and deadline on Monday
        # Should skip weekend and allocate on Monday
        task = self.create_task(
            "Weekend Skip",
            estimated_duration=6.0,
            deadline=datetime(2025, 10, 27, 18, 0, 0),
        )

        result = self.optimize_schedule(start_date=datetime(2025, 10, 20, 9, 0, 0))

        # Verify
        assert len(result.successful_tasks) == 1

        # Should be scheduled on Monday (deadline day)
        self.assert_task_scheduled(
            task,
            expected_start=datetime(2025, 10, 27, 0, 0, 0),
            expected_end=datetime(2025, 10, 27, 23, 59, 59),
        )

        # Only Monday in allocations (no weekend days)
        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert len(updated_task.daily_allocations) == 1
        assert date(2025, 10, 27) in updated_task.daily_allocations

    def test_backward_schedules_task_due_today_after_deadline_time(self):
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

    def test_backward_exact_multiple_of_fractional_max_hours(self):
        """Fractional hours that divide evenly must not spill onto an extra day.

        20.1h at 6.7h/day is exactly 3 days, but the subtraction leaves ~1.8e-15
        rather than 0.0, so a bare `remaining_hours > 0` check walks back one day
        too far and allocates the residue there.
        """
        task = self.create_task(
            "Fractional Task",
            estimated_duration=20.1,
            deadline=datetime(2025, 10, 22, 18, 0, 0),
        )

        result = self.optimize_schedule(
            start_date=datetime(2025, 10, 20, 9, 0, 0),
            max_hours_per_day=6.7,
        )

        assert len(result.successful_tasks) == 1
        assert len(result.failed_tasks) == 0

        # Mon-Wed, working back from the Wednesday deadline
        self.assert_task_scheduled(
            task, expected_end=datetime(2025, 10, 22, 23, 59, 59)
        )

        updated_task = self.repository.get_by_id(task.id)
        assert updated_task is not None
        assert len(updated_task.daily_allocations) == 3
        assert date(2025, 10, 17) not in updated_task.daily_allocations

    def test_backward_exact_fit_against_start_date_is_schedulable(self):
        """A task that exactly fills the days from start_date to deadline must schedule.

        20.1h at 6.7h/day needs Mon-Wed and start_date is Monday. The float residue
        makes the loop reach back to the previous Friday, before start_date, so the
        task is wrongly reported unschedulable.
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
