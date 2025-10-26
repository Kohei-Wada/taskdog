"""Edit task command for TUI."""

from datetime import datetime

from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskValidationError
from presentation.tui.commands.base import TUICommandBase
from presentation.tui.commands.decorators import require_selected_task
from presentation.tui.commands.registry import command_registry
from presentation.tui.forms.task_form_fields import TaskFormData
from presentation.tui.helpers.dependency_helpers import sync_dependencies
from presentation.tui.screens.task_form_dialog import TaskFormDialog
from shared.constants.formats import DATETIME_FORMAT


@command_registry.register("edit_task")
class EditTaskCommand(TUICommandBase):
    """Command to edit a task with input dialog."""

    @require_selected_task
    def execute(self) -> None:
        """Execute the edit task command."""
        # Get selected task - guaranteed to be non-None by decorator
        task = self.get_selected_task()
        assert task and task.id is not None

        # Store original task reference
        original_task = task

        def handle_task_data(form_data: TaskFormData | None) -> None:
            """Handle the task data from the dialog."""
            if form_data is None:
                return  # User cancelled

            try:
                self._handle_task_update(original_task, form_data)
            except TaskValidationError as e:
                self.notify_error("Validation error", e)
            except Exception as e:
                self.notify_error("Error editing task", e)

        # Show task form dialog in edit mode
        dialog = TaskFormDialog(task=task, config=self.context.config)
        self.app.push_screen(dialog, handle_task_data)

    def _detect_changes(self, task: Task, form_data: TaskFormData) -> tuple[bool, bool]:
        """Detect what changed between task and form data.

        Args:
            task: Original task
            form_data: New form data

        Returns:
            Tuple of (has_field_changes, has_dependency_changes)
        """
        # Check dependency changes
        original_deps = set(task.depends_on) if task.depends_on else set()
        new_deps = set(form_data.depends_on) if form_data.depends_on else set()
        dependencies_changed = new_deps != original_deps

        # Convert form data strings to datetime for comparison
        form_deadline = (
            datetime.strptime(form_data.deadline, DATETIME_FORMAT) if form_data.deadline else None
        )
        form_planned_start = (
            datetime.strptime(form_data.planned_start, DATETIME_FORMAT)
            if form_data.planned_start
            else None
        )
        form_planned_end = (
            datetime.strptime(form_data.planned_end, DATETIME_FORMAT)
            if form_data.planned_end
            else None
        )

        # Check field changes
        fields_changed = (
            form_data.name != task.name
            or form_data.priority != task.priority
            or form_deadline != task.deadline
            or form_data.estimated_duration != task.estimated_duration
            or form_planned_start != task.planned_start
            or form_planned_end != task.planned_end
            or form_data.is_fixed != task.is_fixed
            or (form_data.tags or []) != task.tags
        )

        return fields_changed, dependencies_changed

    def _update_task_fields(self, task: Task, form_data: TaskFormData) -> tuple[Task, list[str]]:
        """Update task fields via TaskService.

        Args:
            task: Original task
            form_data: New form data

        Returns:
            Tuple of (updated_task, list_of_updated_field_names)
        """
        # Convert form data strings to datetime
        form_deadline = (
            datetime.strptime(form_data.deadline, DATETIME_FORMAT) if form_data.deadline else None
        )
        form_planned_start = (
            datetime.strptime(form_data.planned_start, DATETIME_FORMAT)
            if form_data.planned_start
            else None
        )
        form_planned_end = (
            datetime.strptime(form_data.planned_end, DATETIME_FORMAT)
            if form_data.planned_end
            else None
        )

        # Update task via TaskService with only changed fields
        # TaskService.update_task returns (updated_task, updated_fields)
        updated_task, updated_fields = self.task_service.update_task(
            task_id=task.id,  # type: ignore
            name=form_data.name if form_data.name != task.name else None,
            priority=form_data.priority if form_data.priority != task.priority else None,
            deadline=form_deadline if form_deadline != task.deadline else None,
            estimated_duration=form_data.estimated_duration
            if form_data.estimated_duration != task.estimated_duration
            else None,
            planned_start=form_planned_start if form_planned_start != task.planned_start else None,
            planned_end=form_planned_end if form_planned_end != task.planned_end else None,
            is_fixed=form_data.is_fixed if form_data.is_fixed != task.is_fixed else None,
            tags=(form_data.tags or []) if (form_data.tags or []) != task.tags else None,
        )

        return updated_task, updated_fields

    def _handle_task_update(self, task: Task, form_data: TaskFormData) -> None:
        """Handle the actual task update logic.

        Args:
            task: Original task
            form_data: New form data from dialog
        """
        # Detect changes
        fields_changed, dependencies_changed = self._detect_changes(task, form_data)

        # Check if anything changed
        if not fields_changed and not dependencies_changed:
            self.notify_warning("No changes made")
            return

        # Update task fields if changed
        updated_fields: list[str] = []
        if fields_changed:
            updated_task, updated_fields = self._update_task_fields(task, form_data)
        else:
            updated_task = task

        # Sync dependencies if changed
        if dependencies_changed:
            original_deps = set(task.depends_on) if task.depends_on else set()
            new_deps = set(form_data.depends_on) if form_data.depends_on else set()
            failed_operations = sync_dependencies(
                task.id,  # type: ignore[arg-type]
                original_deps,
                new_deps,
                self.context.repository,
            )

            updated_fields.append("dependencies")

            if failed_operations:
                self.notify_warning(
                    "Some dependency operations failed:\n" + "\n".join(failed_operations)
                )

        # Reload UI and notify
        self.reload_tasks()

        fields_str = ", ".join(updated_fields)
        self.notify_success(f"Updated task {updated_task.id}: {fields_str}")
