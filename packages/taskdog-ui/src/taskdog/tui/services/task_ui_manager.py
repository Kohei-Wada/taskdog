"""Task UI Manager for orchestrating data lifecycle in TUI."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from taskdog.constants.gantt import MIN_GANTT_DISPLAY_DAYS
from taskdog.services.task_data_loader import TaskData, TaskDataLoader
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


@dataclass(frozen=True)
class FetchParams:
    """Parameters for a task-list fetch, gathered on the UI thread.

    Captures all UI/state-derived inputs (sort, archive filter, gantt window)
    up front so the actual fetch can run on a worker thread without touching
    any widget or app state.
    """

    include_archived: bool
    sort_by: str
    reverse: bool
    date_range: tuple[date, date]


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
        on_error: Callable[
            [ServerConnectionError | AuthenticationError | ServerError], None
        ]
        | None = None,
    ):
        """Initialize TaskUIManager.

        Args:
            state: Shared TUIState instance
            task_data_loader: Service for loading task data
            main_screen_provider: Callable that returns current MainScreen (lazy access)
            on_error: Optional callback for API errors (connection, auth, server)
        """
        self.state = state
        self.task_data_loader = task_data_loader
        self._get_main_screen = main_screen_provider
        self._on_error = on_error

    def handle_api_error(
        self, error: ServerConnectionError | AuthenticationError | ServerError
    ) -> None:
        """Delegate API error to the error callback (UI thread only).

        Args:
            error: The API error to handle
        """
        if self._on_error:
            self._on_error(error)

    def load_tasks(self, keep_scroll_position: bool = False) -> None:
        """Load tasks and update UI synchronously.

        Performs a complete reload cycle on the calling thread: fetches data
        from the API, updates internal caches, and refreshes all UI components.
        Used for the initial load and tests; the app's debounced funnel runs
        the same steps off the UI thread (see ``gather_fetch_params`` /
        ``fetch_with_params`` / ``apply_task_data``).

        Args:
            keep_scroll_position: Whether to preserve scroll position during refresh
        """
        task_data = self._fetch_task_data()
        self.apply_task_data(task_data, keep_scroll_position)

    def gather_fetch_params(self) -> FetchParams:
        """Collect fetch inputs from UI/state. Must run on the UI thread.

        Returns:
            FetchParams snapshot to hand to ``fetch_with_params``.
        """
        return FetchParams(
            include_archived=self.state.show_archived,
            sort_by=self.state.sort_by,
            reverse=self.state.sort_reverse,
            date_range=self._calculate_gantt_date_range(),
        )

    def fetch_with_params(self, params: FetchParams) -> TaskData:
        """Fetch task data for the given params. Thread-safe; touches no UI.

        Raises the underlying API exception on failure so the caller can
        decide how to surface it (the UI-thread error callback must not run
        here).

        Args:
            params: Snapshot from ``gather_fetch_params``.

        Returns:
            Loaded TaskData.
        """
        return self.task_data_loader.load_tasks(
            include_archived=params.include_archived,
            sort_by=params.sort_by,
            reverse=params.reverse,
            date_range=params.date_range,
        )

    def apply_task_data(
        self, task_data: TaskData, keep_scroll_position: bool = False
    ) -> None:
        """Update caches and refresh widgets. Must run on the UI thread.

        Args:
            task_data: Data to cache and render
            keep_scroll_position: Whether to preserve scroll position during refresh
        """
        self._update_cache(task_data)
        self._refresh_ui(task_data, keep_scroll_position)

    def _calculate_gantt_date_range(self) -> tuple[date, date]:
        """Calculate the date range for Gantt chart display.

        The window has a fixed width; the gantt widget's pan offset shifts it
        through time, so archived/past tasks are viewed by panning rather than
        unbounded expansion.

        Returns:
            Tuple of (start_date, end_date) for Gantt chart
        """
        main_screen = self._get_main_screen()
        if main_screen and main_screen.gantt_widget:
            return main_screen.gantt_widget.calculate_date_range()

        # Fallback when gantt_widget is not available
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=MIN_GANTT_DISPLAY_DAYS - 1)
        return (start_date, end_date)

    def _fetch_task_data(self) -> TaskData:
        """Fetch task data, handling API errors gracefully (UI thread).

        Returns:
            TaskData object containing all task information (empty on error)
        """
        params = self.gather_fetch_params()
        try:
            return self.fetch_with_params(params)
        except (ServerConnectionError, AuthenticationError, ServerError) as e:
            self.handle_api_error(e)
            return self.empty_task_data()
        except Exception:
            return self.empty_task_data()

    def empty_task_data(self) -> TaskData:
        """Create empty TaskData to avoid crash on errors. Thread-safe.

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
            task_list_output=empty_task_list_output,
            table_view_models=[],
            gantt_view_model=None,
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

        State caches are already updated by _update_cache() before this is called.
        GanttWidget reads from TUIState.gantt_cache (set by _update_cache).

        Args:
            task_data: TaskData object containing view models
            keep_scroll_position: Whether to preserve scroll position
        """
        main_screen = self._get_main_screen()
        if not main_screen:
            return

        # Update Gantt widget (reads gantt data from TUIState.gantt_cache)
        if main_screen.gantt_widget and task_data.gantt_view_model:
            task_ids = [t.id for t in task_data.all_tasks]
            main_screen.gantt_widget.update_gantt(
                task_ids=task_ids,
                keep_scroll_position=keep_scroll_position,
            )

        # Update Table widget (reads from TUIState.filtered_viewmodels)
        main_screen.refresh_tasks(keep_scroll_position=keep_scroll_position)

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
        except (ServerConnectionError, AuthenticationError, ServerError) as e:
            self.handle_api_error(e)
        except Exception:
            pass

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
        # Get current sort state from gantt widget if available
        sort_by = self.state.sort_by
        main_screen = self._get_main_screen()
        if main_screen and main_screen.gantt_widget:
            sort_by = main_screen.gantt_widget.get_sort_by()

        task_list_output = self.task_data_loader.api_client.list_tasks(
            include_archived=self.state.show_archived,
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
        """Update gantt cache in State and tell widget to re-render.

        Args:
            gantt_view_model: New gantt view model to display
        """
        if not gantt_view_model:
            return

        # Write to State first (single source of truth)
        self.state.gantt_cache = gantt_view_model

        main_screen = self._get_main_screen()
        if main_screen and main_screen.gantt_widget:
            # Preserve cursor/scroll on zoom & pan (range change = full rebuild)
            main_screen.gantt_widget.update_view_model_and_render(
                keep_scroll_position=True
            )
