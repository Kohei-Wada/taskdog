"""Tests for TablePresenter."""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from taskdog.presenters.table_presenter import TablePresenter
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestTablePresenter:
    """Test cases for TablePresenter."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create temporary file and initialize presenter for each test."""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".db"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = SqliteTaskRepository(f"sqlite:///{self.test_filename}")
        self.notes_checker = Mock()
        self.notes_checker.has_task_notes = Mock(return_value=False)
        self.presenter = TablePresenter(self.notes_checker)
        yield
        # Teardown
        if hasattr(self, "repository") and hasattr(self.repository, "close"):
            self.repository.close()
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_present_converts_dto_to_view_models(self):
        """Test present converts TaskListOutput to list of TaskRowViewModels."""
        # Create test tasks
        task1 = self.repository.create(
            name="Task 1", priority=1, status=TaskStatus.PENDING
        )
        task2 = self.repository.create(
            name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS
        )

        # Mock notes checker
        self.notes_checker.has_task_notes.return_value = False

        # Create DTO
        output = TaskListOutput(tasks=[task1, task2], total_count=2, filtered_count=2)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify result
        assert len(view_models) == 2
        assert view_models[0].id == task1.id
        assert view_models[0].name == "Task 1"
        assert view_models[0].status == TaskStatus.PENDING
        assert view_models[1].id == task2.id
        assert view_models[1].name == "Task 2"
        assert view_models[1].status == TaskStatus.IN_PROGRESS

    def test_present_includes_notes_flag(self):
        """Test present includes has_notes flag from notes repository."""
        # Create test task
        task = self.repository.create(name="Task with notes", priority=1)

        # Mock notes repository to return True for this task
        self.notes_checker.has_task_notes.return_value = True

        # Create DTO
        output = TaskListOutput(tasks=[task], total_count=1, filtered_count=1)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify has_notes is True
        assert len(view_models) == 1
        assert view_models[0].has_notes is True
        self.notes_checker.has_task_notes.assert_called_once_with(task.id)

    def test_present_copies_task_fields(self):
        """Test present copies all relevant task fields to view model."""
        # Create test task with all fields
        now = datetime.now()
        deadline = now + timedelta(days=7)
        planned_start = now + timedelta(days=1)
        planned_end = now + timedelta(days=3)

        task = self.repository.create(
            name="Full task",
            priority=5,
            status=TaskStatus.PENDING,
            is_fixed=True,
            estimated_duration=8.0,
            deadline=deadline,
            planned_start=planned_start,
            planned_end=planned_end,
            depends_on=[1, 2, 3],
            tags=["urgent", "backend"],
        )

        # Mock notes checker
        self.notes_checker.has_task_notes.return_value = False

        # Create DTO
        output = TaskListOutput(tasks=[task], total_count=1, filtered_count=1)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify all fields are copied
        vm = view_models[0]
        assert vm.id == task.id
        assert vm.name == "Full task"
        assert vm.priority == 5
        assert vm.is_fixed is True
        assert vm.estimated_duration == 8.0
        assert vm.deadline == deadline
        assert vm.planned_start == planned_start
        assert vm.planned_end == planned_end
        assert vm.depends_on == [1, 2, 3]
        assert vm.tags == ["urgent", "backend"]
        assert vm.is_finished is False

    def test_present_handles_empty_dto(self):
        """Test present handles empty TaskListOutput."""
        # Create empty DTO
        output = TaskListOutput(tasks=[], total_count=0, filtered_count=0)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify empty list
        assert len(view_models) == 0

    @pytest.mark.parametrize(
        "status",
        [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELED,
        ],
        ids=["pending", "in_progress", "completed", "canceled"],
    )
    def test_convert_status_maps_domain_to_presentation(self, status):
        """Test convert_status maps domain status to presentation status."""
        assert TablePresenter.convert_status(status) == status

    def test_present_sets_is_finished_for_completed_task(self):
        """Test present sets is_finished=True for completed tasks."""
        # Create completed task
        task = self.repository.create(
            name="Completed task", priority=1, status=TaskStatus.COMPLETED
        )

        # Mock notes checker
        self.notes_checker.has_task_notes.return_value = False

        # Create DTO
        output = TaskListOutput(tasks=[task], total_count=1, filtered_count=1)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify is_finished is True
        assert view_models[0].is_finished is True

    def test_present_sets_is_finished_for_canceled_task(self):
        """Test present sets is_finished=True for canceled tasks."""
        # Create canceled task
        task = self.repository.create(
            name="Canceled task", priority=1, status=TaskStatus.CANCELED
        )

        # Mock notes checker
        self.notes_checker.has_task_notes.return_value = False

        # Create DTO
        output = TaskListOutput(tasks=[task], total_count=1, filtered_count=1)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify is_finished is True
        assert view_models[0].is_finished is True

    def test_present_copies_dependencies_and_tags(self):
        """Test present creates copies of depends_on and tags lists."""
        # Create task with dependencies and tags
        task = self.repository.create(
            name="Task",
            priority=1,
            depends_on=[1, 2],
            tags=["tag1", "tag2"],
        )

        # Mock notes checker
        self.notes_checker.has_task_notes.return_value = False

        # Create DTO
        output = TaskListOutput(tasks=[task], total_count=1, filtered_count=1)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify lists are copied (not the same object)
        assert view_models[0].depends_on == [1, 2]
        assert view_models[0].tags == ["tag1", "tag2"]
        assert view_models[0].depends_on is not task.depends_on
        assert view_models[0].tags is not task.tags
