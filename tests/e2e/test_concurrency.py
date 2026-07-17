"""E2E: concurrent writes stay consistent through the real server + SQLite.

Taskdog is used de-facto multi-writer (one person driving several AI agents at
once), so these lock in the contract that concurrent HTTP writes neither error
nor lose/corrupt data. It holds today because the engine runs SQLite in WAL mode
with a 30s busy_timeout (see engine_factory.py); these tests would fail if that
serialization guarantee regressed.

Each thread uses its own TaskdogApiClient because a client wraps a single
httpx.Client that must not be shared across threads.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from taskdog_client.taskdog_api_client import TaskdogApiClient

_WRITERS = 20


def test_concurrent_updates_to_same_task_stay_consistent(
    client: TaskdogApiClient, live_server: str
) -> None:
    task = client.create_task(name="contended", priority=1)
    priorities = list(range(2, 2 + _WRITERS))

    def update_priority(priority: int) -> None:
        api = TaskdogApiClient(base_url=live_server)
        try:
            api.update_task(task.id, priority=priority)
        finally:
            api.close()

    with ThreadPoolExecutor(max_workers=_WRITERS) as pool:
        list(pool.map(update_priority, priorities))

    fetched = client.get_task_by_id(task.id)
    # Last-writer-wins: the final value is exactly one of the submitted ones,
    # never a torn/garbage value, and unrelated fields are untouched.
    assert fetched.task.priority in priorities
    assert fetched.task.status == task.status


def test_concurrent_creates_all_persist(
    client: TaskdogApiClient, live_server: str
) -> None:
    def create(index: int) -> int:
        api = TaskdogApiClient(base_url=live_server)
        try:
            return api.create_task(name=f"concurrent-{index}").id
        finally:
            api.close()

    with ThreadPoolExecutor(max_workers=_WRITERS) as pool:
        ids = list(pool.map(create, range(_WRITERS)))

    # No lost writes and no id collisions under concurrent inserts.
    assert len(set(ids)) == _WRITERS
    assert client.list_tasks().total_count == _WRITERS
