"""Task service facade for TUI operations."""

from datetime import date, datetime

from application.dto.optimization_output import OptimizationOutput
from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.queries.filters.task_filter import TaskFilter
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from domain.entities.task import Task
from domain.repositories.task_repository import TaskRepository
from presentation.presenters.gantt_presenter import GanttPresenter
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

    def __init__(self, context: TUIContext, repository: TaskRepository):
        """Initialize the task service.

        Args:
            context: TUI context with all required dependencies
            repository: Task repository (needed for optimize_schedule which doesn't use controller yet)
        """
        self.repository = repository  # Only for optimize_schedule use case
        self.config = context.config
        self.notes_repository = context.notes_repository
        # Get controllers from context (no longer instantiate them)
        self.controller = context.task_controller
        self.query_controller = context.query_controller
        # Initialize GanttPresenter for gantt view models
        self.gantt_presenter = GanttPresenter()

    # ============================================================================
    # Command Operations (Write)
    # ============================================================================

    def optimize_schedule(
        self,
        algorithm: str,
        start_date: datetime | None = None,
        max_hours_per_day: float | None = None,
        force_override: bool = True,
    ) -> OptimizationOutput:
        """Optimize task schedules.

        Args:
            algorithm: Optimization algorithm name
            start_date: Start date (default: calculated)
            max_hours_per_day: Max hours per day (default: from config)
            force_override: Force override existing schedules (default: True for TUI)

        Returns:
            OptimizationOutput containing successful/failed tasks and summary
        """
        if start_date is None:
            start_date = calculate_next_workday()

        optimize_input = OptimizeScheduleInput(
            start_date=start_date,
            max_hours_per_day=max_hours_per_day or self.config.optimization.max_hours_per_day,
            force_override=force_override,
            algorithm_name=algorithm,
            current_time=datetime.now(),
        )

        use_case = OptimizeScheduleUseCase(self.repository, self.config)
        return use_case.execute(optimize_input)

    # ============================================================================
    # Query Operations (Read)
    # ============================================================================

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
        gantt_result = self.query_controller.get_gantt_data(
            filter_obj=filter_obj,
            sort_by=sort_by,
            reverse=False,
            start_date=start_date,
            end_date=end_date,
        )
        # Convert DTO to ViewModel
        return self.gantt_presenter.present(gantt_result)
