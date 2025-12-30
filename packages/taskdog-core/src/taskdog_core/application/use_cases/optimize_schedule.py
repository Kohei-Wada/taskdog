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
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    NoSchedulableTasksError,
    TaskNotFoundException,
    TaskNotSchedulableError,
)
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
            TaskNotFoundException: If any specified task_id does not exist
            NoSchedulableTasksError: If no tasks can be scheduled
            Exception: If optimization fails
        """
        # Get all tasks and backup their states before optimization
        all_tasks = self.repository.get_all()
        task_states_before: dict[int, datetime | None] = {
            t.id: t.planned_start for t in all_tasks if t.id is not None
        }

        # Determine target tasks for optimization
        if input_dto.task_ids:
            # Specific tasks requested: validate that all task IDs exist
            task_map = {t.id: t for t in all_tasks if t.id is not None}
            missing_ids = [tid for tid in input_dto.task_ids if tid not in task_map]
            if missing_ids:
                if len(missing_ids) == 1:
                    raise TaskNotFoundException(missing_ids[0])
                raise TaskNotFoundException(
                    f"Tasks with IDs {', '.join(map(str, missing_ids))} not found"
                )
            target_tasks = [task_map[tid] for tid in input_dto.task_ids]
        else:
            # All tasks are candidates
            target_tasks = all_tasks

        # Validate and filter schedulable tasks (common logic for both cases)
        schedulable_tasks = []
        reasons: dict[int, str] = {}
        for task in target_tasks:
            try:
                # Delegate validation to entity (domain logic)
                task.validate_schedulable(input_dto.force_override)
                schedulable_tasks.append(task)
            except TaskNotSchedulableError as e:
                # Collect failure reason from exception
                reasons[e.task_id] = e.reason

        # Only raise error when specific tasks were requested but none are schedulable
        # When no task_ids specified, empty result is acceptable (backward compatibility)
        if input_dto.task_ids and not schedulable_tasks:
            raise NoSchedulableTasksError(task_ids=input_dto.task_ids, reasons=reasons)

        # Filter tasks for workload calculation (UseCase responsibility)
        # - Exclude finished tasks (completed/archived)
        # - If force_override=True: only include Fixed and IN_PROGRESS tasks
        # - If force_override=False: include all active scheduled tasks
        workload_tasks = self._filter_workload_tasks(
            all_tasks, input_dto.force_override
        )

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
        # Pass filtered workload_tasks instead of all_tasks
        modified_tasks, daily_allocations, failed_tasks = strategy.optimize_tasks(
            schedulable_tasks=schedulable_tasks,
            all_tasks_for_context=workload_tasks,
            input_dto=input_dto,
            holiday_checker=self.holiday_checker,
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
            TaskSummaryDto.from_entity(task) for task in modified_tasks
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

    def _filter_workload_tasks(
        self, all_tasks: list[Task], force_override: bool
    ) -> list[Task]:
        """Filter tasks that should be included in workload calculation.

        Business Rules:
        - Exclude finished tasks (completed/archived) - they don't contribute to future workload
        - If force_override=True:
          - Include Fixed tasks (immovable time constraints)
          - Include IN_PROGRESS tasks (already started, should not be rescheduled)
          - Exclude PENDING non-fixed tasks (will be rescheduled)
        - If force_override=False:
          - Include all active tasks with schedules

        Args:
            all_tasks: All tasks in the system
            force_override: Whether existing schedules will be overridden

        Returns:
            List of tasks to include in workload calculation
        """
        filtered = []
        for task in all_tasks:
            # Skip finished tasks (completed/archived) - they don't contribute to future workload
            if not task.should_count_in_workload():
                continue

            # If force_override=True, only include Fixed and IN_PROGRESS tasks
            # (PENDING non-fixed tasks will be rescheduled, so exclude them from workload)
            if force_override:
                if task.is_fixed or task.status == TaskStatus.IN_PROGRESS:
                    filtered.append(task)
            else:
                # If force_override=False, include all active tasks
                filtered.append(task)

        return filtered
