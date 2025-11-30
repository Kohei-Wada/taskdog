"""Tests for TaskUIManager service."""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from taskdog.services.task_data_loader import TaskData, TaskDataLoader
from taskdog.tui.services.task_ui_manager import TaskUIManager
from taskdog.tui.state.tui_state import TUIState
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError


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
    task_id: int, name: str, status: TaskStatus
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
        is_finished=status in (TaskStatus.COMPLETED, TaskStatus.CANCELED),
        has_notes=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def create_gantt_viewmodel() -> GanttViewModel:
    """Helper to create GanttViewModel with minimal fields."""
    return GanttViewModel(
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        tasks=[],
        task_daily_hours={},
        daily_workload={},
        holidays=set(),
    )


def create_task_data(
    tasks: list[TaskRowDto] | None = None,
    viewmodels: list[TaskRowViewModel] | None = None,
    gantt: GanttViewModel | None = None,
) -> TaskData:
    """Helper to create TaskData with defaults."""
    tasks = tasks or []
    viewmodels = viewmodels or []
    return TaskData(
        all_tasks=tasks,
        filtered_tasks=tasks,
        task_list_output=TaskListOutput(
            tasks=tasks,
            total_count=len(tasks),
            filtered_count=len(tasks),
            gantt_data=None,
        ),
        table_view_models=viewmodels,
        gantt_view_model=gantt,
        filtered_gantt_view_model=gantt,
    )


