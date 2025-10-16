"""Taskdog TUI application."""

from typing import ClassVar

from textual.app import App

from application.dto.complete_task_input import CompleteTaskInput
from application.dto.create_task_input import CreateTaskInput
from application.dto.remove_task_input import RemoveTaskInput
from application.dto.start_task_input import StartTaskInput
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.task_query_service import TaskQueryService
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import Task
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository
from presentation.tui.screens.main_screen import MainScreen


class TaskdogTUI(App):
    """Taskdog TUI application."""

    BINDINGS: ClassVar = [
        ("q", "quit", "Quit"),
        ("a", "add_task", "Add"),
        ("s", "start_task", "Start"),
        ("d", "done_task", "Done"),
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
        height: auto;
        max-height: 50;
        border: solid $primary;
        margin-bottom: 1;
        overflow-y: auto;
    }

    #task-table {
        height: auto;
        min-height: 10;
        border: solid $primary;
    }

    MainScreen {
        background: $surface;
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
        self._load_tasks()
        self.notify("Tasks refreshed")

    def action_add_task(self) -> None:
        """Add a new task."""
        # For now, create a simple default task
        # TODO: Implement input dialog for task name
        try:
            use_case = CreateTaskUseCase(self.repository)
            task_input = CreateTaskInput(name="New Task", priority=1)
            task = use_case.execute(task_input)
            self._load_tasks()
            self.notify(f"Added task: {task.name} (ID: {task.id})")
        except Exception as e:
            self.notify(f"Error adding task: {e}", severity="error")

    def action_start_task(self) -> None:
        """Start the selected task."""
        if not self.main_screen or not self.main_screen.task_table:
            return

        task = self.main_screen.task_table.get_selected_task()
        if not task or task.id is None:
            self.notify("No task selected", severity="warning")
            return

        try:
            use_case = StartTaskUseCase(self.repository, self.time_tracker)
            start_input = StartTaskInput(task_id=task.id)
            use_case.execute(start_input)
            self._load_tasks()
            self.notify(f"Started task: {task.name} (ID: {task.id})")
        except Exception as e:
            self.notify(f"Error starting task: {e}", severity="error")

    def action_done_task(self) -> None:
        """Complete the selected task."""
        if not self.main_screen or not self.main_screen.task_table:
            return

        task = self.main_screen.task_table.get_selected_task()
        if not task or task.id is None:
            self.notify("No task selected", severity="warning")
            return

        try:
            use_case = CompleteTaskUseCase(self.repository, self.time_tracker)
            complete_input = CompleteTaskInput(task_id=task.id)
            use_case.execute(complete_input)
            self._load_tasks()
            self.notify(f"Completed task: {task.name} (ID: {task.id})")
        except Exception as e:
            self.notify(f"Error completing task: {e}", severity="error")

    def action_delete_task(self) -> None:
        """Delete the selected task."""
        if not self.main_screen or not self.main_screen.task_table:
            return

        task = self.main_screen.task_table.get_selected_task()
        if not task or task.id is None:
            self.notify("No task selected", severity="warning")
            return

        # TODO: Add confirmation dialog
        try:
            use_case = RemoveTaskUseCase(self.repository)
            remove_input = RemoveTaskInput(task_id=task.id)
            use_case.execute(remove_input)
            self._load_tasks()
            self.notify(f"Deleted task: {task.name} (ID: {task.id})")
        except Exception as e:
            self.notify(f"Error deleting task: {e}", severity="error")

    def action_show_details(self) -> None:
        """Show details of the selected task."""
        if not self.main_screen or not self.main_screen.task_table:
            return

        task = self.main_screen.task_table.get_selected_task()
        if not task:
            self.notify("No task selected", severity="warning")
            return

        # For now, just show a notification with task details
        # Later we can implement a detailed view screen
        details = f"""
Task Details:
  ID: {task.id}
  Name: {task.name}
  Priority: {task.priority}
  Status: {task.status.value}
  Deadline: {task.deadline or 'Not set'}
  Estimated: {task.estimated_duration or 'Not set'}h
        """.strip()
        self.notify(details)
