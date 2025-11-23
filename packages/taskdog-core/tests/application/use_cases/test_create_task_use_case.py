import unittest
from datetime import datetime

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestCreateTaskUseCase(InMemoryDatabaseTestCase):
    """Test cases for CreateTaskUseCase"""

    def setUp(self):
        """Initialize use case for each test"""
        super().setUp()
        self.use_case = CreateTaskUseCase(self.repository)

    def test_execute_creates_task_with_id(self):
        """Test execute creates task with auto-generated ID"""
        input_dto = CreateTaskInput(name="Test Task", priority=1)

        result = self.use_case.execute(input_dto)

        self.assertIsNotNone(result.id)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "Test Task")
        self.assertEqual(result.priority, 1)

    def test_execute_assigns_sequential_ids(self):
        """Test execute assigns sequential IDs"""
        input1 = CreateTaskInput(name="Task 1", priority=1)
        input2 = CreateTaskInput(name="Task 2", priority=2)
        input3 = CreateTaskInput(name="Task 3", priority=3)

        result1 = self.use_case.execute(input1)
        result2 = self.use_case.execute(input2)
        result3 = self.use_case.execute(input3)

        self.assertEqual(result1.id, 1)
        self.assertEqual(result2.id, 2)
        self.assertEqual(result3.id, 3)

    def test_execute_persists_to_repository(self):
        """Test execute saves task to repository"""
        input_dto = CreateTaskInput(name="Persistent Task", priority=2)

        result = self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(result.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Persistent Task")
        self.assertEqual(retrieved.priority, 2)

    def test_execute_with_all_optional_fields(self):
        """Test execute with all optional fields"""
        input_dto = CreateTaskInput(
            name="Full Task",
            priority=3,
            planned_start=datetime(2025, 1, 1, 9, 0, 0),
            planned_end=datetime(2025, 1, 31, 17, 0, 0),
            deadline=datetime(2025, 2, 1, 18, 0, 0),
            estimated_duration=10.5,
        )

        result = self.use_case.execute(input_dto)

        self.assertEqual(result.name, "Full Task")
        self.assertEqual(result.priority, 3)
        self.assertEqual(result.planned_start, datetime(2025, 1, 1, 9, 0, 0))
        self.assertEqual(result.planned_end, datetime(2025, 1, 31, 17, 0, 0))
        self.assertEqual(result.deadline, datetime(2025, 2, 1, 18, 0, 0))
        self.assertEqual(result.estimated_duration, 10.5)

    def test_execute_with_none_optional_fields(self):
        """Test execute with None optional fields"""
        input_dto = CreateTaskInput(
            name="Minimal Task",
            priority=1,
            planned_start=None,
            planned_end=None,
            deadline=None,
            estimated_duration=None,
        )

        result = self.use_case.execute(input_dto)

        self.assertEqual(result.name, "Minimal Task")
        self.assertEqual(result.priority, 1)
        self.assertIsNone(result.planned_start)
        self.assertIsNone(result.planned_end)
        self.assertIsNone(result.deadline)
        self.assertIsNone(result.estimated_duration)


if __name__ == "__main__":
    unittest.main()
