"""Tests for DTO to Pydantic response model converters."""

from datetime import date, datetime
from unittest.mock import Mock

import pytest

from taskdog_core.application.dto.gantt_output import (
    GanttDateRange,
    GanttOutput,
)
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import (
    GanttTaskDto,
    TaskDetailDto,
)
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_server.api.converters import (
    convert_to_task_detail_response,
    convert_to_task_list_response,
    convert_to_update_task_response,
)


class TestConvertToUpdateTaskResponse:
    """Test cases for convert_to_update_task_response."""

    def test_convert_with_updated_fields(self):
        """Test converting TaskUpdateOutput with updated_fields."""
        # Arrange
        now = datetime.now()
        task = TaskOperationOutput(
            id=1,
            name="Updated Task",
            status=TaskStatus.COMPLETED,
            priority=3,
            deadline=now,
            estimated_duration=10.0,
            planned_start=now,
            planned_end=now,
            actual_start=now,
            actual_end=now,
            actual_duration=9.5,
            depends_on=[],
            tags=["updated"],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=9.5,
            daily_allocations={},
        )
        dto = TaskUpdateOutput(task=task, updated_fields=["name", "priority", "status"])

        # Act
        response = convert_to_update_task_response(dto)

        # Assert
        assert response.id == 1
        assert response.name == "Updated Task"
        assert response.status == TaskStatus.COMPLETED
        assert response.priority == 3
        assert response.updated_fields == ["name", "priority", "status"]

    def test_convert_with_empty_updated_fields(self):
        """Test converting TaskUpdateOutput with no updated fields."""
        # Arrange
        task = TaskOperationOutput(
            id=1,
            name="Test Task",
            status=TaskStatus.PENDING,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            actual_duration=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            daily_allocations={},
        )
        dto = TaskUpdateOutput(task=task, updated_fields=[])

        # Act
        response = convert_to_update_task_response(dto)

        # Assert
        assert response.id == 1
        assert response.updated_fields == []


class TestConvertToTaskListResponse:
    """Test cases for convert_to_task_list_response."""

    def test_convert_empty_list(self):
        """Test converting empty task list."""
        # Arrange
        dto = TaskListOutput(tasks=[], total_count=0, filtered_count=0, gantt_data=None)
        notes_repo = Mock()
        notes_repo.get_task_ids_with_notes = Mock(return_value=set())

        # Act
        response = convert_to_task_list_response(dto, notes_repo)

        # Assert
        assert response.tasks == []
        assert response.total_count == 0
        assert response.filtered_count == 0
        assert response.gantt is None

    def test_convert_task_list_without_gantt(self):
        """Test converting task list without gantt data."""
        # Arrange
        now = datetime.now()
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        dto = TaskListOutput(
            tasks=[task], total_count=10, filtered_count=1, gantt_data=None
        )
        notes_repo = Mock()
        notes_repo.get_task_ids_with_notes = Mock(return_value=set())

        # Act
        response = convert_to_task_list_response(dto, notes_repo)

        # Assert
        assert len(response.tasks) == 1
        assert response.tasks[0].id == 1
        assert response.tasks[0].name == "Test Task"
        assert response.tasks[0].has_notes is False
        assert response.total_count == 10
        assert response.filtered_count == 1
        assert response.gantt is None
        notes_repo.get_task_ids_with_notes.assert_called_once_with([1])

    def test_convert_task_list_with_notes(self):
        """Test converting task list with notes."""
        # Arrange
        now = datetime.now()
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        dto = TaskListOutput(
            tasks=[task], total_count=1, filtered_count=1, gantt_data=None
        )
        notes_repo = Mock()
        notes_repo.get_task_ids_with_notes = Mock(return_value={1})

        # Act
        response = convert_to_task_list_response(dto, notes_repo)

        # Assert
        assert response.tasks[0].has_notes is True

    def test_convert_task_list_with_gantt_data(self):
        """Test converting task list with gantt data."""
        # Arrange
        now = datetime.now()
        task = Task(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        gantt_task = GanttTaskDto(
            id=1,
            name="Test Task",
            status=TaskStatus.PENDING,
            estimated_duration=8.0,
            planned_start=now,
            planned_end=now,
            actual_start=None,
            actual_end=None,
            deadline=None,
            is_finished=False,
        )
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 5)
        gantt_output = GanttOutput(
            date_range=GanttDateRange(start_date=start_date, end_date=end_date),
            tasks=[gantt_task],
            task_daily_hours={1: {date(2025, 1, 1): 4.0, date(2025, 1, 2): 4.0}},
            daily_workload={date(2025, 1, 1): 8.0, date(2025, 1, 2): 8.0},
            holidays={date(2025, 1, 4)},
        )
        dto = TaskListOutput(
            tasks=[task], total_count=1, filtered_count=1, gantt_data=gantt_output
        )
        notes_repo = Mock()
        notes_repo.get_task_ids_with_notes = Mock(return_value=set())

        # Act
        response = convert_to_task_list_response(dto, notes_repo)

        # Assert
        assert response.gantt is not None
        assert response.gantt.date_range.start_date == start_date
        assert response.gantt.date_range.end_date == end_date
        assert len(response.gantt.tasks) == 1
        assert response.gantt.tasks[0].id == 1
        assert response.gantt.tasks[0].name == "Test Task"
        # Check date conversion to ISO strings
        assert "2025-01-01" in response.gantt.task_daily_hours[1]
        assert "2025-01-02" in response.gantt.task_daily_hours[1]
        assert response.gantt.task_daily_hours[1]["2025-01-01"] == 4.0
        assert "2025-01-01" in response.gantt.daily_workload
        assert response.gantt.daily_workload["2025-01-01"] == 8.0
        assert "2025-01-04" in response.gantt.holidays

    def test_convert_multiple_tasks(self):
        """Test converting task list with multiple tasks."""
        # Arrange
        now = datetime.now()
        task1 = Task(
            id=1,
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=2,
            status=TaskStatus.IN_PROGRESS,
            created_at=now,
            updated_at=now,
        )
        dto = TaskListOutput(
            tasks=[task1, task2], total_count=2, filtered_count=2, gantt_data=None
        )
        notes_repo = Mock()
        # Task 1 has notes, task 2 does not
        notes_repo.get_task_ids_with_notes = Mock(return_value={1})

        # Act
        response = convert_to_task_list_response(dto, notes_repo)

        # Assert
        assert len(response.tasks) == 2
        assert response.tasks[0].id == 1
        assert response.tasks[0].has_notes is True
        assert response.tasks[1].id == 2
        assert response.tasks[1].has_notes is False


