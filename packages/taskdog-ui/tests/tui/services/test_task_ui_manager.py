"""Tests for TaskUIManager service."""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from taskdog.services.task_data_loader import TaskData, TaskDataLoader
from taskdog.tui.services.task_ui_manager import TaskUIManager
from taskdog.tui.state.tui_state import TUIState
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog.view_models.task_view_model import TaskRowViewModel
from taskdog_core.application.dto.gantt_output import GanttDateRange, GanttOutput
from taskdog_core.application.dto.task_dto import TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    AuthenticationError,
    ServerConnectionError,
    ServerError,
)

_DATE_RANGE = (date.today(), date.today() + timedelta(days=7))


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


def create_gantt_output() -> GanttOutput:
    """Helper to create a minimal valid GanttOutput (API gantt payload)."""
    return GanttOutput(
        date_range=GanttDateRange(
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31)
        ),
        tasks=[],
        task_daily_hours={},
        daily_workload={},
        holidays=set(),
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
        task_list_output=TaskListOutput(
            tasks=tasks,
            total_count=len(tasks),
            filtered_count=len(tasks),
            gantt_data=None,
        ),
        table_view_models=viewmodels,
        gantt_view_model=gantt,
    )


class TestTaskUIManager:
    """Test cases for TaskUIManager class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.state = TUIState()
        self.task_data_loader = MagicMock(spec=TaskDataLoader)
        self.main_screen = MagicMock()
        self.main_screen.gantt_widget = MagicMock()
        self.main_screen.task_table = MagicMock()
        self.main_screen.gantt_widget.calculate_date_range.return_value = _DATE_RANGE
        self.app = MagicMock()
        self.on_error = MagicMock()

        self.manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: self.main_screen,
            app=self.app,
            on_error=self.on_error,
        )

    def test_init_with_dependencies(self):
        """Test TaskUIManager initializes with required dependencies."""
        assert self.manager.state is self.state
        assert self.manager.task_data_loader is self.task_data_loader
        assert self.manager._get_main_screen is not None
        assert self.manager._app is self.app
        assert self.manager._on_error is self.on_error

    def test_load_tasks_dispatches_worker(self):
        """Test load_tasks samples geometry on the main thread and dispatches a worker."""
        self.manager.load_tasks()

        # Date range must be sampled on the (main) thread before handing off.
        self.main_screen.gantt_widget.calculate_date_range.assert_called_once()
        # The blocking work is offloaded to a worker, not run inline.
        self.app.run_worker.assert_called_once()
        # Close the coroutine handed to the (mocked) worker to avoid warnings.
        self.app.run_worker.call_args[0][0].close()

    @pytest.mark.asyncio
    async def test_load_tasks_worker_updates_cache_and_ui(self):
        """Test the worker fetches data, updates cache, and refreshes UI."""
        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        gantt = create_gantt_viewmodel()
        task_data = create_task_data([task], [vm], gantt)
        self.task_data_loader.load_tasks.return_value = task_data

        await self.manager._load_tasks_worker(_DATE_RANGE, "id", False, False)

        # Verify data loader was called off-thread
        self.task_data_loader.load_tasks.assert_called_once()
        # Verify state cache was updated
        assert len(self.state.tasks_cache) == 1
        assert len(self.state.viewmodels_cache) == 1
        # Verify UI widgets were refreshed
        self.main_screen.gantt_widget.update_gantt.assert_called_once()
        self.main_screen.refresh_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_tasks_worker_keep_scroll_position(self):
        """Test the worker passes keep_scroll_position through to refresh_tasks."""
        self.task_data_loader.load_tasks.return_value = create_task_data()

        await self.manager._load_tasks_worker(_DATE_RANGE, "id", False, True)

        self.main_screen.refresh_tasks.assert_called_once()
        call_kwargs = self.main_screen.refresh_tasks.call_args[1]
        assert call_kwargs.get("keep_scroll_position") is True

    @pytest.mark.asyncio
    async def test_load_tasks_worker_skips_ui_when_unmounted(self):
        """Test the worker does not touch UI if the screen is gone after fetching."""
        manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: None,
            app=self.app,
        )
        self.task_data_loader.load_tasks.return_value = create_task_data()

        # Should not raise even though there is no main screen to update.
        await manager._load_tasks_worker(_DATE_RANGE, "id", False, False)

    def test_load_task_data_uses_given_settings(self):
        """Test _load_task_data forwards the sampled sort/date settings to the loader."""
        self.task_data_loader.load_tasks.return_value = create_task_data()

        self.manager._load_task_data(_DATE_RANGE, "priority", True)

        call_kwargs = self.task_data_loader.load_tasks.call_args[1]
        assert call_kwargs["sort_by"] == "priority"
        assert call_kwargs["reverse"] is True
        assert call_kwargs["date_range"] == _DATE_RANGE
        assert call_kwargs["include_archived"] is False

    def test_calculate_gantt_date_range_uses_widget(self):
        """Test _calculate_gantt_date_range delegates to gantt_widget."""
        expected_range = (date(2024, 1, 1), date(2024, 1, 31))
        self.main_screen.gantt_widget.calculate_date_range.return_value = expected_range

        result = self.manager._calculate_gantt_date_range()

        assert result == expected_range
        self.main_screen.gantt_widget.calculate_date_range.assert_called_once()

    def test_calculate_gantt_date_range_fallback(self):
        """Test _calculate_gantt_date_range uses fallback when widget unavailable."""
        manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: None,
            app=self.app,
        )

        start_date, end_date = manager._calculate_gantt_date_range()

        today = date.today()
        expected_start = today - timedelta(days=today.weekday())
        assert start_date == expected_start
        assert end_date > start_date

    @pytest.mark.asyncio
    async def test_worker_handles_connection_error(self):
        """Test the worker reports ServerConnectionError and falls back to empty data."""
        self.task_data_loader.load_tasks.side_effect = ServerConnectionError(
            base_url="http://localhost:8000",
            original_error=ConnectionError("Connection refused"),
        )

        await self.manager._load_tasks_worker(_DATE_RANGE, "id", False, False)

        self.on_error.assert_called_once()
        assert isinstance(self.on_error.call_args[0][0], ServerConnectionError)
        # Empty data is applied: no rows cached, table still refreshed.
        assert self.state.tasks_cache == []
        self.main_screen.refresh_tasks.assert_called_once()

    def test_update_cache_updates_state(self):
        """Test _update_cache updates TUIState correctly."""
        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        gantt = create_gantt_viewmodel()
        task_data = create_task_data([task], [vm], gantt)

        self.manager._update_cache(task_data)

        assert len(self.state.tasks_cache) == 1
        assert self.state.tasks_cache[0].id == 1
        assert len(self.state.viewmodels_cache) == 1
        assert self.state.viewmodels_cache[0].id == 1
        assert self.state.gantt_cache == gantt

    def test_refresh_ui_without_main_screen(self):
        """Test _refresh_ui does nothing when main_screen is None."""
        manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: None,
            app=self.app,
        )
        task_data = create_task_data()

        # Execute - should not raise
        manager._refresh_ui(task_data, keep_scroll_position=False)

    def test_refresh_ui_updates_gantt_widget(self):
        """Test _refresh_ui updates gantt widget (reads from State cache)."""
        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        gantt = create_gantt_viewmodel()
        task_data = create_task_data([task], [vm], gantt)

        self.manager._refresh_ui(task_data, keep_scroll_position=False)

        self.main_screen.gantt_widget.update_gantt.assert_called_once()
        call_kwargs = self.main_screen.gantt_widget.update_gantt.call_args[1]
        assert call_kwargs["task_ids"] == [1]

    def test_refresh_ui_updates_task_table(self):
        """Test _refresh_ui updates task table with viewmodels."""
        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        task_data = create_task_data([task], [vm])

        self.manager._refresh_ui(task_data, keep_scroll_position=True)

        self.main_screen.refresh_tasks.assert_called_once_with(
            keep_scroll_position=True
        )


class TestRecalculateGantt:
    """Test cases for recalculate_gantt method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.state = TUIState()
        self.task_data_loader = MagicMock(spec=TaskDataLoader)
        self.main_screen = MagicMock()
        self.main_screen.gantt_widget = MagicMock()
        # Setup default return values for gantt_widget methods
        self.main_screen.gantt_widget.get_filter_include_archived.return_value = False
        self.main_screen.gantt_widget.get_sort_by.return_value = "deadline"
        self.app = MagicMock()
        self.on_error = MagicMock()

        # Setup mock API client and presenter on task_data_loader
        self.task_data_loader.api_client = MagicMock()
        self.task_data_loader.gantt_presenter = MagicMock()

        self.manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: self.main_screen,
            app=self.app,
            on_error=self.on_error,
        )

    def test_recalculate_gantt_fetches_and_updates_widget(self):
        """Test recalculate_gantt fetches data and updates widget."""
        gantt = create_gantt_viewmodel()
        task_list_output = TaskListOutput(
            tasks=[],
            total_count=0,
            filtered_count=0,
            gantt_data=create_gantt_output(),
        )
        self.task_data_loader.api_client.list_tasks.return_value = task_list_output
        self.task_data_loader.gantt_presenter.present.return_value = gantt

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        self.manager.recalculate_gantt(start_date, end_date)

        self.task_data_loader.api_client.list_tasks.assert_called_once_with(
            include_archived=False,  # from gantt_widget.get_filter_include_archived()
            sort_by="deadline",  # from gantt_widget.get_sort_by()
            reverse=self.state.sort_reverse,
            include_gantt=True,
            gantt_start_date=start_date,
            gantt_end_date=end_date,
        )

        self.task_data_loader.gantt_presenter.present.assert_called_once()

        assert self.state.gantt_cache == gantt
        self.main_screen.gantt_widget.update_view_model_and_render.assert_called_once()

    def test_recalculate_gantt_respects_gantt_widget_filter_state(self):
        """Test recalculate_gantt uses filter/sort state from gantt_widget."""
        self.main_screen.gantt_widget.get_filter_include_archived.return_value = True
        self.main_screen.gantt_widget.get_sort_by.return_value = "priority"

        gantt = create_gantt_viewmodel()
        task_list_output = TaskListOutput(
            tasks=[],
            total_count=0,
            filtered_count=0,
            gantt_data=create_gantt_output(),
        )
        self.task_data_loader.api_client.list_tasks.return_value = task_list_output
        self.task_data_loader.gantt_presenter.present.return_value = gantt

        self.manager.recalculate_gantt(date(2024, 1, 1), date(2024, 1, 31))

        call_kwargs = self.task_data_loader.api_client.list_tasks.call_args[1]
        assert call_kwargs["include_archived"] is True
        assert call_kwargs["sort_by"] == "priority"

    def test_recalculate_gantt_handles_connection_error(self):
        """Test recalculate_gantt calls error callback on failure."""
        self.task_data_loader.api_client.list_tasks.side_effect = ServerConnectionError(
            base_url="http://localhost:8000",
            original_error=ConnectionError("Connection refused"),
        )

        self.manager.recalculate_gantt(date(2024, 1, 1), date(2024, 1, 31))

        self.on_error.assert_called_once()
        error_arg = self.on_error.call_args[0][0]
        assert isinstance(error_arg, ServerConnectionError)

        self.main_screen.gantt_widget.update_view_model_and_render.assert_not_called()

    def test_recalculate_gantt_without_main_screen(self):
        """Test recalculate_gantt handles missing main_screen gracefully."""
        manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: None,
            app=self.app,
            on_error=self.on_error,
        )

        gantt = create_gantt_viewmodel()
        task_list_output = TaskListOutput(
            tasks=[],
            total_count=0,
            filtered_count=0,
            gantt_data=create_gantt_output(),
        )
        self.task_data_loader.api_client.list_tasks.return_value = task_list_output
        self.task_data_loader.gantt_presenter.present.return_value = gantt

        manager.recalculate_gantt(date(2024, 1, 1), date(2024, 1, 31))

        self.task_data_loader.api_client.list_tasks.assert_called_once()

    def test_recalculate_gantt_without_gantt_data(self):
        """Test recalculate_gantt handles None gantt_data gracefully."""
        task_list_output = TaskListOutput(
            tasks=[],
            total_count=0,
            filtered_count=0,
            gantt_data=None,
        )
        self.task_data_loader.api_client.list_tasks.return_value = task_list_output

        self.manager.recalculate_gantt(date(2024, 1, 1), date(2024, 1, 31))

        self.task_data_loader.gantt_presenter.present.assert_not_called()
        self.main_screen.gantt_widget.update_view_model_and_render.assert_not_called()


