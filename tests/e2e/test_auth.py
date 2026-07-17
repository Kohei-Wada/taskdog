"""E2E: an auth-enabled server rejects unauthenticated requests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from taskdog_client.taskdog_api_client import TaskdogApiClient

from taskdog_core.domain.exceptions.task_exceptions import AuthenticationError
from tests.e2e.harness import spawn_server, terminate_server

if TYPE_CHECKING:
    from collections.abc import Iterator

_API_KEY = "e2e-test-key"


@pytest.fixture
def auth_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    root = tmp_path_factory.mktemp("e2e-auth")
    cfg_dir = root / "config" / "taskdog"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "server.toml").write_text(
        "[auth]\n"
        "enabled = true\n\n"
        "[[auth.api_keys]]\n"
        'name = "e2e"\n'
        f'key = "{_API_KEY}"\n'
    )
    process, base_url = spawn_server(root / "tasks.db", root / "config", auth=True)
    try:
        yield base_url
    finally:
        terminate_server(process)


def test_missing_key_is_rejected(auth_server: str) -> None:
    api = TaskdogApiClient(base_url=auth_server)
    try:
        with pytest.raises(AuthenticationError):
            api.create_task(name="no key")
    finally:
        api.close()


def test_valid_key_is_accepted(auth_server: str) -> None:
    api = TaskdogApiClient(base_url=auth_server, api_key=_API_KEY)
    try:
        created = api.create_task(name="with key")
        assert created.id > 0
    finally:
        api.close()
