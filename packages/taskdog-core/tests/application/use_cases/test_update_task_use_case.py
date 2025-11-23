"""Tests for UpdateTaskUseCase."""

import unittest
from datetime import datetime, timedelta

from taskdog_core.application.dto.update_task_input import UpdateTaskInput
from taskdog_core.application.use_cases.update_task import UpdateTaskUseCase
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestUpdateTaskUseCase(InMemoryDatabaseTestCase):
    """Test cases for UpdateTaskUseCase"""

    def setUp(self):
        """Initialize use case for each test"""
        super().setUp()
        self.use_case = UpdateTaskUseCase(self.repository)

    def test_execute_update_single_field(self):
        """Test updating a single field - parameterized test"""
        future_date_7 = datetime.now() + timedelta(days=7)
        future_date_14 = datetime.now() + timedelta(days=14)
        future_date_30 = datetime.now() + timedelta(days=30)

        test_cases = [
            ("priority", {"priority": 3}, "priority", 3, "Update priority"),
            (
                "planned_start",
                {"planned_start": future_date_7},
                "planned_start",
                future_date_7,
                "Update planned start",
            ),
            (
                "planned_end",
                {"planned_end": future_date_14},
                "planned_end",
                future_date_14,
                "Update planned end",
            ),
            (
                "deadline",
                {"deadline": future_date_30},
                "deadline",
                future_date_30,
                "Update deadline",
            ),
            (
                "estimated_duration",
                {"estimated_duration": 4.5},
                "estimated_duration",
                4.5,
                "Update estimated duration",
            ),
        ]

        for (
            field_name,
            update_kwargs,
            expected_field,
            expected_value,
            description,
        ) in test_cases:
            with self.subTest(description=description):
                task = Task(name="Test Task", priority=1)
                task.id = self.repository.generate_next_id()
                self.repository.save(task)

                input_dto = UpdateTaskInput(task_id=task.id, **update_kwargs)
                result = self.use_case.execute(input_dto)

                self.assertEqual(getattr(result.task, field_name), expected_value)
                self.assertIn(expected_field, result.updated_fields)
                self.assertEqual(len(result.updated_fields), 1)

    def test_execute_update_status(self):
        """Test updating task status with time tracking"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, status=TaskStatus.IN_PROGRESS)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.task.status, TaskStatus.IN_PROGRESS)
        self.assertIn("status", result.updated_fields)
        # Verify time tracking was triggered
        self.assertIsNotNone(result.task.actual_start)

    def test_execute_update_multiple_fields(self):
        """Test updating multiple fields at once"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Use future date
        future_date = datetime.now() + timedelta(days=7)
        input_dto = UpdateTaskInput(
            task_id=task.id,
            priority=2,
            planned_start=future_date,
            estimated_duration=3.0,
        )
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.task.priority, 2)
        self.assertEqual(result.task.planned_start, future_date)
        self.assertEqual(result.task.estimated_duration, 3.0)
        self.assertEqual(len(result.updated_fields), 3)
        self.assertIn("priority", result.updated_fields)
        self.assertIn("planned_start", result.updated_fields)
        self.assertIn("estimated_duration", result.updated_fields)

    def test_execute_no_updates(self):
        """Test when no fields are updated"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(len(result.updated_fields), 0)
        # Verify no save was called by checking the task remains unchanged
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.priority, 1)

    def test_execute_with_invalid_task_raises_error(self):
        """Test with non-existent task raises TaskNotFoundException"""
        input_dto = UpdateTaskInput(task_id=999, priority=2)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_update_all_fields_at_once(self):
        """Test updating all fields simultaneously"""
        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        planned_start = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        planned_end = base_date.replace(hour=18, minute=0, second=0, microsecond=0)
        deadline = (base_date + timedelta(days=3)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )

        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(
            task_id=task.id,
            status=TaskStatus.IN_PROGRESS,
            priority=3,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=8.0,
        )
        result = self.use_case.execute(input_dto)

        # Verify all fields were updated
        self.assertEqual(result.task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(result.task.priority, 3)
        self.assertEqual(result.task.planned_start, planned_start)
        self.assertEqual(result.task.planned_end, planned_end)
        self.assertEqual(result.task.deadline, deadline)
        self.assertEqual(result.task.estimated_duration, 8.0)
        self.assertIsNotNone(result.task.actual_start)

        # Verify all field names are in updated_fields
        self.assertEqual(len(result.updated_fields), 6)
        self.assertIn("status", result.updated_fields)
        self.assertIn("priority", result.updated_fields)
        self.assertIn("planned_start", result.updated_fields)
        self.assertIn("planned_end", result.updated_fields)
        self.assertIn("deadline", result.updated_fields)
        self.assertIn("estimated_duration", result.updated_fields)

    def test_execute_status_change_records_end_time(self):
        """Test that changing status to finished states records actual_end timestamp"""
        test_cases = [
            (TaskStatus.COMPLETED, "Change to COMPLETED"),
            (TaskStatus.CANCELED, "Change to CANCELED"),
        ]

        for target_status, description in test_cases:
            with self.subTest(description=description):
                task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
                # Use a fixed past date for actual_start (already started tasks can have past dates)
                task.actual_start = datetime.now() - timedelta(days=1)
                task.id = self.repository.generate_next_id()
                self.repository.save(task)

                input_dto = UpdateTaskInput(task_id=task.id, status=target_status)
                result = self.use_case.execute(input_dto)

                self.assertEqual(result.task.status, target_status)
                self.assertIsNotNone(result.task.actual_end)
                self.assertIn("status", result.updated_fields)

    def test_execute_updates_are_persisted(self):
        """Test that updates are correctly persisted to repository"""
        # Use dynamic future date to avoid test failures as time passes
        deadline = (datetime.now() + timedelta(days=60)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )

        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, priority=5, deadline=deadline)
        self.use_case.execute(input_dto)

        # Reload from repository to verify persistence
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.priority, 5)
        self.assertEqual(persisted_task.deadline, deadline)

    def test_execute_update_estimated_duration_succeeds_for_leaf_task(self):
        """Test that estimated_duration can be set for leaf tasks (no children)"""
        task = Task(name="Leaf Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, estimated_duration=3.5)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.task.estimated_duration, 3.5)
        self.assertIn("estimated_duration", result.updated_fields)

    def test_execute_clears_daily_allocations_when_updating_planned_start(self):
        """Test that daily_allocations is cleared when planned_start is updated (issue #171)"""

        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        start_date = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = (base_date + timedelta(days=2)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        new_start = (base_date + timedelta(days=4)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            start_date.date(): 3.0,
            (start_date + timedelta(days=1)).date(): 2.5,
        }
        task.planned_start = start_date
        task.planned_end = end_date
        self.repository.save(task)

        # Update planned_start to a different date
        input_dto = UpdateTaskInput(task_id=task.id, planned_start=new_start)
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations was cleared (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.daily_allocations, {})  # type: ignore[union-attr]
        self.assertIn("planned_start", result.updated_fields)
        self.assertIn("daily_allocations", result.updated_fields)
        self.assertEqual(result.task.planned_start, new_start)

    def test_execute_clears_daily_allocations_when_updating_planned_end(self):
        """Test that daily_allocations is cleared when planned_end is updated (issue #171)"""

        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        start_date = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = (base_date + timedelta(days=2)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        new_end = (base_date + timedelta(days=7)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            start_date.date(): 3.0,
            (start_date + timedelta(days=1)).date(): 2.5,
        }
        task.planned_start = start_date
        task.planned_end = end_date
        self.repository.save(task)

        # Update planned_end to a different date
        input_dto = UpdateTaskInput(task_id=task.id, planned_end=new_end)
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations was cleared (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.daily_allocations, {})  # type: ignore[union-attr]
        self.assertIn("planned_end", result.updated_fields)
        self.assertIn("daily_allocations", result.updated_fields)
        self.assertEqual(result.task.planned_end, new_end)

    def test_execute_clears_daily_allocations_when_updating_both_planned_dates(self):
        """Test that daily_allocations is cleared when both planned dates are updated"""

        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        start_date = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = (base_date + timedelta(days=2)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        new_start = (base_date + timedelta(days=9)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        new_end = (base_date + timedelta(days=11)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            start_date.date(): 3.0,
            (start_date + timedelta(days=1)).date(): 2.5,
        }
        task.planned_start = start_date
        task.planned_end = end_date
        self.repository.save(task)

        # Update both planned_start and planned_end
        input_dto = UpdateTaskInput(
            task_id=task.id, planned_start=new_start, planned_end=new_end
        )
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations was cleared (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.daily_allocations, {})  # type: ignore[union-attr]
        self.assertIn("planned_start", result.updated_fields)
        self.assertIn("planned_end", result.updated_fields)
        self.assertIn("daily_allocations", result.updated_fields)

    def test_execute_does_not_add_daily_allocations_field_when_already_empty(self):
        """Test that daily_allocations field is not added when already empty"""
        # Use dynamic future dates to avoid test failures as time passes
        base_date = datetime.now() + timedelta(days=30)
        start_date = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = (base_date + timedelta(days=2)).replace(
            hour=18, minute=0, second=0, microsecond=0
        )
        new_start = (base_date + timedelta(days=4)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        task = Task(name="Task without allocations", priority=1)
        task.id = self.repository.generate_next_id()
        task.planned_start = start_date
        task.planned_end = end_date
        # daily_allocations is already empty by default
        self.repository.save(task)

        # Update planned_start
        input_dto = UpdateTaskInput(task_id=task.id, planned_start=new_start)
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations is still empty and NOT in updated_fields (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.daily_allocations, {})  # type: ignore[union-attr]
        self.assertIn("planned_start", result.updated_fields)
        self.assertNotIn("daily_allocations", result.updated_fields)


if __name__ == "__main__":
    unittest.main()
