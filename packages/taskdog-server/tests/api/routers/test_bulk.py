"""Tests for bulk task operation endpoints."""

from datetime import datetime

from taskdog_core.domain.entities.task import TaskStatus


class TestBulkStartRouter:
    """Test cases for POST /api/v1/bulk/tasks/start."""

    def test_bulk_start_all_succeed(self, client, repository, task_factory):
        """Test starting multiple pending tasks."""
        task1 = task_factory.create(
            name="Task 1", priority=1, status=TaskStatus.PENDING
        )
        task2 = task_factory.create(
            name="Task 2", priority=2, status=TaskStatus.PENDING
        )

        response = client.post(
            "/api/v1/bulk/tasks/start",
            json={"task_ids": [task1.id, task2.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "start"
        assert data["total"] == 2
        assert data["succeeded"] == 2
        assert data["failed"] == 0
        assert len(data["results"]) == 2

        for result in data["results"]:
            assert result["success"] is True
            assert result["task"]["status"] == "IN_PROGRESS"
            assert result["task"]["actual_start"] is not None
            assert result["error"] is None

        # Verify in database
        for task_id in [task1.id, task2.id]:
            updated = repository.get_by_id(task_id)
            assert updated.status == TaskStatus.IN_PROGRESS

    def test_bulk_start_partial_failure(self, client, repository, task_factory):
        """Test bulk start with mix of valid and invalid tasks."""
        task = task_factory.create(
            name="Valid Task", priority=1, status=TaskStatus.PENDING
        )

        response = client.post(
            "/api/v1/bulk/tasks/start",
            json={"task_ids": [task.id, 999]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["succeeded"] == 1
        assert data["failed"] == 1

        # First result should succeed
        assert data["results"][0]["task_id"] == task.id
        assert data["results"][0]["success"] is True

        # Second result should fail
        assert data["results"][1]["task_id"] == 999
        assert data["results"][1]["success"] is False
        assert data["results"][1]["error"] is not None

    def test_bulk_start_all_fail(self, client):
        """Test bulk start when all tasks fail."""
        response = client.post(
            "/api/v1/bulk/tasks/start",
            json={"task_ids": [997, 998, 999]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["succeeded"] == 0
        assert data["failed"] == 3

        for result in data["results"]:
            assert result["success"] is False
            assert result["task"] is None

    def test_bulk_start_already_started(self, client, repository, task_factory):
        """Test bulk start with already in-progress tasks."""
        task = task_factory.create(name="In Progress", priority=1)
        task.status = TaskStatus.IN_PROGRESS
        task.actual_start = datetime.now()
        repository.save(task)

        response = client.post(
            "/api/v1/bulk/tasks/start",
            json={"task_ids": [task.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["succeeded"] == 0
        assert data["failed"] == 1
        assert data["results"][0]["success"] is False

    def test_bulk_start_single_task(self, client, repository, task_factory):
        """Test bulk start with a single task."""
        task = task_factory.create(
            name="Solo Task", priority=1, status=TaskStatus.PENDING
        )

        response = client.post(
            "/api/v1/bulk/tasks/start",
            json={"task_ids": [task.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["succeeded"] == 1
        assert data["results"][0]["task"]["status"] == "IN_PROGRESS"

    def test_bulk_start_empty_task_ids_returns_422(self, client):
        """Test bulk start with empty task_ids list returns validation error."""
        response = client.post(
            "/api/v1/bulk/tasks/start",
            json={"task_ids": []},
        )

        assert response.status_code == 422

    def test_bulk_start_missing_task_ids_returns_422(self, client):
        """Test bulk start without task_ids field returns validation error."""
        response = client.post(
            "/api/v1/bulk/tasks/start",
            json={},
        )

        assert response.status_code == 422

    def test_bulk_start_preserves_order(self, client, repository, task_factory):
        """Test that results maintain the same order as input task_ids."""
        task1 = task_factory.create(
            name="Task A", priority=1, status=TaskStatus.PENDING
        )
        task2 = task_factory.create(
            name="Task B", priority=2, status=TaskStatus.PENDING
        )
        task3 = task_factory.create(
            name="Task C", priority=3, status=TaskStatus.PENDING
        )

        response = client.post(
            "/api/v1/bulk/tasks/start",
            json={"task_ids": [task3.id, task1.id, task2.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["task_id"] == task3.id
        assert data["results"][1]["task_id"] == task1.id
        assert data["results"][2]["task_id"] == task2.id
