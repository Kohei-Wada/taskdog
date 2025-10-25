"""Taskdog TUI application."""

from importlib.resources import files
from pathlib import Path
from typing import ClassVar

from textual.app import App

from application.queries.filters.non_archived_filter import NonArchivedFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.notes_repository import NotesRepository
from infrastructure.persistence.task_repository import TaskRepository
from presentation.tui.commands.factory import CommandFactory
from presentation.tui.context import TUIContext
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
        ("p", "pause_task", "Pause"),
        ("d", "done_task", "Done"),
        ("c", "cancel_task", "Cancel"),
        ("R", "reopen_task", "Reopen"),
        ("o", "optimize", "Optimize"),
        ("O", "optimize_force", "Force Optimize"),
        ("x", "delete_task", "Archive"),
        ("X", "hard_delete_task", "Delete"),
        ("r", "refresh", "Refresh"),
        ("i", "show_details", "Info"),
        ("e", "edit_task", "Edit"),
        ("v", "edit_note", "Edit Note"),
        ("S", "cycle_gantt_sort", "Sort"),
        ("/", "show_search", "Search"),
        ("escape", "hide_search", "Clear Search"),
    ]

    # Mapping of action names to command names and kwargs
    # Format: {action_name: (command_name, kwargs)}
    _ACTION_TO_COMMAND: ClassVar[dict[str, tuple[str, dict]]] = {
        "refresh": ("refresh", {}),
        "add_task": ("add_task", {}),
        "start_task": ("start_task", {}),
        "pause_task": ("pause_task", {}),
        "done_task": ("done_task", {}),
        "cancel_task": ("cancel_task", {}),
        "reopen_task": ("reopen_task", {}),
        "delete_task": ("delete_task", {}),
        "hard_delete_task": ("hard_delete_task", {}),
        "show_details": ("show_details", {}),
        "edit_task": ("edit_task", {}),
        "optimize": ("optimize", {"force_override": False}),
        "optimize_force": ("optimize", {"force_override": True}),
        "edit_note": ("edit_note", {}),
    }

    # Load CSS from external files
    CSS_PATH: ClassVar[list[str | Path]] = _get_css_paths()

    # Disable mouse support
    ENABLE_MOUSE: ClassVar[bool] = False

    def __init__(
        self,
        repository: TaskRepository,
        time_tracker: TimeTracker,
        config: Config | None = None,
        *args,
        **kwargs,
    ):
        """Initialize the TUI application.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker service
            config: Application configuration (optional, loads from file by default)
        """
        super().__init__(*args, **kwargs)
        self.repository = repository
        self.time_tracker = time_tracker
        self.query_service = TaskQueryService(repository)
        self.config = config if config is not None else ConfigManager.load()
        self.main_screen: MainScreen | None = None
        self._gantt_sort_by: str = "deadline"  # Default gantt sort order

        # Initialize TUIContext
        self.notes_repository = NotesRepository()
        self.context = TUIContext(
            repository=repository,
            time_tracker=time_tracker,
            query_service=self.query_service,
            config=self.config,
            notes_repository=self.notes_repository,
        )

        # Initialize TaskService with context
        self.task_service = TaskService(self.context)

        # Initialize CommandFactory for command execution
        self.command_factory = CommandFactory(self, self.context, self.task_service)

    def __getattribute__(self, name: str):
        """Dynamically create action_* methods based on _ACTION_TO_COMMAND mapping.

        This allows us to avoid writing boilerplate action_* methods for each command.
        When Textual calls action_foo(), this method intercepts it and executes
        the corresponding command via command_factory.
        """
        # First try to get the attribute normally
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            # Check if it's an action_ method that should be generated
            if name.startswith("action_"):
                action_name = name[7:]  # Remove "action_" prefix
                action_to_command = object.__getattribute__(self, "_ACTION_TO_COMMAND")

                if action_name in action_to_command:
                    command_name, kwargs = action_to_command[action_name]
                    command_factory = object.__getattribute__(self, "command_factory")

                    # Return a method that executes the command
                    def action_method() -> None:
                        command_factory.execute(command_name, **kwargs)

                    return action_method

            # Re-raise the AttributeError if we can't handle it
            raise

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.main_screen = MainScreen(self.notes_repository)
        self.push_screen(self.main_screen)
        # Load tasks after screen is fully mounted
        self.call_after_refresh(self._load_tasks)
        # Start 1-second auto-refresh timer for elapsed time updates
        self.set_interval(1.0, self._refresh_elapsed_time)

    def _load_tasks(self) -> list[Task]:
        """Load tasks from repository and update both gantt and table.

        Returns:
            List of loaded tasks
        """
        # Reload tasks from file to detect external changes
        self.repository.reload()

        # Get all non-deleted tasks (PENDING, IN_PROGRESS, COMPLETED, CANCELED)
        # Deleted tasks are excluded from display
        non_archived_filter = NonArchivedFilter()
        tasks = self.query_service.get_filtered_tasks(
            non_archived_filter, sort_by=self._gantt_sort_by
        )

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

                # Get pre-computed gantt data from TaskService with appropriate date range
                gantt_result = self.task_service.get_gantt_data(
                    task_ids=task_ids,
                    sort_by=self._gantt_sort_by,
                    start_date=start_date,
                    end_date=end_date,
                )
                self.main_screen.gantt_widget.update_gantt(
                    task_ids=task_ids,
                    gantt_result=gantt_result,
                    sort_by=self._gantt_sort_by,
                )

            if self.main_screen.task_table:
                self.main_screen.task_table.refresh_tasks(tasks)

        return tasks

    def action_cycle_gantt_sort(self) -> None:
        """Show sort selection dialog."""

        def handle_sort_selection(sort_by: str | None) -> None:
            """Handle the sort selection from the dialog.

            Args:
                sort_by: Selected sort order, or None if cancelled
            """
            if sort_by is None:
                return  # User cancelled

            self._gantt_sort_by = sort_by
            self._load_tasks()

        # Import here to avoid circular dependency
        from presentation.tui.screens.sort_selection_screen import SortSelectionScreen

        # Show sort selection screen
        self.push_screen(SortSelectionScreen(self._gantt_sort_by), handle_sort_selection)

    def action_show_search(self) -> None:
        """Show the search input."""
        if self.main_screen:
            self.main_screen.show_search()

    def action_hide_search(self) -> None:
        """Hide the search input and clear the filter."""
        if self.main_screen:
            self.main_screen.hide_search()

    def _refresh_elapsed_time(self) -> None:
        """Refresh the task table to update elapsed time for IN_PROGRESS tasks.

        This is called every second by the auto-refresh timer.
        Only updates the table display without reloading from repository.
        """
        if self.main_screen and self.main_screen.task_table:
            # Get current tasks from the table (already loaded in memory)
            tasks = self.main_screen.task_table._all_tasks
            if tasks:
                # Refresh the table display with current tasks
                # This will recalculate elapsed time for IN_PROGRESS tasks
                self.main_screen.task_table.refresh_tasks(tasks)
