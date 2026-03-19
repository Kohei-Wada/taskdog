"""Tests for bulk operation endpoints."""

from datetime import datetime

import pytest

from taskdog_core.domain.entities.task import TaskStatus


class TestBulkLifecycleOperations:
    """Test cases for bulk lifecycle endpoints."""

    @pytest.mark.parametrize(
        "operation,initial_status,expected_status",
        [
            ("start", TaskStatus.PENDING, "IN_PROGRESS"),
            ("cancel", TaskStatus.PENDING, "CANCELED"),
        ],
        ids=["start", "cancel"],
    )
    def test_single_task_success(
        self, client, task_factory, operation, initial_status, expected_status
    ):
        """Test bulk operation on a single task."""
        task = task_factory.create(name="Task 1", priority=1, status=initial_status)

        response = client.post(
            f"/api/v1/tasks/bulk/{operation}",
            json={"task_ids": [task.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["success"] is True
        assert data["results"][0]["task_id"] == task.id
        assert data["results"][0]["task"]["status"] == expected_status

    def test_bulk_start_multiple_tasks(self, client, task_factory):
        """Test bulk start on multiple tasks."""
        t1 = task_factory.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        t2 = task_factory.create(name="Task 2", priority=2, status=TaskStatus.PENDING)

        response = client.post(
            "/api/v1/tasks/bulk/start",
            json={"task_ids": [t1.id, t2.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert all(r["success"] for r in data["results"])
        assert all(r["task"]["status"] == "IN_PROGRESS" for r in data["results"])

    def test_bulk_complete_in_progress_tasks(self, client, repository, task_factory):
        """Test bulk complete on in-progress tasks."""
        t1 = task_factory.create(name="Task 1", priority=1)
        t1.status = TaskStatus.IN_PROGRESS
        t1.actual_start = datetime.now()
        repository.save(t1)

        t2 = task_factory.create(name="Task 2", priority=2)
        t2.status = TaskStatus.IN_PROGRESS
        t2.actual_start = datetime.now()
        repository.save(t2)

        response = client.post(
            "/api/v1/tasks/bulk/complete",
            json={"task_ids": [t1.id, t2.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(r["success"] for r in data["results"])
        assert all(r["task"]["status"] == "COMPLETED" for r in data["results"])

    def test_bulk_pause_in_progress_tasks(self, client, repository, task_factory):
        """Test bulk pause on in-progress tasks."""
        t1 = task_factory.create(name="Task 1", priority=1)
        t1.status = TaskStatus.IN_PROGRESS
        t1.actual_start = datetime.now()
        repository.save(t1)

        response = client.post(
            "/api/v1/tasks/bulk/pause",
            json={"task_ids": [t1.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["success"] is True
        assert data["results"][0]["task"]["status"] == "PENDING"

    @pytest.mark.parametrize(
        "initial_status",
        [TaskStatus.COMPLETED, TaskStatus.CANCELED],
        ids=["from_completed", "from_canceled"],
    )
    def test_bulk_reopen_finished_tasks(
        self, client, repository, task_factory, initial_status
    ):
        """Test bulk reopen on completed/canceled tasks."""
        task = task_factory.create(name="Task 1", priority=1)
        task.status = initial_status
        task.actual_end = datetime.now()
        if initial_status == TaskStatus.COMPLETED:
            task.actual_start = datetime.now()
        repository.save(task)

        response = client.post(
            "/api/v1/tasks/bulk/reopen",
            json={"task_ids": [task.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["success"] is True
        assert data["results"][0]["task"]["status"] == "PENDING"

    def test_mixed_success_and_failure(self, client, task_factory):
        """Test bulk operation with mix of valid and invalid task IDs."""
        task = task_factory.create(
            name="Valid Task", priority=1, status=TaskStatus.PENDING
        )

        response = client.post(
            "/api/v1/tasks/bulk/start",
            json={"task_ids": [task.id, 99999]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

        # First task should succeed
        assert data["results"][0]["success"] is True
        assert data["results"][0]["task"]["status"] == "IN_PROGRESS"

        # Second task should fail
        assert data["results"][1]["success"] is False
        assert data["results"][1]["error"] is not None
        assert data["results"][1]["task"] is None

    def test_empty_task_ids_returns_validation_error(self, client):
        """Test that empty task_ids list returns 422."""
        response = client.post(
            "/api/v1/tasks/bulk/start",
            json={"task_ids": []},
        )
        assert response.status_code == 422

    def test_audit_logs_created_for_each_task(self, client, task_factory):
        """Test that audit logs are created for each successful task."""
        t1 = task_factory.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        t2 = task_factory.create(name="Task 2", priority=2, status=TaskStatus.PENDING)

        client.post(
            "/api/v1/tasks/bulk/start",
            json={"task_ids": [t1.id, t2.id]},
        )

        # Verify via audit log API
        logs_response = client.get(
            "/api/v1/audit-logs", params={"operation": "start_task"}
        )
        assert logs_response.status_code == 200
        logs_data = logs_response.json()
        task_ids_in_logs = {log["resource_id"] for log in logs_data["logs"]}
        assert t1.id in task_ids_in_logs
        assert t2.id in task_ids_in_logs


class TestBulkCrudOperations:
    """Test cases for bulk CRUD endpoints (archive, restore, delete)."""

    def test_bulk_archive(self, client, repository, task_factory):
        """Test bulk archive of tasks."""
        t1 = task_factory.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        t2 = task_factory.create(name="Task 2", priority=2, status=TaskStatus.PENDING)

        response = client.post(
            "/api/v1/tasks/bulk/archive",
            json={"task_ids": [t1.id, t2.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(r["success"] for r in data["results"])
        assert all(r["task"]["is_archived"] for r in data["results"])

        # Verify in database
        assert repository.get_by_id(t1.id).is_archived
        assert repository.get_by_id(t2.id).is_archived

    def test_bulk_restore(self, client, repository, task_factory):
        """Test bulk restore of archived tasks."""
        t1 = task_factory.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        t1.is_archived = True
        repository.save(t1)

        response = client.post(
            "/api/v1/tasks/bulk/restore",
            json={"task_ids": [t1.id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["success"] is True
        assert data["results"][0]["task"]["is_archived"] is False

        # Verify in database
        assert not repository.get_by_id(t1.id).is_archived

    def test_bulk_delete(self, client, repository, task_factory):
        """Test bulk hard delete of tasks."""
        t1 = task_factory.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        t2 = task_factory.create(name="Task 2", priority=2, status=TaskStatus.PENDING)
        t1_id, t2_id = t1.id, t2.id

        response = client.post(
            "/api/v1/tasks/bulk/delete",
            json={"task_ids": [t1_id, t2_id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(r["success"] for r in data["results"])
        # Delete returns no task data
        assert all(r["task"] is None for r in data["results"])

        # Verify deleted from database
        assert repository.get_by_id(t1_id) is None
        assert repository.get_by_id(t2_id) is None

    def test_bulk_delete_nonexistent_task(self, client):
        """Test bulk delete with nonexistent task ID."""
        response = client.post(
            "/api/v1/tasks/bulk/delete",
            json={"task_ids": [99999]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["success"] is False
        assert data["results"][0]["error"] is not None

    def test_bulk_archive_mixed(self, client, task_factory):
        """Test bulk archive with valid and invalid IDs."""
        task = task_factory.create(
            name="Valid Task", priority=1, status=TaskStatus.PENDING
        )

        response = client.post(
            "/api/v1/tasks/bulk/archive",
            json={"task_ids": [task.id, 99999]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["success"] is True
        assert data["results"][1]["success"] is False

    def test_bulk_crud_audit_logs(self, client, task_factory):
        """Test audit logs are created for bulk CRUD operations."""
        t1 = task_factory.create(name="Task 1", priority=1, status=TaskStatus.PENDING)

        client.post(
            "/api/v1/tasks/bulk/archive",
            json={"task_ids": [t1.id]},
        )

        # Verify via audit log API
        logs_response = client.get(
            "/api/v1/audit-logs",
            params={"operation": "archive_task", "resource_id": t1.id},
        )
        assert logs_response.status_code == 200
        logs_data = logs_response.json()
        assert any(log["resource_id"] == t1.id for log in logs_data["logs"])
