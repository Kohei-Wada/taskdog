"""Tests for OptimizeScheduleUseCase."""

import unittest
from datetime import date, datetime

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.application.use_cases.optimize_schedule import (
    OptimizeScheduleInput,
    OptimizeScheduleUseCase,
)
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.shared.config_manager import ConfigManager
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestOptimizeScheduleUseCase(InMemoryDatabaseTestCase):
    """Test cases for OptimizeScheduleUseCase."""

    def setUp(self):
        """Initialize use cases for each test."""
        super().setUp()
        self.create_use_case = CreateTaskUseCase(self.repository)
        config = ConfigManager.load()
        self.optimize_use_case = OptimizeScheduleUseCase(
            self.repository,
            config.time.default_start_hour,
            config.time.default_end_hour,
        )

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
        self.assertEqual(len(result.successful_tasks), 1)

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(result.successful_tasks[0].id)
        assert task is not None
        self.assertIsNotNone(task.planned_start)
        self.assertIsNotNone(task.planned_end)

        # Task should be scheduled on the start date
        self.assertEqual(task.planned_start, datetime(2025, 10, 15, 9, 0, 0))
        self.assertEqual(task.planned_end, datetime(2025, 10, 15, 18, 0, 0))

        # Verify daily_allocations
        self.assertIsNotNone(task.daily_allocations)
        self.assertEqual(task.daily_allocations[date(2025, 10, 15)], 4.0)

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
        self.assertEqual(len(result.successful_tasks), 3)
        for task_dto in result.successful_tasks:
            # Re-fetch task from repository to verify scheduling
            task = self.repository.get_by_id(task_dto.id)
            assert task is not None
            self.assertEqual(task.planned_start, datetime(2025, 10, 15, 9, 0, 0))
            self.assertEqual(task.planned_end, datetime(2025, 10, 15, 18, 0, 0))

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
        self.assertEqual(len(result.successful_tasks), 2)

        # Re-fetch tasks from repository to verify scheduling
        task1 = self.repository.get_by_id(result1.id)
        task2 = self.repository.get_by_id(result2.id)
        assert task1 is not None and task2 is not None

        # First task (priority 200, 5h) starts on start date and fits in one day
        self.assertEqual(task1.planned_start, datetime(2025, 10, 15, 9, 0, 0))
        self.assertEqual(task1.planned_end, datetime(2025, 10, 15, 18, 0, 0))
        # Verify daily_allocations for task1
        self.assertEqual(task1.daily_allocations[date(2025, 10, 15)], 5.0)

        # Second task (priority 100, 5h) starts on same day (1h left) and spans to next day
        self.assertEqual(task2.planned_start, datetime(2025, 10, 15, 9, 0, 0))
        self.assertEqual(task2.planned_end, datetime(2025, 10, 16, 18, 0, 0))
        # Verify daily_allocations for task2: 1h on first day, 4h on second day
        self.assertEqual(task2.daily_allocations[date(2025, 10, 15)], 1.0)
        self.assertEqual(task2.daily_allocations[date(2025, 10, 16)], 4.0)

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
        self.assertEqual(task.planned_start, datetime(2025, 10, 17, 9, 0, 0))
        # And end on Monday (skipping weekend)
        # Friday: 5h allocated
        self.assertEqual(task.planned_end, datetime(2025, 10, 17, 18, 0, 0))

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
        self.assertEqual(len(result.successful_tasks), 2)
        for task_dto in result.successful_tasks:
            # Re-fetch task from repository to verify scheduling
            task = self.repository.get_by_id(task_dto.id)
            assert task is not None
            self.assertEqual(task.planned_start, datetime(2025, 10, 15, 9, 0, 0))

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
        self.assertEqual(len(result.successful_tasks), 2)
        # All tasks fit in one day
        for task_dto in result.successful_tasks:
            # Re-fetch task from repository to verify scheduling
            task = self.repository.get_by_id(task_dto.id)
            assert task is not None
            self.assertEqual(task.planned_start, datetime(2025, 10, 15, 9, 0, 0))

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
        self.assertEqual(len(result.successful_tasks), 0)

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
        self.assertEqual(len(result.successful_tasks), 0)

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
        self.assertEqual(len(result.successful_tasks), 0)

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
        self.assertEqual(len(result.successful_tasks), 0)

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
        self.assertEqual(len(result.successful_tasks), 1)

        # Re-fetch task from repository to verify scheduling
        task = self.repository.get_by_id(task_result.id)
        assert task is not None
        self.assertNotEqual(task.planned_start, old_start)
        self.assertEqual(task.planned_start, datetime(2025, 10, 15, 9, 0, 0))


if __name__ == "__main__":
    unittest.main()
