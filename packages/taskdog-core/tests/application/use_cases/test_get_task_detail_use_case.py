"""Tests for GetTaskDetailUseCase."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from taskdog_core.application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)


class TestGetTaskDetailUseCase:
    """Test cases for GetTaskDetailUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.notes_repository = FileNotesRepository()
        self.use_case = GetTaskDetailUseCase(self.repository, self.notes_repository)

        # Create temporary directory for notes
        self.notes_dir = tempfile.mkdtemp()

    @pytest.fixture(autouse=True)
    def teardown(self, request):
        """Clean up temporary files after each test."""

        def cleanup():
            if hasattr(self, "notes_dir") and os.path.exists(self.notes_dir):
                for file in Path(self.notes_dir).glob("*.md"):
                    file.unlink()
                os.rmdir(self.notes_dir)

        request.addfinalizer(cleanup)

    def test_execute_returns_task_detail_dto(self):
        """Test execute returns TaskDetailDTO with task data."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = GetTaskDetailInput(task.id)
        result = self.use_case.execute(input_dto)

        assert result.task.id == task.id
        assert result.task.name == "Test Task"
        assert result.has_notes is False
        assert result.notes_content is None

    def test_execute_with_notes_file(self):
        """Test execute returns notes content when notes file exists."""
        task = self.repository.create(name="Test Task", priority=1)

        # Create notes file using NotesRepository
        notes_path = self.notes_repository.get_notes_path(task.id)
        self.notes_repository.ensure_notes_dir()
        notes_content = "# Test Notes\n\nThis is a test note."
        self.notes_repository.write_notes(task.id, notes_content)

        try:
            input_dto = GetTaskDetailInput(task.id)
            result = self.use_case.execute(input_dto)

            assert result.has_notes is True
            assert result.notes_content == notes_content
        finally:
            # Clean up notes file
            if notes_path.exists():
                notes_path.unlink()

    def test_execute_without_notes_file(self):
        """Test execute handles missing notes file gracefully."""
        task = self.repository.create(name="Test Task", priority=1)

        input_dto = GetTaskDetailInput(task.id)
        result = self.use_case.execute(input_dto)

        assert result.has_notes is False
        assert result.notes_content is None

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = GetTaskDetailInput(task_id=999)

        with pytest.raises(TaskNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert exc_info.value.task_id == 999

    def test_execute_preserves_task_properties(self):
        """Test execute preserves all task properties in DTO."""
        task = self.repository.create(
            name="Complex Task",
            priority=2,
            planned_start=datetime(2024, 1, 1, 10, 0, 0),
            planned_end=datetime(2024, 1, 1, 12, 0, 0),
            deadline=datetime(2024, 1, 1, 18, 0, 0),
            estimated_duration=2.5,
        )

        input_dto = GetTaskDetailInput(task.id)
        result = self.use_case.execute(input_dto)

        assert result.task.name == "Complex Task"
        assert result.task.priority == 2
        assert result.task.planned_start == datetime(2024, 1, 1, 10, 0, 0)
        assert result.task.planned_end == datetime(2024, 1, 1, 12, 0, 0)
        assert result.task.deadline == datetime(2024, 1, 1, 18, 0, 0)
        assert result.task.estimated_duration == 2.5

    def test_execute_handles_corrupt_notes_file(self):
        """Test execute handles unreadable notes file gracefully."""
        task = self.repository.create(name="Test Task", priority=1)

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
                assert result.has_notes is True
                assert result.notes_content is None
        finally:
            # Restore permissions and clean up
            if hasattr(os, "chmod") and notes_path.exists():
                os.chmod(notes_path, 0o644)
                notes_path.unlink()
