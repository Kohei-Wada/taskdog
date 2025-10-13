"""Use case for updating a task."""

from application.dto.update_task_input import UpdateTaskInput
from application.services.hierarchy_manager import HierarchyManager
from application.services.task_validator import TaskValidator
from application.use_cases.base import UseCase
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
        self.validator = TaskValidator()
        self.hierarchy_manager = HierarchyManager(repository)

    def execute(self, input_dto: UpdateTaskInput) -> tuple[Task, list[str]]:  # noqa: C901
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

        # Track original parent_id for updating old parent's estimated_duration
        original_parent_id = task.parent_id

        updated_fields = []
        parent_id_changed = False
        estimated_duration_changed = False

        # Handle parent_id separately for validation
        # Use UNSET sentinel to distinguish "not provided" from "explicitly None"
        from application.dto.update_task_input import UNSET, _Unset

        if input_dto.parent_id is not UNSET:
            # Validate if parent_id is not None and not UNSET
            if input_dto.parent_id is not None and not isinstance(input_dto.parent_id, _Unset):
                # Type narrowing: parent_id is int here
                parent_id_int: int = input_dto.parent_id
                self.validator.validate_parent(
                    parent_id=parent_id_int,
                    repository=self.repository,
                    task_id=input_dto.task_id,
                )
            # Update parent_id (int | None)
            if not isinstance(input_dto.parent_id, _Unset):
                if task.parent_id != input_dto.parent_id:
                    parent_id_changed = True
                task.parent_id = input_dto.parent_id
            updated_fields.append("parent_id")

        # Handle status separately for time tracking
        if input_dto.status is not None:
            self.time_tracker.record_time_on_status_change(task, input_dto.status)
            task.status = input_dto.status
            updated_fields.append("status")

        # Validate estimated_duration before updating (cannot set for parent tasks)
        if input_dto.estimated_duration is not None:
            # Task from repository always has ID
            assert task.id is not None
            self.validator.validate_can_set_estimated_duration(task.id, self.repository)

        # Update remaining fields using dictionary mapping
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
                # Track if estimated_duration changed
                if field_name == "estimated_duration":
                    estimated_duration_changed = True
                setattr(task, field_name, value)
                updated_fields.append(field_name)

        if updated_fields:
            self.repository.save(task)

            # Update parent's estimated_duration if necessary
            if parent_id_changed:
                # Parent changed: update both old and new parent
                if original_parent_id is not None:
                    self.hierarchy_manager.update_parent_estimated_duration(original_parent_id)
                if task.parent_id is not None:
                    self.hierarchy_manager.update_parent_estimated_duration(task.parent_id)
            elif estimated_duration_changed and task.parent_id is not None:
                # Estimated duration changed: update current parent
                self.hierarchy_manager.update_parent_estimated_duration(task.parent_id)

        return task, updated_fields
