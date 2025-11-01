"""Task controller for orchestrating use cases.

This controller provides a shared interface between CLI and TUI layers,
eliminating code duplication in use case instantiation and DTO construction.
"""

from datetime import datetime

from application.dto.archive_task_input import ArchiveTaskInput
from application.dto.cancel_task_input import CancelTaskInput
from application.dto.complete_task_input import CompleteTaskInput
from application.dto.create_task_input import CreateTaskInput
from application.dto.log_hours_input import LogHoursInput
from application.dto.manage_dependencies_input import (
    AddDependencyInput,
    RemoveDependencyInput,
)
from application.dto.optimization_output import OptimizationOutput
from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.dto.pause_task_input import PauseTaskInput
from application.dto.remove_task_input import RemoveTaskInput
from application.dto.reopen_task_input import ReopenTaskInput
from application.dto.restore_task_input import RestoreTaskInput
from application.dto.set_task_tags_input import SetTaskTagsInput
from application.dto.start_task_input import StartTaskInput
from application.dto.statistics_output import CalculateStatisticsInput, StatisticsOutput
from application.dto.task_detail_output import GetTaskDetailOutput
from application.dto.task_operation_output import TaskOperationOutput
from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.add_dependency import AddDependencyUseCase
from application.use_cases.archive_task import ArchiveTaskUseCase
from application.use_cases.calculate_statistics import CalculateStatisticsUseCase
from application.use_cases.cancel_task import CancelTaskUseCase
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.get_task_detail import GetTaskDetailInput, GetTaskDetailUseCase
from application.use_cases.log_hours import LogHoursUseCase
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from application.use_cases.pause_task import PauseTaskUseCase
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from application.use_cases.reopen_task import ReopenTaskUseCase
from application.use_cases.restore_task import RestoreTaskUseCase
from application.use_cases.set_task_tags import SetTaskTagsUseCase
from application.use_cases.start_task import StartTaskUseCase
from application.use_cases.update_task import UpdateTaskUseCase
from domain.entities.task import Task, TaskStatus
from domain.repositories.notes_repository import NotesRepository
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from shared.config_manager import Config


