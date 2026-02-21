"""Pytest fixtures for taskdog-core tests.

This module provides shared fixtures for all tests in taskdog-core.
Repository fixtures are defined here; task fixtures are imported from
the shared fixtures module.
"""

import sys
from pathlib import Path

import pytest

# Add tests directory to path for fixtures module
_tests_path = Path(__file__).parent.resolve()
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
from fixtures.repositories import InMemoryTaskRepository  # noqa: E402

# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture
def repository():
    """Function-scoped in-memory repository for test isolation.

    Uses InMemoryTaskRepository (pure Python dict-based) instead of
    SqliteTaskRepository for faster test execution.
    """
    repo = InMemoryTaskRepository()
    yield repo
    repo.clear()
