"""Tests for TUI state management."""

from datetime import date, datetime

import pytest

from taskdog.tui.state.tui_state import TUIState
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.domain.entities.task import TaskStatus


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
        assert self.state.sort_by == "deadline"
        assert self.state.sort_reverse is False
        assert self.state.viewmodels_cache == []
        assert self.state.gantt_cache is None

    def test_filtered_viewmodels_returns_all(self):
        """Test filtered_viewmodels returns all viewmodels from cache."""
        # Setup viewmodels with mixed statuses
        vms = [
            create_task_viewmodel(1, "Task 1", TaskStatus.COMPLETED, True),
            create_task_viewmodel(2, "Task 2", TaskStatus.PENDING, False),
        ]
        self.state.viewmodels_cache = vms

        # Should return all
        filtered = self.state.filtered_viewmodels
        assert len(filtered) == 2

    def test_update_caches_atomically(self):
        """Test update_caches updates all fields atomically."""
        # Create test data
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
        self.state.update_caches(vms, gantt)

        # Verify all fields are updated
        assert self.state.viewmodels_cache == vms
        assert self.state.gantt_cache == gantt

    def test_update_caches_without_gantt(self):
        """Test update_caches can update without gantt (optional parameter)."""
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
        self.state.update_caches(vms)

        # Verify gantt cache is unchanged
        assert self.state.gantt_cache == initial_gantt
