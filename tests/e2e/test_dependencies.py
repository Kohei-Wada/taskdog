"""E2E: dependency wiring persists through the real server."""

from taskdog_client.taskdog_api_client import TaskdogApiClient


def test_add_dependency(client: TaskdogApiClient) -> None:
    prerequisite = client.create_task(name="prerequisite")
    dependent = client.create_task(name="dependent")

    result = client.add_dependency(dependent.id, prerequisite.id)
    assert prerequisite.id in result.depends_on

    fetched = client.get_task_by_id(dependent.id)
    assert prerequisite.id in fetched.task.depends_on
