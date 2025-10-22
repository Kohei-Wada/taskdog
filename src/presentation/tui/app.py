"""Taskdog TUI application."""

from importlib.resources import files
from pathlib import Path
from typing import ClassVar

from textual.app import App

from application.queries.filters.non_archived_filter import NonArchivedFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository
from presentation.tui.commands import *  # noqa: F403  # Import all commands for registration
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
        ("x", "delete_task", "Delete"),
        ("r", "refresh", "Refresh"),
        ("i", "show_details", "Info"),
        ("e", "edit_task", "Edit"),
        ("v", "edit_note", "Edit Note"),
        ("S", "cycle_gantt_sort", "Sort Gantt"),
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
        self.context = TUIContext(
            repository=repository,
            time_tracker=time_tracker,
            query_service=self.query_service,
            config=self.config,
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
        self.main_screen = MainScreen()
        self.push_screen(self.main_screen)
        # Load tasks after screen is fully mounted
        self.call_after_refresh(self._load_tasks)

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
                self.main_screen.gantt_widget.update_gantt(tasks, sort_by=self._gantt_sort_by)

            if self.main_screen.task_table:
                self.main_screen.task_table.refresh_tasks(tasks)

        return tasks

    def action_cycle_gantt_sort(self) -> None:
        """Cycle through gantt sort options (deadline ↔ planned_start)."""
        # Toggle between deadline and planned_start
        if self._gantt_sort_by == "deadline":
            self._gantt_sort_by = "planned_start"
        else:
            self._gantt_sort_by = "deadline"

        # Reload tasks to apply new sort
        self._load_tasks()
