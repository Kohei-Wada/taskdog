"""Taskdog TUI application."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from textual.app import App
from textual.binding import Binding
from textual.command import CommandPalette

if TYPE_CHECKING:
    from taskdog.infrastructure.api_client import TaskdogApiClient

from taskdog.infrastructure.websocket import WebSocketClient
from taskdog.presenters.gantt_presenter import GanttPresenter
from taskdog.presenters.table_presenter import TablePresenter
from taskdog.services.task_data_loader import TaskDataLoader
from taskdog.tui.commands.factory import CommandFactory
from taskdog.tui.constants.ui_settings import (
    ACTION_TO_COMMAND_MAP,
    AUTO_REFRESH_INTERVAL_SECONDS,
    DEFAULT_GANTT_DISPLAY_DAYS,
    SORT_KEY_LABELS,
)
from taskdog.tui.context import TUIContext
from taskdog.tui.events import GanttResizeRequested, TasksRefreshed
from taskdog.tui.palette.providers import (
    ExportCommandProvider,
    ExportFormatProvider,
    HelpCommandProvider,
    OptimizeCommandProvider,
    SortCommandProvider,
    SortOptionsProvider,
)
from taskdog.tui.screens.main_screen import MainScreen
from taskdog.tui.services.websocket_handler import WebSocketHandler
from taskdog.tui.state import TUIState
from taskdog.tui.utils.css_loader import get_css_paths
from taskdog_core.domain.exceptions.task_exceptions import ServerConnectionError
from taskdog_core.shared.config_manager import Config, ConfigManager


class TaskdogTUI(App):
    """Taskdog TUI application."""

    BINDINGS: ClassVar = [
        Binding(
            "q",
            "quit",
            "Quit",
            show=True,
            tooltip="Quit the app and return to the command prompt",
        ),
        Binding("a", "add", "Add", show=True, tooltip="Create a new task"),
        Binding("s", "start", "Start", show=False, tooltip="Start the selected task"),
        Binding(
            "P",
            "pause",
            "Pause",
            show=False,
            tooltip="Pause the selected task and reset to PENDING status",
        ),
        Binding(
            "d",
            "done",
            "Done",
            show=False,
            tooltip="Mark the selected task as completed",
        ),
        Binding(
            "c", "cancel", "Cancel", show=False, tooltip="Cancel the selected task"
        ),
        Binding(
            "R",
            "reopen",
            "Reopen",
            show=False,
            tooltip="Reopen a completed or canceled task",
        ),
        Binding(
            "x",
            "rm",
            "Archive",
            show=False,
            tooltip="Archive the selected task (soft delete)",
        ),
        Binding(
            "X",
            "hard_delete",
            "Delete",
            show=False,
            tooltip="Permanently delete the selected task",
        ),
        Binding(
            "r",
            "refresh",
            "Refresh",
            show=True,
            tooltip="Refresh the task list from the server",
        ),
        Binding(
            "i",
            "show",
            "Info",
            show=False,
            tooltip="Show detailed information about the selected task",
        ),
        Binding(
            "e",
            "edit",
            "Edit",
            show=False,
            tooltip="Edit the selected task's properties",
        ),
        Binding(
            "v",
            "note",
            "Edit Note",
            show=False,
            tooltip="Edit markdown notes for the selected task",
        ),
        Binding(
            "t",
            "toggle_completed",
            "Toggle Done",
            show=False,
            tooltip="Toggle visibility of completed and canceled tasks",
        ),
        Binding(
            "/", "show_search", "Search", show=False, tooltip="Search for tasks by name"
        ),
        Binding(
            "ctrl+r",
            "show_search",
            "Search",
            show=False,
            tooltip="Search for tasks by name",
        ),
        Binding(
            "escape",
            "hide_search",
            "Clear Search",
            show=False,
            tooltip="Clear the search filter and show all tasks",
        ),
        Binding(
            "ctrl+t",
            "toggle_sort_reverse",
            "Toggle Sort",
            show=False,
            tooltip="Toggle sort direction (ascending ⇔ descending)",
        ),
        Binding(
            "?",
            "show_help",
            "Help",
            show=True,
            tooltip="Show help screen with keybindings and usage instructions",
        ),
    ]

    # Register custom command providers
    COMMANDS = App.COMMANDS | {
        SortCommandProvider,
        OptimizeCommandProvider,
        ExportCommandProvider,
        HelpCommandProvider,
    }

    # Load CSS from external files
    CSS_PATH: ClassVar[list[str | Path]] = get_css_paths()

    # Enable mouse support
    ENABLE_MOUSE: ClassVar[bool] = True

    def __init__(
        self,
        api_client: "TaskdogApiClient",
        config: Config | None = None,
        *args,
        **kwargs,
    ):
        """Initialize the TUI application.

        TUI operates through the API client for all task operations.
        Notes are managed via API client as well.

        Args:
            api_client: API client for server communication (required)
            config: Application configuration (optional, loads from file by default)
        """
        super().__init__(*args, **kwargs)
        from taskdog.infrastructure.api_client import TaskdogApiClient

        if not isinstance(api_client, TaskdogApiClient):
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                # Type annotation for api_client parameter
                pass

        self.api_client = api_client
        self.config = config if config is not None else ConfigManager.load()
        self.main_screen: MainScreen | None = None

        # Initialize TUI state (Single Source of Truth for all app state)
        self.state = TUIState()

        # NOTE: All legacy state fields migrated to self.state (Phase 2 complete)
        # - _gantt_sort_by, _gantt_reverse, _hide_completed → state (Step 2-3)
        # - _all_tasks, _gantt_view_model → state (Step 4)
        # - viewmodels → state (Step 5)

        # Initialize TUIContext with API client and state
        self.context = TUIContext(
            api_client=self.api_client,
            config=self.config,
            state=self.state,  # Share same state instance
        )

        # Initialize presenters for view models (will be updated to not use notes_repository)
        self.table_presenter = TablePresenter(api_client)
        self.gantt_presenter = GanttPresenter(api_client)

        # Initialize TaskDataLoader for data fetching
        self.task_data_loader = TaskDataLoader(
            api_client=self.api_client,
            table_presenter=self.table_presenter,
            gantt_presenter=self.gantt_presenter,
        )

        # Initialize CommandFactory for command execution
        self.command_factory = CommandFactory(self, self.context)

        # Initialize WebSocket handler for message processing
        self.websocket_handler = WebSocketHandler(self)

        # Initialize WebSocket client for real-time updates
        ws_url = self._get_websocket_url()
        self.websocket_client = WebSocketClient(ws_url, self._handle_websocket_message)

    def _get_websocket_url(self) -> str:
        """Get WebSocket URL from API client configuration.

        Returns:
            WebSocket URL (e.g., "ws://127.0.0.1:8000/ws")
        """
        # Convert HTTP URL to WebSocket URL
        http_url = self.api_client.base_url
        ws_url = http_url.replace("http://", "ws://").replace("https://", "wss://")
        return f"{ws_url}/ws"

    def _handle_websocket_message(self, message: dict[str, Any]) -> None:
        """Handle incoming WebSocket messages.

        Delegates message handling to WebSocketHandler for separation of concerns.

        Args:
            message: WebSocket message dictionary
        """
        self.websocket_handler.handle_message(message)

    def __getattr__(self, name: str):
        """Dynamically handle action_* methods by delegating to command_factory.

        This eliminates the need for 12 nearly-identical action methods.
        When Textual calls action_foo(), this method intercepts it and
        executes the corresponding "foo" command via command_factory.

        Args:
            name: Attribute name being accessed

        Returns:
            Callable that executes the corresponding command

        Raises:
            AttributeError: If the attribute doesn't match an action pattern
        """
        if name in ACTION_TO_COMMAND_MAP:
            command_name = ACTION_TO_COMMAND_MAP[name]

            def execute_command() -> None:
                self.command_factory.execute(command_name)

            return execute_command

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    async def on_mount(self) -> None:
        """Called when app is mounted."""
        self.main_screen = MainScreen(state=self.state)
        self.push_screen(self.main_screen)
        # Load tasks after screen is fully mounted
        self.call_after_refresh(self._load_tasks)
        # Start auto-refresh timer for elapsed time updates
        self.set_interval(AUTO_REFRESH_INTERVAL_SECONDS, self._refresh_elapsed_time)
        # Start connection monitoring timer (check every 3 seconds)
        self.set_interval(3.0, self._check_connection_status)
        # Connect to WebSocket for real-time updates
        await self.websocket_client.connect()
        # Initial connection status check (delayed to allow WebSocket connection to stabilize)
        self.call_later(self._check_connection_status)

    async def on_unmount(self) -> None:
        """Called when app is unmounted."""
        # Disconnect WebSocket
        await self.websocket_client.disconnect()

    def _load_tasks(self, keep_scroll_position: bool = False):
        """Load tasks from repository and update both gantt and table.

        Args:
            keep_scroll_position: Whether to preserve scroll position during refresh

        Returns:
            List of loaded tasks
        """
        task_data = self._fetch_task_data()
        self._update_cache(task_data)
        self._refresh_ui(task_data, keep_scroll_position)
        return task_data.filtered_tasks

    def _calculate_gantt_date_range(self):
        """Calculate the date range for Gantt chart display.

        Returns:
            Tuple of (start_date, end_date) for Gantt chart
        """
        if self.main_screen and self.main_screen.gantt_widget:
            # Use GanttWidget's public API instead of private method access
            return self.main_screen.gantt_widget.calculate_date_range()

        # Fallback when gantt_widget is not available
        from datetime import date, timedelta

        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=DEFAULT_GANTT_DISPLAY_DAYS - 1)
        return (start_date, end_date)

    def _fetch_task_data(self):
        """Fetch task data using TaskDataLoader.

        Returns:
            TaskData object containing all task information, or None if connection fails
        """
        try:
            date_range = self._calculate_gantt_date_range()

            return self.task_data_loader.load_tasks(
                all=False,  # Non-archived by default
                sort_by=self.state.sort_by,
                reverse=self.state.sort_reverse,
                hide_completed=self.state.hide_completed,
                date_range=date_range,
            )
        except ServerConnectionError as e:
            self.notify(
                f"Server connection failed: {
                    e.original_error.__class__.__name__
                }. Press 'r' to retry.",
                severity="error",
                timeout=10,
            )
            # Return empty task data to avoid crash
            from taskdog.services.task_data_loader import TaskData
            from taskdog_core.application.dto.task_list_output import TaskListOutput

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

    def _update_cache(self, task_data) -> None:
        """Update internal cache with task data.

        Args:
            task_data: TaskData object to cache
        """
        # Update TUIState cache (Phase 2 complete: Steps 4 + 5)
        self.state.update_caches(
            tasks=task_data.all_tasks,
            viewmodels=task_data.table_view_models,
            gantt=task_data.gantt_view_model,
        )

    def _refresh_ui(self, task_data, keep_scroll_position: bool) -> None:
        """Refresh UI widgets with task data.

        Args:
            task_data: TaskData object containing view models
            keep_scroll_position: Whether to preserve scroll position
        """
        if not self.main_screen:
            return

        # Update Gantt widget
        if self.main_screen.gantt_widget and task_data.filtered_gantt_view_model:
            task_ids = [t.id for t in task_data.filtered_tasks]
            self.main_screen.gantt_widget.update_gantt(
                task_ids=task_ids,
                gantt_view_model=task_data.filtered_gantt_view_model,
                sort_by=self.state.sort_by,
                reverse=self.state.sort_reverse,
                all=False,  # Non-archived by default
            )

        # Update Table widget
        if self.main_screen.task_table:
            self.main_screen.task_table.refresh_tasks(
                task_data.table_view_models,
                keep_scroll_position=keep_scroll_position,
            )

    def search_sort(self) -> None:
        """Show a fuzzy search command palette containing all sort options.

        Selecting a sort option will change the sort order.
        """
        self.push_screen(
            CommandPalette(
                providers=[SortOptionsProvider],
                placeholder="Search for sort options…",
            ),
        )

    def search_optimize(self, force_override: bool = False) -> None:
        """Show optimization algorithm selection dialog.

        Args:
            force_override: Whether to force override existing schedules
        """
        # Execute optimize command which will show AlgorithmSelectionScreen
        self.command_factory.execute("optimize", force_override=force_override)

    def search_export(self) -> None:
        """Show a fuzzy search command palette containing all export format options.

        Selecting a format will trigger the export operation.
        """
        self.push_screen(
            CommandPalette(
                providers=[ExportFormatProvider],
                placeholder="Select export format…",
            ),
        )

    def search_help(self) -> None:
        """Show the help screen with keybindings and usage instructions."""
        self.command_factory.execute("show_help")

    def set_sort_order(self, sort_key: str) -> None:
        """Set the sort order for Gantt chart and task list.

        Called when user selects a sort option from Command Palette.

        Args:
            sort_key: Sort key (deadline, planned_start, priority, id)
        """
        self.state.sort_by = sort_key

        # Post TasksRefreshed event to trigger UI refresh with new sort order
        self.post_message(TasksRefreshed())

        # Show notification message with current direction
        sort_label = SORT_KEY_LABELS.get(sort_key, sort_key)
        arrow = "↓" if self.state.sort_reverse else "↑"
        direction = "descending" if self.state.sort_reverse else "ascending"
        self.notify(f"Sorted by {sort_label} {arrow} ({direction})")

    def action_show_search(self) -> None:
        """Show the search input."""
        if self.main_screen:
            self.main_screen.show_search()

    def action_hide_search(self) -> None:
        """Hide the search input and clear the filter."""
        if self.main_screen:
            self.main_screen.hide_search()

    def action_toggle_completed(self) -> None:
        """Toggle visibility of completed and canceled tasks."""
        self.state.hide_completed = not self.state.hide_completed

        # Reload tasks with new filter to recalculate gantt date range
        self._load_tasks(keep_scroll_position=True)

        # Show notification
        status = "hidden" if self.state.hide_completed else "shown"
        self.notify(f"Completed tasks {status}")

    def action_toggle_sort_reverse(self) -> None:
        """Toggle sort direction (ascending ⇔ descending)."""
        self.state.sort_reverse = not self.state.sort_reverse

        # Reload tasks with new sort direction
        self._load_tasks(keep_scroll_position=True)

        # Show notification with current direction
        direction = "descending" if self.state.sort_reverse else "ascending"
        sort_label = SORT_KEY_LABELS.get(self.state.sort_by, self.state.sort_by)
        arrow = "↓" if self.state.sort_reverse else "↑"
        self.notify(f"Sort direction toggled: {sort_label} {arrow} ({direction})")

    def action_command_palette(self) -> None:
        """Show the command palette."""
        self.push_screen(CommandPalette())

    def _refresh_elapsed_time(self) -> None:
        """Refresh the task table to update elapsed time for IN_PROGRESS tasks.

        This is called every second by the auto-refresh timer.
        Only updates the table display without reloading from repository.
        """
        if self.main_screen and self.main_screen.task_table:
            # Get current ViewModels from the table (already loaded in memory)
            view_models = self.main_screen.task_table.all_viewmodels
            if view_models:
                # Refresh the table display with current ViewModels
                # This will recalculate elapsed time for IN_PROGRESS tasks
                # Keep scroll position to avoid stuttering during user navigation
                self.main_screen.task_table.refresh_tasks(
                    view_models, keep_scroll_position=True
                )

    # Event handlers for task operations
    def _handle_task_change_event(self, event) -> None:
        """Handle any task change event by reloading tasks.

        This generic handler is used for all task modification events
        (created, updated, deleted, refreshed) as they all require
        the same response: reload tasks with scroll position preserved.

        Args:
            event: Task change event (TaskCreated/Updated/Deleted/Refreshed)
        """
        self._load_tasks(keep_scroll_position=True)

    # Alias all task change event handlers to the generic handler
    on_task_created = _handle_task_change_event
    on_task_updated = _handle_task_change_event
    on_task_deleted = _handle_task_change_event
    on_tasks_refreshed = _handle_task_change_event

    def on_gantt_resize_requested(self, event: GanttResizeRequested) -> None:
        """Handle gantt resize event.

        Recalculates gantt data for the new display width and updates the widget.

        Args:
            event: GanttResizeRequested event containing display parameters
        """
        if not self.main_screen or not self.main_screen.gantt_widget:
            return

        gantt_widget = self.main_screen.gantt_widget

        try:
            # Use public API to get current filter and sort order
            all = gantt_widget.get_filter_all()
            sort_by = gantt_widget.get_sort_by()

            # Use integrated API to get tasks + gantt data in single request
            task_list_output = self.api_client.list_tasks(
                all=all,
                sort_by=sort_by,
                reverse=self.state.sort_reverse,
                include_gantt=True,
                gantt_start_date=event.start_date,
                gantt_end_date=event.end_date,
            )

            # Convert gantt data to ViewModel
            if task_list_output.gantt_data:
                gantt_view_model = self.gantt_presenter.present(
                    task_list_output.gantt_data
                )

                # Apply display filter based on hide_completed setting
                if self.state.hide_completed:
                    filtered_tasks = self.task_data_loader.apply_display_filter(
                        task_list_output.tasks, self.state.hide_completed
                    )
                    gantt_view_model = self.task_data_loader.filter_gantt_by_tasks(
                        gantt_view_model, filtered_tasks
                    )

                # Use public API to update view model and trigger re-render
                gantt_widget.update_view_model_and_render(gantt_view_model)
        except ServerConnectionError as e:
            self.notify(
                f"Server connection failed: {e.original_error.__class__.__name__}",
                severity="error",
            )

    def _check_connection_status(self) -> None:
        """Check API and WebSocket connection status.

        Updates TUIState with current connection status and refreshes
        the CustomFooter widget display.
        """
        # Check API connection via health endpoint
        api_connected = self.api_client.check_health()

        # Check WebSocket connection
        ws_connected = self.websocket_client.is_connected()

        # Update state
        self.state.update_connection_status(api_connected, ws_connected)

        # Refresh CustomFooter widget if available
        if self.main_screen and self.main_screen.custom_footer:
            self.main_screen.custom_footer.refresh_from_state()
