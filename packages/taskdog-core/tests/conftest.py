"""Pytest fixtures for taskdog-core tests.

This module provides shared fixtures for all tests in taskdog-core.
Repository fixtures are defined here; task fixtures are imported from
the shared fixtures module.
"""

import sys
from pathlib import Path

import pytest

# Add tests directory to path for fixtures module
_tests_path = Path(__file__).parent
if str(_tests_path) not in sys.path:
    sys.path.insert(0, str(_tests_path))

# Import shared fixtures from fixtures module
from fixtures.pytest_fixtures import (  # noqa: E402, F401
    archived_task,
    canceled_task,
    completed_task,
    create_mock_config,
    in_progress_task,
    mock_config,
    pending_task,
    sample_task,
    task_factory,
)

from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (  # noqa: E402
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.file_notes_repository import (  # noqa: E402
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
