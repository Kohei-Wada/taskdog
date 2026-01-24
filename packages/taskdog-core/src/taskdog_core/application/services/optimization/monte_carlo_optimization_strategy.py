"""Monte Carlo optimization strategy implementation."""

import random
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from taskdog_core.application.constants.optimization import MONTE_CARLO_NUM_SIMULATIONS
from taskdog_core.application.dto.optimization_output import SchedulingFailure
from taskdog_core.application.services.optimization.allocation_context import (
    AllocationContext,
)
from taskdog_core.application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.services.optimization.schedule_fitness_calculator import (
    ScheduleFitnessCalculator,
)
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.application.dto.optimize_schedule_input import (
        OptimizeScheduleInput,
    )
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class MonteCarloOptimizationStrategy(OptimizationStrategy):
    """Monte Carlo simulation algorithm for task scheduling optimization.

    This strategy uses random sampling to find optimal schedules:
    1. Filter schedulable tasks
    2. Generate many random task orderings
    3. Simulate scheduling for each ordering
    4. Evaluate score (deadline compliance, priority, workload balance)
    5. Return the best schedule found

    Parameters:
    - Number of simulations: 100
    """

    DISPLAY_NAME = "Monte Carlo"
    DESCRIPTION = "Random sampling approach"

    NUM_SIMULATIONS = MONTE_CARLO_NUM_SIMULATIONS

    def __init__(self, default_start_time: time, default_end_time: time):
        """Initialize strategy with configuration.

        Args:
            default_start_time: Default start time for tasks (e.g., time(9, 0))
            default_end_time: Default end time for tasks (e.g., time(18, 0))
        """
        self.default_start_time = default_start_time
        self.default_end_time = default_end_time
        self.fitness_calculator = ScheduleFitnessCalculator()
        self._evaluation_cache: dict[
            tuple[int | None, ...], float
        ] = {}  # Cache for evaluation results
        self.holiday_checker: IHolidayChecker | None = None

    def optimize_tasks(
        self,
        schedulable_tasks: list[Task],
        all_tasks_for_context: list[Task],
        input_dto: "OptimizeScheduleInput",
        holiday_checker: "IHolidayChecker | None" = None,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using Monte Carlo simulation.

        Args:
            schedulable_tasks: List of tasks to schedule (already filtered by is_schedulable())
            all_tasks_for_context: All tasks in the system (for calculating existing allocations)
            input_dto: Optimization parameters (start_date, max_hours_per_day, etc.)
            holiday_checker: Optional HolidayChecker for holiday detection
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            Tuple of (modified_tasks, daily_allocations, failed_tasks)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date strings to allocated hours
            - failed_tasks: List of tasks that could not be scheduled with reasons
        """
        # No filtering needed - schedulable_tasks is already filtered by UseCase
        if not schedulable_tasks:
            return [], {}, []

        # Store holiday_checker for use in evaluation
        self.holiday_checker = holiday_checker

        # Create allocation context
        # NOTE: all_tasks_for_context should already be filtered by UseCase
        context = AllocationContext.create(
            tasks=all_tasks_for_context,
            start_date=input_dto.start_date,
            max_hours_per_day=input_dto.max_hours_per_day,
            holiday_checker=holiday_checker,
            current_time=input_dto.current_time,
            workload_calculator=workload_calculator,
        )

        # Create greedy strategy instance for allocation
        greedy_strategy = GreedyOptimizationStrategy(
            self.default_start_time,
            self.default_end_time,
        )

        # Clear evaluation cache for new optimization run
        self._evaluation_cache.clear()

        # Run Monte Carlo simulation
        best_order = self._monte_carlo_simulation(
            schedulable_tasks,
            all_tasks_for_context,
            input_dto.start_date,
            input_dto.max_hours_per_day,
            input_dto.force_override,
            greedy_strategy,
            workload_calculator,
        )

        # Schedule tasks according to best order using greedy allocation
        updated_tasks = []
        for task in best_order:
            updated_task = greedy_strategy._allocate_task(task, context)
            if updated_task:
                updated_tasks.append(updated_task)
            else:
                # Record allocation failure
                context.record_allocation_failure(task)

        # Return modified tasks, daily allocations, and failed tasks
        return updated_tasks, context.daily_allocations, context.failed_tasks

    def _monte_carlo_simulation(
        self,
        schedulable_tasks: list[Task],
        all_tasks: list[Task],
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        greedy_strategy: GreedyOptimizationStrategy,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> list[Task]:
        """Run Monte Carlo simulation to find optimal task ordering.

        Args:
            schedulable_tasks: List of tasks to schedule
            all_tasks: All tasks (for initializing allocations)
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            greedy_strategy: Greedy strategy instance
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            List of tasks in optimal order
        """
        best_order = None
        best_score = float("-inf")
        evaluated_orderings: set[tuple[int, ...]] = set()

        for _ in range(self.NUM_SIMULATIONS):
            # Generate random ordering
            random_order = random.sample(schedulable_tasks, len(schedulable_tasks))

            # Skip duplicate orderings
            ordering_key = tuple(
                task.id for task in random_order if task.id is not None
            )
            if ordering_key in evaluated_orderings:
                continue
            evaluated_orderings.add(ordering_key)

            # Evaluate this ordering (with caching)
            score = self._evaluate_ordering_cached(
                random_order,
                all_tasks,
                start_date,
                max_hours_per_day,
                force_override,
                greedy_strategy,
                workload_calculator,
            )

            # Track best ordering
            if score > best_score:
                best_score = score
                best_order = random_order

        return best_order if best_order else schedulable_tasks

    def _evaluate_ordering_cached(
        self,
        task_order: list[Task],
        all_tasks: list[Task],
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        greedy_strategy: GreedyOptimizationStrategy,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> float:
        """Evaluate ordering with caching to avoid redundant calculations.

        Args:
            task_order: Ordering of tasks to evaluate
            all_tasks: All tasks (for initializing allocations)
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            greedy_strategy: Greedy strategy instance
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            Score (higher is better)
        """
        # Create cache key from task IDs (tuple is hashable)
        cache_key = tuple(task.id for task in task_order)

        # Return cached result if available
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]

        # Calculate score
        score = self._evaluate_ordering(
            task_order,
            all_tasks,
            start_date,
            max_hours_per_day,
            force_override,
            greedy_strategy,
            workload_calculator,
        )

        # Cache the result
        self._evaluation_cache[cache_key] = score

        return score

    def _evaluate_ordering(
        self,
        task_order: list[Task],
        all_tasks: list[Task],
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        greedy_strategy: GreedyOptimizationStrategy,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> float:
        """Evaluate a task ordering by simulating scheduling.

        Higher score = better schedule.

        Args:
            task_order: Ordering of tasks to evaluate
            all_tasks: All tasks (for initializing allocations)
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            greedy_strategy: Greedy strategy instance
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            Score (higher is better)
        """
        # Simulate scheduling with this order
        # Create a temporary context for simulation
        # NOTE: all_tasks should already be filtered by caller
        temp_context = AllocationContext.create(
            tasks=all_tasks,
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            holiday_checker=self.holiday_checker,
            current_time=None,
            workload_calculator=workload_calculator,
        )
        scheduled_tasks = []

        for task in task_order:
            updated_task = greedy_strategy._allocate_task(task, temp_context)
            if updated_task:
                scheduled_tasks.append(updated_task)

        # Calculate score using the calculator (with scheduling bonus)
        score = self.fitness_calculator.calculate_fitness(
            scheduled_tasks,
            temp_context.daily_allocations,
            include_scheduling_bonus=True,
        )

        return score
