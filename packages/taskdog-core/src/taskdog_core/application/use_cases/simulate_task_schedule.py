"""Use case for simulating task schedules without saving to database."""

from datetime import date, datetime

from taskdog_core.application.dto.optimization_output import SchedulingFailure
from taskdog_core.application.dto.simulate_task_request import SimulateTaskRequest
from taskdog_core.application.dto.simulation_result import SimulationResult
from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
from taskdog_core.application.services.optimization.strategy_factory import (
    StrategyFactory,
)
from taskdog_core.application.services.workload_calculation_strategy_factory import (
    WorkloadCalculationStrategyFactory,
)
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class SimulateTaskScheduleUseCase(UseCase[SimulateTaskRequest, SimulationResult]):
    """Use case for simulating task schedules without persisting to database.

    Creates a virtual task and runs optimization in memory to predict
    completion dates and workload impact without modifying the database.
    """

    # Virtual task ID marker (negative to avoid conflicts with real task IDs)
    VIRTUAL_TASK_ID = -1

    def __init__(
        self,
        repository: TaskRepository,
        default_start_hour: int,
        default_end_hour: int,
        holiday_checker: IHolidayChecker | None = None,
    ):
        """Initialize use case.

        Args:
            repository: Task repository for reading existing tasks (read-only)
            default_start_hour: Default start hour for tasks (e.g., 9)
            default_end_hour: Default end hour for tasks (e.g., 18)
            holiday_checker: Holiday checker for workday validation (optional)
        """
        self.repository = repository
        self.default_start_hour = default_start_hour
        self.default_end_hour = default_end_hour
        self.holiday_checker = holiday_checker

    def execute(self, input_dto: SimulateTaskRequest) -> SimulationResult:
        """Execute task simulation.

        Args:
            input_dto: Simulation parameters including virtual task details

        Returns:
            SimulationResult containing schedule prediction and workload analysis

        Raises:
            ValueError: If algorithm_name is not recognized
            TaskValidationError: If virtual task parameters are invalid
        """
        # Create virtual task with negative ID to distinguish from real tasks
        virtual_task = self._create_virtual_task(input_dto)

        # Get existing tasks (read-only)
        existing_tasks = self.repository.get_all()

        # Combine virtual task with existing tasks for optimization
        all_tasks = [*existing_tasks, virtual_task]

        # Create WorkloadCalculator for optimization context
        workload_strategy = WorkloadCalculationStrategyFactory.create_for_optimization(
            holiday_checker=self.holiday_checker,
            include_weekends=False,
        )
        workload_calculator = WorkloadCalculator(workload_strategy)

        # Get optimization strategy
        strategy = StrategyFactory.create(
            input_dto.algorithm_name, self.default_start_hour, self.default_end_hour
        )

        # Ensure start_date is set (use current time if not provided)
        start_date = input_dto.start_date or datetime.now()

        # Run optimization (in-memory only, no database writes)
        modified_tasks, daily_allocations, failed_tasks = strategy.optimize_tasks(
            tasks=all_tasks,
            repository=self.repository,  # Used for reference only
            start_date=start_date,
            max_hours_per_day=input_dto.max_hours_per_day,
            force_override=input_dto.force_override,
            holiday_checker=self.holiday_checker,
            current_time=datetime.now(),
            workload_calculator=workload_calculator,
        )

        # IMPORTANT: Do NOT call repository.save_all() - this is a simulation only

        # Extract virtual task result
        virtual_task_result = self._find_virtual_task_result(
            modified_tasks, failed_tasks
        )

        # Build and return simulation result
        return self._build_simulation_result(
            virtual_task_result, input_dto, daily_allocations
        )

    def _create_virtual_task(self, input_dto: SimulateTaskRequest) -> Task:
        """Create a virtual task from simulation request.

        Args:
            input_dto: Simulation request with task parameters

        Returns:
            Task entity with negative ID (virtual task marker)
        """
        return Task(
            id=self.VIRTUAL_TASK_ID,
            name=input_dto.name,
            priority=input_dto.priority,
            estimated_duration=input_dto.estimated_duration,
            deadline=input_dto.deadline,
            depends_on=input_dto.depends_on,
            status=TaskStatus.PENDING,
            is_fixed=False,
        )

    def _find_virtual_task_result(
        self,
        modified_tasks: list[Task],
        failed_tasks: list[SchedulingFailure],
    ) -> tuple[Task | None, str | None]:
        """Find the virtual task in optimization results.

        Args:
            modified_tasks: Successfully scheduled tasks
            failed_tasks: Tasks that failed to be scheduled

        Returns:
            Tuple of (virtual_task, failure_reason)
            - If scheduled: (Task, None)
            - If failed: (None, reason)
            - If not found: (None, "Unknown error")
        """
        # Check if virtual task was successfully scheduled
        for task in modified_tasks:
            if task.id == self.VIRTUAL_TASK_ID:
                return task, None

        # Check if virtual task failed to be scheduled
        for failure in failed_tasks:
            if failure.task.id == self.VIRTUAL_TASK_ID:
                return None, failure.reason

        # Should not reach here, but handle gracefully
        return None, "Virtual task not found in optimization results"

    def _build_simulation_result(
        self,
        virtual_task_result: tuple[Task | None, str | None],
        input_dto: SimulateTaskRequest,
        daily_allocations: dict[date, float],
    ) -> SimulationResult:
        """Build simulation result from virtual task optimization.

        Args:
            virtual_task_result: Tuple of (virtual_task, failure_reason)
            input_dto: Original simulation request
            daily_allocations: Daily hour allocations from optimization

        Returns:
            SimulationResult with schedule and workload information
        """
        virtual_task, failure_reason = virtual_task_result

        # Extract virtual task's daily allocations
        virtual_daily_allocations = {}
        if virtual_task and virtual_task.daily_allocations:
            virtual_daily_allocations = virtual_task.daily_allocations

        # Calculate workload metrics
        peak_workload = 0.0
        peak_date = None
        total_hours = 0.0
        if virtual_daily_allocations:
            peak_workload = max(virtual_daily_allocations.values())
            peak_date = max(
                virtual_daily_allocations.keys(),
                key=lambda d: virtual_daily_allocations[d],
            )
            total_hours = sum(virtual_daily_allocations.values())

        total_days = len(virtual_daily_allocations)
        average_workload = total_hours / total_days if total_days > 0 else 0.0

        return SimulationResult(
            is_schedulable=virtual_task is not None,
            planned_start=virtual_task.planned_start if virtual_task else None,
            planned_end=virtual_task.planned_end if virtual_task else None,
            failure_reason=failure_reason,
            daily_allocations=virtual_daily_allocations,
            peak_workload=peak_workload,
            peak_date=peak_date,
            average_workload=average_workload,
            total_workload_days=total_days,
            virtual_task_name=input_dto.name,
            estimated_duration=input_dto.estimated_duration,
            priority=input_dto.priority,
            deadline=input_dto.deadline,
        )
