"""Tests for lifecycle router (status change endpoints)."""

import unittest
from datetime import datetime

from parameterized import parameterized

from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.test_base import BaseApiRouterTest


class TestLifecycleRouter(BaseApiRouterTest):
    """Test cases for lifecycle router endpoints."""

    def test_start_task_success(self):
        """Test starting a pending task."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/start")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "IN_PROGRESS")
        self.assertIsNotNone(data["actual_start"])

        # Verify in database
        updated_task = self.repository.get_by_id(task.id)
        self.assertEqual(updated_task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(updated_task.actual_start)

    @parameterized.expand(
        [
            ("start", "/api/v1/tasks/999/start"),
            ("complete", "/api/v1/tasks/999/complete"),
            ("pause", "/api/v1/tasks/999/pause"),
            ("cancel", "/api/v1/tasks/999/cancel"),
            ("reopen", "/api/v1/tasks/999/reopen"),
        ]
    )
    def test_lifecycle_operation_not_found(self, operation, endpoint):
        """Test lifecycle operations on non-existent task return 404."""
        response = self.client.post(endpoint)
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    @parameterized.expand(
        [
            ("start", "/api/v1/tasks/{task_id}/start"),
            ("complete", "/api/v1/tasks/{task_id}/complete"),
            ("pause", "/api/v1/tasks/{task_id}/pause"),
            ("cancel", "/api/v1/tasks/{task_id}/cancel"),
        ]
    )
    def test_lifecycle_operation_already_finished_returns_error(
        self, operation, endpoint_template
    ):
        """Test lifecycle operations on completed task return 400."""
        # Arrange
        task = Task(
            name="Completed Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start=datetime.now(),
            actual_end=datetime.now(),
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(endpoint_template.format(task_id=task.id))

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_complete_task_success(self):
        """Test completing an in-progress task."""
        # Arrange
        task = Task(
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime.now(),
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/complete")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "COMPLETED")
        self.assertIsNotNone(data["actual_end"])

        # Verify in database
        updated_task = self.repository.get_by_id(task.id)
        self.assertEqual(updated_task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(updated_task.actual_end)

    def test_pause_task_success(self):
        """Test pausing an in-progress task."""
        # Arrange
        task = Task(
            name="Test Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime.now(),
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/pause")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "PENDING")
        self.assertIsNone(data["actual_start"])
        self.assertIsNone(data["actual_end"])

        # Verify in database
        updated_task = self.repository.get_by_id(task.id)
        self.assertEqual(updated_task.status, TaskStatus.PENDING)
        self.assertIsNone(updated_task.actual_start)

    def test_cancel_task_success(self):
        """Test canceling a task."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/cancel")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "CANCELED")
        self.assertIsNotNone(data["actual_end"])

        # Verify in database
        updated_task = self.repository.get_by_id(task.id)
        self.assertEqual(updated_task.status, TaskStatus.CANCELED)
        self.assertIsNotNone(updated_task.actual_end)

    def test_reopen_task_success(self):
        """Test reopening a completed task."""
        # Arrange
        task = Task(
            name="Completed Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start=datetime.now(),
            actual_end=datetime.now(),
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/reopen")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "PENDING")
        self.assertIsNone(data["actual_start"])
        self.assertIsNone(data["actual_end"])

        # Verify in database
        updated_task = self.repository.get_by_id(task.id)
        self.assertEqual(updated_task.status, TaskStatus.PENDING)
        self.assertIsNone(updated_task.actual_start)
        self.assertIsNone(updated_task.actual_end)

    def test_reopen_canceled_task_success(self):
        """Test reopening a canceled task."""
        # Arrange
        task = Task(
            name="Canceled Task",
            priority=1,
            status=TaskStatus.CANCELED,
            actual_end=datetime.now(),
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/reopen")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "PENDING")

    def test_start_in_progress_task_success(self):
        """Test starting already in-progress task is idempotent."""
        # Arrange
        task = Task(
            name="In Progress Task",
            priority=1,
            status=TaskStatus.IN_PROGRESS,
            actual_start=datetime.now(),
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/start")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "IN_PROGRESS")
        # Start time should be preserved
        self.assertIsNotNone(data["actual_start"])


if __name__ == "__main__":
    unittest.main()
