"""Use case for optimizing task schedules."""

from datetime import datetime

from taskdog_core.application.dto.optimization_output import OptimizationOutput
from taskdog_core.application.dto.optimize_schedule_input import OptimizeScheduleInput
from taskdog_core.application.dto.task_dto import TaskSummaryDto
from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
from taskdog_core.application.services.optimization.strategy_factory import (
    StrategyFactory,
)
from taskdog_core.application.services.optimization_summary_builder import (
    OptimizationSummaryBuilder,
)
from taskdog_core.application.services.schedule_clearer import ScheduleClearer
from taskdog_core.application.services.workload_calculation_strategy_factory import (
    WorkloadCalculationStrategyFactory,
)
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class OptimizeScheduleUseCase(UseCase[OptimizeScheduleInput, OptimizationOutput]):
    """Use case for optimizing task schedules.

    Analyzes all tasks and generates optimal schedules based on
    priorities, deadlines, and workload constraints.
    """

    def __init__(
        self,
        repository: TaskRepository,
        default_start_hour: int,
        default_end_hour: int,
        holiday_checker: IHolidayChecker | None = None,
    ):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            default_start_hour: Default start hour for tasks (e.g., 9)
            default_end_hour: Default end hour for tasks (e.g., 18)
            holiday_checker: Holiday checker for workday validation (optional)
        """
        self.repository = repository
        self.default_start_hour = default_start_hour
        self.default_end_hour = default_end_hour
        self.schedule_clearer = ScheduleClearer(repository)
        self.summary_builder = OptimizationSummaryBuilder(repository)
        self.holiday_checker = holiday_checker

    def execute(self, input_dto: OptimizeScheduleInput) -> OptimizationOutput:
        """Execute schedule optimization.

        Args:
            input_dto: Optimization parameters

        Returns:
            OptimizationOutput containing successful/failed tasks, allocations, and summary

        Raises:
            ValueError: If algorithm_name is not recognized
            Exception: If optimization fails
        """
        # Get all tasks and backup their states before optimization
        all_tasks = self.repository.get_all()
        task_states_before: dict[int, datetime | None] = {
            t.id: t.planned_start for t in all_tasks if t.id is not None
        }

        # Filter schedulable tasks (UseCase responsibility: what to optimize)
        schedulable_tasks = [
            task for task in all_tasks if task.is_schedulable(input_dto.force_override)
        ]

        # Create WorkloadCalculator for optimization context
        # Factory selects appropriate strategy (WeekdayOnlyStrategy for optimization)
        # UseCase constructs the calculator with the strategy
        workload_strategy = WorkloadCalculationStrategyFactory.create_for_optimization(
            holiday_checker=self.holiday_checker,
            include_weekends=False,  # Future: from config
        )
        workload_calculator = WorkloadCalculator(workload_strategy)

        # Get optimization strategy
        strategy = StrategyFactory.create(
            input_dto.algorithm_name, self.default_start_hour, self.default_end_hour
        )

        # Run optimization with injected workload calculator
        # Strategy responsibility: how to optimize
        modified_tasks, daily_allocations, failed_tasks = strategy.optimize_tasks(
            schedulable_tasks=schedulable_tasks,
            all_tasks_for_context=all_tasks,
            start_date=input_dto.start_date,
            max_hours_per_day=input_dto.max_hours_per_day,
            force_override=input_dto.force_override,
            holiday_checker=self.holiday_checker,
            current_time=input_dto.current_time,
            workload_calculator=workload_calculator,
        )

        # Save successfully scheduled tasks (batch operation for performance)
        self.repository.save_all(modified_tasks)

        # Clear schedules for tasks that couldn't be scheduled
        # (when force_override is True, schedulable tasks that failed to schedule
        # should have their old schedules cleared to avoid phantom allocations)
        if input_dto.force_override:
            scheduled_task_ids = {t.id for t in modified_tasks}

            # Find tasks that were schedulable but failed to schedule
            # Use already-filtered schedulable_tasks instead of re-filtering
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
            modified_tasks,
            task_states_before,
            daily_allocations,
            input_dto.max_hours_per_day,
        )

        # Convert Tasks to DTOs
        successful_tasks_dto = [
            self._task_to_summary_dto(task) for task in modified_tasks
        ]
        # failed_tasks is already list[SchedulingFailure] with TaskSummaryDto from strategy
        failed_tasks_dto = failed_tasks

        # Create and return result
        return OptimizationOutput(
            successful_tasks=successful_tasks_dto,
            failed_tasks=failed_tasks_dto,
            daily_allocations=daily_allocations,
            summary=summary,
            task_states_before=task_states_before,
        )

    def _task_to_summary_dto(self, task: Task) -> TaskSummaryDto:
        """Convert Task entity to TaskSummaryDto.

        Args:
            task: Task entity

        Returns:
            TaskSummaryDto with basic task information
        """
        # Tasks from repository must have an ID
        if task.id is None:
            raise ValueError("Task must have an ID")
        return TaskSummaryDto(id=task.id, name=task.name)
