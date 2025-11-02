"""Monte Carlo optimization strategy implementation."""

import random
from datetime import date, datetime
from typing import TYPE_CHECKING

from application.constants.optimization import MONTE_CARLO_NUM_SIMULATIONS
from application.dto.optimization_output import SchedulingFailure
from application.services.optimization.allocation_context import AllocationContext
from application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.optimization.schedule_fitness_calculator import (
    ScheduleFitnessCalculator,
)
from domain.entities.task import Task

if TYPE_CHECKING:
    from domain.repositories.task_repository import TaskRepository
    from domain.services.holiday_checker import IHolidayChecker


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

    def __init__(self, default_start_hour: int, default_end_hour: int):
        """Initialize strategy with configuration.

        Args:
            default_start_hour: Default start hour for tasks (e.g., 9)
            default_end_hour: Default end hour for tasks (e.g., 18)
        """
        self.default_start_hour = default_start_hour
        self.default_end_hour = default_end_hour
        self.fitness_calculator = ScheduleFitnessCalculator()
        self._evaluation_cache: dict[
            tuple[int | None, ...], float
        ] = {}  # Cache for evaluation results

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository: "TaskRepository",
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        holiday_checker: "IHolidayChecker | None" = None,
        current_time: datetime | None = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using Monte Carlo simulation.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            holiday_checker: Optional HolidayChecker for holiday detection
            current_time: Current time for calculating remaining hours on today

        Returns:
            Tuple of (modified_tasks, daily_allocations, failed_tasks)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date strings to allocated hours
            - failed_tasks: List of tasks that could not be scheduled with reasons
        """
        # Filter tasks that need scheduling
        schedulable_tasks = [task for task in tasks if task.is_schedulable(force_override)]

        if not schedulable_tasks:
            return [], {}, []

        # Create allocation context
        context = AllocationContext.create(
            tasks=tasks,
            repository=repository,
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            force_override=force_override,
            holiday_checker=holiday_checker,
            current_time=current_time,
        )

        # Create greedy strategy instance for allocation
        greedy_strategy = GreedyOptimizationStrategy(
            self.default_start_hour,
            self.default_end_hour,
        )

        # Clear evaluation cache for new optimization run
        self._evaluation_cache.clear()

        # Run Monte Carlo simulation
        best_order = self._monte_carlo_simulation(
            schedulable_tasks,
            tasks,
            start_date,
            max_hours_per_day,
            force_override,
            repository,
            greedy_strategy,
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
        repository: "TaskRepository",
        greedy_strategy: GreedyOptimizationStrategy,
    ) -> list[Task]:
        """Run Monte Carlo simulation to find optimal task ordering.

        Args:
            schedulable_tasks: List of tasks to schedule
            all_tasks: All tasks (for initializing allocations)
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules

        Returns:
            List of tasks in optimal order
        """
        best_order = None
        best_score = float("-inf")

        for _ in range(self.NUM_SIMULATIONS):
            # Generate random ordering
            random_order = random.sample(schedulable_tasks, len(schedulable_tasks))

            # Evaluate this ordering (with caching)
            score = self._evaluate_ordering_cached(
                random_order,
                all_tasks,
                start_date,
                max_hours_per_day,
                force_override,
                repository,
                greedy_strategy,
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
        repository: "TaskRepository",
        greedy_strategy: GreedyOptimizationStrategy,
    ) -> float:
        """Evaluate ordering with caching to avoid redundant calculations.

        Args:
            task_order: Ordering of tasks to evaluate
            all_tasks: All tasks (for initializing allocations)
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            repository: Task repository
            allocator: Allocator instance

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
            repository,
            greedy_strategy,
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
        repository: "TaskRepository",
        greedy_strategy: GreedyOptimizationStrategy,
    ) -> float:
        """Evaluate a task ordering by simulating scheduling.

        Higher score = better schedule.

        Args:
            task_order: Ordering of tasks to evaluate
            all_tasks: All tasks (for initializing allocations)
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules

        Returns:
            Score (higher is better)
        """
        # Simulate scheduling with this order
        # Create a temporary context for simulation
        temp_context = AllocationContext.create(
            tasks=all_tasks,
            repository=repository,
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            force_override=force_override,
            holiday_checker=greedy_strategy._get_holiday_checker()
            if hasattr(greedy_strategy, "_get_holiday_checker")
            else None,
            current_time=None,
        )
        scheduled_tasks = []

        for task in task_order:
            updated_task = greedy_strategy._allocate_task(task, temp_context)
            if updated_task:
                scheduled_tasks.append(updated_task)

        # Calculate score using the calculator (with scheduling bonus)
        score = self.fitness_calculator.calculate_fitness(
            scheduled_tasks, temp_context.daily_allocations, include_scheduling_bonus=True
        )

        return score

    def _sort_schedulable_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Not used by Monte Carlo strategy (overrides optimize_tasks)."""
        raise NotImplementedError(
            "MonteCarloOptimizationStrategy overrides optimize_tasks directly"
        )

    def _allocate_task(self, task: Task, context: AllocationContext) -> Task | None:
        """Not used by Monte Carlo strategy (overrides optimize_tasks)."""
        raise NotImplementedError(
            "MonteCarloOptimizationStrategy overrides optimize_tasks directly"
        )
