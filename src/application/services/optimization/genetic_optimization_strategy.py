"""Genetic algorithm optimization strategy implementation."""

import copy
import random
from datetime import datetime

from application.services.hierarchy_manager import HierarchyManager
from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.task_filter import TaskFilter
from application.services.workload_allocator import WorkloadAllocator
from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task


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

    POPULATION_SIZE = 20
    GENERATIONS = 50
    CROSSOVER_RATE = 0.8
    MUTATION_RATE = 0.2

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using genetic algorithm.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules

        Returns:
            Tuple of (modified_tasks, daily_allocations)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date strings to allocated hours
        """
        # Initialize service instances
        task_filter = TaskFilter()
        hierarchy_manager = HierarchyManager(repository)

        # Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        if not schedulable_tasks:
            return [], {}

        # Run genetic algorithm
        best_order = self._genetic_algorithm(schedulable_tasks, start_date, max_hours_per_day)

        # Schedule tasks according to best order
        allocator = WorkloadAllocator(max_hours_per_day, start_date)
        allocator.initialize_allocations(tasks, force_override)

        updated_tasks = []
        for task in best_order:
            updated_task = allocator.allocate_timeblock(task)
            if updated_task:
                updated_tasks.append(updated_task)

        # Update parent task periods based on children
        all_tasks_with_updates = hierarchy_manager.update_parent_periods(tasks, updated_tasks)

        # If force_override, clear schedules for tasks that couldn't be scheduled
        if force_override:
            all_tasks_with_updates = hierarchy_manager.clear_unscheduled_tasks(
                tasks, all_tasks_with_updates
            )

        # Return modified tasks and daily allocations
        return all_tasks_with_updates, allocator.daily_allocations

    def _genetic_algorithm(
        self, tasks: list[Task], start_date: datetime, max_hours_per_day: float
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

        # Evolve population
        for _generation in range(self.GENERATIONS):
            # Evaluate fitness for each individual
            fitness_scores = [
                self._evaluate_fitness(individual, start_date, max_hours_per_day)
                for individual in population
            ]

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
        final_fitness = [
            self._evaluate_fitness(individual, start_date, max_hours_per_day)
            for individual in population
        ]
        best_idx = final_fitness.index(max(final_fitness))
        return population[best_idx]

    def _evaluate_fitness(
        self, task_order: list[Task], start_date: datetime, max_hours_per_day: float
    ) -> float:
        """Evaluate fitness of a task ordering.

        Higher fitness = better schedule.

        Args:
            task_order: Ordering of tasks to evaluate
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day

        Returns:
            Fitness score (higher is better)
        """
        # Simulate scheduling with this order
        allocator = WorkloadAllocator(max_hours_per_day, start_date)
        scheduled_tasks = []

        for task in task_order:
            updated_task = allocator.allocate_timeblock(task)
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
                deadline_dt = datetime.strptime(task.deadline, DATETIME_FORMAT)
                end_dt = datetime.strptime(task.planned_end, DATETIME_FORMAT)
                if end_dt > deadline_dt:
                    days_late = (end_dt - deadline_dt).days
                    deadline_penalty += days_late * 100  # Heavy penalty

        # Workload variance penalty (prefer even distribution)
        if allocator.daily_allocations:
            daily_hours = list(allocator.daily_allocations.values())
            avg_hours = sum(daily_hours) / len(daily_hours)
            variance = sum((h - avg_hours) ** 2 for h in daily_hours) / len(daily_hours)
            workload_penalty = variance * 10
        else:
            workload_penalty = 0

        # Fitness = benefits - penalties
        fitness = priority_score - deadline_penalty - workload_penalty
        return fitness

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
        mutated = copy.copy(individual)
        # Swap two random positions
        idx1, idx2 = random.sample(range(len(mutated)), 2)
        mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]
        return mutated
