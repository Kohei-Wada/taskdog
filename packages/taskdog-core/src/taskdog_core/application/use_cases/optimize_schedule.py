"""Use case for optimizing task schedules."""

from datetime import datetime, time

from taskdog_core.application.dto.optimization_output import OptimizationOutput
from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_schedule_input import OptimizeScheduleInput
from taskdog_core.application.dto.task_dto import TaskSummaryDto
from taskdog_core.application.queries.workload import OptimizationWorkloadCalculator
from taskdog_core.application.services.optimization.strategy_factory import (
    StrategyFactory,
)
from taskdog_core.application.services.optimization_summary_builder import (
    OptimizationSummaryBuilder,
)
from taskdog_core.application.services.schedule_clearer import ScheduleClearer
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
        default_start_time: time,
        default_end_time: time,
        holiday_checker: IHolidayChecker | None = None,
    ):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            default_start_time: Default start time for tasks (e.g., time(9, 0))
            default_end_time: Default end time for tasks (e.g., time(18, 0))
            holiday_checker: Holiday checker for workday validation (optional)
        """
        self.repository = repository
        self.default_start_time = default_start_time
        self.default_end_time = default_end_time
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
        # - If task_ids specified: include all OTHER scheduled tasks (not being rescheduled)
        # - If force_override=True: only include Fixed and IN_PROGRESS tasks
        # - If force_override=False: include all active scheduled tasks
        workload_tasks = self._filter_workload_tasks(
            all_tasks, input_dto.force_override, input_dto.task_ids
        )

        # Create WorkloadCalculator for optimization context
        # OptimizationWorkloadCalculator uses WeekdayOnlyStrategy by default,
        # or AllDaysStrategy if include_all_days=True
        workload_calculator = OptimizationWorkloadCalculator(
            holiday_checker=self.holiday_checker,
            include_all_days=input_dto.include_all_days,
        )

        # Get optimization strategy
        strategy = StrategyFactory.create(
            input_dto.algorithm_name, self.default_start_time, self.default_end_time
        )

        # Create OptimizeParams from input_dto
        params = OptimizeParams(
            start_date=input_dto.start_date,
            max_hours_per_day=input_dto.max_hours_per_day,
            holiday_checker=self.holiday_checker,
            current_time=input_dto.current_time,
            include_all_days=input_dto.include_all_days,
        )

        # Run optimization with injected workload calculator
        # Strategy responsibility: how to optimize
        # Pass filtered workload_tasks instead of all_tasks
        result = strategy.optimize_tasks(
            tasks=schedulable_tasks,
            context_tasks=workload_tasks,
            params=params,
            workload_calculator=workload_calculator,
        )

        # Save successfully scheduled tasks (batch operation for performance)
        self.repository.save_all(result.tasks)

        # Clear schedules for tasks that couldn't be scheduled
        # (when force_override is True, schedulable tasks that failed to schedule
        # should have their old schedules cleared to avoid phantom allocations)
        if input_dto.force_override:
            scheduled_task_ids = {t.id for t in result.tasks}

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
            result.tasks,
            task_states_before,
            result.daily_allocations,
            input_dto.max_hours_per_day,
        )

        # Convert Tasks to DTOs
        successful_tasks_dto = [
            TaskSummaryDto.from_entity(task) for task in result.tasks
        ]

        # Create and return result
        return OptimizationOutput(
            successful_tasks=successful_tasks_dto,
            failed_tasks=result.failures,
            daily_allocations=result.daily_allocations,
            summary=summary,
            task_states_before=task_states_before,
        )

    def _filter_workload_tasks(
        self,
        all_tasks: list[Task],
        force_override: bool,
        task_ids: list[int] | None = None,
    ) -> list[Task]:
        """Filter tasks that should be included in workload calculation.

        Business Rules:
        - Exclude finished tasks (completed/archived) - they don't contribute to future workload
        - If task_ids specified (partial reschedule):
          - Include all OTHER scheduled tasks (not in task_ids) as constraints
          - This ensures selected tasks are scheduled around existing schedules
        - If task_ids not specified (full optimization):
          - If force_override=True:
            - Include Fixed tasks (immovable time constraints)
            - Include IN_PROGRESS tasks (already started, should not be rescheduled)
            - Exclude PENDING non-fixed tasks (will be rescheduled)
          - If force_override=False:
            - Include all active tasks with schedules

        Args:
            all_tasks: All tasks in the system
            force_override: Whether existing schedules will be overridden
            task_ids: Specific task IDs being rescheduled (None means all tasks)

        Returns:
            List of tasks to include in workload calculation
        """
        # Convert task_ids to a set for O(1) lookup
        target_ids = set(task_ids) if task_ids else set()

        filtered = []
        for task in all_tasks:
            # Skip finished tasks (completed/archived) - they don't contribute to future workload
            if not task.should_count_in_workload():
                continue

            # If specific task_ids are being rescheduled, include all OTHER scheduled tasks
            # as constraints (regardless of force_override)
            if task_ids:
                # Skip tasks that are being rescheduled
                if task.id in target_ids:
                    continue
                # Include all other tasks that have schedules
                if task.planned_start:
                    filtered.append(task)
            else:
                # Full optimization: use force_override logic
                if force_override:
                    # Only include Fixed and IN_PROGRESS tasks
                    if task.is_fixed or task.status == TaskStatus.IN_PROGRESS:
                        filtered.append(task)
                else:
                    # Include all active tasks
                    filtered.append(task)

        return filtered
