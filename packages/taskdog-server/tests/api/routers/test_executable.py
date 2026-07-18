"""Tests for GET /api/v1/tasks/executable."""

from taskdog_core.domain.entities.task import Task, TaskStatus


def test_executable_endpoint_ranks_in_progress_first(client, repository):
    repository.save(Task(id=1, name="p", priority=1, status=TaskStatus.PENDING))
    repository.save(Task(id=2, name="ip", priority=1, status=TaskStatus.IN_PROGRESS))

    resp = client.get("/api/v1/tasks/executable")

    assert resp.status_code == 200
    body = resp.json()
    assert [t["id"] for t in body["tasks"]] == [2, 1]
    assert body["ranking_basis"][0] == "in_progress_first"
