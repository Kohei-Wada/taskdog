import os
import tempfile
import unittest
from pathlib import Path

from application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskNotFoundException
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestGetTaskDetailUseCase(unittest.TestCase):
    """Test cases for GetTaskDetailUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.use_case = GetTaskDetailUseCase(self.repository)

        # Create temporary directory for notes
        self.notes_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

        # Clean up notes directory
        if os.path.exists(self.notes_dir):
            for file in Path(self.notes_dir).glob("*.md"):
                file.unlink()
            os.rmdir(self.notes_dir)

    def test_execute_returns_task_detail_dto(self):
        """Test execute returns TaskDetailDTO with task data"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = GetTaskDetailInput(task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.task.id, task.id)
        self.assertEqual(result.task.name, "Test Task")
        self.assertFalse(result.has_notes)
        self.assertIsNone(result.notes_content)

    def test_execute_with_notes_file(self):
        """Test execute returns notes content when notes file exists"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Create notes file
        notes_path = task.notes_path
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_content = "# Test Notes\n\nThis is a test note."
        notes_path.write_text(notes_content, encoding="utf-8")

        try:
            input_dto = GetTaskDetailInput(task.id)
            result = self.use_case.execute(input_dto)

            self.assertTrue(result.has_notes)
            self.assertEqual(result.notes_content, notes_content)
        finally:
            # Clean up notes file
            if notes_path.exists():
                notes_path.unlink()

    def test_execute_without_notes_file(self):
        """Test execute handles missing notes file gracefully"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = GetTaskDetailInput(task.id)
        result = self.use_case.execute(input_dto)

        self.assertFalse(result.has_notes)
        self.assertIsNone(result.notes_content)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = GetTaskDetailInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_preserves_task_properties(self):
        """Test execute preserves all task properties in DTO"""
        task = Task(
            name="Complex Task",
            priority=2,
            planned_start="2024-01-01 10:00:00",
            planned_end="2024-01-01 12:00:00",
            deadline="2024-01-01 18:00:00",
            estimated_duration=2.5,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = GetTaskDetailInput(task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.task.name, "Complex Task")
        self.assertEqual(result.task.priority, 2)
        self.assertEqual(result.task.planned_start, "2024-01-01 10:00:00")
        self.assertEqual(result.task.planned_end, "2024-01-01 12:00:00")
        self.assertEqual(result.task.deadline, "2024-01-01 18:00:00")
        self.assertEqual(result.task.estimated_duration, 2.5)

    def test_execute_handles_corrupt_notes_file(self):
        """Test execute handles unreadable notes file gracefully"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Create notes file with restricted permissions
        notes_path = task.notes_path
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text("Test content", encoding="utf-8")

        try:
            # Make file unreadable (Unix only)
            if hasattr(os, "chmod"):
                os.chmod(notes_path, 0o000)

                input_dto = GetTaskDetailInput(task.id)
                result = self.use_case.execute(input_dto)

                # Should treat as no notes when reading fails
                self.assertFalse(result.has_notes)
                self.assertIsNone(result.notes_content)
        finally:
            # Restore permissions and clean up
            if hasattr(os, "chmod") and notes_path.exists():
                os.chmod(notes_path, 0o644)
                notes_path.unlink()


if __name__ == "__main__":
    unittest.main()
