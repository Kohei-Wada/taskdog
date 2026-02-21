"""Pytest fixtures for taskdog-server tests.

This module provides shared fixtures for all tests in taskdog-server.
Task fixtures are imported from taskdog-core's shared fixtures module.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add taskdog-core tests to path for shared fixtures
_core_tests_path = (
    Path(__file__).parent.parent.parent / "taskdog-core" / "tests"
).resolve()
if str(_core_tests_path) not in sys.path:
    sys.path.insert(0, str(_core_tests_path))

# Import shared test utilities from core's fixtures module
from fixtures import InMemoryNotesRepository  # noqa: E402
from fixtures.pytest_fixtures import (  # noqa: E402, F401
    archived_task,
    canceled_task,
    completed_task,
    create_mock_config,
    in_progress_task,
    pending_task,
    sample_task,
    task_factory,
)
from fixtures.repositories import InMemoryTaskRepository  # noqa: E402

# Import from taskdog-core
from taskdog_core.controllers.audit_log_controller import (  # noqa: E402
    AuditLogController,
)
from taskdog_core.controllers.query_controller import QueryController  # noqa: E402
from taskdog_core.controllers.task_analytics_controller import (  # noqa: E402
    TaskAnalyticsController,
)
from taskdog_core.controllers.task_crud_controller import (  # noqa: E402
    TaskCrudController,
)
from taskdog_core.controllers.task_lifecycle_controller import (  # noqa: E402
    TaskLifecycleController,
)
from taskdog_core.controllers.task_relationship_controller import (  # noqa: E402
    TaskRelationshipController,
)
from taskdog_core.domain.services.logger import Logger  # noqa: E402
from taskdog_core.infrastructure.persistence.database.sqlite_audit_log_repository import (  # noqa: E402
    SqliteAuditLogRepository,
)
from taskdog_core.infrastructure.time_provider import SystemTimeProvider  # noqa: E402

# Import server-specific modules
from taskdog_server.api.context import ApiContext  # noqa: E402
from taskdog_server.config.server_config_manager import (  # noqa: E402
    ApiKeyEntry,
    AuthConfig,
    ServerConfig,
)
from taskdog_server.websocket.connection_manager import ConnectionManager  # noqa: E402

# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def session_repository():
    """Session-scoped in-memory repository shared across all tests.

    Uses InMemoryTaskRepository (pure Python dict-based) for faster test execution.
    """
    return InMemoryTaskRepository()


@pytest.fixture(scope="session")
def session_audit_log_repository():
    """Session-scoped in-memory audit log repository."""
    repo = SqliteAuditLogRepository("sqlite:///file::memory:?cache=shared&uri=true")
    yield repo
    if hasattr(repo, "close"):
        repo.close()


@pytest.fixture
def audit_log_repository(session_audit_log_repository):
    """Function-scoped fixture that clears audit logs before each test."""
    session_audit_log_repository.clear()
    yield session_audit_log_repository


@pytest.fixture
def repository(session_repository):
    """Function-scoped fixture that clears data before each test."""
    session_repository.clear()
    yield session_repository


@pytest.fixture(scope="session")
def session_notes_repository():
    """Session-scoped in-memory notes repository."""
    return InMemoryNotesRepository()


@pytest.fixture
def notes_repository(session_notes_repository):
    """Function-scoped fixture that clears notes before each test."""
    session_notes_repository.clear()
    yield session_notes_repository


# =============================================================================
# Config Fixtures
# =============================================================================

TEST_API_KEY = "test-api-key-12345"
TEST_CLIENT_NAME = "test-client"


@pytest.fixture(scope="session")
def mock_config():
    """Mock configuration with sensible defaults (session-scoped)."""
    return create_mock_config()


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


class AuthenticatedTestClient:
    """Wrapper around TestClient that automatically adds auth headers."""

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
def app(
    session_repository,
    session_notes_repository,
    session_audit_log_repository,
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
    audit_log_controller = AuditLogController(
        session_audit_log_repository, mock_logger, SystemTimeProvider()
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
        audit_log_controller=audit_log_controller,
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
        audit_router,
        lifecycle_router,
        notes_router,
        relationships_router,
        tags_router,
        tasks_router,
        websocket_router,
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
    test_app.include_router(tags_router, prefix="/api/v1/tags", tags=["tags"])
    test_app.include_router(audit_router, prefix="/api/v1/audit-logs", tags=["audit"])
    test_app.include_router(websocket_router, tags=["websocket"])

    return test_app


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
