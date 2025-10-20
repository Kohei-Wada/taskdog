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
        ("o", "optimize", "Optimize"),
        ("O", "optimize_force", "Force Optimize"),
        ("x", "delete_task", "Delete"),
        ("A", "archive_task", "Archive"),
        ("r", "refresh", "Refresh"),
        ("i", "show_details", "Info"),
        ("e", "edit_task", "Edit"),
        ("v", "edit_note", "Edit Note"),
    ]

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

        # Initialize TUIContext and TaskService
        self.context = TUIContext(
            repository=repository,
            time_tracker=time_tracker,
            query_service=self.query_service,
            config=self.config,
        )
        self.task_service = TaskService(repository, time_tracker, self.query_service, self.config)

        # Initialize CommandFactory for command execution
        self.command_factory = CommandFactory(self, self.context, self.task_service)

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
        tasks = self.query_service.get_filtered_tasks(non_archived_filter, sort_by="planned_start")

        # Update gantt chart and table
        if self.main_screen:
            if self.main_screen.gantt_widget:
                self.main_screen.gantt_widget.update_gantt(tasks)

            if self.main_screen.task_table:
                self.main_screen.task_table.refresh_tasks(tasks)

        return tasks

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
        """Complete the selected task."""
        self.command_factory.execute("done_task")

    def action_delete_task(self) -> None:
        """Delete the selected task."""
        self.command_factory.execute("delete_task")

    def action_archive_task(self) -> None:
        """Archive the selected task."""
        self.command_factory.execute("archive_task")

    def action_show_details(self) -> None:
        """Show details of the selected task."""
        self.command_factory.execute("show_details")

    def action_edit_task(self) -> None:
        """Edit the selected task."""
        self.command_factory.execute("edit_task")

    def action_optimize(self) -> None:
        """Optimize task schedules without force override."""
        self.command_factory.execute("optimize", force_override=False)

    def action_optimize_force(self) -> None:
        """Optimize task schedules with force override."""
        self.command_factory.execute("optimize", force_override=True)

    def action_edit_note(self) -> None:
        """Edit the selected task's note."""
        self.command_factory.execute("edit_note")
