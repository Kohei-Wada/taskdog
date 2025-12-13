"""Pytest fixtures for taskdog-core tests.

This module provides shared fixtures for all tests in taskdog-core.
Fixtures replace the unittest-style InMemoryDatabaseTestCase base class.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)

# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def session_repository():
    """Session-scoped in-memory repository shared across all tests.

    Using a single database connection for the entire test session
    provides ~50-60% speedup compared to creating new databases.
    """
    repo = SqliteTaskRepository("sqlite:///:memory:")
    yield repo
    if hasattr(repo, "close"):
        repo.close()


@pytest.fixture
def repository(session_repository):
    """Function-scoped fixture that clears data before each test.

    Inherits the session-scoped database but clears all tasks
    before each test to ensure test isolation.
    """
    for task in session_repository.get_all():
        session_repository.delete(task.id)
    yield session_repository


@pytest.fixture
def notes_repository(tmp_path):
    """Notes repository using temporary directory."""
    return FileNotesRepository(base_path=str(tmp_path))


# =============================================================================
# Config Fixtures
# =============================================================================


@pytest.fixture
def mock_config():
    """Mock configuration with sensible defaults."""
    config = MagicMock()
    config.task.default_priority = 3
    config.optimization.max_hours_per_day = 8.0
    config.time.default_start_hour = 9
    config.time.default_end_hour = 18
    return config


# =============================================================================
# Task Factory
# =============================================================================


class TaskFactory:
    """Factory for creating test tasks with sensible defaults.

    Simplifies test data creation and reduces boilerplate code.

    Usage:
        def test_something(task_factory):
            task = task_factory.create(name="My Task", estimated_duration=8.0)
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
        priority: int = 100,
        status: TaskStatus = TaskStatus.PENDING,
        estimated_duration: float | None = None,
        deadline: datetime | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        is_fixed: bool = False,
        depends_on: list[int] | None = None,
        tags: list[str] | None = None,
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


@pytest.fixture
def task_factory(repository) -> TaskFactory:
    """Task factory for creating test tasks."""
    return TaskFactory(repository)


# =============================================================================
# Sample Task Fixtures
# =============================================================================


@pytest.fixture
def sample_task(task_factory) -> Task:
    """Basic sample task."""
    return task_factory.create(name="Sample Task", priority=50)


# =============================================================================
# Status-specific Task Fixtures
# =============================================================================


@pytest.fixture
def pending_task(task_factory) -> Task:
    """Task in PENDING status."""
    return task_factory.create(name="Pending Task")


@pytest.fixture
def in_progress_task(repository, task_factory) -> Task:
    """Task in IN_PROGRESS status with actual_start set."""
    task = task_factory.create(name="In Progress Task")
    task.status = TaskStatus.IN_PROGRESS
    task.actual_start = datetime.now()
    repository.save(task)
    return repository.get_by_id(task.id)


@pytest.fixture
def completed_task(repository, task_factory) -> Task:
    """Task in COMPLETED status with actual_start and actual_end set."""
    task = task_factory.create(name="Completed Task")
    task.status = TaskStatus.COMPLETED
    task.actual_start = datetime.now()
    task.actual_end = datetime.now()
    repository.save(task)
    return repository.get_by_id(task.id)


@pytest.fixture
def canceled_task(repository, task_factory) -> Task:
    """Task in CANCELED status."""
    task = task_factory.create(name="Canceled Task")
    task.status = TaskStatus.CANCELED
    task.actual_start = datetime.now()
    task.actual_end = datetime.now()
    repository.save(task)
    return repository.get_by_id(task.id)
