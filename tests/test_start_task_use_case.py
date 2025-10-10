import unittest
import tempfile
import os
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from domain.services.time_tracker import TimeTracker
from application.use_cases.start_task import StartTaskUseCase
from application.dto.start_task_input import StartTaskInput
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException


class TestStartTaskUseCase(unittest.TestCase):
    """Test cases for StartTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = StartTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_sets_status_to_in_progress(self):
        """Test execute sets task status to IN_PROGRESS"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)

    def test_execute_records_actual_start_time(self):
        """Test execute records actual start timestamp"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNotNone(result.actual_start)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(retrieved.actual_start)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = StartTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_does_not_update_actual_end(self):
        """Test execute does not set actual_end when starting"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNone(result.actual_end)

    def test_execute_auto_starts_pending_parent_task(self):
        """Test execute auto-starts parent task if it's PENDING"""
        # Create parent task
        parent = Task(name="Parent Task", priority=1)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child task
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start child task
        input_dto = StartTaskInput(task_id=child.id)
        self.use_case.execute(input_dto)

        # Verify parent is now IN_PROGRESS
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(parent_updated.actual_start)

    def test_execute_does_not_change_in_progress_parent(self):
        """Test execute does not change parent that's already IN_PROGRESS"""
        # Create parent task with IN_PROGRESS status
        parent = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        parent.id = self.repository.generate_next_id()
        parent.actual_start = "2024-01-01 10:00:00"
        self.repository.save(parent)

        # Create child task
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start child task
        input_dto = StartTaskInput(task_id=child.id)
        self.use_case.execute(input_dto)

        # Verify parent status and actual_start remain unchanged
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(parent_updated.actual_start, "2024-01-01 10:00:00")

    def test_execute_does_not_change_completed_parent(self):
        """Test execute does not change parent that's COMPLETED"""
        # Create parent task with COMPLETED status
        parent = Task(name="Parent Task", priority=1, status=TaskStatus.COMPLETED)
        parent.id = self.repository.generate_next_id()
        parent.actual_start = "2024-01-01 10:00:00"
        parent.actual_end = "2024-01-01 12:00:00"
        self.repository.save(parent)

        # Create child task
        child = Task(name="Child Task", priority=2, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        # Start child task
        input_dto = StartTaskInput(task_id=child.id)
        self.use_case.execute(input_dto)

        # Verify parent status remains COMPLETED
        parent_updated = self.repository.get_by_id(parent.id)
        self.assertEqual(parent_updated.status, TaskStatus.COMPLETED)

    def test_execute_without_parent_works_normally(self):
        """Test execute works normally for tasks without parent"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(result.actual_start)


if __name__ == "__main__":
    unittest.main()
