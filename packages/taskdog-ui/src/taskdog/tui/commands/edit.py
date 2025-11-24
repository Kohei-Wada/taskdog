"""Edit task command for TUI."""

from taskdog.tui.commands.base import TUICommandBase
from taskdog.tui.commands.decorators import require_selected_task
from taskdog.tui.commands.registry import command_registry
from taskdog.tui.events import TaskUpdated
from taskdog.tui.forms.task_form_fields import TaskFormData
from taskdog.tui.messages import TUIMessageBuilder
from taskdog.tui.screens.task_form_dialog import TaskFormDialog
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


@command_registry.register("edit")
class EditCommand(TUICommandBase):
    """Command to edit a task with input dialog."""

    @require_selected_task
    def execute(self) -> None:
        """Execute the edit task command."""
        # Get selected task ID - guaranteed to be non-None by decorator
        task_id = self.get_selected_task_id()
        if task_id is None:
            raise ValueError("Task ID cannot be None")

        # Fetch task via API client
        output = self.context.api_client.get_task_by_id(task_id)
        if output.task is None:
            self.notify_warning(f"Task #{task_id} not found")
            return

        # Store original task DTO
        original_task = output.task

        def handle_task_data(form_data: TaskFormData | None) -> None:
            """Handle the task data from the dialog."""
            if form_data is None:
                return  # User cancelled

            # Delegate actual update logic to helper method
            self._handle_task_update(original_task, form_data)

        # Show task form dialog in edit mode
        # Wrap callback with error handling from base class
        dialog = TaskFormDialog(task=original_task)
        self.app.push_screen(dialog, self.handle_error(handle_task_data))

    def _detect_changes(
        self, task: TaskDetailDto, form_data: TaskFormData
    ) -> tuple[bool, bool]:
        """Detect what changed between task and form data.

        Args:
            task: Original task DTO
            form_data: New form data

        Returns:
            Tuple of (has_field_changes, has_dependency_changes)
        """
        # Check dependency changes
        original_deps = set(task.depends_on) if task.depends_on else set()
        new_deps = set(form_data.depends_on) if form_data.depends_on else set()
        dependencies_changed = new_deps != original_deps

        # Check field changes using TaskFormData helper methods
        fields_changed = (
            form_data.name != task.name
            or form_data.priority != task.priority
            or form_data.get_deadline() != task.deadline
            or form_data.estimated_duration != task.estimated_duration
            or form_data.get_planned_start() != task.planned_start
            or form_data.get_planned_end() != task.planned_end
            or form_data.is_fixed != task.is_fixed
            or (form_data.tags or []) != task.tags
        )

        return fields_changed, dependencies_changed

    def _update_task_fields(
        self, task: TaskDetailDto, form_data: TaskFormData
    ) -> tuple[TaskOperationOutput, list[str]]:
        """Update task fields via TaskController.

        Args:
            task: Original task DTO
            form_data: New form data

        Returns:
            Tuple of (updated_task_output, list_of_updated_field_names)
        """
        # Get datetime values using TaskFormData helper methods
        form_deadline = form_data.get_deadline()
        form_planned_start = form_data.get_planned_start()
        form_planned_end = form_data.get_planned_end()

        # Update task via API client with only changed fields
        result = self.context.api_client.update_task(
            task_id=task.id,
            name=form_data.name if form_data.name != task.name else None,
            priority=form_data.priority
            if form_data.priority != task.priority
            else None,
            deadline=form_deadline if form_deadline != task.deadline else None,
            estimated_duration=form_data.estimated_duration
            if form_data.estimated_duration != task.estimated_duration
            else None,
            planned_start=form_planned_start
            if form_planned_start != task.planned_start
            else None,
            planned_end=form_planned_end
            if form_planned_end != task.planned_end
            else None,
            is_fixed=form_data.is_fixed
            if form_data.is_fixed != task.is_fixed
            else None,
            tags=(form_data.tags or [])
            if (form_data.tags or []) != task.tags
            else None,
        )

        return result.task, result.updated_fields

    def _handle_task_update(self, task: TaskDetailDto, form_data: TaskFormData) -> None:
        """Handle the actual task update logic.

        Args:
            task: Original task DTO
            form_data: New form data from dialog
        """
        # Detect changes
        fields_changed, dependencies_changed = self._detect_changes(task, form_data)

        # Early return if nothing changed
        if not fields_changed and not dependencies_changed:
            self.notify_warning("No changes made")
            return

        # Update task fields if changed
        updated_fields: list[str] = []
        updated_task: TaskOperationOutput | TaskDetailDto
        if fields_changed:
            updated_task, updated_fields = self._update_task_fields(task, form_data)
        else:
            updated_task = task

        # Sync dependencies if changed
        if dependencies_changed:
            self._sync_dependencies(task, form_data)
            updated_fields.append("dependencies")

        # Post TaskUpdated event to trigger UI refresh
        if updated_task.id is None:
            raise ValueError("Updated task must have an ID")
        self.app.post_message(TaskUpdated(updated_task.id))

        msg = TUIMessageBuilder.task_updated(updated_task.id, updated_fields)
        self.notify_success(msg)

    def _sync_dependencies(self, task: TaskDetailDto, form_data: TaskFormData) -> None:
        """Synchronize task dependencies.

        Args:
            task: Original task DTO
            form_data: New form data with updated dependencies
        """
        original_deps = set(task.depends_on) if task.depends_on else set()
        new_deps = set(form_data.depends_on) if form_data.depends_on else set()

        # Calculate differences
        deps_to_remove = list(original_deps - new_deps)
        deps_to_add = list(new_deps - original_deps)

        # Use base class helper method for dependency management
        failed_operations = self.manage_dependencies(
            task.id, add_deps=deps_to_add, remove_deps=deps_to_remove
        )

        # Report any failures
        if failed_operations:
            self.notify_warning(
                "Some dependency operations failed:\n" + "\n".join(failed_operations)
            )
