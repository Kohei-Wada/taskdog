import unittest
import os
import tempfile
from datetime import datetime
from pathlib import Path

from taskdog_core.application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestGetTaskDetailUseCase(InMemoryDatabaseTestCase):
    """Test cases for GetTaskDetailUseCase"""

    def setUp(self):
        """Initialize use case for each test"""
        super().setUp()
        self.notes_repository = FileNotesRepository()
        self.use_case = GetTaskDetailUseCase(self.repository, self.notes_repository)

        # Create temporary directory for notes
        self.notes_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files after each test"""
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

        # Create notes file using NotesRepository
        notes_path = self.notes_repository.get_notes_path(task.id)
        self.notes_repository.ensure_notes_dir()
        notes_content = "# Test Notes\n\nThis is a test note."
        self.notes_repository.write_notes(task.id, notes_content)

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
            planned_start=datetime(2024, 1, 1, 10, 0, 0),
            planned_end=datetime(2024, 1, 1, 12, 0, 0),
            deadline=datetime(2024, 1, 1, 18, 0, 0),
            estimated_duration=2.5,
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = GetTaskDetailInput(task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.task.name, "Complex Task")
        self.assertEqual(result.task.priority, 2)
        self.assertEqual(result.task.planned_start, datetime(2024, 1, 1, 10, 0, 0))
        self.assertEqual(result.task.planned_end, datetime(2024, 1, 1, 12, 0, 0))
        self.assertEqual(result.task.deadline, datetime(2024, 1, 1, 18, 0, 0))
        self.assertEqual(result.task.estimated_duration, 2.5)

    def test_execute_handles_corrupt_notes_file(self):
        """Test execute handles unreadable notes file gracefully"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Create notes file with restricted permissions using NotesRepository
        notes_path = self.notes_repository.get_notes_path(task.id)
        self.notes_repository.ensure_notes_dir()
        self.notes_repository.write_notes(task.id, "Test content")

        try:
            # Make file unreadable (Unix only)
            if hasattr(os, "chmod"):
                os.chmod(notes_path, 0o000)

                input_dto = GetTaskDetailInput(task.id)
                result = self.use_case.execute(input_dto)

                # File exists so has_notes is True, but content should be None due to read error
                self.assertTrue(result.has_notes)
                self.assertIsNone(result.notes_content)
        finally:
            # Restore permissions and clean up
            if hasattr(os, "chmod") and notes_path.exists():
                os.chmod(notes_path, 0o644)
                notes_path.unlink()


if __name__ == "__main__":
    unittest.main()
