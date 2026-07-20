"""E2E: concurrent writes stay consistent through the real server + SQLite.

Taskdog is used de-facto multi-writer (one person driving several AI agents at
once), so these lock in the contract that concurrent HTTP writes never corrupt
data. Since #961, an update whose read-time version is stale is cleanly rejected
with a 409 conflict rather than silently overwriting a newer write, so a
contended update either commits or raises ``ConcurrencyConflictError`` - never a
500 or a torn/garbage value. Concurrent creates still all persist.

Each thread uses its own TaskdogApiClient because a client wraps a single
httpx.Client that must not be shared across threads.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from taskdog_client.taskdog_api_client import TaskdogApiClient

from taskdog_core.domain.exceptions.task_exceptions import ConcurrencyConflictError

_WRITERS = 20


def test_concurrent_updates_to_same_task_stay_consistent(
    client: TaskdogApiClient, live_server: str
) -> None:
    task = client.create_task(name="contended", priority=1)
    priorities = list(range(2, 2 + _WRITERS))

    def update_priority(priority: int) -> str:
        api = TaskdogApiClient(base_url=live_server)
        try:
            api.update_task(task.id, priority=priority)
            return "ok"
        except ConcurrencyConflictError:
            # Optimistic locking (#961): a writer that read a stale version is
            # rejected with 409 instead of silently clobbering a newer write.
            return "conflict"
        finally:
            api.close()

    with ThreadPoolExecutor(max_workers=_WRITERS) as pool:
        outcomes = list(pool.map(update_priority, priorities))

    # Every writer either committed or was cleanly rejected with a conflict -
    # never a 500 or a torn/garbage value - and at least one write landed.
    assert set(outcomes) <= {"ok", "conflict"}
    assert "ok" in outcomes
    fetched = client.get_task_by_id(task.id)
    # Final value is exactly one of the submitted ones, and unrelated fields are
    # untouched.
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

    # No lost writes and no id collisions under concurrent inserts. Checked as a
    # subset of the listing so the assertion verifies "every one of my creates
    # persisted" without assuming the DB is globally empty.
    assert len(set(ids)) == _WRITERS
    persisted = {task.id for task in client.list_tasks().tasks}
    assert set(ids) <= persisted
