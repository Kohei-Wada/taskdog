"""Pytest fixtures for taskdog-server tests.

This module provides shared fixtures for all tests in taskdog-server.
Fixtures replace the unittest-style BaseApiRouterTest base class.
"""

from unittest.mock import MagicMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from taskdog_core.controllers.query_controller import QueryController
from taskdog_core.controllers.task_analytics_controller import TaskAnalyticsController
from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.services.logger import Logger
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.time_provider import SystemTimeProvider
from taskdog_server.api.context import ApiContext
from taskdog_server.config.server_config_manager import (
    ApiKeyEntry,
    AuthConfig,
    ServerConfig,
)
from taskdog_server.websocket.connection_manager import ConnectionManager

# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def session_repository():
    """Session-scoped in-memory repository shared across all tests.

    Using a single database connection for the entire test session
    provides ~50-60% speedup compared to creating new databases.
    The "file::memory:?cache=shared" syntax ensures all connections see the same data.
    """
    repo = SqliteTaskRepository("sqlite:///file::memory:?cache=shared&uri=true")
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
def notes_repository(session_notes_repository):
    """Function-scoped fixture that clears notes before each test.

    Inherits the session-scoped InMemoryNotesRepository but clears all notes
    before each test to ensure test isolation.
    """
    session_notes_repository.clear()
    yield session_notes_repository


# =============================================================================
# Config Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def mock_config():
    """Mock configuration with sensible defaults (session-scoped)."""
    config = MagicMock()
    config.task.default_priority = 3
    config.optimization.max_hours_per_day = 8.0
    config.optimization.default_algorithm = "greedy"
    config.region.country = None
    config.time.default_start_hour = 9
    config.time.default_end_hour = 18
    return config


# Test API key for authentication
TEST_API_KEY = "test-api-key-12345"
TEST_CLIENT_NAME = "test-client"


@pytest.fixture(scope="session")
def server_config():
    """Server configuration with test API key (session-scoped)."""
    return ServerConfig(
        auth=AuthConfig(
            enabled=True,
            api_keys=(ApiKeyEntry(name=TEST_CLIENT_NAME, key=TEST_API_KEY),),
        )
    )


@pytest.fixture(scope="session")
def auth_headers():
    """HTTP headers with test API key."""
    return {"X-Api-Key": TEST_API_KEY}


@pytest.fixture(scope="session")
def mock_logger():
    """Mock logger for controllers."""
    return Mock(spec=Logger)


# =============================================================================
# FastAPI App and Client Fixtures
# =============================================================================


class InMemoryNotesRepository:
    """In-memory notes repository for testing.

    Provides a simple dict-based storage for notes that can be cleared between tests.
    """

    def __init__(self):
        self._notes: dict[int, str] = {}

    def has_notes(self, task_id: int) -> bool:
        """Check if task has notes."""
        return task_id in self._notes and len(self._notes[task_id]) > 0

    def read_notes(self, task_id: int) -> str | None:
        """Read notes for task."""
        return self._notes.get(task_id)

    def write_notes(self, task_id: int, content: str) -> None:
        """Write notes for task."""
        self._notes[task_id] = content

    def delete_notes(self, task_id: int) -> None:
        """Delete notes for task."""
        if task_id in self._notes:
            del self._notes[task_id]

    def clear(self) -> None:
        """Clear all notes."""
        self._notes.clear()


@pytest.fixture(scope="session")
def session_notes_repository():
    """Session-scoped in-memory notes repository."""
    return InMemoryNotesRepository()


