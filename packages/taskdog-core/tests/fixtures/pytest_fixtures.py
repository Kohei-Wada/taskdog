"""Shared pytest fixtures for taskdog tests.

These fixtures depend on a `repository` fixture that must be provided
by the package-specific conftest.py.

Usage in conftest.py:
    from fixtures.pytest_fixtures import (
        task_factory,
        sample_task,
        pending_task,
        in_progress_task,
        completed_task,
        canceled_task,
        archived_task,
        mock_config,
    )
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus

from .factories import TaskFactory


def create_mock_config(
    max_hours_per_day: float = 8.0,
    default_start_hour: int = 9,
    default_end_hour: int = 18,
    country: str | None = None,
) -> MagicMock:
    """Create a mock configuration with customizable defaults.

    This is a helper function rather than a fixture to allow customization.
    """
    config = MagicMock()
    config.optimization.max_hours_per_day = max_hours_per_day
    config.time.default_start_hour = default_start_hour
    config.time.default_end_hour = default_end_hour
    config.region.country = country
    return config


@pytest.fixture
def task_factory(repository) -> TaskFactory:
    """Task factory for creating test tasks.

    Requires a `repository` fixture to be defined in the consuming package.
    """
    return TaskFactory(repository)


@pytest.fixture
def sample_task(task_factory) -> Task:
    """Basic sample task."""
    return task_factory.create(name="Sample Task", priority=50)


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


@pytest.fixture
def archived_task(task_factory) -> Task:
    """Archived task."""
    return task_factory.create(name="Archived Task", is_archived=True)


@pytest.fixture
def mock_config():
    """Mock configuration with sensible defaults."""
    return create_mock_config()
