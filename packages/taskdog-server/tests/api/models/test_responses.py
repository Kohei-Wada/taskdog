"""Tests for Pydantic response models."""

import unittest
from datetime import date, datetime

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


class TestTaskOperationResponse(unittest.TestCase):
    """Test cases for TaskOperationResponse model."""

    def test_create_response_with_minimal_data(self):
        """Test creating response with minimal required fields."""
        # Act
        response = TaskOperationResponse(
            id=1, name="Test Task", status=TaskStatus.PENDING, priority=3
        )

        # Assert
        self.assertEqual(response.id, 1)
        self.assertEqual(response.name, "Test Task")
        self.assertEqual(response.status, TaskStatus.PENDING)
        self.assertEqual(response.priority, 3)
        self.assertEqual(response.depends_on, [])
        self.assertEqual(response.tags, [])
        self.assertEqual(response.is_fixed, False)
        self.assertEqual(response.is_archived, False)

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
            actual_daily_hours={"2024-01-15": 8.5},
        )

        # Assert
        self.assertEqual(response.id, 1)
        self.assertEqual(response.status, TaskStatus.COMPLETED)
        self.assertEqual(response.depends_on, [2, 3])
        self.assertEqual(response.tags, ["backend", "api"])
        self.assertEqual(response.is_fixed, True)
        self.assertEqual(response.actual_duration_hours, 8.5)


class TestUpdateTaskResponse(unittest.TestCase):
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
        self.assertEqual(response.id, 1)
        self.assertEqual(response.updated_fields, ["name", "priority"])


class TestTaskResponse(unittest.TestCase):
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
        self.assertEqual(response.id, 1)
        self.assertEqual(response.name, "Test Task")
        self.assertEqual(response.is_finished, False)
        self.assertEqual(response.has_notes, False)

    def test_response_is_frozen(self):
        """Test that response model is immutable."""
        # Arrange
        from pydantic import ValidationError

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
        with self.assertRaises(ValidationError):
            response.name = "Changed"


class TestTaskDetailResponse(unittest.TestCase):
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
            actual_daily_hours={"2024-01-15": 3.5},
            is_active=False,
            is_finished=False,
            can_be_modified=True,
            is_schedulable=True,
            notes="# Test Notes",
            created_at=now,
            updated_at=now,
        )

        # Assert
        self.assertEqual(response.id, 1)
        self.assertEqual(
            response.daily_allocations, {"2024-01-15": 4.0, "2024-01-16": 4.0}
        )
        self.assertEqual(response.notes, "# Test Notes")
        self.assertEqual(response.is_schedulable, True)


class TestTaskListResponse(unittest.TestCase):
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
        self.assertEqual(len(response.tasks), 1)
        self.assertEqual(response.total_count, 100)
        self.assertEqual(response.filtered_count, 1)
        self.assertIsNone(response.gantt)


class TestGanttResponse(unittest.TestCase):
    """Test cases for Gantt chart response models."""

    def test_create_gantt_date_range(self):
        """Test creating Gantt date range."""
        # Arrange
        start = date(2024, 1, 15)
        end = date(2024, 1, 20)

        # Act
        range_obj = GanttDateRange(start_date=start, end_date=end)

        # Assert
        self.assertEqual(range_obj.start_date, start)
        self.assertEqual(range_obj.end_date, end)

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
        self.assertEqual(task.id, 1)
        self.assertEqual(task.daily_allocations, {"2024-01-15": 4.0, "2024-01-16": 4.0})

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
        self.assertEqual(response.date_range.start_date, start)
        self.assertEqual(response.daily_workload["2024-01-15"], 8.0)
        self.assertEqual(response.holidays, ["2024-01-16"])