class TestConvertToTaskDetailResponse:
    """Test cases for convert_to_task_detail_response."""

    def test_convert_minimal_task_detail(self):
        """Test converting task detail with minimal fields."""
        # Arrange
        now = datetime.now()
        task_dto = TaskDetailDto(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=None,
            actual_end=None,
            actual_duration=None,
            estimated_duration=None,
            daily_allocations={},
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            created_at=now,
            updated_at=now,
            actual_duration_hours=None,
            is_active=False,
            is_finished=False,
            can_be_modified=True,
            is_schedulable=True,
        )
        dto = TaskDetailOutput(task=task_dto, notes_content=None, has_notes=False)

        # Act
        response = convert_to_task_detail_response(dto)

        # Assert
        assert response.id == 1
        assert response.name == "Test Task"
        assert response.priority == 1
        assert response.status == TaskStatus.PENDING
        assert response.notes is None
        assert response.daily_allocations == {}

    def test_convert_full_task_detail(self):
        """Test converting task detail with all fields."""
        # Arrange
        now = datetime.now()
        task_dto = TaskDetailDto(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            planned_start=now,
            planned_end=now,
            deadline=now,
            actual_start=now,
            actual_end=None,
            actual_duration=3.5,
            estimated_duration=8.0,
            daily_allocations={date(2025, 1, 1): 4.0, date(2025, 1, 2): 4.0},
            is_fixed=True,
            depends_on=[2, 3],
            tags=["backend", "api"],
            is_archived=False,
            created_at=now,
            updated_at=now,
            actual_duration_hours=3.5,
            is_active=True,
            is_finished=False,
            can_be_modified=True,
            is_schedulable=False,
        )
        dto = TaskDetailOutput(
            task=task_dto, notes_content="# Task Notes\n\nSome notes.", has_notes=True
        )

        # Act
        response = convert_to_task_detail_response(dto)

        # Assert
        assert response.id == 1
        assert response.name == "Test Task"
        assert response.status == TaskStatus.IN_PROGRESS
        assert response.estimated_duration == 8.0
        assert response.depends_on == [2, 3]
        assert response.tags == ["backend", "api"]
        assert response.is_fixed is True
        assert response.notes == "# Task Notes\n\nSome notes."
        # Check date conversion to ISO strings
        assert "2025-01-01" in response.daily_allocations
        assert response.daily_allocations["2025-01-01"] == 4.0

    @pytest.mark.parametrize(
        "scenario,status,expected_active,expected_finished",
        [
            ("is_active", TaskStatus.IN_PROGRESS, True, False),
            ("not_active", TaskStatus.PENDING, False, False),
            ("is_finished", TaskStatus.COMPLETED, False, True),
            ("not_finished", TaskStatus.PENDING, False, False),
        ],
    )
    def test_convert_computed_properties(
        self, scenario, status, expected_active, expected_finished
    ):
        """Test converting task detail with computed properties."""
        # Arrange
        now = datetime.now()
        actual_start = (
            now if status in [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED] else None
        )
        actual_end = now if status == TaskStatus.COMPLETED else None

        task_dto = TaskDetailDto(
            id=1,
            name="Test Task",
            priority=1,
            status=status,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=actual_start,
            actual_end=actual_end,
            actual_duration=None,
            estimated_duration=None,
            daily_allocations={},
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            created_at=now,
            updated_at=now,
            actual_duration_hours=None,
            is_active=expected_active,
            is_finished=expected_finished,
            can_be_modified=not expected_finished,
            is_schedulable=True,
        )
        dto = TaskDetailOutput(task=task_dto, notes_content=None, has_notes=False)

        # Act
        response = convert_to_task_detail_response(dto)

        # Assert
        assert response.is_active == expected_active
        assert response.is_finished == expected_finished

    def test_convert_with_empty_notes(self):
        """Test converting task detail with empty notes."""
        # Arrange
        now = datetime.now()
        task_dto = TaskDetailDto(
            id=1,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=None,
            actual_end=None,
            actual_duration=None,
            estimated_duration=None,
            daily_allocations={},
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            created_at=now,
            updated_at=now,
            actual_duration_hours=None,
            is_active=False,
            is_finished=False,
            can_be_modified=True,
            is_schedulable=True,
        )
        dto = TaskDetailOutput(task=task_dto, notes_content="", has_notes=False)

        # Act
        response = convert_to_task_detail_response(dto)

        # Assert
        assert response.notes == ""
