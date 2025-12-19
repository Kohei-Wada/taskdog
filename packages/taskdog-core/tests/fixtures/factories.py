"""Test factories for creating task entities.

This module provides factory classes for creating test data with sensible defaults.
"""

from datetime import datetime

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.repositories.task_repository import TaskRepository


class TaskFactory:
    """Factory for creating test tasks with sensible defaults.

    Simplifies test data creation and reduces boilerplate code.

    Usage:
        def test_something(task_factory):
            task = task_factory.create(name="My Task", estimated_duration=8.0)
            tasks = task_factory.create_batch(5, priority=1)
    """

    def __init__(self, repository: TaskRepository):
        """Initialize factory with repository.

        Args:
            repository: Task repository to use for saving tasks
        """
        self.repository = repository
        self._task_counter = 1

    def create(
        self,
        name: str | None = None,
        priority: int = 100,
        status: TaskStatus = TaskStatus.PENDING,
        estimated_duration: float | None = None,
        deadline: datetime | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        is_fixed: bool = False,
        depends_on: list[int] | None = None,
        tags: list[str] | None = None,
        is_archived: bool = False,
        **kwargs,
    ) -> Task:
        """Create and save a task with auto-generated name if not provided.

        Uses repository.create() with database AUTOINCREMENT for ID assignment.

        Args:
            name: Task name (auto-generated if None)
            priority: Task priority (default: 100)
            status: Task status (default: PENDING)
            estimated_duration: Estimated duration in hours
            deadline: Task deadline
            planned_start: Planned start datetime
            planned_end: Planned end datetime
            is_fixed: Whether task is fixed (not reschedulable)
            depends_on: List of dependency task IDs
            tags: List of tag names
            is_archived: Whether task is archived
            **kwargs: Additional task attributes

        Returns:
            Created and saved task
        """
        if name is None:
            name = f"Test Task {self._task_counter}"
            self._task_counter += 1

        create_kwargs = {
            **kwargs,
            "status": status,
            "is_fixed": is_fixed,
            "is_archived": is_archived,
        }
        if estimated_duration is not None:
            create_kwargs["estimated_duration"] = estimated_duration
        if deadline is not None:
            create_kwargs["deadline"] = deadline
        if planned_start is not None:
            create_kwargs["planned_start"] = planned_start
        if planned_end is not None:
            create_kwargs["planned_end"] = planned_end
        if depends_on is not None:
            create_kwargs["depends_on"] = depends_on
        if tags is not None:
            create_kwargs["tags"] = tags

        return self.repository.create(
            name=name,
            priority=priority,
            **create_kwargs,
        )

    def create_batch(self, count: int, **kwargs) -> list[Task]:
        """Create multiple tasks with the same attributes.

        Args:
            count: Number of tasks to create
            **kwargs: Attributes to pass to create()

        Returns:
            List of created tasks
        """
        return [self.create(**kwargs) for _ in range(count)]
