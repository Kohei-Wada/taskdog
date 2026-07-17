"""E2E: full create -> read -> update -> delete cycle over real HTTP + SQLite."""

from taskdog_client.taskdog_api_client import TaskdogApiClient


def test_crud_round_trip(client: TaskdogApiClient) -> None:
    created = client.create_task(name="original", priority=3)
    assert created.id > 0
    assert created.name == "original"

    updated = client.update_task(created.id, name="renamed", priority=5)
    assert updated.task.name == "renamed"
    assert updated.task.priority == 5

    fetched = client.get_task_by_id(created.id)
    assert fetched.task.name == "renamed"

    client.remove_task(created.id)
    remaining = client.list_tasks(include_archived=True)
    assert all(task.id != created.id for task in remaining.tasks)
