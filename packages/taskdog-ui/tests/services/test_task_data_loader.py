"""Tests for TaskDataLoader."""

from datetime import date
from unittest.mock import Mock

import pytest

from taskdog.services.task_data_loader import TaskData, TaskDataLoader
from taskdog.view_models.gantt_view_model import GanttViewModel, TaskGanttRowViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.gantt_output import GanttOutput
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestTaskDataLoader:
    """Test cases for TaskDataLoader."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.api_client = Mock()
        self.table_presenter = Mock()
        self.gantt_presenter = Mock()

        self.loader = TaskDataLoader(
            api_client=self.api_client,
            table_presenter=self.table_presenter,
            gantt_presenter=self.gantt_presenter,
        )

    def test_load_tasks_without_gantt(self):
        """Test loading tasks without gantt data."""
        # Setup mocks
        task1 = Task(id=1, name="Task 1", priority=1, status=TaskStatus.PENDING)
        task2 = Task(id=2, name="Task 2", priority=2, status=TaskStatus.COMPLETED)

        task_list_output = TaskListOutput(
            tasks=[task1, task2], total_count=2, filtered_count=2
        )
        self.api_client.list_tasks.return_value = task_list_output

        view_model1 = Mock(spec=TaskRowViewModel)
        view_model2 = Mock(spec=TaskRowViewModel)
        self.table_presenter.present.return_value = [view_model1, view_model2]

        # Execute
        result = self.loader.load_tasks(
            all=False,
            sort_by="deadline",
            date_range=None,
        )

        # Verify
        assert isinstance(result, TaskData)
        assert len(result.all_tasks) == 2
        assert len(result.filtered_tasks) == 2
        assert len(result.table_view_models) == 2
        assert result.gantt_view_model is None
        assert result.filtered_gantt_view_model is None

        # Verify API call
        self.api_client.list_tasks.assert_called_once()
        call_args = self.api_client.list_tasks.call_args
        assert call_args.kwargs["sort_by"] == "deadline"
        assert call_args.kwargs["reverse"] is False

    def test_load_tasks_with_gantt(self):
        """Test loading tasks with gantt data."""
        # Setup mocks
        task1 = Task(id=1, name="Task 1", priority=1, status=TaskStatus.PENDING)

        # Mock gantt data within task_list_output
        gantt_output = Mock(spec=GanttOutput)

        task_list_output = TaskListOutput(
            tasks=[task1],
            total_count=1,
            filtered_count=1,
            gantt_data=gantt_output,  # Include gantt data in response
        )
        self.api_client.list_tasks.return_value = task_list_output

        gantt_task_vm = TaskGanttRowViewModel(
            id=1,
            name="Task 1",
            formatted_name="Task 1",
            estimated_duration=None,
            formatted_estimated_duration="-",
            status=TaskStatus.PENDING,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            is_finished=False,
        )
        gantt_view_model = GanttViewModel(
            tasks=[gantt_task_vm],
            task_daily_hours={},
            daily_workload={},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            holidays=set(),
        )
        self.gantt_presenter.present.return_value = gantt_view_model

        view_model1 = Mock(spec=TaskRowViewModel)
        self.table_presenter.present.return_value = [view_model1]

        # Execute with date range
        result = self.loader.load_tasks(
            all=False,
            sort_by="deadline",
            date_range=(date(2025, 1, 1), date(2025, 1, 7)),
        )

        # Verify
        assert result.gantt_view_model is not None
        assert result.filtered_gantt_view_model is not None
        assert len(result.gantt_view_model.tasks) == 1

        # Verify API call now uses include_gantt instead of get_gantt_data
        call_args = self.api_client.list_tasks.call_args
        assert call_args.kwargs["sort_by"] == "deadline"
        assert call_args.kwargs["reverse"] is False
        assert call_args.kwargs["include_gantt"] is True
        assert call_args.kwargs["gantt_start_date"] == date(2025, 1, 1)
        assert call_args.kwargs["gantt_end_date"] == date(2025, 1, 7)

    def test_filter_gantt_by_tasks(self):
        """Test filtering gantt view model by tasks."""
        task1 = Task(id=1, name="Task 1", priority=1, status=TaskStatus.PENDING)
        task2 = Task(id=2, name="Task 2", priority=2, status=TaskStatus.PENDING)

        gantt_task1 = TaskGanttRowViewModel(
            id=1,
            name="Task 1",
            formatted_name="Task 1",
            estimated_duration=None,
            formatted_estimated_duration="-",
            status=TaskStatus.PENDING,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            is_finished=False,
        )
        gantt_task2 = TaskGanttRowViewModel(
            id=2,
            name="Task 2",
            formatted_name="Task 2",
            estimated_duration=None,
            formatted_estimated_duration="-",
            status=TaskStatus.PENDING,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            is_finished=False,
        )
        gantt_task3 = TaskGanttRowViewModel(
            id=3,
            name="Task 3",
            formatted_name="Task 3",
            estimated_duration=None,
            formatted_estimated_duration="-",
            status=TaskStatus.PENDING,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            deadline=None,
            is_finished=False,
        )

        gantt_view_model = GanttViewModel(
            tasks=[gantt_task1, gantt_task2, gantt_task3],
            task_daily_hours={},
            daily_workload={},
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            holidays=set(),
        )

        # Filter to only show task1 and task2
        result = self.loader.filter_gantt_by_tasks(gantt_view_model, [task1, task2])

        assert len(result.tasks) == 2
        task_ids = {t.id for t in result.tasks}
        assert task_ids == {1, 2}
        # Other properties should be preserved
        assert result.start_date == gantt_view_model.start_date
        assert result.end_date == gantt_view_model.end_date
