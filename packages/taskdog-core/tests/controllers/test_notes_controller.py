"""Tests for NotesController."""

from unittest.mock import Mock

import pytest

from taskdog_core.controllers.notes_controller import NotesController
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestNotesController:
    """Test cases for NotesController."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=SqliteTaskRepository)
        self.notes_repository = Mock(spec=NotesRepository)
        self.controller = NotesController(
            repository=self.repository,
            notes_repository=self.notes_repository,
        )
        self.task = Task(id=1, name="Test Task", priority=1, status=TaskStatus.PENDING)

    def test_get_notes_returns_output(self):
        """Test get_notes returns NotesOutput with content."""
        self.repository.get_by_id.return_value = self.task
        self.notes_repository.has_notes.return_value = True
        self.notes_repository.read_notes.return_value = "# Hello"

        result = self.controller.get_notes(1)

        assert result.task_id == 1
        assert result.task_name == "Test Task"
        assert result.content == "# Hello"
        assert result.has_notes is True

    def test_get_notes_returns_empty_when_no_notes(self):
        """Test get_notes returns empty content when no notes exist."""
        self.repository.get_by_id.return_value = self.task
        self.notes_repository.has_notes.return_value = False
        self.notes_repository.read_notes.return_value = None

        result = self.controller.get_notes(1)

        assert result.content == ""
        assert result.has_notes is False

    def test_get_notes_raises_when_task_not_found(self):
        """Test get_notes raises TaskNotFoundException for missing task."""
        self.repository.get_by_id.return_value = None

        with pytest.raises(TaskNotFoundException):
            self.controller.get_notes(999)

    def test_update_notes_writes_and_returns_output(self):
        """Test update_notes writes content and returns NotesOutput."""
        self.repository.get_by_id.return_value = self.task
        self.notes_repository.has_notes.return_value = True

        result = self.controller.update_notes(1, "New content")

        self.notes_repository.write_notes.assert_called_once_with(1, "New content")
        assert result.task_id == 1
        assert result.task_name == "Test Task"
        assert result.content == "New content"
        assert result.has_notes is True

    def test_update_notes_raises_when_task_not_found(self):
        """Test update_notes raises TaskNotFoundException for missing task."""
        self.repository.get_by_id.return_value = None

        with pytest.raises(TaskNotFoundException):
            self.controller.update_notes(999, "content")

        self.notes_repository.write_notes.assert_not_called()

    def test_delete_notes_writes_empty_and_returns_output(self):
        """Test delete_notes clears content and returns NotesOutput."""
        self.repository.get_by_id.return_value = self.task

        result = self.controller.delete_notes(1)

        self.notes_repository.write_notes.assert_called_once_with(1, "")
        assert result.task_id == 1
        assert result.task_name == "Test Task"
        assert result.content == ""
        assert result.has_notes is False

    def test_delete_notes_raises_when_task_not_found(self):
        """Test delete_notes raises TaskNotFoundException for missing task."""
        self.repository.get_by_id.return_value = None

        with pytest.raises(TaskNotFoundException):
            self.controller.delete_notes(999)

        self.notes_repository.write_notes.assert_not_called()
