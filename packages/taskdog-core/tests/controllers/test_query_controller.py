"""Tests for QueryController."""

from datetime import date, datetime, timedelta

import pytest

from taskdog_core.application.dto.query_inputs import ListTasksInput
from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.domain.entities.task import TaskStatus
from tests.helpers.time_provider import FakeTimeProvider


class TestQueryController:
    """Test cases for QueryController."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize controller for each test."""
        self.repository = repository
        self.controller = QueryController(self.repository, None, FakeTimeProvider())

    def test_list_tasks_returns_output_dto(self):
        """Test list_tasks returns TaskListOutput with correct structure."""
        # Create test tasks
        self.repository.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        self.repository.create(name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS)

        # Get task list using Input DTO
        input_dto = ListTasksInput(include_archived=True)
        result = self.controller.list_tasks(input_dto)

        # Verify result structure
        assert len(result.tasks) == 2
        assert result.total_count == 2
        assert result.filtered_count == 2

    def test_list_tasks_with_filter(self):
        """Test list_tasks applies filter correctly."""
        # Create test tasks with different statuses
        self.repository.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        self.repository.create(name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS)
        self.repository.create(name="Task 3", priority=3, status=TaskStatus.COMPLETED)

        # Filter for PENDING tasks only using Input DTO
        input_dto = ListTasksInput(include_archived=True, status="PENDING")
        result = self.controller.list_tasks(input_dto)

        # Verify filtering
        assert len(result.tasks) == 1
        assert result.tasks[0].name == "Task 1"
        assert result.total_count == 3
        assert result.filtered_count == 1

    def test_get_tasks_by_ids_returns_found_tasks_in_input_order(self):
        """get_tasks_by_ids returns requested tasks preserving input id order."""
        t1 = self.repository.create(name="Task 1", priority=1)
        t2 = self.repository.create(name="Task 2", priority=2)
        t3 = self.repository.create(name="Task 3", priority=3)

        result = self.controller.get_tasks_by_ids([t3.id, t1.id, t2.id])

        assert [t.id for t in result.tasks] == [t3.id, t1.id, t2.id]
        assert result.total_count == 3
        assert result.filtered_count == 3

    def test_get_tasks_by_ids_skips_missing_ids(self):
        """Missing ids are silently skipped, not raised."""
        t1 = self.repository.create(name="Task 1", priority=1)

        result = self.controller.get_tasks_by_ids([t1.id, 9999])

        assert [t.id for t in result.tasks] == [t1.id]
        assert result.filtered_count == 1

    def test_get_tasks_by_ids_empty_input(self):
        """Empty id list returns an empty result."""
        result = self.controller.get_tasks_by_ids([])

        assert result.tasks == []
        assert result.total_count == 0

    def test_list_tasks_with_sorting(self):
        """Test list_tasks sorts correctly."""
        # Create test tasks with different priorities
        self.repository.create(name="Low", priority=1, status=TaskStatus.PENDING)
        self.repository.create(name="High", priority=10, status=TaskStatus.PENDING)
        self.repository.create(name="Medium", priority=5, status=TaskStatus.PENDING)

        # Sort by priority using Input DTO (higher priority first)
        input_dto = ListTasksInput(
            include_archived=True, sort_by="priority", reverse=False
        )
        result = self.controller.list_tasks(input_dto)

        # Verify sorting (High=10, Medium=5, Low=1)
        assert result.tasks[0].name == "High"
        assert result.tasks[1].name == "Medium"
        assert result.tasks[2].name == "Low"

    def test_list_tasks_with_composite_filter(self):
        """Test list_tasks with combined filters via Input DTO."""
        # Create test tasks
        self.repository.create(
            name="Active", priority=1, status=TaskStatus.PENDING, is_archived=False
        )
        self.repository.create(
            name="Archived", priority=2, status=TaskStatus.PENDING, is_archived=True
        )

        # Use Input DTO with status and non-archived filter
        input_dto = ListTasksInput(include_archived=False, status="PENDING")
        result = self.controller.list_tasks(input_dto)

        # Verify filtering
        assert len(result.tasks) == 1
        assert result.tasks[0].name == "Active"

    def test_list_tasks_with_gantt_returns_shared_tasks_and_overlay(self):
        """include_gantt yields the shared task list plus a Gantt overlay."""
        # Create test task with schedule
        today = date.today()
        self.repository.create(
            name="Scheduled Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
            estimated_duration=16.0,
        )

        input_dto = ListTasksInput(include_archived=True)
        result = self.controller.list_tasks(input_dto, include_gantt=True)

        # Tasks come from the shared list; overlay carries Gantt-only data
        assert len(result.tasks) == 1
        assert result.gantt_data is not None
        assert result.gantt_data.date_range is not None

    def test_list_tasks_with_gantt_date_range(self):
        """Chart date range drives the overlay date range."""
        # Create test task
        today = date.today()
        self.repository.create(
            name="Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
        )

        start_date = today
        end_date = today + timedelta(days=5)
        input_dto = ListTasksInput(include_archived=True)
        result = self.controller.list_tasks(
            input_dto,
            include_gantt=True,
            gantt_start_date=start_date,
            gantt_end_date=end_date,
        )

        # Verify date range
        assert result.gantt_data.date_range.start_date == start_date
        assert result.gantt_data.date_range.end_date == end_date

    def test_list_tasks_with_gantt_calculates_total_estimated_duration(self):
        """Overlay total_estimated_duration sums task estimates."""
        # Create test tasks with different estimated durations
        today = date.today()
        self.repository.create(
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
            estimated_duration=8.0,
        )
        self.repository.create(
            name="Task 2",
            priority=2,
            status=TaskStatus.IN_PROGRESS,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=1), datetime.min.time()
            ),
            estimated_duration=16.5,
        )
        self.repository.create(
            name="Task 3",
            priority=3,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=3), datetime.min.time()
            ),
            # No estimated_duration - should be ignored in calculation
        )

        input_dto = ListTasksInput(include_archived=True)
        result = self.controller.list_tasks(input_dto, include_gantt=True)

        # Verify total_estimated_duration (8.0 + 16.5 = 24.5)
        assert result.gantt_data.total_estimated_duration == 24.5
        assert len(result.tasks) == 3

    def test_list_tasks_with_gantt_total_estimated_duration_zero_when_no_estimates(
        self,
    ):
        """Overlay total is zero when no tasks have estimated durations."""
        # Create test task without estimated_duration
        today = date.today()
        self.repository.create(
            name="Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=datetime.combine(today, datetime.min.time()),
            planned_end=datetime.combine(
                today + timedelta(days=2), datetime.min.time()
            ),
        )

        input_dto = ListTasksInput(include_archived=True)
        result = self.controller.list_tasks(input_dto, include_gantt=True)

        # Verify total_estimated_duration is 0.0
        assert result.gantt_data.total_estimated_duration == 0.0

    def test_get_tag_statistics_returns_output_dto(self):
        """Test get_tag_statistics returns TagStatisticsOutput."""
        # Create test tasks with tags
        self.repository.create(
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["work", "urgent"],
        )
        self.repository.create(
            name="Task 2", priority=2, status=TaskStatus.PENDING, tags=["work"]
        )
        self.repository.create(
            name="Task 3", priority=3, status=TaskStatus.PENDING, tags=[]
        )

        # Get tag statistics
        result = self.controller.get_tag_statistics()

        # Verify result structure
        assert result.tag_counts is not None
        assert result.total_tags == 2  # "work" and "urgent"
        assert result.total_tagged_tasks == 2  # task1 and task2
        assert result.tag_counts["work"] == 2
        assert result.tag_counts["urgent"] == 1

    def test_get_tag_statistics_with_no_tags(self):
        """Test get_tag_statistics when no tasks have tags."""
        # Create test task without tags
        self.repository.create(
            name="No Tags", priority=1, status=TaskStatus.PENDING, tags=[]
        )

        # Get tag statistics
        result = self.controller.get_tag_statistics()

        # Verify empty statistics
        assert len(result.tag_counts) == 0
        assert result.total_tags == 0
        assert result.total_tagged_tasks == 0

    def test_get_task_by_id_returns_task(self):
        """Test get_task_by_id returns task DTO."""
        # Create test task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Get task by ID
        result = self.controller.get_task_by_id(task.id)

        # Verify result
        assert result.task is not None
        assert result.task.id == task.id
        assert result.task.name == "Test Task"

    def test_get_task_by_id_returns_none_when_not_found(self):
        """Test get_task_by_id returns None for missing task."""
        # Try to get non-existent task
        result = self.controller.get_task_by_id(999)

        # Verify task is None in output
        assert result.task is None
