"""Tests for Pydantic response models."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_server.api.models.responses import (
    CompletionStatistics,
    DeadlineStatistics,
    EstimationStatistics,
    GanttDateRange,
    GanttResponse,
    GanttTaskResponse,
    NotesResponse,
    OptimizationResponse,
    OptimizationSummary,
    PriorityDistribution,
    SchedulingFailure,
    StatisticsResponse,
    TagStatisticsItem,
    TagStatisticsResponse,
    TaskDetailResponse,
    TaskListResponse,
    TaskOperationResponse,
    TaskResponse,
    TimeStatistics,
    TrendData,
    UpdateTaskResponse,
)


class TestTaskOperationResponse:
    """Test cases for TaskOperationResponse model."""

    def test_create_response_with_minimal_data(self):
        """Test creating response with minimal required fields."""
        # Act
        response = TaskOperationResponse(
            id=1, name="Test Task", status=TaskStatus.PENDING, priority=3
        )

        # Assert
        assert response.id == 1
        assert response.name == "Test Task"
        assert response.status == TaskStatus.PENDING
        assert response.priority == 3
        assert response.depends_on == []
        assert response.tags == []
        assert response.is_fixed is False
        assert response.is_archived is False

    def test_create_response_with_full_data(self):
        """Test creating response with all fields."""
        # Arrange
        now = datetime.now()

        # Act
        response = TaskOperationResponse(
            id=1,
            name="Test Task",
            status=TaskStatus.COMPLETED,
            priority=1,
            deadline=now,
            estimated_duration=8.0,
            planned_start=now,
            planned_end=now,
            actual_start=now,
            actual_end=now,
            depends_on=[2, 3],
            tags=["backend", "api"],
            is_fixed=True,
            is_archived=False,
            actual_duration_hours=8.5,
        )

        # Assert
        assert response.id == 1
        assert response.status == TaskStatus.COMPLETED
        assert response.depends_on == [2, 3]
        assert response.tags == ["backend", "api"]
        assert response.is_fixed is True
        assert response.actual_duration_hours == 8.5

    def test_from_dto_converts_task_operation_output(self):
        """Test from_dto creates response from TaskOperationOutput."""
        # Arrange
        now = datetime.now()
        dto = TaskOperationOutput(
            id=1,
            name="Test Task",
            status=TaskStatus.IN_PROGRESS,
            priority=2,
            deadline=now,
            estimated_duration=4.0,
            planned_start=now,
            planned_end=now,
            actual_start=now,
            actual_end=None,
            depends_on=[3],
            tags=["urgent"],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=2.5,
            daily_allocations={},
        )

        # Act
        response = TaskOperationResponse.from_dto(dto)

        # Assert
        assert response.id == dto.id
        assert response.name == dto.name
        assert response.status == dto.status
        assert response.priority == dto.priority
        assert response.deadline == dto.deadline
        assert response.estimated_duration == dto.estimated_duration
        assert response.depends_on == dto.depends_on
        assert response.tags == dto.tags
        assert response.actual_duration_hours == dto.actual_duration_hours


class TestUpdateTaskResponse:
    """Test cases for UpdateTaskResponse model."""

    def test_create_response_with_updated_fields(self):
        """Test creating response with updated fields list."""
        # Act
        response = UpdateTaskResponse(
            id=1,
            name="Test Task",
            status=TaskStatus.PENDING,
            priority=3,
            updated_fields=["name", "priority"],
        )

        # Assert
        assert response.id == 1
        assert response.updated_fields == ["name", "priority"]

    def test_from_dto_converts_task_update_output(self):
        """Test from_dto creates response from TaskUpdateOutput."""
        # Arrange
        now = datetime.now()
        task = TaskOperationOutput(
            id=1,
            name="Updated Task",
            status=TaskStatus.PENDING,
            priority=5,
            deadline=now,
            estimated_duration=8.0,
            planned_start=now,
            planned_end=now,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=["refactored"],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            daily_allocations={},
        )
        dto = TaskUpdateOutput(task=task, updated_fields=["name", "priority", "tags"])

        # Act
        response = UpdateTaskResponse.from_dto(dto)

        # Assert
        assert response.id == task.id
        assert response.name == task.name
        assert response.priority == task.priority
        assert response.tags == task.tags
        assert response.updated_fields == ["name", "priority", "tags"]


class TestTaskResponse:
    """Test cases for TaskResponse model."""

    def test_create_response_with_required_fields(self):
        """Test creating task list response."""
        # Arrange
        now = datetime.now()

        # Act
        response = TaskResponse(
            id=1,
            name="Test Task",
            priority=3,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        # Assert
        assert response.id == 1
        assert response.name == "Test Task"
        assert response.is_finished is False
        assert response.has_notes is False

    def test_response_is_frozen(self):
        """Test that response model is immutable."""
        # Arrange
        now = datetime.now()
        response = TaskResponse(
            id=1,
            name="Test Task",
            priority=3,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            response.name = "Changed"


class TestTaskDetailResponse:
    """Test cases for TaskDetailResponse model."""

    def test_create_detail_response(self):
        """Test creating detailed task response."""
        # Arrange
        now = datetime.now()

        # Act
        response = TaskDetailResponse(
            id=1,
            name="Test Task",
            priority=3,
            status=TaskStatus.PENDING,
            daily_allocations={"2024-01-15": 4.0, "2024-01-16": 4.0},
            is_active=False,
            is_finished=False,
            can_be_modified=True,
            is_schedulable=True,
            notes="# Test Notes",
            created_at=now,
            updated_at=now,
        )

        # Assert
        assert response.id == 1
        assert response.daily_allocations == {"2024-01-15": 4.0, "2024-01-16": 4.0}
        assert response.notes == "# Test Notes"
        assert response.is_schedulable is True

    def test_from_dto_converts_task_detail_output(self):
        """Test from_dto creates response from TaskDetailOutput."""
        # Arrange
        now = datetime.now()
        task_dto = TaskDetailDto(
            id=1,
            name="Detailed Task",
            priority=2,
            status=TaskStatus.IN_PROGRESS,
            planned_start=now,
            planned_end=now,
            deadline=now,
            actual_start=now,
            actual_end=None,
            estimated_duration=8.0,
            daily_allocations={date(2024, 1, 15): 4.0, date(2024, 1, 16): 4.0},
            is_fixed=False,
            depends_on=[2, 3],
            tags=["backend"],
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
            task=task_dto, notes_content="# Notes Content", has_notes=True
        )

        # Act
        response = TaskDetailResponse.from_dto(dto)

        # Assert
        assert response.id == task_dto.id
        assert response.name == task_dto.name
        assert response.status == task_dto.status
        assert response.priority == task_dto.priority
        assert response.depends_on == task_dto.depends_on
        assert response.tags == task_dto.tags
        assert response.is_active == task_dto.is_active
        assert response.is_schedulable == task_dto.is_schedulable
        assert response.notes == "# Notes Content"
        # Check date dict conversion (date -> ISO string)
        assert response.daily_allocations == {"2024-01-15": 4.0, "2024-01-16": 4.0}


class TestTaskListResponse:
    """Test cases for TaskListResponse model."""

    def test_create_list_response(self):
        """Test creating task list response."""
        # Arrange
        now = datetime.now()
        task = TaskResponse(
            id=1,
            name="Task 1",
            priority=3,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        # Act
        response = TaskListResponse(tasks=[task], total_count=100, filtered_count=1)

        # Assert
        assert len(response.tasks) == 1
        assert response.total_count == 100
        assert response.filtered_count == 1
        assert response.gantt is None


class TestGanttResponse:
    """Test cases for Gantt chart response models."""

    def test_create_gantt_date_range(self):
        """Test creating Gantt date range."""
        # Arrange
        start = date(2024, 1, 15)
        end = date(2024, 1, 20)

        # Act
        range_obj = GanttDateRange(start_date=start, end_date=end)

        # Assert
        assert range_obj.start_date == start
        assert range_obj.end_date == end

    def test_create_gantt_task_response(self):
        """Test creating Gantt task response."""
        # Arrange
        now = datetime.now()

        # Act
        task = GanttTaskResponse(
            id=1,
            name="Test Task",
            status=TaskStatus.PENDING,
            estimated_duration=8.0,
            planned_start=now,
            planned_end=now,
            daily_allocations={"2024-01-15": 4.0, "2024-01-16": 4.0},
        )

        # Assert
        assert task.id == 1
        assert task.daily_allocations == {"2024-01-15": 4.0, "2024-01-16": 4.0}

    def test_create_gantt_response(self):
        """Test creating complete Gantt response."""
        # Arrange
        start = date(2024, 1, 15)
        end = date(2024, 1, 20)
        date_range = GanttDateRange(start_date=start, end_date=end)

        # Act
        response = GanttResponse(
            date_range=date_range,
            tasks=[],
            task_daily_hours={1: {"2024-01-15": 4.0}},
            daily_workload={"2024-01-15": 8.0, "2024-01-16": 6.0},
            holidays=["2024-01-16"],
        )

        # Assert
        assert response.date_range.start_date == start
        assert response.daily_workload["2024-01-15"] == 8.0
        assert response.holidays == ["2024-01-16"]


class TestStatisticsResponses:
    """Test cases for statistics response models."""

    def test_completion_statistics(self):
        """Test completion statistics model."""
        # Act
        stats = CompletionStatistics(
            total=100,
            completed=60,
            in_progress=20,
            pending=15,
            canceled=5,
            completion_rate=0.6,
        )

        # Assert
        assert stats.total == 100
        assert stats.completed == 60
        assert stats.completion_rate == 0.6

    def test_time_statistics(self):
        """Test time statistics model."""
        # Act
        stats = TimeStatistics(
            total_logged_hours=160.0,
            average_task_duration=8.0,
            total_estimated_hours=200.0,
        )

        # Assert
        assert stats.total_logged_hours == 160.0
        assert stats.average_task_duration == 8.0

    def test_estimation_statistics(self):
        """Test estimation statistics model."""
        # Act
        stats = EstimationStatistics(
            average_deviation=2.5,
            average_deviation_percentage=15.0,
            tasks_with_estimates=50,
        )

        # Assert
        assert stats.average_deviation == 2.5
        assert stats.tasks_with_estimates == 50

    def test_deadline_statistics(self):
        """Test deadline statistics model."""
        # Act
        stats = DeadlineStatistics(met=45, missed=5, no_deadline=50, adherence_rate=0.9)

        # Assert
        assert stats.met == 45
        assert stats.missed == 5
        assert stats.adherence_rate == 0.9

    def test_priority_distribution(self):
        """Test priority distribution model."""
        # Act
        dist = PriorityDistribution(distribution={1: 10, 2: 20, 3: 30})

        # Assert
        assert dist.distribution[1] == 10
        assert dist.distribution[3] == 30

    def test_trend_data(self):
        """Test trend data model."""
        # Act
        trends = TrendData(
            completed_per_day={"2024-01-15": 5, "2024-01-16": 3},
            hours_per_day={"2024-01-15": 8.0, "2024-01-16": 6.5},
        )

        # Assert
        assert trends.completed_per_day["2024-01-15"] == 5
        assert trends.hours_per_day["2024-01-16"] == 6.5

    def test_statistics_response(self):
        """Test complete statistics response."""
        # Arrange
        completion = CompletionStatistics(
            total=100,
            completed=60,
            in_progress=20,
            pending=15,
            canceled=5,
            completion_rate=0.6,
        )
        priority = PriorityDistribution(distribution={1: 10, 2: 20, 3: 30})

        # Act
        response = StatisticsResponse(completion=completion, priority=priority)

        # Assert
        assert response.completion.total == 100
        assert response.time is None
        assert response.estimation is None


class TestTagStatisticsResponses:
    """Test cases for tag statistics response models."""

    def test_tag_statistics_item(self):
        """Test tag statistics item model."""
        # Act
        item = TagStatisticsItem(tag="backend", count=25, completion_rate=0.8)

        # Assert
        assert item.tag == "backend"
        assert item.count == 25
        assert item.completion_rate == 0.8

    def test_tag_statistics_response(self):
        """Test tag statistics response model."""
        # Arrange
        items = [
            TagStatisticsItem(tag="backend", count=25, completion_rate=0.8),
            TagStatisticsItem(tag="frontend", count=15, completion_rate=0.6),
        ]

        # Act
        response = TagStatisticsResponse(tags=items, total_tags=2)

        # Assert
        assert len(response.tags) == 2
        assert response.total_tags == 2
        assert response.tags[0].tag == "backend"


class TestOptimizationResponses:
    """Test cases for optimization response models."""

    def test_scheduling_failure(self):
        """Test scheduling failure model."""
        # Act
        failure = SchedulingFailure(
            task_id=1, task_name="Failed Task", reason="Insufficient time"
        )

        # Assert
        assert failure.task_id == 1
        assert failure.task_name == "Failed Task"
        assert failure.reason == "Insufficient time"

    def test_optimization_summary(self):
        """Test optimization summary model."""
        # Arrange
        start = date(2024, 1, 15)
        end = date(2024, 1, 20)

        # Act
        summary = OptimizationSummary(
            total_tasks=10,
            scheduled_tasks=8,
            failed_tasks=2,
            total_hours=64.0,
            start_date=start,
            end_date=end,
            algorithm="greedy",
        )

        # Assert
        assert summary.total_tasks == 10
        assert summary.scheduled_tasks == 8
        assert summary.algorithm == "greedy"

    def test_optimization_response(self):
        """Test optimization response model."""
        # Arrange
        summary = OptimizationSummary(
            total_tasks=10,
            scheduled_tasks=8,
            failed_tasks=2,
            total_hours=64.0,
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 20),
            algorithm="greedy",
        )
        failures = [
            SchedulingFailure(task_id=1, task_name="Task 1", reason="Insufficient time")
        ]

        # Act
        response = OptimizationResponse(
            summary=summary,
            failures=failures,
            message="Partially optimized: 8 succeeded, 2 failed.",
        )

        # Assert
        assert response.summary.total_tasks == 10
        assert len(response.failures) == 1
        assert "Partially optimized" in response.message


class TestNotesResponse:
    """Test cases for notes response model."""

    def test_notes_response_with_content(self):
        """Test notes response with content."""
        # Act
        response = NotesResponse(
            task_id=1, content="# Test Notes\n\nSome content.", has_notes=True
        )

        # Assert
        assert response.task_id == 1
        assert response.content == "# Test Notes\n\nSome content."
        assert response.has_notes is True

    def test_notes_response_empty(self):
        """Test notes response with no content."""
        # Act
        response = NotesResponse(task_id=1, content="", has_notes=False)

        # Assert
        assert response.task_id == 1
        assert response.content == ""
        assert response.has_notes is False