class TestErrorHandling:
    """Test cases for error handling in TaskUIManager."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.state = TUIState()
        self.task_data_loader = MagicMock(spec=TaskDataLoader)
        self.main_screen = MagicMock()
        self.main_screen.gantt_widget = MagicMock()
        self.main_screen.gantt_widget.calculate_date_range.return_value = _DATE_RANGE
        self.main_screen.gantt_widget.get_filter_include_archived.return_value = False
        self.main_screen.gantt_widget.get_sort_by.return_value = "deadline"
        self.app = MagicMock()
        self.on_error = MagicMock()

        # Setup mock API client and presenter on task_data_loader
        self.task_data_loader.api_client = MagicMock()
        self.task_data_loader.gantt_presenter = MagicMock()

        self.manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: self.main_screen,
            app=self.app,
            on_error=self.on_error,
        )

    @pytest.mark.asyncio
    async def test_worker_handles_authentication_error(self):
        """Test the worker reports AuthenticationError and falls back to empty data."""
        self.task_data_loader.load_tasks.side_effect = AuthenticationError(
            message="Unauthorized",
        )

        await self.manager._load_tasks_worker(_DATE_RANGE, "id", False, False)

        self.on_error.assert_called_once()
        assert isinstance(self.on_error.call_args[0][0], AuthenticationError)
        assert self.state.tasks_cache == []

    @pytest.mark.asyncio
    async def test_worker_handles_server_error(self):
        """Test the worker reports ServerError and falls back to empty data."""
        self.task_data_loader.load_tasks.side_effect = ServerError(
            status_code=500,
            message="Internal Server Error",
        )

        await self.manager._load_tasks_worker(_DATE_RANGE, "id", False, False)

        self.on_error.assert_called_once()
        assert isinstance(self.on_error.call_args[0][0], ServerError)
        assert self.state.tasks_cache == []

    def test_recalculate_gantt_handles_authentication_error(self):
        """Test recalculate_gantt calls error callback with AuthenticationError."""
        self.task_data_loader.api_client.list_tasks.side_effect = AuthenticationError(
            message="Unauthorized",
        )

        self.manager.recalculate_gantt(date(2024, 1, 1), date(2024, 1, 31))

        self.on_error.assert_called_once()
        assert isinstance(self.on_error.call_args[0][0], AuthenticationError)
        self.main_screen.gantt_widget.update_view_model_and_render.assert_not_called()

    def test_recalculate_gantt_handles_server_error(self):
        """Test recalculate_gantt calls error callback with ServerError."""
        self.task_data_loader.api_client.list_tasks.side_effect = ServerError(
            status_code=500,
            message="Internal Server Error",
        )

        self.manager.recalculate_gantt(date(2024, 1, 1), date(2024, 1, 31))

        self.on_error.assert_called_once()
        assert isinstance(self.on_error.call_args[0][0], ServerError)
        self.main_screen.gantt_widget.update_view_model_and_render.assert_not_called()


class TestCreateEmptyTaskData:
    """Test cases for _create_empty_task_data method."""

    def test_create_empty_task_data_returns_empty_data(self):
        """Test _create_empty_task_data returns valid empty TaskData."""
        state = TUIState()
        task_data_loader = MagicMock(spec=TaskDataLoader)
        manager = TaskUIManager(
            state=state,
            task_data_loader=task_data_loader,
            main_screen_provider=lambda: None,
            app=MagicMock(),
        )

        result = manager._create_empty_task_data()

        assert result.all_tasks == []
        assert result.table_view_models == []
        assert result.gantt_view_model is None
        assert result.task_list_output.total_count == 0
        assert result.task_list_output.filtered_count == 0


class TestRefreshUIEdgeCases:
    """Test cases for _refresh_ui edge cases."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.state = TUIState()
        self.task_data_loader = MagicMock(spec=TaskDataLoader)
        self.main_screen = MagicMock()
        self.app = MagicMock()

    def test_refresh_ui_without_gantt_widget(self):
        """Test _refresh_ui handles missing gantt_widget gracefully."""
        self.main_screen.gantt_widget = None

        manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: self.main_screen,
            app=self.app,
        )

        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        gantt = create_gantt_viewmodel()
        task_data = create_task_data([task], [vm], gantt)

        manager._refresh_ui(task_data, keep_scroll_position=False)

        self.main_screen.refresh_tasks.assert_called_once()

    def test_refresh_ui_without_gantt_view_model(self):
        """Test _refresh_ui handles None gantt_view_model gracefully."""
        self.main_screen.gantt_widget = MagicMock()

        manager = TaskUIManager(
            state=self.state,
            task_data_loader=self.task_data_loader,
            main_screen_provider=lambda: self.main_screen,
            app=self.app,
        )

        task = create_task_dto(1, "Test Task", TaskStatus.PENDING)
        vm = create_task_viewmodel(1, "Test Task", TaskStatus.PENDING)
        task_data = TaskData(
            all_tasks=[task],
            task_list_output=TaskListOutput(
                tasks=[task],
                total_count=1,
                filtered_count=1,
                gantt_data=None,
            ),
            table_view_models=[vm],
            gantt_view_model=None,
        )

        manager._refresh_ui(task_data, keep_scroll_position=False)

        self.main_screen.gantt_widget.update_gantt.assert_not_called()
        self.main_screen.refresh_tasks.assert_called_once()


class TestTaskUIManagerWithoutErrorCallback:
    """Test TaskUIManager behavior without error callback."""

    @pytest.mark.asyncio
    async def test_connection_error_without_callback(self):
        """Test the worker handles an API error gracefully without a callback."""
        state = TUIState()
        task_data_loader = MagicMock(spec=TaskDataLoader)
        main_screen = MagicMock()
        main_screen.gantt_widget = MagicMock()

        manager = TaskUIManager(
            state=state,
            task_data_loader=task_data_loader,
            main_screen_provider=lambda: main_screen,
            app=MagicMock(),
        )

        task_data_loader.load_tasks.side_effect = ServerConnectionError(
            base_url="http://localhost:8000",
            original_error=ConnectionError("Connection refused"),
        )

        # Execute - should not raise even without an error callback
        await manager._load_tasks_worker(_DATE_RANGE, "id", False, False)

        assert state.tasks_cache == []
