"""Schedule fitness calculator for optimization strategies."""

from datetime import date

from domain.entities.task import Task

# Constants for fitness calculation
DEADLINE_PENALTY_MULTIPLIER = 100
WORKLOAD_VARIANCE_MULTIPLIER = 10
SCHEDULED_TASK_BONUS = 50


class ScheduleFitnessCalculator:
    """Evaluates the quality of a task schedule.

    Used by optimization strategies (Genetic, Monte Carlo) to calculate
    fitness scores based on multiple criteria:
    - Priority score: Higher priority tasks scheduled earlier
    - Deadline penalty: Tasks finishing after their deadline
    - Workload variance penalty: Uneven distribution of work hours
    - Scheduling bonus: Number of tasks successfully scheduled
    """

    def calculate_fitness(
        self,
        scheduled_tasks: list[Task],
        daily_allocations: dict[date, float],
        include_scheduling_bonus: bool = False,
    ) -> float:
        """Calculate fitness score for a schedule.

        Higher fitness = better schedule.

        Args:
            scheduled_tasks: Tasks that were successfully scheduled
            daily_allocations: Daily work hour allocations
            include_scheduling_bonus: Whether to add bonus for number of scheduled tasks

        Returns:
            Fitness score (higher is better)
        """
        priority_score = self._calculate_priority_score(scheduled_tasks)
        deadline_penalty = self._calculate_deadline_penalty(scheduled_tasks)
        workload_penalty = self._calculate_workload_penalty(daily_allocations)

        fitness = priority_score - deadline_penalty - workload_penalty

        if include_scheduling_bonus:
            scheduling_bonus = len(scheduled_tasks) * SCHEDULED_TASK_BONUS
            fitness += scheduling_bonus

        return fitness

    def _calculate_priority_score(self, scheduled_tasks: list[Task]) -> float:
        """Calculate priority score.

        Higher priority tasks scheduled earlier receive higher scores.

        Args:
            scheduled_tasks: Tasks in scheduled order

        Returns:
            Priority score (higher is better)
        """
        priority_score = 0.0

        for i, task in enumerate(scheduled_tasks):
            if task.priority:
                # Earlier tasks (lower i) get higher weight
                priority_score += task.priority * (len(scheduled_tasks) - i)

        return priority_score

    def _calculate_deadline_penalty(self, scheduled_tasks: list[Task]) -> float:
        """Calculate deadline penalty.

        Tasks finishing after their deadline incur penalties.

        Args:
            scheduled_tasks: Tasks to evaluate

        Returns:
            Deadline penalty (higher is worse)
        """
        deadline_penalty = 0.0

        for task in scheduled_tasks:
            if task.deadline and task.planned_end and task.planned_end > task.deadline:
                days_late = (task.planned_end - task.deadline).days
                deadline_penalty += days_late * DEADLINE_PENALTY_MULTIPLIER

        return deadline_penalty

    def _calculate_workload_penalty(self, daily_allocations: dict[date, float]) -> float:
        """Calculate workload variance penalty.

        Uneven distribution of work hours across days incurs penalties.
        Lower variance = more balanced schedule = lower penalty.

        Args:
            daily_allocations: Daily work hour allocations

        Returns:
            Workload penalty (higher is worse)
        """
        if not daily_allocations:
            return 0.0

        daily_hours = list(daily_allocations.values())
        avg_hours = sum(daily_hours) / len(daily_hours)
        variance = sum((h - avg_hours) ** 2 for h in daily_hours) / len(daily_hours)

        return variance * WORKLOAD_VARIANCE_MULTIPLIER
