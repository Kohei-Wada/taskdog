"""Taskdog TUI application."""

from importlib.resources import files
from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.command import CommandPalette

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.incomplete_or_active_filter import (
    IncompleteOrActiveFilter,
)
from application.queries.filters.non_archived_filter import NonArchivedFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task
from domain.repositories.notes_repository import NotesRepository
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from presentation.controllers.query_controller import QueryController
from presentation.controllers.task_controller import TaskController
from presentation.mappers.task_mapper import TaskMapper
from presentation.tui.commands.factory import CommandFactory
from presentation.tui.context import TUIContext
from presentation.tui.events import TaskCreated, TaskDeleted, TasksRefreshed, TaskUpdated
from presentation.tui.palette.providers import (
    OptimizeCommandProvider,
    SortCommandProvider,
    SortOptionsProvider,
)
from presentation.tui.screens.main_screen import MainScreen
from presentation.tui.services.task_service import TaskService
from shared.config_manager import Config, ConfigManager


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
    COMMANDS = App.COMMANDS | {SortCommandProvider, OptimizeCommandProvider}

    # Mapping of sort keys to display labels
    _SORT_KEY_LABELS: ClassVar[dict[str, str]] = {
        "deadline": "Deadline",
        "planned_start": "Planned Start",
        "priority": "Priority",
        "estimated_duration": "Duration",
        "id": "ID",
    }

    # Load CSS from external files
    CSS_PATH: ClassVar[list[str | Path]] = _get_css_paths()

    # Disable mouse support
    ENABLE_MOUSE: ClassVar[bool] = False

    def __init__(
        self,
        repository: TaskRepository,
        time_tracker: TimeTracker,
        notes_repository: NotesRepository,
        config: Config | None = None,
        *args,
        **kwargs,
    ):
        """Initialize the TUI application.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker service
            notes_repository: Notes repository for notes file operations
            config: Application configuration (optional, loads from file by default)
        """
        super().__init__(*args, **kwargs)
        self.repository = repository
        self.time_tracker = time_tracker
        self.notes_repository = notes_repository
        self.query_service = TaskQueryService(repository)
        self.config = config if config is not None else ConfigManager.load()
        self.main_screen: MainScreen | None = None
        self._gantt_sort_by: str = "deadline"  # Default gantt sort order
        self._hide_completed: bool = False  # Default: show all tasks

        # Initialize controllers
        task_controller = TaskController(repository, time_tracker, self.config, notes_repository)
        query_controller = QueryController(repository)

        # Initialize TUIContext
        self.context = TUIContext(
            config=self.config,
            notes_repository=notes_repository,
            task_controller=task_controller,
            query_controller=query_controller,
        )

        # Initialize TaskService with context
        self.task_service = TaskService(self.context, repository)

        # Initialize CommandFactory for command execution
        self.command_factory = CommandFactory(self, self.context, self.task_service)

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

    def _load_tasks(self, keep_scroll_position: bool = False) -> list[Task]:
        """Load tasks from repository and update both gantt and table.

        Args:
            keep_scroll_position: Whether to preserve scroll position during refresh

        Returns:
            List of loaded tasks
        """
        # Reload tasks from file to detect external changes
        self.repository.reload()

        # Get all non-deleted tasks (PENDING, IN_PROGRESS, COMPLETED, CANCELED)
        # Deleted tasks are excluded from display
        # If hide_completed is True, also exclude COMPLETED and CANCELED tasks
        if self._hide_completed:
            task_filter = CompositeFilter([NonArchivedFilter(), IncompleteOrActiveFilter()])
        else:
            task_filter = NonArchivedFilter()
        tasks = self.query_service.get_filtered_tasks(task_filter, sort_by=self._gantt_sort_by)

        # Update gantt chart and table
        if self.main_screen:
            if self.main_screen.gantt_widget:
                # Calculate appropriate date range based on screen width
                from datetime import timedelta

                from shared.utils.date_utils import get_previous_monday

                # Use gantt widget's display calculation if available
                widget = self.main_screen.gantt_widget
                display_days = (
                    widget._calculate_display_days()
                    if hasattr(widget, "_calculate_display_days")
                    else 28
                )
                start_date = get_previous_monday()
                end_date = start_date + timedelta(days=display_days - 1)

                # Extract task IDs
                task_ids = [t.id for t in tasks]

                # Get pre-computed gantt view model from TaskService with appropriate date range
                gantt_view_model = self.task_service.get_gantt_data(
                    task_ids=task_ids,
                    sort_by=self._gantt_sort_by,
                    start_date=start_date,
                    end_date=end_date,
                )
                self.main_screen.gantt_widget.update_gantt(
                    task_ids=task_ids,
                    gantt_view_model=gantt_view_model,
                    sort_by=self._gantt_sort_by,
                )

            if self.main_screen.task_table:
                # Convert tasks to ViewModels
                task_mapper = TaskMapper(self.notes_repository)
                view_models = task_mapper.to_row_view_models(tasks)
                self.main_screen.task_table.refresh_tasks(
                    view_models, keep_scroll_position=keep_scroll_position
                )

        return tasks

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

        # Reload tasks with new filter
        self.post_message(TasksRefreshed())

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
                self.main_screen.task_table.refresh_tasks(view_models, keep_scroll_position=True)

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
