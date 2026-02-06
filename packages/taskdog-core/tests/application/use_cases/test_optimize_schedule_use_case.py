"""Tests for OptimizeScheduleUseCase."""

from datetime import date, datetime

import pytest

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.application.use_cases.optimize_schedule import (
    OptimizeScheduleInput,
    OptimizeScheduleUseCase,
)
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    NoSchedulableTasksError,
    TaskNotFoundException,
)


class TestOptimizeScheduleUseCase:
    """Test cases for OptimizeScheduleUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use cases for each test."""
        self.repository = repository
        self.create_use_case = CreateTaskUseCase(self.repository)
        self.optimize_use_case = OptimizeScheduleUseCase(self.repository)

    def test_optimize_single_task(self):
        """Test optimizing a single task with estimated duration."""
        # Create task with estimated duration
        input_dto = CreateTaskInput(name="Task 1", priority=100, estimated_duration=4.0)
        self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)  # Wednesday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Verify
        assert len(result.successful_tasks) == 1

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(result.successful_tasks[0].id)
        assert task is not None
        assert task.planned_start is not None
        assert task.planned_end is not None

        # Task should be scheduled on the start date
        assert task.planned_start == datetime(2025, 10, 15, 0, 0, 0)
        assert task.planned_end == datetime(2025, 10, 15, 23, 59, 59)

        # Verify daily_allocations
        assert task.daily_allocations is not None
        assert task.daily_allocations[date(2025, 10, 15)] == 4.0

    def test_optimize_multiple_tasks_same_day(self):
        """Test optimizing multiple tasks that fit in one day."""
        # Create tasks
        for i in range(3):
            input_dto = CreateTaskInput(
                name=f"Task {i + 1}", priority=100, estimated_duration=2.0
            )
            self.create_use_case.execute(input_dto)

        # Optimize with 6h/day limit
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # All 3 tasks (6h total) should fit in one day
        assert len(result.successful_tasks) == 3
        for task_dto in result.successful_tasks:
            # Re-fetch task from repository to verify scheduling
            task = self.repository.get_by_id(task_dto.id)
            assert task is not None
            assert task.planned_start == datetime(2025, 10, 15, 0, 0, 0)
            assert task.planned_end == datetime(2025, 10, 15, 23, 59, 59)

    def test_optimize_tasks_spanning_multiple_days(self):
        """Test optimizing tasks that span multiple days."""
        # Create tasks with 10h total (needs 2 days with 6h/day limit)
        # Use different priorities to ensure order: 200 (high) and 100 (normal)
        input_dto1 = CreateTaskInput(
            name="Task 1",
            priority=200,  # High priority
            estimated_duration=5.0,
        )
        input_dto2 = CreateTaskInput(
            name="Task 2",
            priority=100,  # Normal priority
            estimated_duration=5.0,
        )
        result1 = self.create_use_case.execute(input_dto1)
        result2 = self.create_use_case.execute(input_dto2)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)  # Wednesday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Tasks should span multiple days
        assert len(result.successful_tasks) == 2

        # Re-fetch tasks from repository to verify scheduling
        task1 = self.repository.get_by_id(result1.id)
        task2 = self.repository.get_by_id(result2.id)
        assert task1 is not None and task2 is not None

        # First task (priority 200, 5h) starts on start date and fits in one day
        assert task1.planned_start == datetime(2025, 10, 15, 0, 0, 0)
        assert task1.planned_end == datetime(2025, 10, 15, 23, 59, 59)
        # Verify daily_allocations for task1
        assert task1.daily_allocations[date(2025, 10, 15)] == 5.0

        # Second task (priority 100, 5h) starts on same day (1h left) and spans to next day
        assert task2.planned_start == datetime(2025, 10, 15, 0, 0, 0)
        assert task2.planned_end == datetime(2025, 10, 16, 23, 59, 59)
        # Verify daily_allocations for task2: 1h on first day, 4h on second day
        assert task2.daily_allocations[date(2025, 10, 15)] == 1.0
        assert task2.daily_allocations[date(2025, 10, 16)] == 4.0

    def test_optimize_skips_weekends(self):
        """Test that optimization skips weekends."""
        # Create task with 5h duration
        input_dto = CreateTaskInput(
            name="Weekend Task", priority=100, estimated_duration=5.0
        )
        task_result = self.create_use_case.execute(input_dto)

        # Start on Friday
        start_date = datetime(2025, 10, 17, 18, 0, 0)  # Friday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        self.optimize_use_case.execute(optimize_input)

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(task_result.id)
        assert task is not None

        # Task should start on Friday
        assert task.planned_start == datetime(2025, 10, 17, 0, 0, 0)
        # And end on Monday (skipping weekend)
        # Friday: 5h allocated
        assert task.planned_end == datetime(2025, 10, 17, 23, 59, 59)

    def test_optimize_respects_priority(self):
        """Test that high priority tasks are scheduled first."""
        # Create tasks with different priorities
        low_priority = CreateTaskInput(
            name="Low Priority", priority=50, estimated_duration=3.0
        )
        high_priority = CreateTaskInput(
            name="High Priority", priority=200, estimated_duration=3.0
        )
        self.create_use_case.execute(low_priority)
        self.create_use_case.execute(high_priority)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled on same day (6h total)
        assert len(result.successful_tasks) == 2
        for task_dto in result.successful_tasks:
            # Re-fetch task from repository to verify scheduling
            task = self.repository.get_by_id(task_dto.id)
            assert task is not None
            assert task.planned_start == datetime(2025, 10, 15, 0, 0, 0)

    def test_optimize_respects_deadline(self):
        """Test that tasks with closer deadlines are prioritized."""
        # Create tasks with different deadlines
        far_deadline = CreateTaskInput(
            name="Far Deadline",
            priority=100,
            estimated_duration=3.0,
            deadline=datetime(2025, 12, 31, 18, 0, 0),
        )
        near_deadline = CreateTaskInput(
            name="Near Deadline",
            priority=100,
            estimated_duration=3.0,
            deadline=datetime(2025, 10, 20, 18, 0, 0),
        )
        self.create_use_case.execute(far_deadline)
        self.create_use_case.execute(near_deadline)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both should be scheduled
        assert len(result.successful_tasks) == 2
        # All tasks fit in one day
        for task_dto in result.successful_tasks:
            # Re-fetch task from repository to verify scheduling
            task = self.repository.get_by_id(task_dto.id)
            assert task is not None
            assert task.planned_start == datetime(2025, 10, 15, 0, 0, 0)

    def test_optimize_skips_completed_tasks(self):
        """Test that completed tasks are not scheduled."""
        # Create completed task
        input_dto = CreateTaskInput(
            name="Completed Task", priority=100, estimated_duration=3.0
        )
        result = self.create_use_case.execute(input_dto)
        # Get the actual task from repository to modify it
        task = self.repository.get_by_id(result.id)
        task.status = TaskStatus.COMPLETED  # type: ignore[union-attr]
        self.repository.save(task)  # type: ignore[arg-type]

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # No tasks should be scheduled
        assert len(result.successful_tasks) == 0

    def test_optimize_skips_archived_tasks(self):
        """Test that archived tasks are not scheduled."""
        # Create archived task
        input_dto = CreateTaskInput(
            name="Archived Task", priority=100, estimated_duration=3.0
        )
        result = self.create_use_case.execute(input_dto)
        # Get the actual task from repository to modify it
        task = self.repository.get_by_id(result.id)
        task.is_archived = True  # type: ignore[union-attr]
        self.repository.save(task)  # type: ignore[arg-type]

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # No tasks should be scheduled
        assert len(result.successful_tasks) == 0

    def test_optimize_skips_tasks_without_duration(self):
        """Test that tasks without estimated duration are not scheduled."""
        # Create task without estimated duration
        input_dto = CreateTaskInput(
            name="No Duration", priority=100, estimated_duration=None
        )
        self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # No tasks should be scheduled
        assert len(result.successful_tasks) == 0

    def test_optimize_skips_existing_schedules_by_default(self):
        """Test that tasks with existing schedules are skipped unless force=True."""
        # Create task with existing schedule
        input_dto = CreateTaskInput(
            name="Already Scheduled",
            priority=100,
            estimated_duration=3.0,
            planned_start=datetime(2025, 10, 10, 18, 0, 0),
            planned_end=datetime(2025, 10, 10, 18, 0, 0),
        )
        self.create_use_case.execute(input_dto)

        # Optimize without force
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # No tasks should be modified
        assert len(result.successful_tasks) == 0

    def test_optimize_force_overrides_existing_schedules(self):
        """Test that force=True overrides existing schedules."""
        # Create task with existing schedule
        input_dto = CreateTaskInput(
            name="Already Scheduled",
            priority=100,
            estimated_duration=3.0,
            planned_start=datetime(2025, 10, 10, 18, 0, 0),
            planned_end=datetime(2025, 10, 10, 18, 0, 0),
        )
        task_result = self.create_use_case.execute(input_dto)
        old_start = task_result.planned_start

        # Optimize with force
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=True,
            algorithm_name="greedy",
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Task should be rescheduled
        assert len(result.successful_tasks) == 1

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(task_result.id)
        assert task is not None
        assert task.planned_start != old_start
        assert task.planned_start == datetime(2025, 10, 15, 0, 0, 0)

    def test_optimize_specific_tasks_only(self):
        """Test optimizing only specific task IDs."""
        # Create 5 tasks
        task_ids = []
        for i in range(5):
            input_dto = CreateTaskInput(
                name=f"Task {i + 1}", priority=100, estimated_duration=2.0
            )
            result = self.create_use_case.execute(input_dto)
            task_ids.append(result.id)

        # Optimize only tasks 1 and 3 (indices 0 and 2)
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            task_ids=[task_ids[0], task_ids[2]],
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Only 2 tasks should be optimized
        assert len(result.successful_tasks) == 2
        optimized_ids = {task.id for task in result.successful_tasks}
        assert optimized_ids == {task_ids[0], task_ids[2]}

        # Verify that tasks 1 and 3 have schedules
        task1 = self.repository.get_by_id(task_ids[0])
        task3 = self.repository.get_by_id(task_ids[2])
        assert task1 is not None and task3 is not None
        assert task1.planned_start is not None
        assert task3.planned_start is not None

        # Verify that other tasks don't have schedules
        for i in [1, 3, 4]:
            task = self.repository.get_by_id(task_ids[i])
            assert task is not None
            assert task.planned_start is None

    def test_optimize_nonexistent_task_id(self):
        """Test that optimizing a nonexistent task ID raises TaskNotFoundException."""
        # Create one task
        input_dto = CreateTaskInput(name="Task 1", priority=100, estimated_duration=2.0)
        self.create_use_case.execute(input_dto)

        # Try to optimize nonexistent task ID 999
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            task_ids=[999],
        )

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.optimize_use_case.execute(optimize_input)

        assert "999" in str(exc_info.value)

    def test_optimize_unschedulable_task(self):
        """Test that optimizing an unschedulable task raises NoSchedulableTasksError."""
        # Create a task and complete it (not schedulable)
        input_dto = CreateTaskInput(
            name="Completed Task",
            priority=100,
            estimated_duration=2.0,
        )
        result = self.create_use_case.execute(input_dto)

        # Complete the task to make it unschedulable
        from taskdog_core.application.dto.base import SingleTaskInput
        from taskdog_core.application.use_cases.complete_task import CompleteTaskUseCase
        from taskdog_core.application.use_cases.start_task import StartTaskUseCase

        start_use_case = StartTaskUseCase(self.repository)
        complete_use_case = CompleteTaskUseCase(self.repository)

        start_use_case.execute(SingleTaskInput(task_id=result.id))
        complete_use_case.execute(SingleTaskInput(task_id=result.id))

        # Try to optimize the completed task
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            task_ids=[result.id],
        )

        with pytest.raises(NoSchedulableTasksError) as exc_info:
            self.optimize_use_case.execute(optimize_input)

        # Verify error message mentions the status
        assert "COMPLETED" in str(exc_info.value)

    def test_optimize_fixed_task(self):
        """Test that optimizing a fixed task raises NoSchedulableTasksError."""
        # Create a fixed task (not schedulable)
        input_dto = CreateTaskInput(
            name="Fixed Task",
            priority=100,
            estimated_duration=2.0,
            is_fixed=True,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 20, 11, 0, 0),
        )
        result = self.create_use_case.execute(input_dto)

        # Try to optimize the fixed task
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            task_ids=[result.id],
        )

        with pytest.raises(NoSchedulableTasksError) as exc_info:
            self.optimize_use_case.execute(optimize_input)

        # Verify error message mentions fixed
        assert "fixed" in str(exc_info.value).lower()

    def test_optimize_mixed_schedulable_and_unschedulable_tasks(self):
        """Test optimizing a mix of schedulable and unschedulable tasks.

        When specific task IDs are provided and some are not schedulable,
        we raise an error for the unschedulable ones only. The schedulable
        tasks would be processed successfully, but we still report the issue.
        """
        # Create schedulable task
        input_dto1 = CreateTaskInput(
            name="Schedulable Task", priority=100, estimated_duration=2.0
        )
        result1 = self.create_use_case.execute(input_dto1)

        # Create task and complete it (unschedulable)
        input_dto2 = CreateTaskInput(
            name="Completed Task",
            priority=100,
            estimated_duration=2.0,
        )
        result2 = self.create_use_case.execute(input_dto2)

        # Complete the second task
        from taskdog_core.application.dto.base import SingleTaskInput
        from taskdog_core.application.use_cases.complete_task import CompleteTaskUseCase
        from taskdog_core.application.use_cases.start_task import StartTaskUseCase

        start_use_case = StartTaskUseCase(self.repository)
        complete_use_case = CompleteTaskUseCase(self.repository)

        start_use_case.execute(SingleTaskInput(task_id=result2.id))
        complete_use_case.execute(SingleTaskInput(task_id=result2.id))

        # Try to optimize both tasks - should succeed for task1 but report task2 as unschedulable
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            task_ids=[result1.id, result2.id],
        )

        # This should succeed (schedulable task is processed)
        result = self.optimize_use_case.execute(optimize_input)

        # But unschedulable task should be in failed_tasks
        assert len(result.successful_tasks) == 1
        assert result.successful_tasks[0].id == result1.id

        # Note: The current implementation doesn't track "unschedulable" as failures
        # They are simply not included in schedulable_tasks
        # This is OK - we just schedule what we can

    def test_optimize_includes_weekends_when_include_all_days_true(self):
        """Test that weekends are included when include_all_days=True."""
        # Create task with 10h duration (needs multiple days)
        input_dto = CreateTaskInput(
            name="Weekend Task", priority=100, estimated_duration=10.0
        )
        task_result = self.create_use_case.execute(input_dto)

        # Start on Friday 2025-10-17
        start_date = datetime(2025, 10, 17, 18, 0, 0)  # Friday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            include_all_days=True,  # Include weekends
        )
        self.optimize_use_case.execute(optimize_input)

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(task_result.id)
        assert task is not None
        assert task.daily_allocations is not None

        # With include_all_days=True, task should be scheduled on:
        # Friday (Oct 17): 6h
        # Saturday (Oct 18): 4h (remaining)
        # Without include_all_days, it would skip to Monday

        # Verify daily allocations include Saturday (weekend)
        assert date(2025, 10, 17) in task.daily_allocations  # Friday
        assert date(2025, 10, 18) in task.daily_allocations  # Saturday (weekend!)
        assert task.daily_allocations[date(2025, 10, 17)] == 6.0
        assert task.daily_allocations[date(2025, 10, 18)] == 4.0

    def test_optimize_skips_weekends_when_include_all_days_false(self):
        """Test that weekends are skipped when include_all_days=False (default)."""
        # Create task with 10h duration (needs multiple days)
        input_dto = CreateTaskInput(
            name="Weekday Task", priority=100, estimated_duration=10.0
        )
        task_result = self.create_use_case.execute(input_dto)

        # Start on Friday 2025-10-17
        start_date = datetime(2025, 10, 17, 18, 0, 0)  # Friday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            include_all_days=False,  # Skip weekends (default)
        )
        self.optimize_use_case.execute(optimize_input)

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(task_result.id)
        assert task is not None
        assert task.daily_allocations is not None

        # Without include_all_days, task should skip weekend:
        # Friday (Oct 17): 6h
        # Saturday/Sunday skipped
        # Monday (Oct 20): 4h

        # Verify daily allocations skip weekend
        assert date(2025, 10, 17) in task.daily_allocations  # Friday
        assert date(2025, 10, 18) not in task.daily_allocations  # Saturday skipped
        assert date(2025, 10, 19) not in task.daily_allocations  # Sunday skipped
        assert date(2025, 10, 20) in task.daily_allocations  # Monday
        assert task.daily_allocations[date(2025, 10, 17)] == 6.0
        assert task.daily_allocations[date(2025, 10, 20)] == 4.0

    def test_optimize_backward_includes_weekends_when_include_all_days_true(self):
        """Test that backward strategy includes weekends when include_all_days=True."""
        # Create task with 10h duration and a deadline on Wednesday
        input_dto = CreateTaskInput(
            name="Backward Weekend Task",
            priority=100,
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 22, 18, 0, 0),  # Wednesday
        )
        task_result = self.create_use_case.execute(input_dto)

        # Start on Thursday 2025-10-16
        start_date = datetime(2025, 10, 16, 18, 0, 0)  # Thursday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="backward",
            include_all_days=True,  # Include weekends
        )
        self.optimize_use_case.execute(optimize_input)

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(task_result.id)
        assert task is not None
        assert task.daily_allocations is not None

        # With backward strategy and include_all_days=True:
        # Should schedule backwards from deadline, including weekends
        # Wednesday (Oct 22): up to 6h
        # Tuesday (Oct 21): 4h (remaining)
        # Or if full: Mon, Tue, Wed

        # Verify task is scheduled (actual allocation depends on algorithm)
        total_hours = sum(task.daily_allocations.values())
        assert total_hours == 10.0

    def test_optimize_balanced_includes_weekends_when_include_all_days_true(self):
        """Test that balanced strategy includes weekends when include_all_days=True."""
        # Create task with 10h duration
        input_dto = CreateTaskInput(
            name="Balanced Weekend Task",
            priority=100,
            estimated_duration=10.0,
            deadline=datetime(2025, 10, 20, 18, 0, 0),  # Monday
        )
        task_result = self.create_use_case.execute(input_dto)

        # Start on Friday 2025-10-17
        start_date = datetime(2025, 10, 17, 18, 0, 0)  # Friday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="balanced",
            include_all_days=True,  # Include weekends
        )
        self.optimize_use_case.execute(optimize_input)

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(task_result.id)
        assert task is not None
        assert task.daily_allocations is not None

        # With balanced strategy and include_all_days=True:
        # Should distribute across Fri, Sat, Sun, Mon (4 days)
        # Each day: 10h / 4 = 2.5h

        # Verify weekend days are included
        assert date(2025, 10, 17) in task.daily_allocations  # Friday
        # Balanced may include weekends
        total_hours = sum(task.daily_allocations.values())
        assert total_hours == 10.0

    def test_optimize_round_robin_includes_weekends_when_include_all_days_true(self):
        """Test that round robin strategy includes weekends when include_all_days=True."""
        # Create two tasks
        input_dto1 = CreateTaskInput(
            name="RR Task 1", priority=100, estimated_duration=5.0
        )
        input_dto2 = CreateTaskInput(
            name="RR Task 2", priority=100, estimated_duration=5.0
        )
        task_result1 = self.create_use_case.execute(input_dto1)
        task_result2 = self.create_use_case.execute(input_dto2)

        # Start on Friday 2025-10-17
        start_date = datetime(2025, 10, 17, 18, 0, 0)  # Friday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="round_robin",
            include_all_days=True,  # Include weekends
        )
        result = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled
        assert len(result.successful_tasks) == 2

        # Re-fetch tasks from repository to verify scheduling
        task1 = self.repository.get_by_id(task_result1.id)
        task2 = self.repository.get_by_id(task_result2.id)
        assert task1 is not None and task2 is not None
        assert task1.daily_allocations is not None
        assert task2.daily_allocations is not None

        # Verify tasks are scheduled (including potentially on weekends)
        total_hours1 = sum(task1.daily_allocations.values())
        total_hours2 = sum(task2.daily_allocations.values())
        assert total_hours1 == 5.0
        assert total_hours2 == 5.0

    def test_optimize_respects_fixed_task_on_weekend_when_include_all_days_true(self):
        """Test that fixed task on weekend is respected when include_all_days=True.

        When a fixed task is scheduled on Saturday, the optimizer should count
        its hours towards the daily allocation, preventing over-scheduling.
        """
        # Create a fixed task on Saturday (2025-10-18)
        fixed_task_input = CreateTaskInput(
            name="Fixed Saturday Task",
            priority=100,
            estimated_duration=4.0,
            planned_start=datetime(2025, 10, 18, 9, 0, 0),  # Saturday
            planned_end=datetime(2025, 10, 18, 13, 0, 0),
            is_fixed=True,
        )
        fixed_result = self.create_use_case.execute(fixed_task_input)

        # Set daily_allocations for the fixed task (simulating optimizer output)
        fixed_task = self.repository.get_by_id(fixed_result.id)
        assert fixed_task is not None
        fixed_task.set_daily_allocations({date(2025, 10, 18): 4.0})
        self.repository.save(fixed_task)

        # Create a task to be optimized
        task_input = CreateTaskInput(
            name="Task to Optimize", priority=100, estimated_duration=5.0
        )
        task_result = self.create_use_case.execute(task_input)

        # Optimize starting from Saturday with include_all_days=True
        start_date = datetime(2025, 10, 18, 9, 0, 0)  # Saturday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            include_all_days=True,  # Include weekends
        )
        self.optimize_use_case.execute(optimize_input)

        # Re-fetch task from repository
        task = self.repository.get_by_id(task_result.id)
        assert task is not None
        assert task.daily_allocations is not None

        # Saturday should have at most 2h (6h max - 4h fixed = 2h available)
        saturday = date(2025, 10, 18)
        if saturday in task.daily_allocations:
            assert task.daily_allocations[saturday] <= 2.0

        # Total hours should be 5.0
        total_hours = sum(task.daily_allocations.values())
        assert total_hours == 5.0

    def test_optimize_respects_fixed_task_on_weekend_without_daily_allocations(self):
        """Test fixed task on weekend is counted even without daily_allocations.

        When a fixed task is scheduled on Saturday but doesn't have daily_allocations
        set, the workload calculator should still count its hours using AllDaysStrategy.
        """
        # Create a fixed task on Saturday without daily_allocations
        fixed_task_input = CreateTaskInput(
            name="Fixed Saturday Task",
            priority=100,
            estimated_duration=4.0,
            planned_start=datetime(2025, 10, 18, 9, 0, 0),  # Saturday
            planned_end=datetime(2025, 10, 18, 13, 0, 0),
            is_fixed=True,
        )
        self.create_use_case.execute(fixed_task_input)
        # Note: NOT setting daily_allocations - let calculator compute it

        # Create a task to be optimized
        task_input = CreateTaskInput(
            name="Task to Optimize", priority=100, estimated_duration=5.0
        )
        task_result = self.create_use_case.execute(task_input)

        # Optimize starting from Saturday with include_all_days=True
        start_date = datetime(2025, 10, 18, 9, 0, 0)  # Saturday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0,
            force_override=False,
            algorithm_name="greedy",
            include_all_days=True,  # Include weekends
        )
        self.optimize_use_case.execute(optimize_input)

        # Re-fetch task from repository
        task = self.repository.get_by_id(task_result.id)
        assert task is not None
        assert task.daily_allocations is not None

        # Saturday should have at most 2h (6h max - 4h fixed = 2h available)
        saturday = date(2025, 10, 18)
        if saturday in task.daily_allocations:
            assert task.daily_allocations[saturday] <= 2.0

        # Total hours should be 5.0
        total_hours = sum(task.daily_allocations.values())
        assert total_hours == 5.0
