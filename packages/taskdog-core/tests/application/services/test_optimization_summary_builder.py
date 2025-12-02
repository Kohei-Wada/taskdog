"""Tests for OptimizationSummaryBuilder."""

from datetime import date, datetime

import pytest

from taskdog_core.application.services.optimization_summary_builder import (
    OptimizationSummaryBuilder,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestOptimizationSummaryBuilder:
    """Test cases for OptimizationSummaryBuilder."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Set up test fixtures."""
        self.repository = repository
        self.builder = OptimizationSummaryBuilder(self.repository)

    def test_build_with_new_tasks(self):
        """Test build calculates correct counts for newly scheduled tasks."""
        # Create tasks
        task1 = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 14, 9, 0, 0),
            planned_end=datetime(2025, 10, 14, 17, 0, 0),
            estimated_duration=8.0,
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 15, 9, 0, 0),
            planned_end=datetime(2025, 10, 15, 17, 0, 0),
            estimated_duration=8.0,
        )
        self.repository.save(task1)
        self.repository.save(task2)

        modified_tasks = [task1, task2]
        task_states_before = {1: None, 2: None}  # Both were unscheduled
        daily_allocations = {date(2025, 10, 14): 8.0, date(2025, 10, 15): 8.0}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        assert summary.new_count == 2
        assert summary.rescheduled_count == 0
        assert summary.total_hours == 16.0
        assert summary.days_span == 2
        assert len(summary.overloaded_days) == 0

    def test_build_with_rescheduled_tasks(self):
        """Test build calculates correct counts for rescheduled tasks."""
        task = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 15, 9, 0, 0),
            planned_end=datetime(2025, 10, 15, 17, 0, 0),
            estimated_duration=8.0,
        )
        self.repository.save(task)

        modified_tasks = [task]
        task_states_before = {1: "2025-10-14 09:00:00"}  # Was previously scheduled
        daily_allocations = {date(2025, 10, 15): 8.0}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        assert summary.new_count == 0
        assert summary.rescheduled_count == 1

    def test_build_with_deadline_conflicts(self):
        """Test build detects deadline conflicts."""
        task = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 14, 9, 0, 0),
            planned_end=datetime(2025, 10, 16, 17, 0, 0),  # Ends after deadline
            deadline=datetime(2025, 10, 15, 18, 0, 0),
            estimated_duration=16.0,
        )
        self.repository.save(task)

        modified_tasks = [task]
        task_states_before = {1: None}
        daily_allocations = {date(2025, 10, 14): 8.0, date(2025, 10, 15): 8.0}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        assert summary.deadline_conflicts == 1

    def test_build_with_overloaded_days(self):
        """Test build detects overloaded days."""
        task = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 14, 9, 0, 0),
            planned_end=datetime(2025, 10, 14, 17, 0, 0),
            estimated_duration=10.0,
        )
        self.repository.save(task)

        modified_tasks = [task]
        task_states_before = {1: None}
        daily_allocations = {date(2025, 10, 14): 10.0}  # Exceeds max
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        assert len(summary.overloaded_days) == 1
        assert summary.overloaded_days[0] == ("2025-10-14", 10.0)

    def test_build_with_unscheduled_tasks(self):
        """Test build detects unscheduled tasks."""
        # Create scheduled task
        scheduled_task = Task(
            id=1,
            name="Scheduled",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime(2025, 10, 14, 9, 0, 0),
            planned_end=datetime(2025, 10, 14, 17, 0, 0),
            estimated_duration=8.0,
        )
        # Create unscheduled task
        unscheduled_task = Task(
            id=2,
            name="Unscheduled",
            priority=1,
            status=TaskStatus.PENDING,
            estimated_duration=8.0,
            # No planned_start/end
        )
        self.repository.save(scheduled_task)
        self.repository.save(unscheduled_task)

        modified_tasks = [scheduled_task]
        task_states_before = {1: None}
        daily_allocations = {date(2025, 10, 14): 8.0}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        assert len(summary.unscheduled_tasks) == 1
        assert summary.unscheduled_tasks[0].id == 2

    def test_build_ignores_completed_tasks(self):
        """Test build ignores completed tasks when checking unscheduled."""
        # Create completed task without schedule
        completed_task = Task(
            id=1,
            name="Completed",
            priority=1,
            status=TaskStatus.COMPLETED,
            estimated_duration=8.0,
            # No planned_start/end
        )
        self.repository.save(completed_task)

        modified_tasks = []
        task_states_before = {}
        daily_allocations = {}
        max_hours_per_day = 8.0

        summary = self.builder.build(
            modified_tasks, task_states_before, daily_allocations, max_hours_per_day
        )

        assert len(summary.unscheduled_tasks) == 0
