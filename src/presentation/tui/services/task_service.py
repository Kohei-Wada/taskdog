"""Task service facade for TUI operations."""

from datetime import datetime

from application.dto.optimization_output import OptimizationOutput
from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from domain.repositories.task_repository import TaskRepository
from presentation.tui.context import TUIContext
from shared.utils.date_utils import calculate_next_workday


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
