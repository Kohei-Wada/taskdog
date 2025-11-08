"""Tests for AppState class."""

import unittest
from datetime import datetime

from taskdog.tui.state import AppState
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.domain.entities.task import TaskStatus


class TestAppState(unittest.TestCase):
    """Test cases for AppState."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = AppState()

    def test_initial_state(self):
        """Test initial state values."""
        self.assertFalse(self.state.hide_completed)
        self.assertEqual(self.state.gantt_sort_by, "deadline")
        self.assertEqual(self.state.all_tasks, [])
        self.assertIsNone(self.state.gantt_view_model)
        self.assertEqual(self.state.cached_viewmodels, {})

    def test_toggle_completed(self):
        """Test toggling hide_completed flag."""
        self.assertFalse(self.state.hide_completed)

        self.state.toggle_completed()
        self.assertTrue(self.state.hide_completed)

        self.state.toggle_completed()
        self.assertFalse(self.state.hide_completed)

    def test_set_sort_by(self):
        """Test setting sort_by field."""
        self.assertEqual(self.state.gantt_sort_by, "deadline")

        self.state.set_sort_by("priority")
        self.assertEqual(self.state.gantt_sort_by, "priority")

        self.state.set_sort_by("planned_start")
        self.assertEqual(self.state.gantt_sort_by, "planned_start")

    def test_update_all_tasks(self):
        """Test updating all_tasks cache."""
        task1 = TaskRowDto(
            id=1,
            name="Task 1",
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
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )
        task2 = TaskRowDto(
            id=2,
            name="Task 2",
            priority=2,
            status=TaskStatus.COMPLETED,
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
            is_finished=True,
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )

        self.state.all_tasks = [task1, task2]
        self.assertEqual(len(self.state.all_tasks), 2)
        self.assertEqual(self.state.all_tasks[0].id, 1)
        self.assertEqual(self.state.all_tasks[1].id, 2)

    def test_update_gantt_view_model(self):
        """Test updating gantt_view_model cache."""
        gantt_vm = GanttViewModel(
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 1, 14).date(),
            tasks=[],
            task_daily_hours={},
            daily_workload={},
            holidays=set(),
        )

        self.state.gantt_view_model = gantt_vm
        self.assertIsNotNone(self.state.gantt_view_model)
        self.assertEqual(self.state.gantt_view_model.total_days, 14)

    def test_clear_cached_viewmodels(self):
        """Test clearing cached ViewModels."""
        self.state.cached_viewmodels = {1: "vm1", 2: "vm2"}
        self.assertEqual(len(self.state.cached_viewmodels), 2)

        self.state.clear_cached_viewmodels()
        self.assertEqual(len(self.state.cached_viewmodels), 0)

    def test_get_filtered_tasks_hide_completed(self):
        """Test getting filtered tasks with hide_completed=True."""
        task1 = TaskRowDto(
            id=1,
            name="Task 1",
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
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )
        task2 = TaskRowDto(
            id=2,
            name="Task 2",
            priority=2,
            status=TaskStatus.COMPLETED,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=datetime(2025, 1, 1, 9, 0),
            actual_end=datetime(2025, 1, 1, 17, 0),
            estimated_duration=None,
            actual_duration_hours=8.0,
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            is_finished=True,
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 17, 0),
        )
        task3 = TaskRowDto(
            id=3,
            name="Task 3",
            priority=3,
            status=TaskStatus.IN_PROGRESS,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=datetime(2025, 1, 2, 9, 0),
            actual_end=None,
            estimated_duration=None,
            actual_duration_hours=None,
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            is_finished=False,
            created_at=datetime(2025, 1, 2, 9, 0),
            updated_at=datetime(2025, 1, 2, 9, 0),
        )

        self.state.all_tasks = [task1, task2, task3]

        # Without filter
        self.state.hide_completed = False
        filtered = self.state.get_filtered_tasks()
        self.assertEqual(len(filtered), 3)

        # With filter
        self.state.hide_completed = True
        filtered = self.state.get_filtered_tasks()
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].id, 1)
        self.assertEqual(filtered[1].id, 3)

    def test_get_filtered_tasks_exclude_archived(self):
        """Test that archived tasks are always filtered out."""
        task1 = TaskRowDto(
            id=1,
            name="Task 1",
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
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )
        task2 = TaskRowDto(
            id=2,
            name="Task 2",
            priority=2,
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
            is_archived=True,  # Archived
            is_finished=False,
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )

        self.state.all_tasks = [task1, task2]

        filtered = self.state.get_filtered_tasks()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 1)

    def test_set_search_query(self):
        """Test setting search query."""
        self.assertEqual(self.state.search_query, "")

        self.state.set_search_query("test query")
        self.assertEqual(self.state.search_query, "test query")

        self.state.set_search_query("")
        self.assertEqual(self.state.search_query, "")

    def test_compute_table_viewmodels(self):
        """Test computing table ViewModels from current state."""
        from unittest.mock import Mock

        # Setup test data
        task1 = TaskRowDto(
            id=1,
            name="Task 1",
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
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )

        self.state.all_tasks = [task1]

        # Mock presenter
        mock_presenter = Mock()
        mock_viewmodel = Mock()
        mock_presenter.present.return_value = [mock_viewmodel]

        # Compute ViewModels
        self.state.compute_table_viewmodels(mock_presenter)

        # Verify presenter was called with correct output
        self.assertEqual(len(self.state.table_viewmodels), 1)
        mock_presenter.present.assert_called_once()

        # Verify the output passed to presenter
        call_args = mock_presenter.present.call_args[0][0]
        self.assertEqual(len(call_args.tasks), 1)
        self.assertEqual(call_args.total_count, 1)
        self.assertEqual(call_args.filtered_count, 1)

    def test_compute_table_viewmodels_with_filters(self):
        """Test computing table ViewModels with hide_completed filter."""
        from unittest.mock import Mock

        # Setup test data with completed task
        task1 = TaskRowDto(
            id=1,
            name="Task 1",
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
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )
        task2 = TaskRowDto(
            id=2,
            name="Task 2",
            priority=2,
            status=TaskStatus.COMPLETED,
            planned_start=None,
            planned_end=None,
            deadline=None,
            actual_start=datetime(2025, 1, 1, 9, 0),
            actual_end=datetime(2025, 1, 1, 17, 0),
            estimated_duration=None,
            actual_duration_hours=8.0,
            is_fixed=False,
            depends_on=[],
            tags=[],
            is_archived=False,
            is_finished=True,
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 17, 0),
        )

        self.state.all_tasks = [task1, task2]
        self.state.hide_completed = True

        # Mock presenter
        mock_presenter = Mock()
        mock_viewmodel = Mock()
        mock_presenter.present.return_value = [mock_viewmodel]

        # Compute ViewModels
        self.state.compute_table_viewmodels(mock_presenter)

        # Verify presenter received only non-completed tasks
        call_args = mock_presenter.present.call_args[0][0]
        self.assertEqual(len(call_args.tasks), 1)
        self.assertEqual(call_args.tasks[0].id, 1)
        self.assertEqual(call_args.total_count, 2)
        self.assertEqual(call_args.filtered_count, 1)

    def test_compute_filtered_gantt(self):
        """Test computing filtered gantt ViewModel."""
        from unittest.mock import Mock

        # Setup test data
        task1 = TaskRowDto(
            id=1,
            name="Task 1",
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
            created_at=datetime(2025, 1, 1, 9, 0),
            updated_at=datetime(2025, 1, 1, 9, 0),
        )

        self.state.all_tasks = [task1]
        self.state.gantt_view_model = Mock()

        # Mock loader
        mock_loader = Mock()
        mock_filtered_gantt = Mock()
        mock_loader.filter_gantt_by_tasks.return_value = mock_filtered_gantt

        # Compute filtered gantt
        self.state.compute_filtered_gantt(mock_loader)

        # Verify loader was called
        mock_loader.filter_gantt_by_tasks.assert_called_once()
        self.assertEqual(self.state.filtered_gantt_viewmodel, mock_filtered_gantt)

    def test_compute_filtered_gantt_no_gantt_view_model(self):
        """Test computing filtered gantt when no gantt view model exists."""
        from unittest.mock import Mock

        self.state.gantt_view_model = None
        mock_loader = Mock()

        # Compute filtered gantt
        self.state.compute_filtered_gantt(mock_loader)

        # Verify loader was not called and result is None
        mock_loader.filter_gantt_by_tasks.assert_not_called()
        self.assertIsNone(self.state.filtered_gantt_viewmodel)

    def test_set_change_callback(self):
        """Test setting state change callback."""
        callback_calls = []

        def callback(action: str):
            callback_calls.append(action)

        self.state.set_change_callback(callback)

        # Modify state - should trigger callback
        self.state.toggle_completed()
        self.assertEqual(len(callback_calls), 1)
        self.assertEqual(callback_calls[0], "toggle_completed")

        # Another modification
        self.state.set_sort_by("priority")
        self.assertEqual(len(callback_calls), 2)
        self.assertEqual(callback_calls[1], "set_sort_by")

    def test_notify_change_without_callback(self):
        """Test that _notify_change works without callback set."""
        # Should not raise error
        self.state.toggle_completed()
        self.assertTrue(self.state.hide_completed)

    def test_state_change_notifications(self):
        """Test that all state-changing methods trigger notifications."""
        callback_calls = []

        def callback(action: str):
            callback_calls.append(action)

        self.state.set_change_callback(callback)

        # Test all state-changing methods
        self.state.toggle_completed()
        self.state.set_sort_by("priority")
        self.state.set_search_query("test")
        self.state.update_tasks_cache([])
        self.state.update_gantt_cache(None)

        expected_actions = [
            "toggle_completed",
            "set_sort_by",
            "set_search_query",
            "update_tasks_cache",
            "update_gantt_cache",
        ]
        self.assertEqual(callback_calls, expected_actions)


if __name__ == "__main__":
    unittest.main()
