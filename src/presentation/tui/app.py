"""Taskdog TUI application."""

from datetime import datetime, timedelta
from typing import ClassVar

from textual.app import App

from application.dto.complete_task_input import CompleteTaskInput
from application.dto.create_task_input import CreateTaskInput
from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.dto.remove_task_input import RemoveTaskInput
from application.dto.start_task_input import StartTaskInput
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.task_query_service import TaskQueryService
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import Task
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository
from presentation.tui.screens.algorithm_selection_screen import AlgorithmSelectionScreen
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

    def action_optimize(self) -> None:
        """Optimize task schedules - shows algorithm selection dialog."""

        def handle_algorithm_selection(algorithm: str | None) -> None:
            """Handle the selected algorithm."""
            if algorithm is None:
                return  # User cancelled

            try:
                # Calculate start date (next weekday or today)
                today = datetime.now()
                # If today is a weekday, use today; otherwise use next Monday
                if today.weekday() < 5:  # Monday=0, Friday=4
                    start_date = today
                else:
                    # Move to next Monday
                    days_until_monday = (7 - today.weekday()) % 7
                    start_date = today + timedelta(days=days_until_monday)

                # Create optimization input with selected algorithm
                optimize_input = OptimizeScheduleInput(
                    start_date=start_date,
                    max_hours_per_day=6.0,
                    force_override=True,
                    dry_run=False,
                    algorithm_name=algorithm,
                )

                # Execute optimization
                use_case = OptimizeScheduleUseCase(self.repository)
                optimized_tasks, _ = use_case.execute(optimize_input)

                # Reload tasks to show updated schedules
                self._load_tasks()

                # Show result notification
                if optimized_tasks:
                    task_count = len(optimized_tasks)
                    self.notify(
                        f"Optimized {task_count} task(s) using '{algorithm}'. "
                        f"Check gantt chart for updated schedules."
                    )
                else:
                    self.notify(
                        "No tasks were optimized. Check task requirements.", severity="warning"
                    )

            except Exception as e:
                self.notify(f"Error optimizing schedules: {e}", severity="error")

        # Show algorithm selection screen
        self.push_screen(AlgorithmSelectionScreen(), handle_algorithm_selection)
