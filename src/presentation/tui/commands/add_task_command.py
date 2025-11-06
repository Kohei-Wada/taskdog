"""Add task command for TUI."""

from datetime import datetime

from domain.exceptions.task_exceptions import TaskValidationError
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.registry import command_registry
from presentation.tui.events import TaskCreated
from presentation.tui.forms.task_form_fields import TaskFormData
from presentation.tui.screens.task_form_dialog import TaskFormDialog
from shared.constants.formats import DATETIME_FORMAT


@command_registry.register("add_task")
class AddTaskCommand(TUICommandBase):
    """Command to add a new task with input dialog."""

    def execute(self) -> None:
        """Execute the add task command."""

        def handle_task_data(form_data: TaskFormData | None) -> None:
            """Handle the task data from the dialog.

            Args:
                form_data: Form data or None if cancelled
            """
            if form_data is None:
                return  # User cancelled

            # Convert form data strings to datetime
            deadline = (
                datetime.strptime(form_data.deadline, DATETIME_FORMAT)
                if form_data.deadline
                else None
            )
            planned_start = (
                datetime.strptime(form_data.planned_start, DATETIME_FORMAT)
                if form_data.planned_start
                else None
            )
            planned_end = (
                datetime.strptime(form_data.planned_end, DATETIME_FORMAT)
                if form_data.planned_end
                else None
            )

            # Create task via API client
            task = self.context.api_client.create_task(
                name=form_data.name,
                priority=form_data.priority,
                deadline=deadline,
                estimated_duration=form_data.estimated_duration,
                planned_start=planned_start,
                planned_end=planned_end,
                is_fixed=form_data.is_fixed,
                tags=form_data.tags,
            )

            # Add dependencies if specified
            if form_data.depends_on and task.id is not None:
                failed_dependencies = []

                for dep_id in form_data.depends_on:
                    try:
                        self.context.api_client.add_dependency(task.id, dep_id)
                    except TaskValidationError as e:
                        failed_dependencies.append((dep_id, str(e)))

                # Show warnings for failed dependencies
                if failed_dependencies:
                    error_msgs = [
                        f"Dependency {dep_id}: {error}" for dep_id, error in failed_dependencies
                    ]
                    self.notify_warning(
                        "Task created but some dependencies failed:\n" + "\n".join(error_msgs)
                    )

            # Post TaskCreated event to trigger UI refresh
            if task.id is None:
                raise ValueError("Created task must have an ID")
            self.app.post_message(TaskCreated(task.id))
            self.notify_success(f"Added task: {task.name} (ID: {task.id})")

        # Show task form dialog in add mode (no task parameter)
        # Wrap callback with error handling from base class
        dialog = TaskFormDialog(config=self.context.config)
        self.app.push_screen(dialog, self.handle_error(handle_task_data))
