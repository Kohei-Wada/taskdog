"""Tests for GetTaskDetailUseCase."""

from datetime import datetime

import pytest

from taskdog_core.application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException
from taskdog_core.infrastructure.persistence.database.sqlite_notes_repository import (
    SqliteNotesRepository,
)
from tests.helpers.time_provider import FakeTimeProvider


class TestGetTaskDetailUseCase:
    """Test cases for GetTaskDetailUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.time_provider = FakeTimeProvider()
        self.notes_repository = SqliteNotesRepository(
            "sqlite:///:memory:", self.time_provider
        )
        self.use_case = GetTaskDetailUseCase(self.repository, self.notes_repository)

    @pytest.fixture(autouse=True)
    def teardown(self, request):
        """Clean up notes repository after each test."""

        def cleanup():
            if hasattr(self, "notes_repository"):
                self.notes_repository.clear()

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

    def test_execute_with_notes(self):
        """Test execute returns notes content when notes exist."""
        task = self.repository.create(name="Test Task", priority=1)

        # Create notes using NotesRepository
        notes_content = "# Test Notes\n\nThis is a test note."
        self.notes_repository.write_notes(task.id, notes_content)

        input_dto = GetTaskDetailInput(task.id)
        result = self.use_case.execute(input_dto)

        assert result.has_notes is True
        assert result.notes_content == notes_content

    def test_execute_without_notes(self):
        """Test execute handles missing notes gracefully."""
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
