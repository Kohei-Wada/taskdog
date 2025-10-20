import os
import tempfile
import unittest
from datetime import datetime, timedelta

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from domain.constants import DATETIME_FORMAT
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

    def test_execute_update_priority(self):
        """Test updating task priority"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, priority=3)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.priority, 3)
        self.assertIn("priority", updated_fields)
        self.assertEqual(len(updated_fields), 1)

    def test_execute_update_status(self):
        """Test updating task status with time tracking"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, status=TaskStatus.IN_PROGRESS)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.status, TaskStatus.IN_PROGRESS)
        self.assertIn("status", updated_fields)
        # Verify time tracking was triggered
        self.assertIsNotNone(result_task.actual_start)

    def test_execute_update_planned_start(self):
        """Test updating planned start time"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Use future date
        future_date = (datetime.now() + timedelta(days=7)).strftime(DATETIME_FORMAT)
        input_dto = UpdateTaskInput(task_id=task.id, planned_start=future_date)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.planned_start, future_date)
        self.assertIn("planned_start", updated_fields)
        self.assertEqual(len(updated_fields), 1)

    def test_execute_update_planned_end(self):
        """Test updating planned end time"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Use future date
        future_date = (datetime.now() + timedelta(days=14)).strftime(DATETIME_FORMAT)
        input_dto = UpdateTaskInput(task_id=task.id, planned_end=future_date)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.planned_end, future_date)
        self.assertIn("planned_end", updated_fields)
        self.assertEqual(len(updated_fields), 1)

    def test_execute_update_deadline(self):
        """Test updating deadline"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Use future date
        future_date = (datetime.now() + timedelta(days=30)).strftime(DATETIME_FORMAT)
        input_dto = UpdateTaskInput(task_id=task.id, deadline=future_date)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.deadline, future_date)
        self.assertIn("deadline", updated_fields)
        self.assertEqual(len(updated_fields), 1)

    def test_execute_update_estimated_duration(self):
        """Test updating estimated duration"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, estimated_duration=4.5)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.estimated_duration, 4.5)
        self.assertIn("estimated_duration", updated_fields)
        self.assertEqual(len(updated_fields), 1)

    def test_execute_update_multiple_fields(self):
        """Test updating multiple fields at once"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Use future date
        future_date = (datetime.now() + timedelta(days=7)).strftime(DATETIME_FORMAT)
        input_dto = UpdateTaskInput(
            task_id=task.id,
            priority=2,
            planned_start=future_date,
            estimated_duration=3.0,
        )
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.priority, 2)
        self.assertEqual(result_task.planned_start, future_date)
        self.assertEqual(result_task.estimated_duration, 3.0)
        self.assertEqual(len(updated_fields), 3)
        self.assertIn("priority", updated_fields)
        self.assertIn("planned_start", updated_fields)
        self.assertIn("estimated_duration", updated_fields)

    def test_execute_no_updates(self):
        """Test when no fields are updated"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id)
        _result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(len(updated_fields), 0)
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
            planned_start="2025-10-12 09:00:00",
            planned_end="2025-10-12 18:00:00",
            deadline="2025-10-15 18:00:00",
            estimated_duration=8.0,
        )
        result_task, updated_fields = self.use_case.execute(input_dto)

        # Verify all fields were updated
        self.assertEqual(result_task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(result_task.priority, 3)
        self.assertEqual(result_task.planned_start, "2025-10-12 09:00:00")
        self.assertEqual(result_task.planned_end, "2025-10-12 18:00:00")
        self.assertEqual(result_task.deadline, "2025-10-15 18:00:00")
        self.assertEqual(result_task.estimated_duration, 8.0)
        self.assertIsNotNone(result_task.actual_start)

        # Verify all field names are in updated_fields
        self.assertEqual(len(updated_fields), 6)
        self.assertIn("status", updated_fields)
        self.assertIn("priority", updated_fields)
        self.assertIn("planned_start", updated_fields)
        self.assertIn("planned_end", updated_fields)
        self.assertIn("deadline", updated_fields)
        self.assertIn("estimated_duration", updated_fields)

    def test_execute_status_change_to_completed_records_end_time(self):
        """Test that changing status to COMPLETED records actual_end timestamp"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.actual_start = "2025-10-12 09:00:00"
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, status=TaskStatus.COMPLETED)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(result_task.actual_end)
        self.assertIn("status", updated_fields)

    def test_execute_status_change_to_canceled_records_end_time(self):
        """Test that changing status to CANCELED records actual_end timestamp"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.actual_start = "2025-10-12 09:00:00"
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, status=TaskStatus.CANCELED)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.status, TaskStatus.CANCELED)
        self.assertIsNotNone(result_task.actual_end)
        self.assertIn("status", updated_fields)

    def test_execute_updates_are_persisted(self):
        """Test that updates are correctly persisted to repository"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, priority=5, deadline="2025-10-20 18:00:00")
        self.use_case.execute(input_dto)

        # Reload from repository to verify persistence
        persisted_task = self.repository.get_by_id(task.id)
        self.assertEqual(persisted_task.priority, 5)
        self.assertEqual(persisted_task.deadline, "2025-10-20 18:00:00")

    def test_execute_update_estimated_duration_succeeds_for_leaf_task(self):
        """Test that estimated_duration can be set for leaf tasks (no children)"""
        task = Task(name="Leaf Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = UpdateTaskInput(task_id=task.id, estimated_duration=3.5)
        result_task, updated_fields = self.use_case.execute(input_dto)

        self.assertEqual(result_task.estimated_duration, 3.5)
        self.assertIn("estimated_duration", updated_fields)


if __name__ == "__main__":
    unittest.main()
