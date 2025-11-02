"""Abstract base class for optimization strategies using Template Method Pattern."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import TYPE_CHECKING

from application.dto.optimization_output import SchedulingFailure
from application.dto.task_dto import TaskSummaryDto
from application.sorters.optimization_task_sorter import OptimizationTaskSorter
from domain.entities.task import Task, TaskStatus

if TYPE_CHECKING:
    from domain.repositories.task_repository import TaskRepository
    from domain.services.holiday_checker import IHolidayChecker


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
        repository: "TaskRepository",
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        holiday_checker: "IHolidayChecker | None" = None,
        current_time: datetime | None = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using template method pattern.

        This method defines the common workflow for all optimization strategies.
        Subclasses customize behavior by implementing abstract methods.

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
            - daily_allocations: Dict mapping date objects to allocated hours
            - failed_tasks: List of tasks that could not be scheduled with reasons
        """
        # 1. Initialize context (instance variables for use by subclasses)
        self.repository = repository
        self.start_date = start_date
        self.max_hours_per_day = max_hours_per_day
        self.holiday_checker = holiday_checker
        self.current_time = current_time
        self.daily_allocations: dict[date, float] = {}
        self.failed_tasks: list[SchedulingFailure] = []

        # 2. Initialize daily_allocations with existing scheduled tasks
        self._initialize_allocations(tasks, force_override)

        # 3. Filter tasks that need scheduling
        schedulable_tasks = [task for task in tasks if task.is_schedulable(force_override)]

        # 4. Sort tasks by strategy-specific priority
        sorted_tasks = self._sort_schedulable_tasks(schedulable_tasks, start_date)

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

        Fixed tasks are ALWAYS included in daily_allocations, regardless of force_override,
        because they represent immovable time constraints (meetings, deadlines, etc.) that
        must be respected when scheduling other tasks.

        Args:
            tasks: All tasks in the system
            force_override: Whether existing schedules will be overridden
        """
        for task in tasks:
            # Skip finished tasks (completed/archived) - they don't contribute to future workload
            if not task.should_count_in_workload():
                continue

            # Skip tasks without schedules
            if not (task.planned_start and task.estimated_duration):
                continue

            # ALWAYS include fixed tasks in daily_allocations (they cannot be rescheduled)
            # Also include IN_PROGRESS tasks (they should not be rescheduled)
            # If force_override, skip PENDING non-fixed tasks (they will be rescheduled)
            if force_override and not task.is_fixed and task.status != TaskStatus.IN_PROGRESS:
                continue

            # Get daily allocations for this task
            # Use task.daily_allocations if available, otherwise calculate from WorkloadCalculator
            if task.daily_allocations:
                task_daily_hours = task.daily_allocations
            else:
                # Calculate daily hours using WorkloadCalculator
                from application.queries.workload_calculator import WorkloadCalculator

                calculator = WorkloadCalculator()
                task_daily_hours = calculator.get_task_daily_hours(task)

            # Add to global daily_allocations
            for date_obj, hours in task_daily_hours.items():
                if date_obj in self.daily_allocations:
                    self.daily_allocations[date_obj] += hours
                else:
                    self.daily_allocations[date_obj] = hours

    def _record_failure(self, task: Task, reason: str) -> None:
        """Record a task scheduling failure with a reason.

        Subclasses can call this method to record specific failure reasons
        for tasks that could not be scheduled.

        Args:
            task: The task that failed to be scheduled
            reason: Human-readable reason for the failure
        """
        # Convert Task to TaskSummaryDto
        if task.id is None:
            raise ValueError("Task must have an ID")
        task_dto = TaskSummaryDto(id=task.id, name=task.name)
        self.failed_tasks.append(SchedulingFailure(task=task_dto, reason=reason))

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

    def _sort_schedulable_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by strategy-specific priority.

        Default implementation sorts by deadline urgency, priority field, and task ID.
        Strategies can override this method for custom sorting logic.

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization

        Returns:
            Sorted task list (highest priority first)
        """
        sorter = OptimizationTaskSorter(start_date)
        return sorter.sort_by_priority(tasks)

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
