"""Genetic algorithm optimization strategy implementation."""

import copy
import random
from datetime import date, datetime
from typing import TYPE_CHECKING

from application.constants.optimization import (
    DEADLINE_PENALTY_MULTIPLIER,
    GENETIC_CROSSOVER_RATE,
    GENETIC_GENERATIONS,
    GENETIC_MUTATION_RATE,
    GENETIC_POPULATION_SIZE,
)
from application.dto.optimization_output import SchedulingFailure
from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task
from shared.config_manager import Config

if TYPE_CHECKING:
    from domain.repositories.task_repository import TaskRepository
    from domain.services.holiday_checker import IHolidayChecker


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
    EARLY_TERMINATION_GENERATIONS = 10  # Terminate if no improvement for N generations

    def __init__(self, config: Config):
        """Initialize strategy with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        # Cache for fitness evaluations: stores (fitness, daily_allocations, scheduled_tasks)
        self._fitness_cache: dict[
            tuple[int | None, ...], tuple[float, dict[date, float], list[Task]]
        ] = {}

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
        """Optimize task schedules using genetic algorithm.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            holiday_checker: Optional HolidayChecker for holiday detection

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

        # Initialize context for allocation
        self.repository = repository
        self.start_date = start_date
        self.max_hours_per_day = max_hours_per_day
        self.holiday_checker = holiday_checker
        self.current_time = current_time
        self.daily_allocations: dict[date, float] = {}
        self.failed_tasks: list[SchedulingFailure] = []
        self._initialize_allocations(tasks, force_override)

        # Create allocator instance
        allocator = GreedyForwardAllocator(self.config, self.holiday_checker, self.current_time)

        # Clear fitness cache for new optimization run
        self._fitness_cache.clear()

        # Run genetic algorithm to find best task order
        best_order = self._genetic_algorithm(
            schedulable_tasks, start_date, max_hours_per_day, repository, allocator
        )

        # Reuse cached allocation results for the best order (performance optimization)
        cache_key = tuple(task.id for task in best_order)
        if cache_key in self._fitness_cache:
            # Use cached results to avoid redundant allocation
            _fitness, cached_daily_allocations, cached_scheduled_tasks = self._fitness_cache[
                cache_key
            ]
            # Update self.daily_allocations with cached results
            self.daily_allocations.update(cached_daily_allocations)
            updated_tasks = cached_scheduled_tasks

            # Record failed tasks (tasks that were not successfully scheduled)
            scheduled_task_ids = {task.id for task in cached_scheduled_tasks}
            for task in best_order:
                if task.id not in scheduled_task_ids:
                    # Task was not successfully scheduled - record failure
                    self._record_allocation_failure(task, None)
        else:
            # Fallback: allocate tasks if cache miss (shouldn't happen normally)
            updated_tasks = []
            for task in best_order:
                updated_task = allocator.allocate(
                    task, start_date, max_hours_per_day, self.daily_allocations, repository
                )
                if updated_task:
                    updated_tasks.append(updated_task)
                else:
                    # Record allocation failure
                    self._record_allocation_failure(task, updated_task)

        # Return modified tasks, daily allocations, and failed tasks
        return updated_tasks, self.daily_allocations, self.failed_tasks

    def _genetic_algorithm(
        self,
        tasks: list[Task],
        start_date: datetime,
        max_hours_per_day: float,
        repository: "TaskRepository",
        allocator: GreedyForwardAllocator,
    ) -> list[Task]:
        """Run genetic algorithm to find optimal task ordering.

        Args:
            tasks: List of tasks to schedule
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day

        Returns:
            List of tasks in optimal order
        """
        # Generate initial population
        population = [random.sample(tasks, len(tasks)) for _ in range(self.POPULATION_SIZE)]

        # Track best fitness for early termination
        best_fitness_ever = float("-inf")
        generations_without_improvement = 0

        # Evolve population
        for _generation in range(self.GENERATIONS):
            # Evaluate fitness for each individual (only need fitness scores for evolution)
            fitness_scores = [
                self._evaluate_fitness_cached(
                    individual, start_date, max_hours_per_day, repository, allocator
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
                individual, start_date, max_hours_per_day, repository, allocator
            )
            for individual in population
        ]
        # Find best individual by fitness score
        best_idx = max(range(len(final_results)), key=lambda i: final_results[i][0])
        return population[best_idx]

    def _evaluate_fitness_cached(
        self,
        task_order: list[Task],
        start_date: datetime,
        max_hours_per_day: float,
        repository: "TaskRepository",
        allocator: GreedyForwardAllocator,
    ) -> tuple[float, dict[date, float], list[Task]]:
        """Evaluate fitness with caching to avoid redundant calculations.

        Args:
            task_order: Ordering of tasks to evaluate
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            repository: Task repository
            allocator: Allocator instance

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
            task_order, start_date, max_hours_per_day, repository, allocator
        )

        # Cache the complete result (fitness + allocations + tasks)
        self._fitness_cache[cache_key] = (fitness, daily_allocations, scheduled_tasks)

        return fitness, daily_allocations, scheduled_tasks

    def _evaluate_fitness(
        self,
        task_order: list[Task],
        start_date: datetime,
        max_hours_per_day: float,
        repository: "TaskRepository",
        allocator: GreedyForwardAllocator,
    ) -> tuple[float, dict[date, float], list[Task]]:
        """Evaluate fitness of a task ordering.

        Higher fitness = better schedule.

        Args:
            task_order: Ordering of tasks to evaluate
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            repository: Task repository
            allocator: Allocator instance

        Returns:
            Tuple of (fitness_score, daily_allocations, scheduled_tasks)
        """
        # Simulate scheduling with this order
        temp_daily_allocations: dict[date, float] = {}
        scheduled_tasks = []

        for task in task_order:
            updated_task = allocator.allocate(
                task, start_date, max_hours_per_day, temp_daily_allocations, repository
            )
            if updated_task:
                scheduled_tasks.append(updated_task)

        # Calculate fitness components
        deadline_penalty = 0.0
        priority_score = 0.0

        for i, task in enumerate(scheduled_tasks):
            # Priority bonus (higher priority tasks scheduled earlier get bonus)
            if task.priority:
                priority_score += task.priority * (len(scheduled_tasks) - i)

            # Deadline penalty (tasks finishing after deadline get penalty)
            if task.deadline and task.planned_end:
                deadline_dt = task.deadline
                end_dt = task.planned_end
                if end_dt > deadline_dt:
                    days_late = (end_dt - deadline_dt).days
                    deadline_penalty += days_late * DEADLINE_PENALTY_MULTIPLIER

        # Workload variance penalty (prefer even distribution)
        if temp_daily_allocations:
            daily_hours = list(temp_daily_allocations.values())
            avg_hours = sum(daily_hours) / len(daily_hours)
            variance = sum((h - avg_hours) ** 2 for h in daily_hours) / len(daily_hours)
            workload_penalty = variance * 10
        else:
            workload_penalty = 0

        # Fitness = benefits - penalties
        fitness = priority_score - deadline_penalty - workload_penalty
        return fitness, temp_daily_allocations, scheduled_tasks

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
        tournament_size = 3

        for _ in range(len(population)):
            # Select random individuals for tournament
            tournament_indices = random.sample(range(len(population)), tournament_size)
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

    def _sort_schedulable_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Not used by genetic strategy (overrides optimize_tasks)."""
        raise NotImplementedError("GeneticOptimizationStrategy overrides optimize_tasks directly")

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Not used by genetic strategy (overrides optimize_tasks)."""
        raise NotImplementedError("GeneticOptimizationStrategy overrides optimize_tasks directly")
