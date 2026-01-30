"""Genetic algorithm optimization strategy implementation."""

import copy
import random
from datetime import date, time
from typing import TYPE_CHECKING

from taskdog_core.application.constants.optimization import (
    GENETIC_CROSSOVER_RATE,
    GENETIC_EARLY_TERMINATION_GENERATIONS,
    GENETIC_GENERATIONS,
    GENETIC_MUTATION_RATE,
    GENETIC_POPULATION_SIZE,
    GENETIC_TOURNAMENT_SIZE,
)
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

if TYPE_CHECKING:
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator


class GeneticOptimizationStrategy(OptimizationStrategy):
    """Genetic algorithm for task scheduling optimization.

    This strategy uses evolutionary computation to find optimal schedules:
    1. Filter schedulable tasks
    2. Generate initial population of random task orderings
    3. Evaluate fitness (deadline compliance, priority, workload balance)
    4. Select, crossover, and mutate to create new generations
    5. Return the best schedule found

    Parameters:
    - Population size: 20
    - Generations: 50
    - Crossover rate: 0.8
    - Mutation rate: 0.2
    """

    DISPLAY_NAME = "Genetic"
    DESCRIPTION = "Evolutionary algorithm"

    POPULATION_SIZE = GENETIC_POPULATION_SIZE
    GENERATIONS = GENETIC_GENERATIONS
    CROSSOVER_RATE = GENETIC_CROSSOVER_RATE
    MUTATION_RATE = GENETIC_MUTATION_RATE
    EARLY_TERMINATION_GENERATIONS = GENETIC_EARLY_TERMINATION_GENERATIONS
    TOURNAMENT_SIZE = GENETIC_TOURNAMENT_SIZE

    def __init__(self, default_start_time: time, default_end_time: time):
        """Initialize strategy with configuration.

        Args:
            default_start_time: Default start time for tasks (e.g., time(9, 0))
            default_end_time: Default end time for tasks (e.g., time(18, 0))
        """
        self.default_start_time = default_start_time
        self.default_end_time = default_end_time
        self.fitness_calculator = ScheduleFitnessCalculator()
        # Cache for fitness evaluations: stores (fitness, daily_allocations, scheduled_tasks)
        self._fitness_cache: dict[
            tuple[int | None, ...], tuple[float, dict[date, float], list[Task]]
        ] = {}
        self._params: OptimizeParams | None = None

    def optimize_tasks(
        self,
        tasks: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> OptimizeResult:
        """Optimize task schedules using genetic algorithm.

        Args:
            tasks: List of tasks to schedule (already filtered by is_schedulable())
            context_tasks: All tasks in the system (for calculating existing allocations)
            params: Optimization parameters (start_date, max_hours_per_day, etc.)
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            OptimizeResult containing modified tasks, daily allocations, and failures
        """
        if not tasks:
            return OptimizeResult()

        # Store params for use in evaluation
        self._params = params

        # Initialize daily allocations from context tasks
        initial_allocations = initialize_allocations(context_tasks, workload_calculator)
        result = OptimizeResult(daily_allocations=dict(initial_allocations))

        # Create greedy strategy instance for allocation
        greedy_strategy = GreedyOptimizationStrategy(
            self.default_start_time,
            self.default_end_time,
        )

        # Clear fitness cache for new optimization run
        self._fitness_cache.clear()

        # Run genetic algorithm to find best task order
        best_order = self._genetic_algorithm(
            tasks,
            params,
            greedy_strategy,
            workload_calculator,
        )

        # Reuse cached allocation results for the best order (performance optimization)
        cache_key = tuple(task.id for task in best_order)
        if cache_key in self._fitness_cache:
            # Use cached results to avoid redundant allocation
            _fitness, cached_daily_allocations, cached_scheduled_tasks = (
                self._fitness_cache[cache_key]
            )
            # Update result.daily_allocations with cached results
            result.daily_allocations.update(cached_daily_allocations)
            result.tasks = cached_scheduled_tasks

            # Record failed tasks (tasks that were not successfully scheduled)
            scheduled_task_ids = {task.id for task in cached_scheduled_tasks}
            for task in best_order:
                if task.id not in scheduled_task_ids:
                    # Task was not successfully scheduled - record failure
                    result.record_allocation_failure(task)
        else:
            # Fallback: allocate tasks if cache miss (shouldn't happen normally)
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

    def _genetic_algorithm(
        self,
        tasks: list[Task],
        params: OptimizeParams,
        greedy_strategy: GreedyOptimizationStrategy,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> list[Task]:
        """Run genetic algorithm to find optimal task ordering.

        Args:
            tasks: List of tasks to schedule
            params: Optimization parameters
            greedy_strategy: Greedy strategy instance
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            List of tasks in optimal order
        """
        # Generate initial population
        population = [
            random.sample(tasks, len(tasks)) for _ in range(self.POPULATION_SIZE)
        ]

        # Track best fitness for early termination
        best_fitness_ever = float("-inf")
        generations_without_improvement = 0

        # Evolve population
        for _generation in range(self.GENERATIONS):
            # Evaluate fitness for each individual (only need fitness scores for evolution)
            fitness_scores = [
                self._evaluate_fitness_cached(
                    individual,
                    params,
                    greedy_strategy,
                    workload_calculator,
                )[0]  # Extract fitness score only
                for individual in population
            ]

            # Check for improvement (early termination)
            current_best = max(fitness_scores)
            if current_best > best_fitness_ever:
                best_fitness_ever = current_best
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1

            # Early termination if no improvement
            if generations_without_improvement >= self.EARLY_TERMINATION_GENERATIONS:
                break

            # Select parents (tournament selection)
            parents = self._select_parents(population, fitness_scores)

            # Create next generation
            next_generation = []

            # Elitism: keep best individual
            best_idx = fitness_scores.index(max(fitness_scores))
            next_generation.append(population[best_idx])

            # Generate offspring
            while len(next_generation) < self.POPULATION_SIZE:
                parent1 = random.choice(parents)
                parent2 = random.choice(parents)

                # Crossover
                if random.random() < self.CROSSOVER_RATE:
                    child = self._crossover(parent1, parent2)
                else:
                    child = copy.copy(parent1)

                # Mutation
                if random.random() < self.MUTATION_RATE:
                    child = self._mutate(child)

                next_generation.append(child)

            population = next_generation

        # Return best individual from final generation
        final_results = [
            self._evaluate_fitness_cached(
                individual,
                params,
                greedy_strategy,
                workload_calculator,
            )
            for individual in population
        ]
        # Find best individual by fitness score
        best_idx = max(range(len(final_results)), key=lambda i: final_results[i][0])
        return population[best_idx]

    def _evaluate_fitness_cached(
        self,
        task_order: list[Task],
        params: OptimizeParams,
        greedy_strategy: GreedyOptimizationStrategy,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> tuple[float, dict[date, float], list[Task]]:
        """Evaluate fitness with caching to avoid redundant calculations.

        Args:
            task_order: Ordering of tasks to evaluate
            params: Optimization parameters
            greedy_strategy: Greedy strategy instance
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            Tuple of (fitness_score, daily_allocations, scheduled_tasks)
        """
        # Create cache key from task IDs (tuple is hashable)
        cache_key = tuple(task.id for task in task_order)

        # Return cached result if available
        if cache_key in self._fitness_cache:
            return self._fitness_cache[cache_key]

        # Calculate fitness and allocation results
        fitness, daily_allocations, scheduled_tasks = self._evaluate_fitness(
            task_order,
            params,
            greedy_strategy,
            workload_calculator,
        )

        # Cache the complete result (fitness + allocations + tasks)
        self._fitness_cache[cache_key] = (fitness, daily_allocations, scheduled_tasks)

        return fitness, daily_allocations, scheduled_tasks

    def _evaluate_fitness(
        self,
        task_order: list[Task],
        params: OptimizeParams,
        greedy_strategy: GreedyOptimizationStrategy,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> tuple[float, dict[date, float], list[Task]]:
        """Evaluate fitness of a task ordering.

        Higher fitness = better schedule.

        Args:
            task_order: Ordering of tasks to evaluate
            params: Optimization parameters
            greedy_strategy: Greedy strategy instance
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            Tuple of (fitness_score, daily_allocations, scheduled_tasks)
        """
        # Simulate scheduling with this order
        # Start with empty allocations for fair comparison across orderings
        daily_allocations: dict[date, float] = {}
        scheduled_tasks = []

        for task in task_order:
            updated_task = greedy_strategy._allocate_task(
                task, daily_allocations, params
            )
            if updated_task:
                scheduled_tasks.append(updated_task)

        # Calculate fitness using the calculator
        fitness = self.fitness_calculator.calculate_fitness(
            scheduled_tasks,
            daily_allocations,
            include_scheduling_bonus=False,
        )

        return fitness, daily_allocations, scheduled_tasks

    def _select_parents(
        self, population: list[list[Task]], fitness_scores: list[float]
    ) -> list[list[Task]]:
        """Select parents using tournament selection.

        Args:
            population: Current population
            fitness_scores: Fitness score for each individual

        Returns:
            List of selected parents
        """
        parents = []

        for _ in range(len(population)):
            # Select random individuals for tournament
            tournament_indices = random.sample(
                range(len(population)), self.TOURNAMENT_SIZE
            )
            # Choose best from tournament
            best_idx = max(tournament_indices, key=lambda i: fitness_scores[i])
            parents.append(population[best_idx])

        return parents

    def _crossover(self, parent1: list[Task], parent2: list[Task]) -> list[Task]:
        """Perform order crossover (OX) between two parents.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Child task ordering
        """
        size = len(parent1)

        # Handle edge case: single task or empty
        if size < 2:
            return list(parent1)

        # Select two random crossover points
        start, end = sorted(random.sample(range(size), 2))

        # Copy segment from parent1
        child: list[Task | None] = [None] * size
        child[start:end] = parent1[start:end]

        # Fill remaining positions from parent2
        parent2_filtered = [t for t in parent2 if t not in child[start:end]]
        child_idx = 0

        for task in parent2_filtered:
            while child[child_idx] is not None:
                child_idx += 1
            child[child_idx] = task

        # Return child (all elements should be Task at this point)
        return [t for t in child if t is not None]

    def _mutate(self, individual: list[Task]) -> list[Task]:
        """Perform swap mutation on an individual.

        Args:
            individual: Task ordering to mutate

        Returns:
            Mutated task ordering
        """
        # Handle edge case: single task or empty
        if len(individual) < 2:
            return list(individual)

        mutated = copy.copy(individual)
        # Swap two random positions
        idx1, idx2 = random.sample(range(len(mutated)), 2)
        mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]
        return mutated
