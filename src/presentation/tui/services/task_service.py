"""Task service facade for TUI operations."""

from datetime import date, datetime

from application.dto.create_task_request import CreateTaskRequest
from application.dto.manage_dependencies_request import (
    AddDependencyRequest,
    RemoveDependencyRequest,
)
from application.dto.optimization_result import OptimizationResult
from application.dto.optimize_schedule_request import OptimizeScheduleRequest
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.filters.task_filter import TaskFilter
from application.use_cases.add_dependency import AddDependencyUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskValidationError
from presentation.controllers.task_controller import TaskController
from presentation.mappers.gantt_mapper import GanttMapper
from presentation.tui.context import TUIContext
from presentation.view_models.gantt_view_model import GanttViewModel
from shared.utils.date_utils import calculate_next_workday


class _TaskIdFilter(TaskFilter):
    """Filter that only includes tasks with specific IDs.

    This is a private helper class used internally by TaskService
    for filtering tasks by ID in gantt chart operations.
    """

    def __init__(self, task_id_set: set[int]):
        """Initialize the filter.

        Args:
            task_id_set: Set of task IDs to include
        """
        self.task_ids = task_id_set

    def filter(self, all_tasks: list[Task]) -> list[Task]:
        """Filter tasks by ID.

        Args:
            all_tasks: All tasks to filter

        Returns:
            List of tasks matching the ID set
        """
        return [t for t in all_tasks if t.id in self.task_ids]


class TaskService:
    """Facade service for task operations in TUI.

    This service provides a simplified interface to use cases,
    reducing boilerplate in command classes. Methods are organized
    into two categories: Commands (write operations) and Queries (read operations).
    """

    def __init__(self, context: TUIContext):
        """Initialize the task service.

        Args:
            context: TUI context with all required dependencies
        """
        self.repository = context.repository
        self.time_tracker = context.time_tracker
        self.query_service = context.query_service
        self.config = context.config
        # Initialize controller for delegating simple operations
        self.controller = TaskController(context.repository, context.time_tracker, context.config)

    # ============================================================================
    # Command Operations (Write)
    # ============================================================================

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
    ) -> Task:
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
            The created task
        """
        use_case = CreateTaskUseCase(self.repository)
        task_input = CreateTaskRequest(
            name=name,
            priority=priority or self.config.task.default_priority,
            deadline=deadline,
            estimated_duration=estimated_duration,
            planned_start=planned_start,
            planned_end=planned_end,
            is_fixed=is_fixed,
            tags=tags,
        )
        return use_case.execute(task_input)

    def optimize_schedule(
        self,
        algorithm: str,
        start_date: datetime | None = None,
        max_hours_per_day: float | None = None,
        force_override: bool = True,
    ) -> OptimizationResult:
        """Optimize task schedules.

        Args:
            algorithm: Optimization algorithm name
            start_date: Start date (default: calculated)
            max_hours_per_day: Max hours per day (default: from config)
            force_override: Force override existing schedules (default: True for TUI)

        Returns:
            OptimizationResult containing successful/failed tasks and summary
        """
        if start_date is None:
            start_date = calculate_next_workday()

        optimize_input = OptimizeScheduleRequest(
            start_date=start_date,
            max_hours_per_day=max_hours_per_day or self.config.optimization.max_hours_per_day,
            force_override=force_override,
            algorithm_name=algorithm,
            current_time=datetime.now(),
        )

        use_case = OptimizeScheduleUseCase(self.repository, self.config)
        return use_case.execute(optimize_input)

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
        """Update a task.

        Args:
            task_id: ID of the task to update
            name: New name (optional)
            priority: New priority (optional)
            status: New status (optional)
            planned_start: New planned start (optional)
            planned_end: New planned end (optional)
            deadline: New deadline (optional)
            estimated_duration: New estimated duration (optional)
            is_fixed: Whether task is fixed (optional)
            tags: New tags list (optional)

        Returns:
            Tuple of (updated task, list of updated field names)
        """
        return self.controller.update_task(
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

    def add_dependencies(self, task_id: int, dependency_ids: list[int]) -> list[tuple[int, str]]:
        """Add multiple dependencies to a task.

        Args:
            task_id: ID of the task to add dependencies to
            dependency_ids: List of dependency task IDs to add

        Returns:
            List of (dependency_id, error_message) tuples for failed additions.
            Empty list if all succeeded.
        """
        if not dependency_ids:
            return []

        use_case = AddDependencyUseCase(self.repository)
        failed_dependencies = []

        for dep_id in dependency_ids:
            try:
                dependency_input = AddDependencyRequest(task_id=task_id, depends_on_id=dep_id)
                use_case.execute(dependency_input)
            except TaskValidationError as e:
                failed_dependencies.append((dep_id, str(e)))

        return failed_dependencies

    def sync_dependencies(
        self,
        task_id: int,
        old_dependency_ids: set[int],
        new_dependency_ids: set[int],
    ) -> list[str]:
        """Synchronize task dependencies by adding/removing as needed.

        Args:
            task_id: ID of the task to sync dependencies for
            old_dependency_ids: Set of current dependency IDs
            new_dependency_ids: Set of desired dependency IDs

        Returns:
            List of error messages for failed operations.
            Empty list if all operations succeeded.
        """
        # Calculate differences
        deps_to_remove = old_dependency_ids - new_dependency_ids
        deps_to_add = new_dependency_ids - old_dependency_ids

        failed_operations = []

        # Remove dependencies
        if deps_to_remove:
            remove_use_case = RemoveDependencyUseCase(self.repository)
            for dep_id in deps_to_remove:
                try:
                    remove_input = RemoveDependencyRequest(task_id=task_id, depends_on_id=dep_id)
                    remove_use_case.execute(remove_input)
                except TaskValidationError as e:
                    failed_operations.append(f"Remove {dep_id}: {e}")

        # Add dependencies
        if deps_to_add:
            add_use_case = AddDependencyUseCase(self.repository)
            for dep_id in deps_to_add:
                try:
                    add_input = AddDependencyRequest(task_id=task_id, depends_on_id=dep_id)
                    add_use_case.execute(add_input)
                except TaskValidationError as e:
                    failed_operations.append(f"Add {dep_id}: {e}")

        return failed_operations

    # ============================================================================
    # Query Operations (Read)
    # ============================================================================

    def get_incomplete_tasks(self, sort_by: str = "id") -> list[Task]:
        """Get incomplete tasks (PENDING, IN_PROGRESS).

        Args:
            sort_by: Sort field

        Returns:
            List of incomplete tasks
        """
        incomplete_filter = IncompleteFilter()
        return self.query_service.get_filtered_tasks(incomplete_filter, sort_by=sort_by)

    def get_gantt_data(
        self,
        task_ids: list[int],
        sort_by: str = "deadline",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> GanttViewModel:
        """Get Gantt chart data for the given tasks.

        Args:
            task_ids: List of task IDs to include in the gantt chart
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            start_date: Optional start date (auto-calculated if not provided)
            end_date: Optional end date (auto-calculated if not provided)

        Returns:
            GanttViewModel containing presentation-ready Gantt data
        """
        filter_obj = _TaskIdFilter(set(task_ids))
        gantt_result = self.query_service.get_gantt_data(
            filter_obj=filter_obj,
            sort_by=sort_by,
            reverse=False,
            start_date=start_date,
            end_date=end_date,
        )
        # Convert DTO to ViewModel
        return GanttMapper.from_gantt_result(gantt_result)
