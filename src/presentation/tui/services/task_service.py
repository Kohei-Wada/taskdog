"""Task service facade for TUI operations."""

from datetime import date, datetime

from application.dto.archive_task_request import ArchiveTaskRequest
from application.dto.cancel_task_request import CancelTaskRequest
from application.dto.complete_task_request import CompleteTaskRequest
from application.dto.create_task_request import CreateTaskRequest
from application.dto.gantt_result import GanttResult
from application.dto.optimization_result import OptimizationResult
from application.dto.optimize_schedule_request import OptimizeScheduleRequest
from application.dto.pause_task_request import PauseTaskRequest
from application.dto.remove_task_request import RemoveTaskRequest
from application.dto.start_task_request import StartTaskRequest
from application.dto.update_task_request import UpdateTaskRequest
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.filters.task_filter import TaskFilter
from application.use_cases.archive_task import ArchiveTaskUseCase
from application.use_cases.cancel_task import CancelTaskUseCase
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from application.use_cases.pause_task import PauseTaskUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from application.use_cases.start_task import StartTaskUseCase
from application.use_cases.update_task import UpdateTaskUseCase
from domain.entities.task import Task, TaskStatus
from presentation.tui.context import TUIContext
from shared.utils.date_utils import calculate_next_workday


class TaskService:
    """Facade service for task operations in TUI.

    This service provides a simplified interface to use cases,
    reducing boilerplate in command classes.
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

    def create_task(
        self,
        name: str,
        priority: int | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        is_fixed: bool = False,
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
        )
        return use_case.execute(task_input)

    def start_task(self, task_id: int) -> Task:
        """Start a task.

        Args:
            task_id: Task ID

        Returns:
            The updated task
        """
        use_case = StartTaskUseCase(self.repository, self.time_tracker)
        start_input = StartTaskRequest(task_id=task_id)
        return use_case.execute(start_input)

    def pause_task(self, task_id: int) -> Task:
        """Pause a task.

        Args:
            task_id: Task ID

        Returns:
            The updated task
        """
        use_case = PauseTaskUseCase(self.repository, self.time_tracker)
        pause_input = PauseTaskRequest(task_id=task_id)
        return use_case.execute(pause_input)

    def complete_task(self, task_id: int) -> Task:
        """Complete a task.

        Args:
            task_id: Task ID

        Returns:
            The updated task
        """
        use_case = CompleteTaskUseCase(self.repository, self.time_tracker)
        complete_input = CompleteTaskRequest(task_id=task_id)
        return use_case.execute(complete_input)

    def cancel_task(self, task_id: int) -> Task:
        """Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            The updated task
        """
        use_case = CancelTaskUseCase(self.repository, self.time_tracker)
        cancel_input = CancelTaskRequest(task_id=task_id)
        return use_case.execute(cancel_input)

    def remove_task(self, task_id: int) -> Task:
        """Remove a task (archive).

        Args:
            task_id: Task ID

        Returns:
            The archived task
        """
        use_case = ArchiveTaskUseCase(self.repository, self.time_tracker)
        archive_input = ArchiveTaskRequest(task_id=task_id)
        return use_case.execute(archive_input)

    def hard_delete_task(self, task_id: int) -> None:
        """Permanently delete a task (hard delete).

        Args:
            task_id: Task ID
        """
        use_case = RemoveTaskUseCase(self.repository)
        remove_input = RemoveTaskRequest(task_id=task_id)
        use_case.execute(remove_input)

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

        Returns:
            Tuple of (updated task, list of updated field names)
        """
        use_case = UpdateTaskUseCase(self.repository, self.time_tracker)
        update_input = UpdateTaskRequest(
            task_id=task_id,
            name=name,
            priority=priority,
            status=status,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=estimated_duration,
            is_fixed=is_fixed,
        )
        return use_case.execute(update_input)

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
    ) -> GanttResult:
        """Get Gantt chart data for the given tasks.

        Args:
            task_ids: List of task IDs to include in the gantt chart
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            start_date: Optional start date (auto-calculated if not provided)
            end_date: Optional end date (auto-calculated if not provided)

        Returns:
            GanttResult containing business data for Gantt visualization
        """

        class TaskIdFilter(TaskFilter):
            """Filter that only includes tasks with specific IDs."""

            def __init__(self, task_id_set: set[int]):
                self.task_ids = task_id_set

            def filter(self, all_tasks: list[Task]) -> list[Task]:
                return [t for t in all_tasks if t.id in self.task_ids]

        filter_obj = TaskIdFilter(set(task_ids))
        return self.query_service.get_gantt_data(
            filter_obj=filter_obj,
            sort_by=sort_by,
            reverse=False,
            start_date=start_date,
            end_date=end_date,
        )
