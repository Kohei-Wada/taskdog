"""Calculate statistics use case."""

from taskdog_core.application.dto.statistics_output import (
    CalculateStatisticsInput,
    StatisticsOutput,
)
from taskdog_core.application.services.task_statistics_calculator import (
    TaskStatisticsCalculator,
)
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.task_repository import TaskRepository


class CalculateStatisticsUseCase(UseCase[CalculateStatisticsInput, StatisticsOutput]):
    """Use case for calculating task statistics.

    This use case retrieves all tasks from the repository and calculates
    comprehensive statistics including basic counts, time tracking,
    estimation accuracy, deadline compliance, priority distribution,
    and trends.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize the use case.

        Args:
            repository: Task repository for retrieving tasks
        """
        self.repository = repository
        self.calculator = TaskStatisticsCalculator()

    def execute(self, input_dto: CalculateStatisticsInput) -> StatisticsOutput:
        """Execute the statistics calculation.

        Args:
            input_dto: Input containing period filter

        Returns:
            StatisticsOutput containing all calculated statistics
        """
        # Get all tasks from repository (including archived for complete statistics)
        tasks = self.repository.get_all()

        # Calculate statistics using the calculator service
        result = self.calculator.calculate_all(tasks, period=input_dto.period)

        return result