class TestTaskUIManager(unittest.TestCase):
    """Test cases for TaskUIManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.state = TUIState()
        self.task_data_loader = MagicMock(spec=TaskDataLoader)
        self.main_screen = MagicMock()
        self.main_screen.gantt_widget = MagicMock()
        self.main_screen.task_table = MagicMock()
        self.on_connection_error = MagicMock()

        self.manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: self.main_screen,
            on_connection_error=self.on_connection_error,
        )

    def test_init_with_dependencies(self):
        """Test TaskUIManager initializes with required dependencies."""
        self.assertIs(self.manager.state, self.state)
        self.assertIs(self.manager.task_data_loader, self.task_data_loader)
        self.assertIsNotNone(self.manager._get_main_screen)
        self.assertIs(self.manager._on_connection_error, self.on_connection_error)

    def test_load_tasks_updates_cache_and_ui(self):
        """Test load_tasks fetches data, updates cache, and refreshes UI."""
        # Setup
        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        gantt = create_gantt_viewmodel()
        task_data = create_task_data([task], [vm], gantt)

        self.task_data_loader.load_tasks.return_value = task_data
        self.main_screen.gantt_widget.calculate_date_range.return_value = (
            date.today(),
            date.today() + timedelta(days=7),
        )

        # Execute
        self.manager.load_tasks()

        # Verify data loader was called
        self.task_data_loader.load_tasks.assert_called_once()

        # Verify state cache was updated
        self.assertEqual(len(self.state.tasks_cache), 1)
        self.assertEqual(len(self.state.viewmodels_cache), 1)

        # Verify UI widgets were refreshed
        self.main_screen.gantt_widget.update_gantt.assert_called_once()
        self.main_screen.task_table.refresh_tasks.assert_called_once()

    def test_load_tasks_with_keep_scroll_position(self):
        """Test load_tasks passes keep_scroll_position to refresh_tasks."""
        # Setup
        task_data = create_task_data()
        self.task_data_loader.load_tasks.return_value = task_data
        self.main_screen.gantt_widget.calculate_date_range.return_value = (
            date.today(),
            date.today() + timedelta(days=7),
        )

        # Execute with keep_scroll_position=True
        self.manager.load_tasks(keep_scroll_position=True)

        # Verify refresh_tasks was called with keep_scroll_position=True
        self.main_screen.task_table.refresh_tasks.assert_called_once()
        call_kwargs = self.main_screen.task_table.refresh_tasks.call_args[1]
        self.assertTrue(call_kwargs.get("keep_scroll_position"))

    def test_calculate_gantt_date_range_uses_widget(self):
        """Test _calculate_gantt_date_range delegates to gantt_widget."""
        # Setup
        expected_range = (date(2024, 1, 1), date(2024, 1, 31))
        self.main_screen.gantt_widget.calculate_date_range.return_value = expected_range

        # Execute
        result = self.manager._calculate_gantt_date_range()

        # Verify
        self.assertEqual(result, expected_range)
        self.main_screen.gantt_widget.calculate_date_range.assert_called_once()

    def test_calculate_gantt_date_range_fallback(self):
        """Test _calculate_gantt_date_range uses fallback when widget unavailable."""
        # Setup - no main_screen
        manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: None,
        )

        # Execute
        start_date, end_date = manager._calculate_gantt_date_range()

        # Verify fallback dates (this week's Monday to DEFAULT_GANTT_DISPLAY_DAYS later)
        today = date.today()
        expected_start = today - timedelta(days=today.weekday())
        self.assertEqual(start_date, expected_start)
        self.assertGreater(end_date, start_date)

    def test_fetch_task_data_handles_connection_error(self):
        """Test _fetch_task_data calls error callback on ServerConnectionError."""
        # Setup
        original_error = ConnectionError("Connection refused")
        self.task_data_loader.load_tasks.side_effect = ServerConnectionError(
            original_error=original_error
        )
        self.main_screen.gantt_widget.calculate_date_range.return_value = (
            date.today(),
            date.today() + timedelta(days=7),
        )

        # Execute
        result = self.manager._fetch_task_data()

        # Verify error callback was called
        self.on_connection_error.assert_called_once()

        # Verify empty TaskData is returned
        self.assertEqual(result.all_tasks, [])
        self.assertEqual(result.filtered_tasks, [])
        self.assertEqual(result.table_view_models, [])
        self.assertIsNone(result.gantt_view_model)

    def test_fetch_task_data_uses_state_settings(self):
        """Test _fetch_task_data uses sort/filter settings from state."""
        # Setup state
        self.state.sort_by = "priority"
        self.state.sort_reverse = True
        self.state.hide_completed = True

        task_data = create_task_data()
        self.task_data_loader.load_tasks.return_value = task_data
        self.main_screen.gantt_widget.calculate_date_range.return_value = (
            date.today(),
            date.today() + timedelta(days=7),
        )

        # Execute
        self.manager._fetch_task_data()

        # Verify data loader was called with state settings
        call_kwargs = self.task_data_loader.load_tasks.call_args[1]
        self.assertEqual(call_kwargs["sort_by"], "priority")
        self.assertTrue(call_kwargs["reverse"])
        self.assertTrue(call_kwargs["hide_completed"])

    def test_update_cache_updates_state(self):
        """Test _update_cache updates TUIState correctly."""
        # Setup
        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        gantt = create_gantt_viewmodel()
        task_data = create_task_data([task], [vm], gantt)

        # Execute
        self.manager._update_cache(task_data)

        # Verify state was updated
        self.assertEqual(len(self.state.tasks_cache), 1)
        self.assertEqual(self.state.tasks_cache[0].id, 1)
        self.assertEqual(len(self.state.viewmodels_cache), 1)
        self.assertEqual(self.state.viewmodels_cache[0].id, 1)
        self.assertEqual(self.state.gantt_cache, gantt)

    def test_refresh_ui_without_main_screen(self):
        """Test _refresh_ui does nothing when main_screen is None."""
        # Setup - no main_screen
        manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: None,
        )
        task_data = create_task_data()

        # Execute - should not raise
        manager._refresh_ui(task_data, keep_scroll_position=False)

    def test_refresh_ui_updates_gantt_widget(self):
        """Test _refresh_ui updates gantt widget with filtered data."""
        # Setup
        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        gantt = create_gantt_viewmodel()
        task_data = create_task_data([task], [vm], gantt)

        # Execute
        self.manager._refresh_ui(task_data, keep_scroll_position=False)

        # Verify gantt widget was updated
        self.main_screen.gantt_widget.update_gantt.assert_called_once()
        call_kwargs = self.main_screen.gantt_widget.update_gantt.call_args[1]
        self.assertEqual(call_kwargs["task_ids"], [1])
        self.assertEqual(call_kwargs["gantt_view_model"], gantt)

    def test_refresh_ui_updates_task_table(self):
        """Test _refresh_ui updates task table with viewmodels."""
        # Setup
        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        task_data = create_task_data([task], [vm])

        # Execute
        self.manager._refresh_ui(task_data, keep_scroll_position=True)

        # Verify task table was updated
        self.main_screen.task_table.refresh_tasks.assert_called_once_with(
            [vm], keep_scroll_position=True
        )


class TestTaskUIManagerWithoutErrorCallback(unittest.TestCase):
    """Test TaskUIManager behavior without error callback."""

    def test_connection_error_without_callback(self):
        """Test _fetch_task_data handles error gracefully without callback."""
        state = TUIState()
        task_data_loader = MagicMock(spec=TaskDataLoader)
        main_screen = MagicMock()
        main_screen.gantt_widget = MagicMock()
        main_screen.gantt_widget.calculate_date_range.return_value = (
            date.today(),
            date.today() + timedelta(days=7),
        )

        # Setup - no error callback
        manager = TaskUIManager(
            state=state,
            task_data_loader=task_data_loader,
            main_screen_provider=lambda: main_screen,
            on_connection_error=None,  # No callback
        )

        original_error = ConnectionError("Connection refused")
        task_data_loader.load_tasks.side_effect = ServerConnectionError(
            original_error=original_error
        )

        # Execute - should not raise
        result = manager._fetch_task_data()

        # Verify empty TaskData is returned
        self.assertEqual(result.all_tasks, [])


if __name__ == "__main__":
    unittest.main()
