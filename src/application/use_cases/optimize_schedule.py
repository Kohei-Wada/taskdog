"""Use case for optimizing task schedules."""

from contextlib import suppress
from datetime import datetime

from application.dto.optimization_result import OptimizationResult
from application.dto.optimize_schedule_request import OptimizeScheduleRequest
from application.services.optimization.strategy_factory import StrategyFactory
from application.services.optimization_summary_builder import OptimizationSummaryBuilder
from application.services.schedule_clearer import ScheduleClearer
from application.use_cases.base import UseCase
from infrastructure.persistence.task_repository import TaskRepository
from shared.config_manager import Config
from shared.utils.holiday_checker import HolidayChecker


class OptimizeScheduleUseCase(UseCase[OptimizeScheduleRequest, OptimizationResult]):
    """Use case for optimizing task schedules.

    Analyzes all tasks and generates optimal schedules based on
    priorities, deadlines, and workload constraints.
    """

    def __init__(self, repository: TaskRepository, config: Config):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            config: Application configuration
        """
        self.repository = repository
        self.config = config
        self.schedule_clearer = ScheduleClearer(repository)
        self.summary_builder = OptimizationSummaryBuilder(repository)

        # Create HolidayChecker if country is configured
        self.holiday_checker: HolidayChecker | None = None
        if config.region.country:
            with suppress(ImportError, NotImplementedError):
                self.holiday_checker = HolidayChecker(config.region.country)

    def execute(self, input_dto: OptimizeScheduleRequest) -> OptimizationResult:
        """Execute schedule optimization.

        Args:
            input_dto: Optimization parameters

        Returns:
            OptimizationResult containing successful/failed tasks, allocations, and summary

        Raises:
            ValueError: If algorithm_name is not recognized
            Exception: If optimization fails
        """
        # Get all tasks and backup their states before optimization
        all_tasks = self.repository.get_all()
        task_states_before: dict[int, datetime | None] = {
            t.id: t.planned_start for t in all_tasks if t.id is not None
        }

        # Get optimization strategy
        strategy = StrategyFactory.create(input_dto.algorithm_name, self.config)

        # Run optimization
        modified_tasks, daily_allocations, failed_tasks = strategy.optimize_tasks(
            tasks=all_tasks,
            repository=self.repository,
            start_date=input_dto.start_date,
            max_hours_per_day=input_dto.max_hours_per_day,
            force_override=input_dto.force_override,
            holiday_checker=self.holiday_checker,
            current_time=input_dto.current_time,
        )

        # Save successfully scheduled tasks (batch operation for performance)
        self.repository.save_all(modified_tasks)

        # Clear schedules for tasks that couldn't be scheduled
        # (when force_override is True, schedulable tasks that failed to schedule
        # should have their old schedules cleared to avoid phantom allocations)
        if input_dto.force_override:
            schedulable_tasks = [
                task for task in all_tasks if task.is_schedulable(input_dto.force_override)
            ]
            scheduled_task_ids = {t.id for t in modified_tasks}

            # Find tasks that were schedulable but failed to schedule
            tasks_to_clear = [
                task
                for task in schedulable_tasks
                if task.id not in scheduled_task_ids and task.planned_start
            ]

            # Clear schedules using ScheduleClearer service
            if tasks_to_clear:
                self.schedule_clearer.clear_schedules(tasks_to_clear)

        # Build optimization summary
        summary = self.summary_builder.build(
            modified_tasks, task_states_before, daily_allocations, input_dto.max_hours_per_day
        )

        # Create and return result
        return OptimizationResult(
            successful_tasks=modified_tasks,
            failed_tasks=failed_tasks,
            daily_allocations=daily_allocations,
            summary=summary,
            task_states_before=task_states_before,
        )
