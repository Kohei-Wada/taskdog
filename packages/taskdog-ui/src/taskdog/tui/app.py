"""Taskdog TUI application."""

from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.app import App
from textual.command import CommandPalette

if TYPE_CHECKING:
    from taskdog.infrastructure.api_client import TaskdogApiClient

from taskdog.presenters.gantt_presenter import GanttPresenter
from taskdog.presenters.table_presenter import TablePresenter
from taskdog.tui.commands.factory import CommandFactory
from taskdog.tui.context import TUIContext
from taskdog.tui.events import (
    GanttResizeRequested,
    TaskCreated,
    TaskDeleted,
    TasksRefreshed,
    TaskUpdated,
)
from taskdog.tui.palette.providers import (
    ExportCommandProvider,
    OptimizeCommandProvider,
    SortCommandProvider,
    SortOptionsProvider,
)
from taskdog.tui.screens.main_screen import MainScreen
from taskdog_core.application.queries.filters.non_archived_filter import (
    NonArchivedFilter,
)
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.holiday_checker import IHolidayChecker
from taskdog_core.shared.config_manager import Config, ConfigManager


def _get_css_paths() -> list[str | Path]:
    """Get CSS file paths using importlib.resources.

    This ensures CSS files are found regardless of how the package is installed.

    Returns:
        List of CSS file paths
    """
    try:
        # Use importlib.resources to locate the styles directory
        styles_dir = files("presentation.tui") / "styles"
        return [
            str(styles_dir / "theme.tcss"),
            str(styles_dir / "components.tcss"),
            str(styles_dir / "main.tcss"),
            str(styles_dir / "dialogs.tcss"),
        ]
    except Exception:
        # Fallback to __file__ for development
        styles_dir = Path(__file__).parent / "styles"
        return [
            styles_dir / "theme.tcss",
            styles_dir / "components.tcss",
            styles_dir / "main.tcss",
            styles_dir / "dialogs.tcss",
        ]


