import os
import tempfile
import unittest

from application.dto.create_task_input import CreateTaskInput
from application.use_cases.create_task import CreateTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestCreateTaskUseCase(unittest.TestCase):
    """Test cases for CreateTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.use_case = CreateTaskUseCase(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_creates_task_with_id(self):
        """Test execute creates task with auto-generated ID"""
        input_dto = CreateTaskInput(name="Test Task", priority=1)

        task = self.use_case.execute(input_dto)

        self.assertIsNotNone(task.id)
        self.assertEqual(task.id, 1)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, 1)

    def test_execute_assigns_sequential_ids(self):
        """Test execute assigns sequential IDs"""
        input1 = CreateTaskInput(name="Task 1", priority=1)
        input2 = CreateTaskInput(name="Task 2", priority=2)
        input3 = CreateTaskInput(name="Task 3", priority=3)

        task1 = self.use_case.execute(input1)
        task2 = self.use_case.execute(input2)
        task3 = self.use_case.execute(input3)

        self.assertEqual(task1.id, 1)
        self.assertEqual(task2.id, 2)
        self.assertEqual(task3.id, 3)

    def test_execute_persists_to_repository(self):
        """Test execute saves task to repository"""
        input_dto = CreateTaskInput(name="Persistent Task", priority=2)

        task = self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(task.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Persistent Task")
        self.assertEqual(retrieved.priority, 2)

    def test_execute_with_parent(self):
        """Test execute creates task with parent"""
        parent_input = CreateTaskInput(name="Parent", priority=1)
        parent = self.use_case.execute(parent_input)

        child_input = CreateTaskInput(name="Child", priority=1, parent_id=parent.id)
        child = self.use_case.execute(child_input)

        self.assertEqual(child.parent_id, parent.id)
        children = self.repository.get_children(parent.id)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].name, "Child")

    def test_execute_with_invalid_parent_raises_error(self):
        """Test execute with non-existent parent raises TaskNotFoundException"""
        input_dto = CreateTaskInput(name="Orphan", priority=1, parent_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_with_all_optional_fields(self):
        """Test execute with all optional fields"""
        input_dto = CreateTaskInput(
            name="Full Task",
            priority=3,
            planned_start="2025-01-01 09:00:00",
            planned_end="2025-01-31 17:00:00",
            deadline="2025-02-01 18:00:00",
            estimated_duration=10.5,
        )

        task = self.use_case.execute(input_dto)

        self.assertEqual(task.name, "Full Task")
        self.assertEqual(task.priority, 3)
        self.assertEqual(task.planned_start, "2025-01-01 09:00:00")
        self.assertEqual(task.planned_end, "2025-01-31 17:00:00")
        self.assertEqual(task.deadline, "2025-02-01 18:00:00")
        self.assertEqual(task.estimated_duration, 10.5)

    def test_execute_with_none_optional_fields(self):
        """Test execute with None optional fields"""
        input_dto = CreateTaskInput(
            name="Minimal Task",
            priority=1,
            parent_id=None,
            planned_start=None,
            planned_end=None,
            deadline=None,
            estimated_duration=None,
        )

        task = self.use_case.execute(input_dto)

        self.assertEqual(task.name, "Minimal Task")
        self.assertEqual(task.priority, 1)
        self.assertIsNone(task.parent_id)
        self.assertIsNone(task.planned_start)
        self.assertIsNone(task.planned_end)
        self.assertIsNone(task.deadline)
        self.assertIsNone(task.estimated_duration)


if __name__ == "__main__":
    unittest.main()