class TestStatisticsResponses(unittest.TestCase):
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
        self.assertEqual(stats.total, 100)
        self.assertEqual(stats.completed, 60)
        self.assertEqual(stats.completion_rate, 0.6)

    def test_time_statistics(self):
        """Test time statistics model."""
        # Act
        stats = TimeStatistics(
            total_logged_hours=160.0,
            average_task_duration=8.0,
            total_estimated_hours=200.0,
        )

        # Assert
        self.assertEqual(stats.total_logged_hours, 160.0)
        self.assertEqual(stats.average_task_duration, 8.0)

    def test_estimation_statistics(self):
        """Test estimation statistics model."""
        # Act
        stats = EstimationStatistics(
            average_deviation=2.5,
            average_deviation_percentage=15.0,
            tasks_with_estimates=50,
        )

        # Assert
        self.assertEqual(stats.average_deviation, 2.5)
        self.assertEqual(stats.tasks_with_estimates, 50)

    def test_deadline_statistics(self):
        """Test deadline statistics model."""
        # Act
        stats = DeadlineStatistics(met=45, missed=5, no_deadline=50, adherence_rate=0.9)

        # Assert
        self.assertEqual(stats.met, 45)
        self.assertEqual(stats.missed, 5)
        self.assertEqual(stats.adherence_rate, 0.9)

    def test_priority_distribution(self):
        """Test priority distribution model."""
        # Act
        dist = PriorityDistribution(distribution={1: 10, 2: 20, 3: 30})

        # Assert
        self.assertEqual(dist.distribution[1], 10)
        self.assertEqual(dist.distribution[3], 30)

    def test_trend_data(self):
        """Test trend data model."""
        # Act
        trends = TrendData(
            completed_per_day={"2024-01-15": 5, "2024-01-16": 3},
            hours_per_day={"2024-01-15": 8.0, "2024-01-16": 6.5},
        )

        # Assert
        self.assertEqual(trends.completed_per_day["2024-01-15"], 5)
        self.assertEqual(trends.hours_per_day["2024-01-16"], 6.5)

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
        self.assertEqual(response.completion.total, 100)
        self.assertIsNone(response.time)
        self.assertIsNone(response.estimation)


class TestTagStatisticsResponses(unittest.TestCase):
    """Test cases for tag statistics response models."""

    def test_tag_statistics_item(self):
        """Test tag statistics item model."""
        # Act
        item = TagStatisticsItem(tag="backend", count=25, completion_rate=0.8)

        # Assert
        self.assertEqual(item.tag, "backend")
        self.assertEqual(item.count, 25)
        self.assertEqual(item.completion_rate, 0.8)

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
        self.assertEqual(len(response.tags), 2)
        self.assertEqual(response.total_tags, 2)
        self.assertEqual(response.tags[0].tag, "backend")


class TestOptimizationResponses(unittest.TestCase):
    """Test cases for optimization response models."""

    def test_scheduling_failure(self):
        """Test scheduling failure model."""
        # Act
        failure = SchedulingFailure(
            task_id=1, task_name="Failed Task", reason="Insufficient time"
        )

        # Assert
        self.assertEqual(failure.task_id, 1)
        self.assertEqual(failure.task_name, "Failed Task")
        self.assertEqual(failure.reason, "Insufficient time")

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
        self.assertEqual(summary.total_tasks, 10)
        self.assertEqual(summary.scheduled_tasks, 8)
        self.assertEqual(summary.algorithm, "greedy")

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
        self.assertEqual(response.summary.total_tasks, 10)
        self.assertEqual(len(response.failures), 1)
        self.assertIn("Partially optimized", response.message)


class TestNotesResponse(unittest.TestCase):
    """Test cases for notes response model."""

    def test_notes_response_with_content(self):
        """Test notes response with content."""
        # Act
        response = NotesResponse(
            task_id=1, content="# Test Notes\n\nSome content.", has_notes=True
        )

        # Assert
        self.assertEqual(response.task_id, 1)
        self.assertEqual(response.content, "# Test Notes\n\nSome content.")
        self.assertEqual(response.has_notes, True)

    def test_notes_response_empty(self):
        """Test notes response with no content."""
        # Act
        response = NotesResponse(task_id=1, content="", has_notes=False)

        # Assert
        self.assertEqual(response.task_id, 1)
        self.assertEqual(response.content, "")
        self.assertEqual(response.has_notes, False)


if __name__ == "__main__":
    unittest.main()
