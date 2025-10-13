"""Use case for optimizing task schedules."""

from datetime import datetime

from application.services.optimization.strategy_factory import StrategyFactory
from application.use_cases.base import UseCase
from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository


class OptimizeScheduleInput:
    """Input data for schedule optimization.

    Attributes:
        start_date: Starting date for optimization (datetime object)
        max_hours_per_day: Maximum work hours per day
        force_override: Whether to override existing schedules
        dry_run: If True, only return preview without saving
        algorithm_name: Name of optimization algorithm to use (default: "greedy")
    """

    def __init__(
        self,
        start_date: datetime,
        max_hours_per_day: float = 6.0,
        force_override: bool = False,
        dry_run: bool = False,
        algorithm_name: str = "greedy",
    ):
        self.start_date = start_date
        self.max_hours_per_day = max_hours_per_day
        self.force_override = force_override
        self.dry_run = dry_run
        self.algorithm_name = algorithm_name


class OptimizeScheduleUseCase(UseCase[OptimizeScheduleInput, tuple[list[Task], dict[str, float]]]):
    """Use case for optimizing task schedules.

    Analyzes all tasks and generates optimal schedules based on
    priorities, deadlines, and workload constraints.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: OptimizeScheduleInput) -> tuple[list[Task], dict[str, float]]:
        """Execute schedule optimization.

        Args:
            input_dto: Optimization parameters

        Returns:
            Tuple of (modified tasks, daily_allocations dict)
            daily_allocations: dict mapping date strings to allocated hours

        Raises:
            ValueError: If algorithm_name is not recognized
            Exception: If optimization fails
        """
        # Get all tasks
        all_tasks = self.repository.get_all()

        # Get optimization strategy
        strategy = StrategyFactory.create(input_dto.algorithm_name)

        # Run optimization
        modified_tasks, daily_allocations = strategy.optimize_tasks(
            tasks=all_tasks,
            repository=self.repository,
            start_date=input_dto.start_date,
            max_hours_per_day=input_dto.max_hours_per_day,
            force_override=input_dto.force_override,
        )

        # Save changes unless dry_run
        if not input_dto.dry_run:
            for task in modified_tasks:
                self.repository.save(task)

        return modified_tasks, daily_allocations
