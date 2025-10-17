"""Monte Carlo optimization strategy implementation."""

import random
from datetime import datetime

from application.dto.optimization_result import SchedulingFailure
from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.task_filter import TaskFilter
from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task


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

    NUM_SIMULATIONS = 100

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float], list[SchedulingFailure]]:
        """Optimize task schedules using Monte Carlo simulation.

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

        # Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        if not schedulable_tasks:
            return [], {}, []

        # Initialize context for allocation
        self.repository = repository
        self.start_date = start_date
        self.max_hours_per_day = max_hours_per_day
        self.daily_allocations: dict[str, float] = {}
        self.failed_tasks: list[SchedulingFailure] = []
        self._initialize_allocations(tasks, force_override)

        # Run Monte Carlo simulation
        best_order = self._monte_carlo_simulation(
            schedulable_tasks, tasks, start_date, max_hours_per_day, force_override, repository
        )

        # Schedule tasks according to best order using greedy allocation
        updated_tasks = []
        for task in best_order:
            updated_task = self._allocate_greedy(
                task, self.daily_allocations, start_date, max_hours_per_day, repository
            )
            if updated_task:
                updated_tasks.append(updated_task)
            else:
                # Record failure with reason
                self._record_failure(task, "Could not find available time slot before deadline")

        # Return modified tasks, daily allocations, and failed tasks
        return updated_tasks, self.daily_allocations, self.failed_tasks

    def _monte_carlo_simulation(
        self,
        schedulable_tasks: list[Task],
        all_tasks: list[Task],
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        repository=None,
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

            # Evaluate this ordering
            score = self._evaluate_ordering(
                random_order, all_tasks, start_date, max_hours_per_day, force_override, repository
            )

            # Track best ordering
            if score > best_score:
                best_score = score
                best_order = random_order

        return best_order if best_order else schedulable_tasks

    def _evaluate_ordering(
        self,
        task_order: list[Task],
        all_tasks: list[Task],
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        repository=None,
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
        temp_daily_allocations: dict[str, float] = {}
        scheduled_tasks = []

        for task in task_order:
            updated_task = self._allocate_greedy(
                task, temp_daily_allocations, start_date, max_hours_per_day, repository
            )
            if updated_task:
                scheduled_tasks.append(updated_task)

        # Calculate score components
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
        if temp_daily_allocations:
            daily_hours = list(temp_daily_allocations.values())
            avg_hours = sum(daily_hours) / len(daily_hours)
            variance = sum((h - avg_hours) ** 2 for h in daily_hours) / len(daily_hours)
            workload_penalty = variance * 10
        else:
            workload_penalty = 0

        # Number of successfully scheduled tasks bonus
        scheduled_bonus = len(scheduled_tasks) * 50

        # Score = benefits - penalties
        score = priority_score + scheduled_bonus - deadline_penalty - workload_penalty
        return score

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Not used by Monte Carlo strategy (overrides optimize_tasks)."""
        raise NotImplementedError(
            "MonteCarloOptimizationStrategy overrides optimize_tasks directly"
        )

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Not used by Monte Carlo strategy (overrides optimize_tasks)."""
        raise NotImplementedError(
            "MonteCarloOptimizationStrategy overrides optimize_tasks directly"
        )
