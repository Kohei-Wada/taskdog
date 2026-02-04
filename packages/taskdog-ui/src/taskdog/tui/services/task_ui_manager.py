"""Task UI Manager for orchestrating data lifecycle in TUI."""

from collections.abc import Callable
from datetime import date, timedelta
from typing import TYPE_CHECKING

from taskdog.services.task_data_loader import TaskData, TaskDataLoader
from taskdog.tui.constants.ui_settings import DEFAULT_GANTT_DISPLAY_DAYS
from taskdog.tui.state import TUIState
from taskdog.view_models.gantt_view_model import GanttViewModel
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.domain.exceptions.task_exceptions import (
    AuthenticationError,
    ServerConnectionError,
    ServerError,
)

if TYPE_CHECKING:
    from taskdog.tui.screens.main_screen import MainScreen


class TaskUIManager:
    """Manages task data lifecycle for TUI.

    Orchestrates data fetching, caching, and UI updates.
    Separates data management concerns from the App class.

    Attributes:
        state: Shared TUIState instance (Single Source of Truth)
        task_data_loader: Service for loading task data from API
    """

    def __init__(
        self,
        state: TUIState,
        task_data_loader: TaskDataLoader,
        main_screen_provider: Callable[[], "MainScreen | None"],
        on_connection_error: Callable[[ServerConnectionError], None] | None = None,
        on_auth_error: Callable[[AuthenticationError], None] | None = None,
        on_server_error: Callable[[ServerError], None] | None = None,
    ):
        """Initialize TaskUIManager.

        Args:
            state: Shared TUIState instance
            task_data_loader: Service for loading task data
            main_screen_provider: Callable that returns current MainScreen (lazy access)
            on_connection_error: Optional callback for connection errors
            on_auth_error: Optional callback for authentication errors
            on_server_error: Optional callback for server errors (5xx)
        """
        self.state = state
        self.task_data_loader = task_data_loader
        self._get_main_screen = main_screen_provider
        self._on_connection_error = on_connection_error
        self._on_auth_error = on_auth_error
        self._on_server_error = on_server_error

    def load_tasks(self, keep_scroll_position: bool = False) -> None:
        """Load tasks and update UI.

        Performs a complete reload cycle: fetches data from API,
        updates internal caches, and refreshes all UI components.

        Args:
            keep_scroll_position: Whether to preserve scroll position during refresh
        """
        task_data = self._fetch_task_data()
        self._update_cache(task_data)
        self._refresh_ui(task_data, keep_scroll_position)

    def _calculate_gantt_date_range(self) -> tuple[date, date]:
        """Calculate the date range for Gantt chart display.

        Returns:
            Tuple of (start_date, end_date) for Gantt chart
        """
        main_screen = self._get_main_screen()
        if main_screen and main_screen.gantt_widget:
            return main_screen.gantt_widget.calculate_date_range()

        # Fallback when gantt_widget is not available
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=DEFAULT_GANTT_DISPLAY_DAYS - 1)
        return (start_date, end_date)

    def _fetch_task_data(self) -> TaskData:
        """Fetch task data using TaskDataLoader.

        Returns:
            TaskData object containing all task information
        """
        try:
            date_range = self._calculate_gantt_date_range()

            return self.task_data_loader.load_tasks(
                all=False,  # Non-archived by default
                sort_by=self.state.sort_by,
                reverse=self.state.sort_reverse,
                date_range=date_range,
            )
        except ServerConnectionError as e:
            if self._on_connection_error:
                self._on_connection_error(e)

            return self._create_empty_task_data()
        except AuthenticationError as e:
            if self._on_auth_error:
                self._on_auth_error(e)

            return self._create_empty_task_data()
        except ServerError as e:
            if self._on_server_error:
                self._on_server_error(e)

            return self._create_empty_task_data()

    def _create_empty_task_data(self) -> TaskData:
        """Create empty TaskData to avoid crash on errors.

        Returns:
            Empty TaskData object
        """
        empty_task_list_output = TaskListOutput(
            tasks=[],
            total_count=0,
            filtered_count=0,
            gantt_data=None,
        )

        return TaskData(
            all_tasks=[],
            filtered_tasks=[],
            task_list_output=empty_task_list_output,
            table_view_models=[],
            gantt_view_model=None,
            filtered_gantt_view_model=None,
        )

    def _update_cache(self, task_data: TaskData) -> None:
        """Update internal cache with task data.

        Args:
            task_data: TaskData object to cache
        """
        self.state.update_caches(
            tasks=task_data.all_tasks,
            viewmodels=task_data.table_view_models,
            gantt=task_data.gantt_view_model,
        )

    def _refresh_ui(self, task_data: TaskData, keep_scroll_position: bool) -> None:
        """Refresh UI widgets with task data.

        Args:
            task_data: TaskData object containing view models
            keep_scroll_position: Whether to preserve scroll position
        """
        main_screen = self._get_main_screen()
        if not main_screen:
            return

        # Update Gantt widget
        if main_screen.gantt_widget and task_data.filtered_gantt_view_model:
            task_ids = [t.id for t in task_data.filtered_tasks]
            main_screen.gantt_widget.update_gantt(
                task_ids=task_ids,
                gantt_view_model=task_data.filtered_gantt_view_model,
                sort_by=self.state.sort_by,
                reverse=self.state.sort_reverse,
                all=False,  # Non-archived by default
                keep_scroll_position=keep_scroll_position,
            )

        # Update Table widget (via main_screen to update search result count)
        main_screen.refresh_tasks(
            task_data.table_view_models,
            keep_scroll_position=keep_scroll_position,
        )

    def recalculate_gantt(self, start_date: date, end_date: date) -> None:
        """Recalculate gantt data for a new date range.

        Called when gantt widget is resized and needs recalculation
        with a different date range.

        Args:
            start_date: New start date for gantt range
            end_date: New end date for gantt range
        """
        try:
            gantt_view_model = self._fetch_gantt_for_range(start_date, end_date)
            self._update_gantt_ui(gantt_view_model)
        except ServerConnectionError as e:
            if self._on_connection_error:
                self._on_connection_error(e)
        except AuthenticationError as e:
            if self._on_auth_error:
                self._on_auth_error(e)
        except ServerError as e:
            if self._on_server_error:
                self._on_server_error(e)

    def _fetch_gantt_for_range(
        self, start_date: date, end_date: date
    ) -> GanttViewModel | None:
        """Fetch gantt data for specific date range.

        Args:
            start_date: Start date for gantt range
            end_date: End date for gantt range

        Returns:
            GanttViewModel or None if no data
        """
        # Get current filter/sort state from gantt widget if available
        all_tasks = False  # Default to non-archived
        sort_by = self.state.sort_by
        main_screen = self._get_main_screen()
        if main_screen and main_screen.gantt_widget:
            all_tasks = main_screen.gantt_widget.get_filter_all()
            sort_by = main_screen.gantt_widget.get_sort_by()

        task_list_output = self.task_data_loader.api_client.list_tasks(
            all=all_tasks,
            sort_by=sort_by,
            reverse=self.state.sort_reverse,
            include_gantt=True,
            gantt_start_date=start_date,
            gantt_end_date=end_date,
        )

        if not task_list_output.gantt_data:
            return None

        gantt_view_model = self.task_data_loader.gantt_presenter.present(
            task_list_output.gantt_data
        )

        return gantt_view_model

    def _update_gantt_ui(self, gantt_view_model: GanttViewModel | None) -> None:
        """Update gantt widget with new view model.

        Args:
            gantt_view_model: New gantt view model to display
        """
        main_screen = self._get_main_screen()
        if not main_screen or not main_screen.gantt_widget:
            return

        if gantt_view_model:
            main_screen.gantt_widget.update_view_model_and_render(gantt_view_model)
