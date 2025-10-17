"""Abstract base class for optimization strategies using Template Method Pattern."""

from abc import ABC, abstractmethod
from datetime import datetime

from application.dto.optimization_result import SchedulingFailure
from application.services.task_filter import TaskFilter
from domain.entities.task import Task, TaskStatus
from domain.services.task_eligibility_checker import TaskEligibilityChecker


class OptimizationStrategy(ABC):
    """Abstract base class for task scheduling optimization strategies.

    This class implements the Template Method pattern to eliminate code duplication
    across optimization strategies.

    The template method `optimize_tasks()` defines the common workflow:
    1. Initialize context (repository, constraints, daily_allocations)
    2. Initialize existing allocations from scheduled tasks
    3. Filter schedulable tasks
    4. Sort tasks by priority (strategy-specific)
    5. Allocate tasks (strategy-specific)
    6. Return results

    Subclasses implement sorting and allocation logic specific to their algorithm.
    Each strategy has full control over its allocation algorithm.
    """

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float], list[SchedulingFailure]]:
        """Optimize task schedules using template method pattern.

        This method defines the common workflow for all optimization strategies.
        Subclasses customize behavior by implementing abstract methods.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules

        Returns:
            Tuple of (modified_tasks, daily_allocations, failed_tasks)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date strings to allocated hours
            - failed_tasks: List of tasks that could not be scheduled with reasons
        """
        # 1. Initialize context (instance variables for use by subclasses)
        self.repository = repository
        self.start_date = start_date
        self.max_hours_per_day = max_hours_per_day
        self.daily_allocations: dict[str, float] = {}
        self.failed_tasks: list[SchedulingFailure] = []

        # 2. Initialize daily_allocations with existing scheduled tasks
        self._initialize_allocations(tasks, force_override)

        # 3. Filter tasks that need scheduling
        task_filter = TaskFilter()
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        # 4. Sort tasks by strategy-specific priority
        sorted_tasks = self._sort_schedulable_tasks(schedulable_tasks, start_date, repository)

        # 5. Allocate time blocks for each task (strategy-specific)
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = self._allocate_task(task, start_date, max_hours_per_day)
            if updated_task:
                updated_tasks.append(updated_task)
            else:
                # Record allocation failure with default reason
                self._record_allocation_failure(task, updated_task)

        # 6. Return modified tasks, daily allocations, and failed tasks
        return updated_tasks, self.daily_allocations, self.failed_tasks

    def _initialize_allocations(self, tasks: list[Task], force_override: bool) -> None:
        """Initialize daily_allocations with existing scheduled tasks.

        This method pre-populates daily_allocations with hours from tasks
        that already have schedules. This ensures that when we optimize new tasks,
        we account for existing workload commitments.

        Args:
            tasks: All tasks in the system
            force_override: Whether existing schedules will be overridden
        """
        for task in tasks:
            # Skip finished tasks (completed/archived) - they don't contribute to future workload
            if not TaskEligibilityChecker.should_count_in_workload(task):
                continue

            # Skip tasks without schedules
            if not (task.planned_start and task.estimated_duration):
                continue

            # If force_override, we'll reschedule PENDING tasks, so don't count their old allocation
            # But IN_PROGRESS tasks should NOT be rescheduled, so count their allocation
            if force_override and task.status != TaskStatus.IN_PROGRESS:
                continue

            # Use daily_allocations if available
            if task.daily_allocations:
                for date_str, hours in task.daily_allocations.items():
                    if date_str in self.daily_allocations:
                        self.daily_allocations[date_str] += hours
                    else:
                        self.daily_allocations[date_str] = hours

    def _record_failure(self, task: Task, reason: str) -> None:
        """Record a task scheduling failure with a reason.

        Subclasses can call this method to record specific failure reasons
        for tasks that could not be scheduled.

        Args:
            task: The task that failed to be scheduled
            reason: Human-readable reason for the failure
        """
        self.failed_tasks.append(SchedulingFailure(task=task, reason=reason))

    def _record_allocation_failure(
        self,
        task: Task,
        updated_task: Task | None,
        default_reason: str = "Could not find available time slot before deadline",
    ) -> None:
        """Record allocation failure if task wasn't successfully scheduled.

        This is a convenience method that checks if allocation succeeded and
        records a failure if it didn't, avoiding duplicate failure records.

        Args:
            task: Original task
            updated_task: Result from allocation (None if failed)
            default_reason: Default failure reason if none recorded
        """
        # Only record if allocation failed and not already recorded
        if not updated_task and not any(f.task.id == task.id for f in self.failed_tasks):
            self._record_failure(task, default_reason)

    @abstractmethod
    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by strategy-specific priority.

        Subclasses must implement this to define their sorting logic.

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Sorted task list
        """
        pass

    @abstractmethod
    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block for a single task.

        Subclasses must implement this to define their allocation logic.
        The strategy has access to:
        - self.daily_allocations: Current daily allocation state
        - self.repository: Task repository for hierarchy queries
        - self.start_date: Starting date for allocation
        - self.max_hours_per_day: Maximum hours per day constraint

        Args:
            task: Task to schedule
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        pass
