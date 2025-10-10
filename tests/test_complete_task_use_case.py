import unittest
import tempfile
import os
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from domain.services.time_tracker import TimeTracker
from application.use_cases.complete_task import CompleteTaskUseCase
from application.dto.complete_task_input import CompleteTaskInput
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException, IncompleteChildrenError


class TestCompleteTaskUseCase(unittest.TestCase):
    """Test cases for CompleteTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = CompleteTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_sets_status_to_completed(self):
        """Test execute sets task status to COMPLETED"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CompleteTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.COMPLETED)

    def test_execute_records_actual_end_time(self):
        """Test execute records actual end timestamp"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CompleteTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNotNone(result.actual_end)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CompleteTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(retrieved.actual_end)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = CompleteTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_does_not_update_actual_start(self):
        """Test execute does not modify actual_start when completing"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        # Set actual_start manually to simulate a started task
        task.actual_start = "2025-10-12 10:00:00"
        self.repository.save(task)

        input_dto = CompleteTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # actual_start should remain unchanged
        self.assertEqual(result.actual_start, "2025-10-12 10:00:00")

    def test_execute_with_incomplete_children_raises_error(self):
        """Test execute with incomplete children raises IncompleteChildrenError"""
        # Create parent task
        parent = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child task with IN_PROGRESS status
        child = Task(name="Child Task", priority=1, status=TaskStatus.IN_PROGRESS, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        input_dto = CompleteTaskInput(task_id=parent.id)

        with self.assertRaises(IncompleteChildrenError) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, parent.id)
        self.assertEqual(len(context.exception.incomplete_children), 1)
        self.assertEqual(context.exception.incomplete_children[0].id, child.id)

    def test_execute_with_all_children_completed_succeeds(self):
        """Test execute succeeds when all children are completed"""
        # Create parent task
        parent = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create child task with COMPLETED status
        child = Task(name="Child Task", priority=1, status=TaskStatus.COMPLETED, parent_id=parent.id)
        child.id = self.repository.generate_next_id()
        self.repository.save(child)

        input_dto = CompleteTaskInput(task_id=parent.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.COMPLETED)

    def test_execute_with_multiple_incomplete_children_raises_error(self):
        """Test execute with multiple incomplete children lists all of them"""
        # Create parent task
        parent = Task(name="Parent Task", priority=1, status=TaskStatus.IN_PROGRESS)
        parent.id = self.repository.generate_next_id()
        self.repository.save(parent)

        # Create two incomplete child tasks
        child1 = Task(name="Child Task 1", priority=1, status=TaskStatus.PENDING, parent_id=parent.id)
        child1.id = self.repository.generate_next_id()
        self.repository.save(child1)

        child2 = Task(name="Child Task 2", priority=1, status=TaskStatus.IN_PROGRESS, parent_id=parent.id)
        child2.id = self.repository.generate_next_id()
        self.repository.save(child2)

        input_dto = CompleteTaskInput(task_id=parent.id)

        with self.assertRaises(IncompleteChildrenError) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, parent.id)
        self.assertEqual(len(context.exception.incomplete_children), 2)


if __name__ == "__main__":
    unittest.main()