class TaskdogTUI(App):
    """Taskdog TUI application."""

    BINDINGS: ClassVar = [
        ("q", "quit", "Quit"),
        ("a", "add_task", "Add"),
        ("s", "start_task", "Start"),
        ("P", "pause_task", "Pause"),
        ("d", "done_task", "Done"),
        ("c", "cancel_task", "Cancel"),
        ("R", "reopen_task", "Reopen"),
        ("x", "delete_task", "Archive"),
        ("X", "hard_delete_task", "Delete"),
        ("r", "refresh", "Refresh"),
        ("i", "show_details", "Info"),
        ("e", "edit_task", "Edit"),
        ("v", "edit_note", "Edit Note"),
        ("t", "toggle_completed", "Toggle Done"),
        ("/", "show_search", "Search"),
        ("escape", "hide_search", "Clear Search"),
    ]

    # Register custom command providers
    COMMANDS = App.COMMANDS | {
        SortCommandProvider,
        OptimizeCommandProvider,
        ExportCommandProvider,
    }

    # Mapping of sort keys to display labels
    _SORT_KEY_LABELS: ClassVar[dict[str, str]] = {
        "deadline": "Deadline",
        "planned_start": "Planned Start",
        "priority": "Priority",
        "estimated_duration": "Duration",
        "id": "ID",
        "name": "Name",
    }

    # Load CSS from external files
    CSS_PATH: ClassVar[list[str | Path]] = _get_css_paths()

    # Disable mouse support
    ENABLE_MOUSE: ClassVar[bool] = False

    def __init__(
        self,
        api_client: "TaskdogApiClient",
        notes_repository: NotesRepository,
        config: Config | None = None,
        holiday_checker: IHolidayChecker | None = None,
        repository: TaskRepository | None = None,
        *args,
        **kwargs,
    ):
        """Initialize the TUI application.

        TUI now requires an API client connection to function.
        Local repository mode is no longer supported.

        Args:
            api_client: API client for server communication (required)
            notes_repository: Notes repository for notes file operations
            config: Application configuration (optional, loads from file by default)
            holiday_checker: Holiday checker for workday validation (optional)
            repository: Task repository (deprecated, kept for compatibility)
        """
        super().__init__(*args, **kwargs)
        from taskdog.infrastructure.api_client import TaskdogApiClient

        if not isinstance(api_client, TaskdogApiClient):
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                # Type annotation for api_client parameter
                pass

        self.api_client = api_client
        self.notes_repository = notes_repository
        self.config = config if config is not None else ConfigManager.load()
        self.holiday_checker = holiday_checker
        self.main_screen: MainScreen | None = None
        self._gantt_sort_by: str = "deadline"  # Default gantt sort order
        self._hide_completed: bool = False  # Default: show all tasks
        self._all_tasks: list = []  # Cache of all tasks for display filtering
        self._gantt_view_model = None  # Cache of gantt view model

        # Create dummy repository if not provided (for API-only mode)
        if repository is None:
            from taskdog_core.infrastructure.persistence.repository_factory import (
                RepositoryFactory,
            )

            repository = RepositoryFactory.create(self.config.storage)

        # Set repository after ensuring it's created
        self.repository = repository

        # Initialize TUIContext with API client
        self.context = TUIContext(
            api_client=self.api_client,
            config=self.config,
            notes_repository=notes_repository,
            holiday_checker=self.holiday_checker,
        )

        # Initialize presenters for view models
        self.table_presenter = TablePresenter(notes_repository)
        self.gantt_presenter = GanttPresenter(notes_repository)

        # Initialize CommandFactory for command execution
        self.command_factory = CommandFactory(self, self.context)

    # Action methods for command execution
    def action_refresh(self) -> None:
        """Refresh the task list."""
        self.command_factory.execute("refresh")

    def action_add_task(self) -> None:
        """Add a new task."""
        self.command_factory.execute("add_task")

    def action_start_task(self) -> None:
        """Start the selected task."""
        self.command_factory.execute("start_task")

    def action_pause_task(self) -> None:
        """Pause the selected task."""
        self.command_factory.execute("pause_task")

    def action_done_task(self) -> None:
        """Mark the selected task as done."""
        self.command_factory.execute("done_task")

    def action_cancel_task(self) -> None:
        """Cancel the selected task."""
        self.command_factory.execute("cancel_task")

    def action_reopen_task(self) -> None:
        """Reopen the selected task."""
        self.command_factory.execute("reopen_task")

    def action_delete_task(self) -> None:
        """Archive the selected task (soft delete)."""
        self.command_factory.execute("delete_task")

    def action_hard_delete_task(self) -> None:
        """Permanently delete the selected task."""
        self.command_factory.execute("hard_delete_task")

    def action_show_details(self) -> None:
        """Show details of the selected task."""
        self.command_factory.execute("show_details")

    def action_edit_task(self) -> None:
        """Edit the selected task."""
        self.command_factory.execute("edit_task")

    def action_edit_note(self) -> None:
        """Edit the note for the selected task."""
        self.command_factory.execute("edit_note")

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.main_screen = MainScreen()
        self.push_screen(self.main_screen)
        # Load tasks after screen is fully mounted
        self.call_after_refresh(self._load_tasks)
        # Start 1-second auto-refresh timer for elapsed time updates
        self.set_interval(1.0, self._refresh_elapsed_time)

    def _load_tasks(self, keep_scroll_position: bool = False):
        """Load tasks from repository and update both gantt and table.

        Args:
            keep_scroll_position: Whether to preserve scroll position during refresh

        Returns:
            List of loaded tasks
        """
        # Note: In API-only mode, tasks are fetched fresh from the API server
        # No need for repository.reload() - api_client always gets latest data

        # Always fetch all non-archived tasks from API and cache them
        task_filter = NonArchivedFilter()

        # Use API client to get fresh data from server
        task_list_output = self.api_client.list_tasks(
            filter_obj=task_filter, sort_by=self._gantt_sort_by, reverse=False
        )
        # Cache all tasks
        self._all_tasks = task_list_output.tasks

        # Apply display filter based on _hide_completed setting
        tasks = self._apply_display_filter(self._all_tasks)

        # Update gantt chart and table
        if self.main_screen:
            if self.main_screen.gantt_widget:
                # Calculate appropriate date range based on screen width
                from datetime import timedelta

                from taskdog_core.shared.utils.date_utils import get_previous_monday

                # Use gantt widget's display calculation if available
                widget = self.main_screen.gantt_widget
                display_days = (
                    widget._calculate_display_days()
                    if hasattr(widget, "_calculate_display_days")
                    else 28
                )
                start_date = get_previous_monday()
                end_date = start_date + timedelta(days=display_days - 1)

                # Get gantt DTO using API client (fetches fresh data from server)
                # Always fetch all tasks, filter will be applied to displayed tasks
                gantt_output = self.api_client.get_gantt_data(
                    filter_obj=NonArchivedFilter(),
                    sort_by=self._gantt_sort_by,
                    reverse=False,
                    start_date=start_date,
                    end_date=end_date,
                    holiday_checker=self.holiday_checker,
                )

                # Convert DTO to ViewModel using GanttPresenter directly
                gantt_view_model = self.gantt_presenter.present(gantt_output)
                # Cache gantt view model for toggle operations
                self._gantt_view_model = gantt_view_model

                # Extract task IDs for widget
                task_ids = [t.id for t in tasks]

                # Filter gantt view model to match displayed tasks
                filtered_task_ids = {t.id for t in tasks}
                filtered_gantt_tasks = [
                    task
                    for task in gantt_view_model.tasks
                    if task.id in filtered_task_ids
                ]

                # Create filtered GanttViewModel for display
                from taskdog.view_models.gantt_view_model import GanttViewModel

                filtered_gantt_vm = GanttViewModel(
                    tasks=filtered_gantt_tasks,
                    task_daily_hours=gantt_view_model.task_daily_hours,
                    daily_workload=gantt_view_model.daily_workload,
                    start_date=gantt_view_model.start_date,
                    end_date=gantt_view_model.end_date,
                    holidays=gantt_view_model.holidays,
                )

                self.main_screen.gantt_widget.update_gantt(
                    task_ids=task_ids,
                    gantt_view_model=filtered_gantt_vm,
                    sort_by=self._gantt_sort_by,
                    task_filter=NonArchivedFilter(),
                )

            if self.main_screen.task_table:
                # Create filtered TaskListOutput for presenter
                from taskdog_core.application.dto.task_list_output import TaskListOutput

                filtered_output = TaskListOutput(
                    tasks=tasks,
                    total_count=task_list_output.total_count,
                    filtered_count=len(tasks),
                )
                # Convert TaskListOutput to ViewModels using TablePresenter directly
                view_models = self.table_presenter.present(filtered_output)
                self.main_screen.task_table.refresh_tasks(
                    view_models, keep_scroll_position=keep_scroll_position
                )

        return tasks

    def _apply_display_filter(self, tasks: list) -> list:
        """Apply display filter based on _hide_completed setting.

        Args:
            tasks: List of all tasks

        Returns:
            Filtered list of tasks based on current display settings
        """
        if not self._hide_completed:
            return tasks

        # Filter out COMPLETED and CANCELED tasks when hide_completed is True
        from taskdog_core.domain.entities.task import TaskStatus

        return [
            task
            for task in tasks
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELED)
        ]

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
        from taskdog.tui.palette.providers import ExportFormatProvider

        self.push_screen(
            CommandPalette(
                providers=[ExportFormatProvider],
                placeholder="Select export format…",
            ),
        )

    def execute_export(self, format_key: str) -> None:
        """Execute export operation with selected format.

        Args:
            format_key: Export format (json, csv, markdown)
        """
        from datetime import datetime
        from pathlib import Path

        from taskdog.exporters import (
            CsvTaskExporter,
            JsonTaskExporter,
            MarkdownTableExporter,
        )

        try:
            # Get all tasks (no filtering)
            result = self.api_client.list_tasks(filter_obj=None)
            tasks = result.tasks

            # Determine file extension and exporter
            if format_key == "json":
                exporter = JsonTaskExporter()
                extension = "json"
            elif format_key == "csv":
                exporter = CsvTaskExporter()
                extension = "csv"
            elif format_key == "markdown":
                exporter = MarkdownTableExporter()
                extension = "md"
            else:
                self.notify(f"Unknown format: {format_key}", severity="error")
                return

            # Generate filename with current date
            today = datetime.now().strftime("%Y%m%d")
            filename = f"Taskdog_export_{today}.{extension}"

            # Use ~/Downloads directory
            downloads_dir = Path.home() / "Downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)
            output_path = downloads_dir / filename

            # Export tasks
            tasks_data = exporter.export(tasks)

            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(tasks_data)

            # Show success notification
            self.notify(
                f"Exported {len(tasks)} tasks to {output_path}", severity="information"
            )

        except Exception as e:
            self.notify(f"Export failed: {e}", severity="error")

    def set_sort_order(self, sort_key: str) -> None:
        """Set the sort order for Gantt chart and task list.

        Called when user selects a sort option from Command Palette.

        Args:
            sort_key: Sort key (deadline, planned_start, priority, id)
        """
        self._gantt_sort_by = sort_key

        # Post TasksRefreshed event to trigger UI refresh with new sort order
        self.post_message(TasksRefreshed())

        # Show notification message
        sort_label = self._SORT_KEY_LABELS.get(sort_key, sort_key)
        self.notify(f"Sorted by {sort_label}")

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
        self._hide_completed = not self._hide_completed

        # Apply filter to cached tasks without API reload
        if self._all_tasks and self.main_screen:
            tasks = self._apply_display_filter(self._all_tasks)

            # Update table view with filtered tasks
            if self.main_screen.task_table:
                from taskdog_core.application.dto.task_list_output import TaskListOutput

                filtered_output = TaskListOutput(
                    tasks=tasks,
                    total_count=len(self._all_tasks),
                    filtered_count=len(tasks),
                )
                view_models = self.table_presenter.present(filtered_output)
                self.main_screen.task_table.refresh_tasks(
                    view_models, keep_scroll_position=True
                )

            # Update gantt view with filtered tasks
            if self.main_screen.gantt_widget and self._gantt_view_model:
                # Create a filtered gantt view model
                filtered_task_ids = {t.id for t in tasks}
                filtered_gantt_tasks = [
                    task
                    for task in self._gantt_view_model.tasks
                    if task.id in filtered_task_ids
                ]

                # Create new GanttViewModel with filtered tasks
                from taskdog.view_models.gantt_view_model import GanttViewModel

                filtered_gantt_vm = GanttViewModel(
                    tasks=filtered_gantt_tasks,
                    task_daily_hours=self._gantt_view_model.task_daily_hours,
                    daily_workload=self._gantt_view_model.daily_workload,
                    start_date=self._gantt_view_model.start_date,
                    end_date=self._gantt_view_model.end_date,
                    holidays=self._gantt_view_model.holidays,
                )

                task_ids = [t.id for t in tasks]
                self.main_screen.gantt_widget.update_gantt(
                    task_ids=task_ids,
                    gantt_view_model=filtered_gantt_vm,
                    sort_by=self._gantt_sort_by,
                    task_filter=NonArchivedFilter(),
                )

        # Show notification
        status = "hidden" if self._hide_completed else "shown"
        self.notify(f"Completed tasks {status}")

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
    def on_task_created(self, event: TaskCreated) -> None:
        """Handle task created event.

        Args:
            event: TaskCreated event containing the new task
        """
        self._load_tasks(keep_scroll_position=True)

    def on_task_updated(self, event: TaskUpdated) -> None:
        """Handle task updated event.

        Args:
            event: TaskUpdated event containing the updated task
        """
        self._load_tasks(keep_scroll_position=True)

    def on_task_deleted(self, event: TaskDeleted) -> None:
        """Handle task deleted event.

        Args:
            event: TaskDeleted event containing the deleted task ID
        """
        self._load_tasks(keep_scroll_position=True)

    def on_tasks_refreshed(self, event: TasksRefreshed) -> None:
        """Handle tasks refreshed event.

        Args:
            event: TasksRefreshed event triggering a full reload
        """
        self._load_tasks(keep_scroll_position=True)

    def on_gantt_resize_requested(self, event: GanttResizeRequested) -> None:
        """Handle gantt resize event.

        Recalculates gantt data for the new display width and updates the widget.

        Args:
            event: GanttResizeRequested event containing display parameters
        """
        if not self.main_screen or not self.main_screen.gantt_widget:
            return

        gantt_widget = self.main_screen.gantt_widget

        # Get the current filter from the gantt widget
        task_filter = (
            gantt_widget._task_filter if hasattr(gantt_widget, "_task_filter") else None
        )
        sort_by = (
            gantt_widget._sort_by if hasattr(gantt_widget, "_sort_by") else "deadline"
        )

        # Get gantt data from API client with the new date range
        gantt_output = self.api_client.get_gantt_data(
            filter_obj=task_filter,
            sort_by=sort_by,
            reverse=False,
            start_date=event.start_date,
            end_date=event.end_date,
            holiday_checker=self.holiday_checker,
        )

        # Convert to ViewModel using GanttPresenter
        gantt_view_model = self.gantt_presenter.present(gantt_output)

        # Update the gantt widget's view model
        gantt_widget._gantt_view_model = gantt_view_model

        # Trigger re-render with updated view model
        gantt_widget.call_after_refresh(gantt_widget._render_gantt)
