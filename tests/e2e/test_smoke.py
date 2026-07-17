"""Smoke test: the production server boots and is reachable via the client."""

from taskdog_client.taskdog_api_client import TaskdogApiClient


def test_server_is_healthy(client: TaskdogApiClient) -> None:
    assert client.check_health() is True


def test_task_persists_across_requests(client: TaskdogApiClient) -> None:
    created = client.create_task(name="smoke task")
    fetched = client.get_task_by_id(created.id)
    assert fetched.task.name == "smoke task"
