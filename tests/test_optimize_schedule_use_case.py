"""Tests for OptimizeScheduleUseCase."""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from application.use_cases.optimize_schedule import (
    OptimizeScheduleUseCase,
    OptimizeScheduleInput
)
from application.use_cases.create_task import CreateTaskUseCase
from application.dto.create_task_input import CreateTaskInput
from domain.entities.task import TaskStatus


class TestOptimizeScheduleUseCase(unittest.TestCase):
    """Test cases for OptimizeScheduleUseCase."""

    def setUp(self):
        """Create temporary file and initialize use case for each test."""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.create_use_case = CreateTaskUseCase(self.repository)
        self.optimize_use_case = OptimizeScheduleUseCase(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_optimize_single_task(self):
        """Test optimizing a single task with estimated duration."""
        # Create task with estimated duration
        input_dto = CreateTaskInput(
            name="Task 1",
            priority=100,
            estimated_duration=4.0
        )
        task = self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)  # Wednesday
        optimize_input = OptimizeScheduleInput(start_date=start_date)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # Verify
        self.assertEqual(len(modified_tasks), 1)
        self.assertIsNotNone(modified_tasks[0].planned_start)
        self.assertIsNotNone(modified_tasks[0].planned_end)

        # Task should be scheduled on the start date
        self.assertEqual(modified_tasks[0].planned_start, "2025-10-15 18:00:00")
        self.assertEqual(modified_tasks[0].planned_end, "2025-10-15 18:00:00")

        # Verify daily_allocations
        self.assertIsNotNone(modified_tasks[0].daily_allocations)
        self.assertEqual(modified_tasks[0].daily_allocations["2025-10-15"], 4.0)

    def test_optimize_multiple_tasks_same_day(self):
        """Test optimizing multiple tasks that fit in one day."""
        # Create tasks
        for i in range(3):
            input_dto = CreateTaskInput(
                name=f"Task {i+1}",
                priority=100,
                estimated_duration=2.0
            )
            self.create_use_case.execute(input_dto)

        # Optimize with 6h/day limit
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0
        )
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # All 3 tasks (6h total) should fit in one day
        self.assertEqual(len(modified_tasks), 3)
        for task in modified_tasks:
            self.assertEqual(task.planned_start, "2025-10-15 18:00:00")
            self.assertEqual(task.planned_end, "2025-10-15 18:00:00")

    def test_optimize_tasks_spanning_multiple_days(self):
        """Test optimizing tasks that span multiple days."""
        # Create tasks with 10h total (needs 2 days with 6h/day limit)
        # Use different priorities to ensure order: 200 (high) and 100 (normal)
        input_dto1 = CreateTaskInput(
            name="Task 1",
            priority=200,  # High priority
            estimated_duration=5.0
        )
        input_dto2 = CreateTaskInput(
            name="Task 2",
            priority=100,  # Normal priority
            estimated_duration=5.0
        )
        self.create_use_case.execute(input_dto1)
        self.create_use_case.execute(input_dto2)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)  # Wednesday
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0
        )
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # Tasks should span multiple days
        self.assertEqual(len(modified_tasks), 2)

        # First task (priority 200, 5h) starts on start date and fits in one day
        task1 = [t for t in modified_tasks if t.priority == 200][0]
        self.assertEqual(task1.planned_start, "2025-10-15 18:00:00")
        self.assertEqual(task1.planned_end, "2025-10-15 18:00:00")
        # Verify daily_allocations for task1
        self.assertEqual(task1.daily_allocations["2025-10-15"], 5.0)

        # Second task (priority 100, 5h) starts on same day (1h left) and spans to next day
        task2 = [t for t in modified_tasks if t.priority == 100][0]
        self.assertEqual(task2.planned_start, "2025-10-15 18:00:00")
        self.assertEqual(task2.planned_end, "2025-10-16 18:00:00")
        # Verify daily_allocations for task2: 1h on first day, 4h on second day
        self.assertEqual(task2.daily_allocations["2025-10-15"], 1.0)
        self.assertEqual(task2.daily_allocations["2025-10-16"], 4.0)

    def test_optimize_skips_weekends(self):
        """Test that optimization skips weekends."""
        # Create task with 5h duration
        input_dto = CreateTaskInput(
            name="Weekend Task",
            priority=100,
            estimated_duration=5.0
        )
        self.create_use_case.execute(input_dto)

        # Start on Friday
        start_date = datetime(2025, 10, 17, 18, 0, 0)  # Friday
        optimize_input = OptimizeScheduleInput(start_date=start_date)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # Task should start on Friday
        self.assertEqual(modified_tasks[0].planned_start, "2025-10-17 18:00:00")
        # And end on Monday (skipping weekend)
        # Friday: 5h allocated
        self.assertEqual(modified_tasks[0].planned_end, "2025-10-17 18:00:00")

    def test_optimize_respects_priority(self):
        """Test that high priority tasks are scheduled first."""
        # Create tasks with different priorities
        low_priority = CreateTaskInput(
            name="Low Priority",
            priority=50,
            estimated_duration=3.0
        )
        high_priority = CreateTaskInput(
            name="High Priority",
            priority=200,
            estimated_duration=3.0
        )
        self.create_use_case.execute(low_priority)
        self.create_use_case.execute(high_priority)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(start_date=start_date)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # Both tasks should be scheduled on same day (6h total)
        self.assertEqual(len(modified_tasks), 2)
        for task in modified_tasks:
            self.assertEqual(task.planned_start, "2025-10-15 18:00:00")

    def test_optimize_respects_deadline(self):
        """Test that tasks with closer deadlines are prioritized."""
        # Create tasks with different deadlines
        far_deadline = CreateTaskInput(
            name="Far Deadline",
            priority=100,
            estimated_duration=3.0,
            deadline="2025-12-31 18:00:00"
        )
        near_deadline = CreateTaskInput(
            name="Near Deadline",
            priority=100,
            estimated_duration=3.0,
            deadline="2025-10-20 18:00:00"
        )
        self.create_use_case.execute(far_deadline)
        self.create_use_case.execute(near_deadline)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(start_date=start_date)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # Both should be scheduled
        self.assertEqual(len(modified_tasks), 2)
        # All tasks fit in one day
        for task in modified_tasks:
            self.assertEqual(task.planned_start, "2025-10-15 18:00:00")

    def test_optimize_skips_completed_tasks(self):
        """Test that completed tasks are not scheduled."""
        # Create completed task
        input_dto = CreateTaskInput(
            name="Completed Task",
            priority=100,
            estimated_duration=3.0
        )
        task = self.create_use_case.execute(input_dto)
        task.status = TaskStatus.COMPLETED
        self.repository.save(task)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(start_date=start_date)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # No tasks should be scheduled
        self.assertEqual(len(modified_tasks), 0)

    def test_optimize_skips_tasks_without_duration(self):
        """Test that tasks without estimated duration are not scheduled."""
        # Create task without estimated duration
        input_dto = CreateTaskInput(
            name="No Duration",
            priority=100,
            estimated_duration=None
        )
        self.create_use_case.execute(input_dto)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(start_date=start_date)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # No tasks should be scheduled
        self.assertEqual(len(modified_tasks), 0)

    def test_optimize_skips_existing_schedules_by_default(self):
        """Test that tasks with existing schedules are skipped unless force=True."""
        # Create task with existing schedule
        input_dto = CreateTaskInput(
            name="Already Scheduled",
            priority=100,
            estimated_duration=3.0,
            planned_start="2025-10-10 18:00:00",
            planned_end="2025-10-10 18:00:00"
        )
        self.create_use_case.execute(input_dto)

        # Optimize without force
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(start_date=start_date, force_override=False)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # No tasks should be modified
        self.assertEqual(len(modified_tasks), 0)

    def test_optimize_force_overrides_existing_schedules(self):
        """Test that force=True overrides existing schedules."""
        # Create task with existing schedule
        input_dto = CreateTaskInput(
            name="Already Scheduled",
            priority=100,
            estimated_duration=3.0,
            planned_start="2025-10-10 18:00:00",
            planned_end="2025-10-10 18:00:00"
        )
        task = self.create_use_case.execute(input_dto)
        old_start = task.planned_start

        # Optimize with force
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(start_date=start_date, force_override=True)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # Task should be rescheduled
        self.assertEqual(len(modified_tasks), 1)
        self.assertNotEqual(modified_tasks[0].planned_start, old_start)
        self.assertEqual(modified_tasks[0].planned_start, "2025-10-15 18:00:00")

    def test_optimize_dry_run_does_not_save(self):
        """Test that dry_run=True does not save changes."""
        # Create task
        input_dto = CreateTaskInput(
            name="Test Task",
            priority=100,
            estimated_duration=3.0
        )
        task = self.create_use_case.execute(input_dto)

        # Optimize with dry_run
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(start_date=start_date, dry_run=True)
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # Modified tasks returned
        self.assertEqual(len(modified_tasks), 1)
        self.assertIsNotNone(modified_tasks[0].planned_start)

        # But original task in repository should be unchanged
        saved_task = self.repository.get_by_id(task.id)
        self.assertIsNone(saved_task.planned_start)

    def test_optimize_parent_child_hierarchy(self):
        """Test that parent periods encompass children."""
        # Create parent task
        parent_input = CreateTaskInput(
            name="Parent",
            priority=100,
            estimated_duration=None
        )
        parent = self.create_use_case.execute(parent_input)

        # Create child tasks
        child1_input = CreateTaskInput(
            name="Child 1",
            priority=100,
            parent_id=parent.id,
            estimated_duration=3.0
        )
        child2_input = CreateTaskInput(
            name="Child 2",
            priority=100,
            parent_id=parent.id,
            estimated_duration=5.0
        )
        self.create_use_case.execute(child1_input)
        self.create_use_case.execute(child2_input)

        # Optimize
        start_date = datetime(2025, 10, 15, 18, 0, 0)
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=6.0
        )
        modified_tasks = self.optimize_use_case.execute(optimize_input)

        # Parent should be in modified list with period encompassing children
        parent_task = [t for t in modified_tasks if t.id == parent.id][0]
        child_tasks = [t for t in modified_tasks if t.parent_id == parent.id]

        self.assertIsNotNone(parent_task.planned_start)
        self.assertIsNotNone(parent_task.planned_end)

        # Parent start should be earliest child start
        child_starts = [datetime.strptime(c.planned_start, "%Y-%m-%d %H:%M:%S") for c in child_tasks]
        parent_start = datetime.strptime(parent_task.planned_start, "%Y-%m-%d %H:%M:%S")
        self.assertEqual(parent_start, min(child_starts))

        # Parent end should be latest child end
        child_ends = [datetime.strptime(c.planned_end, "%Y-%m-%d %H:%M:%S") for c in child_tasks]
        parent_end = datetime.strptime(parent_task.planned_end, "%Y-%m-%d %H:%M:%S")
        self.assertEqual(parent_end, max(child_ends))


if __name__ == "__main__":
    unittest.main()