class TaskController:
    """Controller for task operations.

    This class orchestrates use cases, handling instantiation and DTO construction.
    Presentation layers (CLI/TUI) only need to call controller methods with
    simple parameters, without knowing about use cases or DTOs.

    Attributes:
        repository: Task repository for data persistence
        time_tracker: Time tracker for recording timestamps
        config: Application configuration
        notes_repository: Notes repository for notes file operations (optional)
    """

    def __init__(
        self,
        repository: TaskRepository,
        time_tracker: TimeTracker,
        config: Config,
        notes_repository: NotesRepository | None = None,
    ):
        """Initialize the task controller.

        Args:
            repository: Task repository
            time_tracker: Time tracker service
            config: Configuration
            notes_repository: Notes repository (optional, required for get_task_detail)
        """
        self.repository = repository
        self.time_tracker = time_tracker
        self.config = config
        self.notes_repository = notes_repository

    def start_task(self, task_id: int) -> TaskOperationOutput:
        """Start a task.

        Changes task status to IN_PROGRESS and records actual start time.

        Args:
            task_id: ID of the task to start

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be started
        """
        use_case = StartTaskUseCase(self.repository, self.time_tracker)
        request = StartTaskInput(task_id=task_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def complete_task(self, task_id: int) -> TaskOperationOutput:
        """Complete a task.

        Changes task status to COMPLETED and records actual end time.

        Args:
            task_id: ID of the task to complete

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be completed
        """
        use_case = CompleteTaskUseCase(self.repository, self.time_tracker)
        request = CompleteTaskInput(task_id=task_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def pause_task(self, task_id: int) -> TaskOperationOutput:
        """Pause a task.

        Changes task status to PENDING and clears actual start/end times.

        Args:
            task_id: ID of the task to pause

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be paused
        """
        use_case = PauseTaskUseCase(self.repository, self.time_tracker)
        request = PauseTaskInput(task_id=task_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def cancel_task(self, task_id: int) -> TaskOperationOutput:
        """Cancel a task.

        Changes task status to CANCELED and records actual end time.

        Args:
            task_id: ID of the task to cancel

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be canceled
        """
        use_case = CancelTaskUseCase(self.repository, self.time_tracker)
        request = CancelTaskInput(task_id=task_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def create_task(
        self,
        name: str,
        priority: int | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        is_fixed: bool = False,
        tags: list[str] | None = None,
    ) -> TaskOperationOutput:
        """Create a new task.

        Args:
            name: Task name
            priority: Task priority (default: from config)
            deadline: Task deadline (optional)
            estimated_duration: Estimated duration in hours (optional)
            planned_start: Planned start datetime (optional)
            planned_end: Planned end datetime (optional)
            is_fixed: Whether the task schedule is fixed (default: False)
            tags: List of tags for categorization (optional)

        Returns:
            TaskOperationOutput containing the created task information

        Raises:
            TaskValidationError: If task validation fails
        """
        use_case = CreateTaskUseCase(self.repository)
        request = CreateTaskInput(
            name=name,
            priority=priority or self.config.task.default_priority,
            deadline=deadline,
            estimated_duration=estimated_duration,
            planned_start=planned_start,
            planned_end=planned_end,
            is_fixed=is_fixed,
            tags=tags,
        )
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def reopen_task(self, task_id: int) -> TaskOperationOutput:
        """Reopen a task.

        Changes task status to PENDING and clears actual start/end times.

        Args:
            task_id: ID of the task to reopen

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be reopened
        """
        use_case = ReopenTaskUseCase(self.repository, self.time_tracker)
        request = ReopenTaskInput(task_id=task_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def archive_task(self, task_id: int) -> TaskOperationOutput:
        """Archive a task (soft delete).

        Sets is_archived flag to True, preserving task data.

        Args:
            task_id: ID of the task to archive

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be archived
        """
        use_case = ArchiveTaskUseCase(self.repository)
        request = ArchiveTaskInput(task_id=task_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def remove_task(self, task_id: int) -> None:
        """Remove a task (hard delete).

        Permanently deletes the task from the repository.

        Args:
            task_id: ID of the task to remove

        Raises:
            TaskNotFoundException: If task not found
        """
        use_case = RemoveTaskUseCase(self.repository)
        request = RemoveTaskInput(task_id=task_id)
        use_case.execute(request)

    def restore_task(self, task_id: int) -> TaskOperationOutput:
        """Restore an archived task.

        Sets is_archived flag to False, making the task visible again.

        Args:
            task_id: ID of the task to restore

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be restored
        """
        use_case = RestoreTaskUseCase(self.repository)
        request = RestoreTaskInput(task_id=task_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def add_dependency(self, task_id: int, depends_on_id: int) -> TaskOperationOutput:
        """Add a dependency to a task.

        Args:
            task_id: ID of the task to add dependency to
            depends_on_id: ID of the dependency task to add

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task or dependency not found
            TaskValidationError: If dependency would create a cycle, or task depends on itself
        """
        use_case = AddDependencyUseCase(self.repository)
        request = AddDependencyInput(task_id=task_id, depends_on_id=depends_on_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def remove_dependency(self, task_id: int, depends_on_id: int) -> TaskOperationOutput:
        """Remove a dependency from a task.

        Args:
            task_id: ID of the task to remove dependency from
            depends_on_id: ID of the dependency task to remove

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If dependency doesn't exist on task
        """
        use_case = RemoveDependencyUseCase(self.repository)
        request = RemoveDependencyInput(task_id=task_id, depends_on_id=depends_on_id)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def set_task_tags(self, task_id: int, tags: list[str]) -> TaskOperationOutput:
        """Set task tags (completely replaces existing tags).

        Args:
            task_id: ID of the task to set tags for
            tags: List of tags to set

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If tags are invalid (empty strings or duplicates)
        """
        use_case = SetTaskTagsUseCase(self.repository)
        request = SetTaskTagsInput(task_id=task_id, tags=tags)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def log_hours(self, task_id: int, hours: float, date: str) -> TaskOperationOutput:
        """Log actual hours worked on a task for a specific date.

        Args:
            task_id: ID of the task to log hours for
            hours: Number of hours worked (must be > 0)
            date: Date in YYYY-MM-DD format

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If date format is invalid or hours <= 0
        """
        use_case = LogHoursUseCase(self.repository)
        request = LogHoursInput(task_id=task_id, hours=hours, date=date)
        task = use_case.execute(request)
        return TaskOperationOutput.from_task(task)

    def update_task(
        self,
        task_id: int,
        name: str | None = None,
        priority: int | None = None,
        status: TaskStatus | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        is_fixed: bool | None = None,
        tags: list[str] | None = None,
    ) -> tuple[Task, list[str]]:
        """Update task fields.

        Args:
            task_id: ID of the task to update
            name: New task name (optional)
            priority: New priority (optional)
            status: New status (optional)
            planned_start: New planned start datetime (optional)
            planned_end: New planned end datetime (optional)
            deadline: New deadline (optional)
            estimated_duration: New estimated duration in hours (optional)
            is_fixed: Whether task schedule is fixed (optional)
            tags: New tags list (optional)

        Returns:
            Tuple of (updated task, list of updated field names)

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails for any field
        """
        use_case = UpdateTaskUseCase(self.repository, self.time_tracker)
        request = UpdateTaskInput(
            task_id=task_id,
            name=name,
            priority=priority,
            status=status,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=estimated_duration,
            is_fixed=is_fixed,
            tags=tags,
        )
        return use_case.execute(request)

    def get_task_detail(self, task_id: int) -> GetTaskDetailOutput:
        """Get task details with notes.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            GetTaskDetailOutput containing task and notes information

        Raises:
            TaskNotFoundException: If task not found
            ValueError: If notes_repository is not initialized
        """
        if self.notes_repository is None:
            raise ValueError("notes_repository is required for get_task_detail operation")

        use_case = GetTaskDetailUseCase(self.repository, self.notes_repository)
        input_dto = GetTaskDetailInput(task_id)
        return use_case.execute(input_dto)

    def calculate_statistics(self, period: str = "all") -> StatisticsOutput:
        """Calculate task statistics.

        Args:
            period: Time period for filtering ('7d', '30d', or 'all')

        Returns:
            StatisticsOutput containing comprehensive task statistics

        Raises:
            ValueError: If period is invalid
        """
        if period not in ["all", "7d", "30d"]:
            raise ValueError(f"Invalid period: {period}. Must be 'all', '7d', or '30d'")

        use_case = CalculateStatisticsUseCase(self.repository)
        request = CalculateStatisticsInput(period=period)
        return use_case.execute(request)

    def optimize_schedule(
        self,
        algorithm: str,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool = True,
    ) -> OptimizationOutput:
        """Optimize task schedules.

        Args:
            algorithm: Optimization algorithm name
            start_date: Start date for optimization
            max_hours_per_day: Maximum hours per day
            force_override: Force override existing schedules (default: True)

        Returns:
            OptimizationOutput containing successful/failed tasks and summary

        Raises:
            ValidationError: If algorithm is invalid or parameters are invalid
        """
        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            force_override=force_override,
            algorithm_name=algorithm,
            current_time=datetime.now(),
        )

        use_case = OptimizeScheduleUseCase(self.repository, self.config)
        return use_case.execute(optimize_input)
