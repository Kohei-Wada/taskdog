"""E2E: the executable endpoint ranks tasks through the real server + SQLite."""

from taskdog_client.taskdog_api_client import TaskdogApiClient


def test_executable_ranking_end_to_end(client: TaskdogApiClient) -> None:
    from datetime import datetime

    pending_soon = client.create_task(
        name="pending soon", deadline=datetime(2026, 7, 20, 18, 0)
    )
    pending_later = client.create_task(
        name="pending later", deadline=datetime(2026, 7, 30, 18, 0)
    )
    started = client.create_task(name="started")
    client.start_task(started.id)

    out = client.get_executable_tasks(limit=10)

    ids = [t.id for t in out.tasks]
    # in-progress first, then earliest deadline
    assert ids[0] == started.id
    assert ids.index(pending_soon.id) < ids.index(pending_later.id)
    assert out.ranking_basis[0] == "in_progress_first"
