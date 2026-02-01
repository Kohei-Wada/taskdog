"""Monte Carlo optimization strategy implementation."""

import random
from datetime import time

from taskdog_core.application.constants.optimization import MONTE_CARLO_NUM_SIMULATIONS
from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.application.services.optimization.greedy_based_optimization_strategy import (
    initialize_allocations,
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
        self._params: OptimizeParams | None = None

    def optimize_tasks(
        self,
        tasks: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
    ) -> OptimizeResult:
        """Optimize task schedules using Monte Carlo simulation.

        Args:
            tasks: List of tasks to schedule (already filtered by is_schedulable())
            context_tasks: All tasks in the system (for calculating existing allocations)
            params: Optimization parameters (start_date, max_hours_per_day, etc.)

        Returns:
            OptimizeResult containing modified tasks, daily allocations, and failures
        """
        if not tasks:
            return OptimizeResult()

        # Store params for use in evaluation
        self._params = params

        # Initialize daily allocations from context tasks
        initial_allocations = initialize_allocations(context_tasks)
        result = OptimizeResult(daily_allocations=dict(initial_allocations))

        # Create greedy strategy instance for allocation
        greedy_strategy = GreedyOptimizationStrategy(
            self.default_start_time,
            self.default_end_time,
        )

        # Clear evaluation cache for new optimization run
        self._evaluation_cache.clear()

        # Run Monte Carlo simulation
        best_order = self._monte_carlo_simulation(
            tasks,
            context_tasks,
            params,
            greedy_strategy,
        )

        # Schedule tasks according to best order using greedy allocation
        for task in best_order:
            updated_task = greedy_strategy._allocate_task(
                task, result.daily_allocations, params
            )
            if updated_task:
                result.tasks.append(updated_task)
            else:
                # Record allocation failure
                result.record_allocation_failure(task)

        return result

    def _monte_carlo_simulation(
        self,
        schedulable_tasks: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
        greedy_strategy: GreedyOptimizationStrategy,
    ) -> list[Task]:
        """Run Monte Carlo simulation to find optimal task ordering.

        Args:
            schedulable_tasks: List of tasks to schedule
            context_tasks: All tasks (for initializing allocations)
            params: Optimization parameters
            greedy_strategy: Greedy strategy instance

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
                context_tasks,
                params,
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
        context_tasks: list[Task],
        params: OptimizeParams,
        greedy_strategy: GreedyOptimizationStrategy,
    ) -> float:
        """Evaluate ordering with caching to avoid redundant calculations.

        Args:
            task_order: Ordering of tasks to evaluate
            context_tasks: All tasks (for initializing allocations)
            params: Optimization parameters
            greedy_strategy: Greedy strategy instance

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
            context_tasks,
            params,
            greedy_strategy,
        )

        # Cache the result
        self._evaluation_cache[cache_key] = score

        return score

    def _evaluate_ordering(
        self,
        task_order: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
        greedy_strategy: GreedyOptimizationStrategy,
    ) -> float:
        """Evaluate a task ordering by simulating scheduling.

        Higher score = better schedule.

        Args:
            task_order: Ordering of tasks to evaluate
            context_tasks: All tasks (for initializing allocations)
            params: Optimization parameters
            greedy_strategy: Greedy strategy instance

        Returns:
            Score (higher is better)
        """
        # Simulate scheduling with this order
        # Initialize daily allocations for simulation
        daily_allocations = initialize_allocations(context_tasks)
        scheduled_tasks = []

        for task in task_order:
            updated_task = greedy_strategy._allocate_task(
                task, daily_allocations, params
            )
            if updated_task:
                scheduled_tasks.append(updated_task)

        # Calculate score using the calculator (with scheduling bonus)
        score = self.fitness_calculator.calculate_fitness(
            scheduled_tasks,
            daily_allocations,
            include_scheduling_bonus=True,
        )

        return score
