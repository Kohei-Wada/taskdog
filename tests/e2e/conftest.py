"""Fixtures for API end-to-end tests.

Spawns the production taskdog-server against a temporary SQLite database and
drives it with the shipped TaskdogApiClient over real HTTP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from taskdog_client.taskdog_api_client import TaskdogApiClient

from tests.e2e.harness import spawn_server, terminate_server

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope="session")
def live_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Session-scoped production server on an ephemeral port, temp SQLite DB."""
    root = tmp_path_factory.mktemp("e2e-server")
    db_path = root / "tasks.db"
    cfg_dir = root / "config"
    cfg_dir.mkdir()
    process, base_url = spawn_server(db_path, cfg_dir, auth=False)
    try:
        yield base_url
    finally:
        terminate_server(process)


@pytest.fixture
def client(live_server: str) -> Iterator[TaskdogApiClient]:
    """Real API client bound to the live server."""
    api = TaskdogApiClient(base_url=live_server)
    try:
        yield api
    finally:
        api.close()


@pytest.fixture(autouse=True)
def clean_db(client: TaskdogApiClient) -> None:
    """Remove all tasks (including archived) so each test starts clean."""
    listing = client.list_tasks(include_archived=True)
    for task in listing.tasks:
        client.remove_task(task.id)
