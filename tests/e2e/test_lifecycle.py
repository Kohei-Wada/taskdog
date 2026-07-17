"""E2E: lifecycle state transitions persist through the real server."""

from taskdog_client.taskdog_api_client import TaskdogApiClient

from taskdog_core.domain.entities.task import TaskStatus


def test_start_pause_complete(client: TaskdogApiClient) -> None:
    task = client.create_task(name="lifecycle task")

    started = client.start_task(task.id)
    assert started.status == TaskStatus.IN_PROGRESS

    paused = client.pause_task(task.id)
    assert paused.status == TaskStatus.PENDING

    client.start_task(task.id)
    completed = client.complete_task(task.id)
    assert completed.status == TaskStatus.COMPLETED

    fetched = client.get_task_by_id(task.id)
    assert fetched.task.status == TaskStatus.COMPLETED
