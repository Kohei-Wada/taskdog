"""Use case for updating a task."""

from application.dto.update_task_input import UpdateTaskInput
from application.services.hierarchy_manager import HierarchyManager
from application.use_cases.base import UseCase
from application.validators.validator_registry import TaskFieldValidatorRegistry
from domain.entities.task import Task
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


class UpdateTaskUseCase(UseCase[UpdateTaskInput, tuple[Task, list[str]]]):
    """Use case for updating task properties.

    Supports updating multiple fields and handles time tracking for status changes.
    When estimated_duration or parent_id changes, updates parent's estimated_duration.
    Returns the updated task and list of updated field names.
    """

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker for recording timestamps
        """
        self.repository = repository
        self.time_tracker = time_tracker
        self.validator_registry = TaskFieldValidatorRegistry(repository)
        self.hierarchy_manager = HierarchyManager(repository)

    def _update_parent_id(
        self,
        task: Task,
        input_dto: UpdateTaskInput,
        updated_fields: list[str],
    ) -> bool:
        """Update task parent_id with validation.

        Args:
            task: Task to update
            input_dto: Update input data
            updated_fields: List to append field name to

        Returns:
            True if parent_id changed, False otherwise
        """
        from application.dto.update_task_input import UNSET, _Unset

        if input_dto.parent_id is UNSET:
            return False

        parent_id_changed = False

        # Validate if parent_id is not None and not UNSET
        if input_dto.parent_id is not None and not isinstance(input_dto.parent_id, _Unset):
            # Type narrowing: parent_id is int here
            parent_id_int: int = input_dto.parent_id
            self.validator_registry.validate_field("parent_id", parent_id_int, task)

        # Update parent_id (int | None)
        if not isinstance(input_dto.parent_id, _Unset):
            if task.parent_id != input_dto.parent_id:
                parent_id_changed = True
            task.parent_id = input_dto.parent_id

        updated_fields.append("parent_id")
        return parent_id_changed

    def _update_status(
        self,
        task: Task,
        input_dto: UpdateTaskInput,
        updated_fields: list[str],
    ) -> None:
        """Update task status with time tracking.

        Args:
            task: Task to update
            input_dto: Update input data
            updated_fields: List to append field name to
        """
        if input_dto.status is not None:
            # Validate status transition
            self.validator_registry.validate_field("status", input_dto.status, task)

            self.time_tracker.record_time_on_status_change(task, input_dto.status)
            task.status = input_dto.status
            updated_fields.append("status")

    def _validate_estimated_duration(self, input_dto: UpdateTaskInput, task: Task) -> None:
        """Validate estimated_duration can be set for this task.

        Args:
            input_dto: Update input data
            task: Task to validate

        Raises:
            CannotSetEstimateForParentTaskError: If task has children
        """
        if input_dto.estimated_duration is not None:
            # Validate estimated_duration can be set
            self.validator_registry.validate_field(
                "estimated_duration", input_dto.estimated_duration, task
            )

    def _update_standard_fields(
        self,
        task: Task,
        input_dto: UpdateTaskInput,
        updated_fields: list[str],
    ) -> bool:
        """Update standard fields (name, priority, planned times, deadline, estimated_duration).

        Args:
            task: Task to update
            input_dto: Update input data
            updated_fields: List to append field names to

        Returns:
            True if estimated_duration changed, False otherwise
        """
        estimated_duration_changed = False

        field_mapping = {
            "name": input_dto.name,
            "priority": input_dto.priority,
            "planned_start": input_dto.planned_start,
            "planned_end": input_dto.planned_end,
            "deadline": input_dto.deadline,
            "estimated_duration": input_dto.estimated_duration,
        }

        for field_name, value in field_mapping.items():
            if value is not None:
                # Validate field if validator exists
                self.validator_registry.validate_field(field_name, value, task)

                # Track if estimated_duration changed
                if field_name == "estimated_duration":
                    estimated_duration_changed = True
                setattr(task, field_name, value)
                updated_fields.append(field_name)

        return estimated_duration_changed

    def _propagate_hierarchy_changes(
        self,
        task: Task,
        original_parent_id: int | None,
        parent_id_changed: bool,
        estimated_duration_changed: bool,
    ) -> None:
        """Update parent task's estimated_duration when hierarchy changes.

        Args:
            task: Updated task
            original_parent_id: Original parent_id before update
            parent_id_changed: Whether parent_id was changed
            estimated_duration_changed: Whether estimated_duration was changed
        """
        if parent_id_changed:
            # Parent changed: update both old and new parent
            if original_parent_id is not None:
                self.hierarchy_manager.update_parent_estimated_duration(original_parent_id)
            if task.parent_id is not None:
                self.hierarchy_manager.update_parent_estimated_duration(task.parent_id)
        elif estimated_duration_changed and task.parent_id is not None:
            # Estimated duration changed: update current parent
            self.hierarchy_manager.update_parent_estimated_duration(task.parent_id)

    def execute(self, input_dto: UpdateTaskInput) -> tuple[Task, list[str]]:
        """Execute task update.

        Args:
            input_dto: Task update input data

        Returns:
            Tuple of (updated task, list of updated field names)

        Raises:
            TaskNotFoundException: If task doesn't exist
            CircularReferenceError: If circular parent reference detected
            ParentTaskNotFoundError: If parent doesn't exist
            CannotSetEstimateForParentTaskError: If trying to set estimated_duration for parent task
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)
        original_parent_id = task.parent_id
        updated_fields: list[str] = []

        # Update each field type using specialized methods
        parent_id_changed = self._update_parent_id(task, input_dto, updated_fields)
        self._update_status(task, input_dto, updated_fields)
        self._validate_estimated_duration(input_dto, task)
        estimated_duration_changed = self._update_standard_fields(task, input_dto, updated_fields)

        # Save and propagate changes to parent tasks
        if updated_fields:
            self.repository.save(task)
            self._propagate_hierarchy_changes(
                task, original_parent_id, parent_id_changed, estimated_duration_changed
            )

        return task, updated_fields
