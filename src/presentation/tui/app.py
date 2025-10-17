"""Taskdog TUI application."""

from typing import ClassVar

from textual.app import App

from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository
from presentation.tui.commands.add_task_command import AddTaskCommand
from presentation.tui.commands.complete_task_command import CompleteTaskCommand
from presentation.tui.commands.delete_task_command import DeleteTaskCommand
from presentation.tui.commands.optimize_command import OptimizeCommand
from presentation.tui.commands.refresh_command import RefreshCommand
from presentation.tui.commands.show_details_command import ShowDetailsCommand
from presentation.tui.commands.start_task_command import StartTaskCommand
from presentation.tui.screens.main_screen import MainScreen


class TaskdogTUI(App):
    """Taskdog TUI application."""

    BINDINGS: ClassVar = [
        ("q", "quit", "Quit"),
        ("a", "add_task", "Add"),
        ("s", "start_task", "Start"),
        ("d", "done_task", "Done"),
        ("o", "optimize", "Optimize"),
        ("delete", "delete_task", "Delete"),
        ("r", "refresh", "Refresh"),
        ("enter", "show_details", "Details"),
    ]

    CSS = """
    #title {
        padding: 1;
        background: $boost;
        text-align: center;
    }

    #gantt-title, #table-title {
        padding: 1 0;
        text-align: left;
        background: $panel;
    }

    #gantt-widget {
        width: 100%;
        height: auto;
        max-height: 50;
        border: solid $primary;
        margin-bottom: 1;
        overflow-y: auto;
        overflow-x: auto;
    }

    #task-table {
        height: auto;
        min-height: 10;
        border: solid $primary;
    }

    MainScreen {
        background: $surface;
    }

    /* Algorithm selection dialog */
    AlgorithmSelectionScreen {
        align: center middle;
    }

    #algorithm-dialog {
        width: 80;
        height: auto;
        max-height: 30;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }

    #dialog-title {
        text-align: center;
        padding: 1;
        background: $boost;
    }

    #algorithm-list {
        height: auto;
        max-height: 15;
        margin: 1 0;
        border: solid $accent;
    }

    #button-container {
        height: auto;
        align: center middle;
    }

    #button-container Button {
        margin: 0 1;
    }

    /* Confirmation dialog */
    ConfirmationDialog {
        align: center middle;
    }

    #confirmation-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $error;
        padding: 1;
    }

    #dialog-message {
        text-align: center;
        padding: 1 2;
        margin: 1 0;
    }

    /* Add task dialog */
    AddTaskDialog {
        align: center middle;
    }

    #add-task-dialog {
        width: 70;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }

    #form-container {
        padding: 1 0;
        margin: 1 0;
    }

    .field-label {
        padding: 1 0 0 0;
        color: $text-muted;
    }

    Input {
        margin: 0 0 1 0;
    }
    """

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker, *args, **kwargs):
        """Initialize the TUI application.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker service
        """
        super().__init__(*args, **kwargs)
        self.repository = repository
        self.time_tracker = time_tracker
        self.query_service = TaskQueryService(repository)
        self.main_screen: MainScreen | None = None

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
        # Get incomplete tasks (PENDING, IN_PROGRESS, FAILED)
        incomplete_filter = IncompleteFilter()
        tasks = self.query_service.get_filtered_tasks(incomplete_filter, sort_by="id")

        # Update both gantt chart and table
        if self.main_screen:
            if self.main_screen.gantt_widget:
                self.main_screen.gantt_widget.update_gantt(tasks)

            if self.main_screen.task_table:
                self.main_screen.task_table.load_tasks(tasks)

        return tasks

    def action_refresh(self) -> None:
        """Refresh the task list."""
        RefreshCommand(self).execute()

    def action_add_task(self) -> None:
        """Add a new task."""
        AddTaskCommand(self).execute()

    def action_start_task(self) -> None:
        """Start the selected task."""
        StartTaskCommand(self).execute()

    def action_done_task(self) -> None:
        """Complete the selected task."""
        CompleteTaskCommand(self).execute()

    def action_delete_task(self) -> None:
        """Delete the selected task."""
        DeleteTaskCommand(self).execute()

    def action_show_details(self) -> None:
        """Show details of the selected task."""
        ShowDetailsCommand(self).execute()

    def action_optimize(self) -> None:
        """Optimize task schedules."""
        OptimizeCommand(self).execute()