@pytest.fixture(scope="session")
def app(
    session_repository,
    session_notes_repository,
    mock_config,
    mock_logger,
    server_config,
):
    """FastAPI application with all routers (session-scoped)."""
    # Create controllers once (reused across all tests)
    query_controller = QueryController(
        session_repository, session_notes_repository, mock_logger
    )
    lifecycle_controller = TaskLifecycleController(
        session_repository, mock_config, mock_logger
    )
    relationship_controller = TaskRelationshipController(
        session_repository, mock_config, mock_logger
    )
    analytics_controller = TaskAnalyticsController(
        session_repository, mock_config, None, mock_logger
    )
    crud_controller = TaskCrudController(
        session_repository, session_notes_repository, mock_config, mock_logger
    )

    # Create API context once
    api_context = ApiContext(
        repository=session_repository,
        config=mock_config,
        notes_repository=session_notes_repository,
        query_controller=query_controller,
        lifecycle_controller=lifecycle_controller,
        relationship_controller=relationship_controller,
        analytics_controller=analytics_controller,
        crud_controller=crud_controller,
        holiday_checker=None,
        time_provider=SystemTimeProvider(),
    )

    # Create FastAPI app once with all routers
    test_app = FastAPI(
        title="Taskdog API Test",
        description="Test instance",
        version="1.0.0",
    )

    # Set context on app.state BEFORE creating TestClient
    test_app.state.api_context = api_context
    test_app.state.server_config = server_config
    test_app.state.connection_manager = ConnectionManager()

    # Import and register all routers
    from taskdog_server.api.routers import (
        analytics_router,
        lifecycle_router,
        notes_router,
        relationships_router,
        tasks_router,
    )

    test_app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
    test_app.include_router(
        lifecycle_router, prefix="/api/v1/tasks", tags=["lifecycle"]
    )
    test_app.include_router(
        relationships_router, prefix="/api/v1/tasks", tags=["relationships"]
    )
    test_app.include_router(notes_router, prefix="/api/v1/tasks", tags=["notes"])
    test_app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

    return test_app


class AuthenticatedTestClient:
    """Wrapper around TestClient that automatically adds auth headers.

    This allows existing tests to work without modification while ensuring
    all requests include the required API key header.
    """

    def __init__(self, client: TestClient, auth_headers: dict[str, str]):
        self._client = client
        self._auth_headers = auth_headers

    def _merge_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        """Merge auth headers with provided headers."""
        merged = dict(self._auth_headers)
        if headers:
            merged.update(headers)
        return merged

    def get(self, url: str, **kwargs):
        """GET request with auth headers."""
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
        return self._client.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        """POST request with auth headers."""
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
        return self._client.post(url, **kwargs)

    def put(self, url: str, **kwargs):
        """PUT request with auth headers."""
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
        return self._client.put(url, **kwargs)

    def patch(self, url: str, **kwargs):
        """PATCH request with auth headers."""
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
        return self._client.patch(url, **kwargs)

    def delete(self, url: str, **kwargs):
        """DELETE request with auth headers."""
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
        return self._client.delete(url, **kwargs)


@pytest.fixture(scope="session")
def session_client(app):
    """TestClient (session-scoped for performance)."""
    return TestClient(app)


@pytest.fixture
def client(session_client, repository, auth_headers):
    """Function-scoped client that ensures repository is cleared.

    This fixture depends on 'repository' to ensure data is cleared
    before each test, while reusing the session-scoped TestClient.

    Returns an AuthenticatedTestClient that automatically adds auth headers.
    """
    return AuthenticatedTestClient(session_client, auth_headers)


# =============================================================================
# Task Factory
# =============================================================================


class TaskFactory:
    """Factory for creating test tasks with sensible defaults.

    Simplifies test data creation and reduces boilerplate code.

    Usage:
        def test_something(task_factory):
            task = task_factory.create(name="My Task", estimated_duration=8.0)
            tasks = task_factory.create_batch(5, priority=1)
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
        **kwargs,
    ) -> Task:
        """Create and save a task with auto-generated name if not provided.

        Uses repository.create() with database AUTOINCREMENT for ID assignment.

        Args:
            name: Task name (auto-generated if None)
            priority: Task priority (default: 100)
            status: Task status (default: PENDING)
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
        }

        return self.repository.create(
            name=name,
            priority=priority,
            **create_kwargs,
        )

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
        """Reset the task counter to 1."""
        self._task_counter = 1


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


@pytest.fixture
def pending_task(task_factory) -> Task:
    """Task in PENDING status."""
    return task_factory.create(name="Pending Task")


@pytest.fixture
def in_progress_task(repository, task_factory) -> Task:
    """Task in IN_PROGRESS status with actual_start set."""
    from datetime import datetime

    task = task_factory.create(name="In Progress Task")
    task.status = TaskStatus.IN_PROGRESS
    task.actual_start = datetime.now()
    repository.save(task)
    return repository.get_by_id(task.id)


@pytest.fixture
def completed_task(repository, task_factory) -> Task:
    """Task in COMPLETED status with actual_start and actual_end set."""
    from datetime import datetime

    task = task_factory.create(name="Completed Task")
    task.status = TaskStatus.COMPLETED
    task.actual_start = datetime.now()
    task.actual_end = datetime.now()
    repository.save(task)
    return repository.get_by_id(task.id)


@pytest.fixture
def archived_task(task_factory) -> Task:
    """Archived task."""
    return task_factory.create(name="Archived Task", is_archived=True)
