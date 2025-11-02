"""Task analytics controller for statistics and optimization operations.

This controller handles read-heavy analytics and optimization operations:
- calculate_statistics: Calculate comprehensive task statistics for different periods
- optimize_schedule: Auto-schedule tasks using various optimization algorithms
"""

from datetime import datetime

from application.dto.optimization_output import OptimizationOutput
from application.dto.optimize_schedule_input import OptimizeScheduleInput
from application.dto.statistics_output import CalculateStatisticsInput, StatisticsOutput
from application.use_cases.calculate_statistics import CalculateStatisticsUseCase
from application.use_cases.optimize_schedule import OptimizeScheduleUseCase
from domain.repositories.task_repository import TaskRepository
from domain.services.holiday_checker import IHolidayChecker
from presentation.controllers.base_controller import BaseTaskController
from shared.config_manager import Config


class TaskAnalyticsController(BaseTaskController):
    """Controller for task analytics and optimization operations.

    Handles read-heavy operations and schedule optimization:
    - Calculate statistics for different time periods (7d, 30d, all)
    - Optimize task schedules using various algorithms (greedy, balanced, etc.)

    All operations are read-heavy or computational, minimizing database writes.

    Attributes:
        repository: Task repository (inherited from BaseTaskController)
        config: Application configuration (inherited from BaseTaskController)
        holiday_checker: Holiday checker for workday validation (optional)
    """

    def __init__(
        self,
        repository: TaskRepository,
        config: Config,
        holiday_checker: IHolidayChecker | None = None,
    ):
        """Initialize the analytics controller.

        Args:
            repository: Task repository
            config: Application configuration
            holiday_checker: Holiday checker for workday validation (optional)
        """
        super().__init__(repository, config)
        self.holiday_checker = holiday_checker

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

        use_case = OptimizeScheduleUseCase(
            self.repository,
            self.config.time.default_start_hour,
            self.config.time.default_end_hour,
            self.holiday_checker,
        )
        return use_case.execute(optimize_input)
