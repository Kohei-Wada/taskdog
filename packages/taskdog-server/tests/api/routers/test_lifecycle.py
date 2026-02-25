"""Tests for lifecycle router (status change endpoints)."""

from datetime import datetime

import pytest

from taskdog_core.domain.entities.task import TaskStatus


class TestLifecycleRouter:
    """Test cases for lifecycle router endpoints."""

    def test_start_task_success(self, client, repository, task_factory):
        """Test starting a pending task."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.post(f"/api/v1/tasks/{task.id}/start")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"
        assert data["actual_start"] is not None

        # Verify in database
        updated_task = repository.get_by_id(task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.actual_start is not None

    @pytest.mark.parametrize(
        "operation,endpoint",
        [
            ("start", "/api/v1/tasks/999/start"),
            ("complete", "/api/v1/tasks/999/complete"),
            ("pause", "/api/v1/tasks/999/pause"),
            ("cancel", "/api/v1/tasks/999/cancel"),
            ("reopen", "/api/v1/tasks/999/reopen"),
        ],
    )
    def test_lifecycle_operation_not_found(self, client, operation, endpoint):
        """Test lifecycle operations on non-existent task return 404."""
        response = client.post(endpoint)
        assert response.status_code == 404
        assert "detail" in response.json()

    @pytest.mark.parametrize(
        "operation,endpoint_template",
        [
            ("start", "/api/v1/tasks/{task_id}/start"),
            ("complete", "/api/v1/tasks/{task_id}/complete"),
            ("pause", "/api/v1/tasks/{task_id}/pause"),
            ("cancel", "/api/v1/tasks/{task_id}/cancel"),
        ],
    )
    def test_lifecycle_operation_already_finished_returns_error(
        self, client, repository, task_factory, operation, endpoint_template
    ):
        """Test lifecycle operations on completed task return 400."""
        # Arrange
        task = task_factory.create(name="Completed Task", priority=1)
        task.status = TaskStatus.COMPLETED
        task.actual_start = datetime.now()
        task.actual_end = datetime.now()
        repository.save(task)

        # Act
        response = client.post(endpoint_template.format(task_id=task.id))

        # Assert
        assert response.status_code == 400

    def test_complete_task_success(self, client, repository, task_factory):
        """Test completing an in-progress task."""
        # Arrange
        task = task_factory.create(name="Test Task", priority=1)
        task.status = TaskStatus.IN_PROGRESS
        task.actual_start = datetime.now()
        repository.save(task)

        # Act
        response = client.post(f"/api/v1/tasks/{task.id}/complete")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["actual_end"] is not None

        # Verify in database
        updated_task = repository.get_by_id(task.id)
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.actual_end is not None

    def test_pause_task_success(self, client, repository, task_factory):
        """Test pausing an in-progress task."""
        # Arrange
        task = task_factory.create(name="Test Task", priority=1)
        task.status = TaskStatus.IN_PROGRESS
        task.actual_start = datetime.now()
        repository.save(task)

        # Act
        response = client.post(f"/api/v1/tasks/{task.id}/pause")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["actual_start"] is None
        assert data["actual_end"] is None

        # Verify in database
        updated_task = repository.get_by_id(task.id)
        assert updated_task.status == TaskStatus.PENDING
        assert updated_task.actual_start is None

    def test_cancel_task_success(self, client, repository, task_factory):
        """Test canceling a task."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.post(f"/api/v1/tasks/{task.id}/cancel")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELED"
        assert data["actual_end"] is not None

        # Verify in database
        updated_task = repository.get_by_id(task.id)
        assert updated_task.status == TaskStatus.CANCELED
        assert updated_task.actual_end is not None

    @pytest.mark.parametrize(
        "initial_status,has_actual_start",
        [
            (TaskStatus.COMPLETED, True),
            (TaskStatus.CANCELED, False),
        ],
        ids=["from_completed", "from_canceled"],
    )
    def test_reopen_task_success(
        self, client, repository, task_factory, initial_status, has_actual_start
    ):
        """Test reopening a completed or canceled task."""
        task = task_factory.create(name="Finished Task", priority=1)
        task.status = initial_status
        if has_actual_start:
            task.actual_start = datetime.now()
        task.actual_end = datetime.now()
        repository.save(task)
        response = client.post(f"/api/v1/tasks/{task.id}/reopen")
        assert response.status_code == 200
        assert response.json()["status"] == "PENDING"

    def test_start_in_progress_task_returns_error(
        self, client, repository, task_factory
    ):
        """Test starting already in-progress task returns 400 error."""
        # Arrange
        task = task_factory.create(name="In Progress Task", priority=1)
        task.status = TaskStatus.IN_PROGRESS
        task.actual_start = datetime.now()
        repository.save(task)

        # Act
        response = client.post(f"/api/v1/tasks/{task.id}/start")

        # Assert
        assert response.status_code == 400
        assert "already IN_PROGRESS" in response.json()["detail"]
