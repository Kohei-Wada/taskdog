"""Tests for TablePresenter."""

from datetime import datetime, timedelta

import pytest
from fixtures.repositories import InMemoryTaskRepository

from taskdog.presenters.table_presenter import TablePresenter
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus


class TestTablePresenter:
    """Test cases for TablePresenter."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize presenter and repository for each test."""
        self.repository = InMemoryTaskRepository()
        self.presenter = TablePresenter()

    def _to_dto(self, task) -> TaskRowDto:
        """Convert Task entity to TaskRowDto."""
        return TaskRowDto.from_entity(task)

    def test_present_converts_dto_to_view_models(self):
        """Test present converts TaskListOutput to list of TaskRowViewModels."""
        # Create test tasks
        task1 = self._to_dto(
            self.repository.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        )
        task2 = self._to_dto(
            self.repository.create(
                name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS
            )
        )

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

    def test_present_includes_has_notes_from_dto(self):
        """Test present uses has_notes from TaskRowDto."""
        now = datetime.now()
        task_with_notes = TaskRowDto(
            id=1,
            name="Task with notes",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=None,
            actual_end=None,
            estimated_duration=None,
            actual_duration_hours=None,
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            is_finished=False,
            created_at=now,
            updated_at=now,
            has_notes=True,
        )

        output = TaskListOutput(
            tasks=[task_with_notes], total_count=1, filtered_count=1
        )
        view_models = self.presenter.present(output)

        assert len(view_models) == 1
        assert view_models[0].has_notes is True

    def test_present_copies_task_fields(self):
        """Test present copies all relevant task fields to view model."""
        # Create test task with all fields
        now = datetime.now()
        deadline = now + timedelta(days=7)
        planned_start = now + timedelta(days=1)
        planned_end = now + timedelta(days=3)

        task = self._to_dto(
            self.repository.create(
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
        )

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

    def test_present_sets_is_finished_for_completed_task(self):
        """Test present sets is_finished=True for completed tasks."""
        # Create completed task
        task = self._to_dto(
            self.repository.create(
                name="Completed task", priority=1, status=TaskStatus.COMPLETED
            )
        )

        # Create DTO
        output = TaskListOutput(tasks=[task], total_count=1, filtered_count=1)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify is_finished is True
        assert view_models[0].is_finished is True

    def test_present_sets_is_finished_for_canceled_task(self):
        """Test present sets is_finished=True for canceled tasks."""
        # Create canceled task
        task = self._to_dto(
            self.repository.create(
                name="Canceled task", priority=1, status=TaskStatus.CANCELED
            )
        )

        # Create DTO
        output = TaskListOutput(tasks=[task], total_count=1, filtered_count=1)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify is_finished is True
        assert view_models[0].is_finished is True

    def test_present_copies_dependencies_and_tags(self):
        """Test present creates copies of depends_on and tags lists."""
        # Create task with dependencies and tags
        task = self._to_dto(
            self.repository.create(
                name="Task",
                priority=1,
                depends_on=[1, 2],
                tags=["tag1", "tag2"],
            )
        )

        # Create DTO
        output = TaskListOutput(tasks=[task], total_count=1, filtered_count=1)

        # Convert to view models
        view_models = self.presenter.present(output)

        # Verify lists are copied (not the same object)
        assert view_models[0].depends_on == [1, 2]
        assert view_models[0].tags == ["tag1", "tag2"]
        assert view_models[0].depends_on is not task.depends_on
        assert view_models[0].tags is not task.tags
