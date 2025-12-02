"""Tests for TUI state management."""

from datetime import date, datetime

import pytest

from taskdog.tui.state.tui_state import TUIState
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus


def create_task_dto(task_id: int, name: str, status: TaskStatus) -> TaskRowDto:
    """Helper to create TaskRowDto with minimal fields."""
    return TaskRowDto(
        id=task_id,
        name=name,
        status=status,
        priority=1,
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
        is_finished=status in (TaskStatus.COMPLETED, TaskStatus.CANCELED),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def create_task_viewmodel(
    task_id: int, name: str, status: TaskStatus, is_finished: bool
) -> TaskRowViewModel:
    """Helper to create TaskRowViewModel with minimal fields."""
    return TaskRowViewModel(
        id=task_id,
        name=name,
        status=status,
        priority=1,
        is_fixed=False,
        estimated_duration=None,
        actual_duration_hours=None,
        deadline=None,
        planned_start=None,
        planned_end=None,
        actual_start=None,
        actual_end=None,
        depends_on=[],
        tags=[],
        is_finished=is_finished,
        has_notes=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestTUIState:
    """Test cases for TUIState class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.state = TUIState()

    def test_default_values(self):
        """Test default state values are correctly initialized."""
        assert self.state.hide_completed is False
        assert self.state.sort_by == "deadline"
        assert self.state.sort_reverse is False
        assert self.state.tasks_cache == []
        assert self.state.viewmodels_cache == []
        assert self.state.gantt_cache is None

    def test_filtered_tasks_show_all(self):
        """Test filtered_tasks returns all tasks when hide_completed=False."""
        # Setup tasks with mixed statuses
        tasks = [
            create_task_dto(1, "Task 1", TaskStatus.COMPLETED),
            create_task_dto(2, "Task 2", TaskStatus.PENDING),
            create_task_dto(3, "Task 3", TaskStatus.CANCELED),
        ]
        self.state.tasks_cache = tasks
        self.state.hide_completed = False

        # Should return all tasks
        filtered = self.state.filtered_tasks
        assert len(filtered) == 3

    def test_filtered_tasks_hide_completed(self):
        """Test filtered_tasks hides completed/canceled when hide_completed=True."""
        # Setup tasks with mixed statuses
        tasks = [
            create_task_dto(1, "Task 1", TaskStatus.COMPLETED),
            create_task_dto(2, "Task 2", TaskStatus.PENDING),
            create_task_dto(3, "Task 3", TaskStatus.CANCELED),
            create_task_dto(4, "Task 4", TaskStatus.IN_PROGRESS),
        ]
        self.state.tasks_cache = tasks
        self.state.hide_completed = True

        # Should return only non-finished tasks
        filtered = self.state.filtered_tasks
        assert len(filtered) == 2
        assert filtered[0].id == 2
        assert filtered[1].id == 4

    def test_filtered_viewmodels_show_all(self):
        """Test filtered_viewmodels returns all when hide_completed=False."""
        # Setup viewmodels with mixed statuses
        vms = [
            create_task_viewmodel(1, "Task 1", TaskStatus.COMPLETED, True),
            create_task_viewmodel(2, "Task 2", TaskStatus.PENDING, False),
        ]
        self.state.viewmodels_cache = vms
        self.state.hide_completed = False

        # Should return all
        filtered = self.state.filtered_viewmodels
        assert len(filtered) == 2

    def test_filtered_viewmodels_hide_completed(self):
        """Test filtered_viewmodels hides finished when hide_completed=True."""
        # Setup viewmodels with mixed statuses
        vms = [
            create_task_viewmodel(1, "Task 1", TaskStatus.COMPLETED, True),
            create_task_viewmodel(2, "Task 2", TaskStatus.PENDING, False),
            create_task_viewmodel(3, "Task 3", TaskStatus.CANCELED, True),
        ]
        self.state.viewmodels_cache = vms
        self.state.hide_completed = True

        # Should return only non-finished
        filtered = self.state.filtered_viewmodels
        assert len(filtered) == 1
        assert filtered[0].id == 2
        assert filtered[0].is_finished is False

    def test_update_caches_atomically(self):
        """Test update_caches updates all fields atomically."""
        # Create test data
        tasks = [create_task_dto(1, "Task 1", TaskStatus.PENDING)]
        vms = [create_task_viewmodel(1, "Task 1", TaskStatus.PENDING, False)]
        gantt = GanttViewModel(
            start_date=date.today(),
            end_date=date.today(),
            tasks=[],
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
        )

        # Update all caches
        self.state.update_caches(tasks, vms, gantt)

        # Verify all fields are updated
        assert self.state.tasks_cache == tasks
        assert self.state.viewmodels_cache == vms
        assert self.state.gantt_cache == gantt

    def test_update_caches_without_gantt(self):
        """Test update_caches can update without gantt (optional parameter)."""
        tasks = [create_task_dto(1, "Task 1", TaskStatus.PENDING)]
        vms = [create_task_viewmodel(1, "Task 1", TaskStatus.PENDING, False)]

        # Set initial gantt cache
        initial_gantt = GanttViewModel(
            start_date=date.today(),
            end_date=date.today(),
            tasks=[],
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
        )
        self.state.gantt_cache = initial_gantt

        # Update without gantt parameter
        self.state.update_caches(tasks, vms)

        # Verify gantt cache is unchanged
        assert self.state.gantt_cache == initial_gantt

    def test_update_caches_validation_error(self):
        """Test update_caches raises error when lengths mismatch."""
        tasks = [
            create_task_dto(1, "Task 1", TaskStatus.PENDING),
            create_task_dto(2, "Task 2", TaskStatus.PENDING),
        ]
        vms = [create_task_viewmodel(1, "Task 1", TaskStatus.PENDING, False)]

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            self.state.update_caches(tasks, vms)

        assert "must have same length" in str(exc_info.value)
        assert "2 != 1" in str(exc_info.value)

    def test_clear_caches(self):
        """Test clear_caches removes all cached data."""
        # Setup initial caches
        self.state.tasks_cache = [create_task_dto(1, "Task 1", TaskStatus.PENDING)]
        self.state.viewmodels_cache = [
            create_task_viewmodel(1, "Task 1", TaskStatus.PENDING, False)
        ]
        self.state.gantt_cache = GanttViewModel(
            start_date=date.today(),
            end_date=date.today(),
            tasks=[],
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
        )

        # Clear all caches
        self.state.clear_caches()

        # Verify all caches are cleared
        assert self.state.tasks_cache == []
        assert self.state.viewmodels_cache == []
        assert self.state.gantt_cache is None

    def test_invalidate_gantt_cache(self):
        """Test invalidate_gantt_cache only clears gantt cache."""
        # Setup initial caches
        self.state.tasks_cache = [create_task_dto(1, "Task 1", TaskStatus.PENDING)]
        self.state.viewmodels_cache = [
            create_task_viewmodel(1, "Task 1", TaskStatus.PENDING, False)
        ]
        self.state.gantt_cache = GanttViewModel(
            start_date=date.today(),
            end_date=date.today(),
            tasks=[],
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
        )

        # Invalidate only gantt cache
        self.state.invalidate_gantt_cache()

        # Verify only gantt cache is cleared
        assert len(self.state.tasks_cache) == 1
        assert len(self.state.viewmodels_cache) == 1
        assert self.state.gantt_cache is None
