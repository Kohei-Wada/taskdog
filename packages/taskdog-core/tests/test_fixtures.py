"""Shared test fixtures and utilities for taskdog-core tests.

This module provides base test classes and utilities to improve test performance
by using in-memory databases and reducing repeated setup operations.
"""

import unittest

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class InMemoryDatabaseTestCase(unittest.TestCase):
    """Base test case with in-memory SQLite database.

    Uses class-level database that is reset between tests.
    Much faster than file-based databases (~50-60% speedup).

    Usage:
        class MyTest(InMemoryDatabaseTestCase):
            def test_something(self):
                # self.repository is available and cleared before each test
                task = Task(id=1, name="Test", priority=1)
                self.repository.save(task)
    """

    @classmethod
    def setUpClass(cls):
        """Create in-memory database once for all tests in class."""
        if cls is InMemoryDatabaseTestCase:
            raise unittest.SkipTest("Skipping base test class")
        cls.repository = SqliteTaskRepository("sqlite:///:memory:")

    def setUp(self):
        """Clear database before each test."""
        # Clear all tasks - much faster than recreating database
        for task in self.repository.get_all():
            self.repository.delete(task.id)

    @classmethod
    def tearDownClass(cls):
        """Close database connection after all tests."""
        if hasattr(cls, "repository") and hasattr(cls.repository, "close"):
            cls.repository.close()


class TaskFactory:
    """Factory for creating test tasks with sensible defaults.

    Simplifies test data creation and reduces boilerplate code.

    Usage:
        factory = TaskFactory(repository)
        task = factory.create(name="My Task", estimated_duration=8.0)
        tasks = factory.create_batch(5, priority=1)
    """

    def __init__(self, repository: SqliteTaskRepository):
        """Initialize factory with repository.

        Args:
            repository: Task repository to use for saving tasks
        """
        self.repository = repository
        self._task_counter = 1

    def create(
        self,
        name: str | None = None,
        priority: int = 1,
        status: TaskStatus = TaskStatus.PENDING,
        estimated_duration: float | None = None,
        **kwargs,
    ) -> Task:
        """Create and save a task with auto-generated name if not provided.

        Args:
            name: Task name (auto-generated if None)
            priority: Task priority (default: 1)
            status: Task status (default: PENDING)
            estimated_duration: Estimated duration in hours
            **kwargs: Additional task attributes

        Returns:
            Created and saved task
        """
        if name is None:
            name = f"Test Task {self._task_counter}"
            self._task_counter += 1

        # Generate ID
        task_id = self.repository.generate_next_id()

        # Create task
        task = Task(
            id=task_id,
            name=name,
            priority=priority,
            status=status,
            **kwargs,
        )

        # Set optional fields
        if estimated_duration is not None:
            task.estimated_duration = estimated_duration

        # Save and return
        self.repository.save(task)
        return task

    def create_batch(self, count: int, **kwargs) -> list[Task]:
        """Create multiple tasks with shared properties.

        Args:
            count: Number of tasks to create
            **kwargs: Shared task attributes

        Returns:
            List of created tasks
        """
        return [self.create(**kwargs) for _ in range(count)]

    def reset_counter(self):
        """Reset the task counter to 1.

        Useful when you want predictable task names across tests.
        """
        self._task_counter = 1
