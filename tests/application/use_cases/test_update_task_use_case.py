import os
import tempfile
import unittest
from datetime import datetime, timedelta

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestUpdateTaskUseCase(unittest.TestCase):
    """Test cases for UpdateTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = UpdateTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

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

        for field_name, update_kwargs, expected_field, expected_value, description in test_cases:
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
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(
            task_id=task.id,
            status=TaskStatus.IN_PROGRESS,
            priority=3,
            planned_start=datetime(2025, 10, 12, 9, 0, 0),
            planned_end=datetime(2025, 10, 12, 18, 0, 0),
            deadline=datetime(2025, 10, 15, 18, 0, 0),
            estimated_duration=8.0,
        )
        result = self.use_case.execute(input_dto)

        # Verify all fields were updated
        self.assertEqual(result.task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(result.task.priority, 3)
        self.assertEqual(result.task.planned_start, datetime(2025, 10, 12, 9, 0, 0))
        self.assertEqual(result.task.planned_end, datetime(2025, 10, 12, 18, 0, 0))
        self.assertEqual(result.task.deadline, datetime(2025, 10, 15, 18, 0, 0))
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
                task.actual_start = datetime(2025, 10, 12, 9, 0, 0)
                task.id = self.repository.generate_next_id()
                self.repository.save(task)

                input_dto = UpdateTaskInput(task_id=task.id, status=target_status)
                result = self.use_case.execute(input_dto)

                self.assertEqual(result.task.status, target_status)
                self.assertIsNotNone(result.task.actual_end)
                self.assertIn("status", result.updated_fields)

    def test_execute_updates_are_persisted(self):
        """Test that updates are correctly persisted to repository"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(
            task_id=task.id, priority=5, deadline=datetime(2026, 10, 20, 18, 0, 0)
        )
        self.use_case.execute(input_dto)

        # Reload from repository to verify persistence
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.priority, 5)
        self.assertEqual(persisted_task.deadline, datetime(2026, 10, 20, 18, 0, 0))

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
        from datetime import date

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            date(2025, 11, 1): 3.0,
            date(2025, 11, 2): 2.5,
        }
        task.planned_start = datetime(2025, 11, 1, 9, 0, 0)
        task.planned_end = datetime(2025, 11, 3, 18, 0, 0)
        self.repository.save(task)

        # Update planned_start to a different date
        new_start = datetime(2025, 11, 5, 9, 0, 0)
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
        from datetime import date

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            date(2025, 11, 1): 3.0,
            date(2025, 11, 2): 2.5,
        }
        task.planned_start = datetime(2025, 11, 1, 9, 0, 0)
        task.planned_end = datetime(2025, 11, 3, 18, 0, 0)
        self.repository.save(task)

        # Update planned_end to a different date
        new_end = datetime(2025, 11, 8, 18, 0, 0)
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
        from datetime import date

        task = Task(name="Task with allocations", priority=1)
        task.id = self.repository.generate_next_id()
        # Set daily_allocations as if optimized
        task.daily_allocations = {
            date(2025, 11, 1): 3.0,
            date(2025, 11, 2): 2.5,
        }
        task.planned_start = datetime(2025, 11, 1, 9, 0, 0)
        task.planned_end = datetime(2025, 11, 3, 18, 0, 0)
        self.repository.save(task)

        # Update both planned_start and planned_end
        new_start = datetime(2025, 11, 10, 9, 0, 0)
        new_end = datetime(2025, 11, 12, 18, 0, 0)
        input_dto = UpdateTaskInput(task_id=task.id, planned_start=new_start, planned_end=new_end)
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations was cleared (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.daily_allocations, {})  # type: ignore[union-attr]
        self.assertIn("planned_start", result.updated_fields)
        self.assertIn("planned_end", result.updated_fields)
        self.assertIn("daily_allocations", result.updated_fields)

    def test_execute_does_not_add_daily_allocations_field_when_already_empty(self):
        """Test that daily_allocations field is not added when already empty"""
        task = Task(name="Task without allocations", priority=1)
        task.id = self.repository.generate_next_id()
        task.planned_start = datetime(2025, 11, 1, 9, 0, 0)
        task.planned_end = datetime(2025, 11, 3, 18, 0, 0)
        # daily_allocations is already empty by default
        self.repository.save(task)

        # Update planned_start
        new_start = datetime(2025, 11, 5, 9, 0, 0)
        input_dto = UpdateTaskInput(task_id=task.id, planned_start=new_start)
        result = self.use_case.execute(input_dto)

        # Verify daily_allocations is still empty and NOT in updated_fields (check persisted task)
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.daily_allocations, {})  # type: ignore[union-attr]
        self.assertIn("planned_start", result.updated_fields)
        self.assertNotIn("daily_allocations", result.updated_fields)


if __name__ == "__main__":
    unittest.main()
