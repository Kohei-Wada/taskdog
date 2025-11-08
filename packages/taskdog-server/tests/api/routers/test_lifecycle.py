"""Tests for lifecycle router (status change endpoints)."""

import unittest
from datetime import datetime

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

    def test_start_task_not_found(self):
        """Test starting non-existent task returns 404."""
        # Act
        response = self.client.post("/api/v1/tasks/999/start")

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_start_task_already_finished_returns_error(self):
        """Test starting completed task returns 400."""
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
        response = self.client.post(f"/api/v1/tasks/{task.id}/start")

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

    def test_complete_task_not_found(self):
        """Test completing non-existent task returns 404."""
        # Act
        response = self.client.post("/api/v1/tasks/999/complete")

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_complete_task_already_finished_returns_error(self):
        """Test completing already completed task returns 400."""
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
        response = self.client.post(f"/api/v1/tasks/{task.id}/complete")

        # Assert
        self.assertEqual(response.status_code, 400)

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

    def test_pause_task_not_found(self):
        """Test pausing non-existent task returns 404."""
        # Act
        response = self.client.post("/api/v1/tasks/999/pause")

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_pause_task_already_finished_returns_error(self):
        """Test pausing completed task returns 400."""
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
        response = self.client.post(f"/api/v1/tasks/{task.id}/pause")

        # Assert
        self.assertEqual(response.status_code, 400)

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

    def test_cancel_task_not_found(self):
        """Test canceling non-existent task returns 404."""
        # Act
        response = self.client.post("/api/v1/tasks/999/cancel")

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_cancel_task_already_finished_returns_error(self):
        """Test canceling completed task returns 400."""
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
        response = self.client.post(f"/api/v1/tasks/{task.id}/cancel")

        # Assert
        self.assertEqual(response.status_code, 400)

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

    def test_reopen_task_not_found(self):
        """Test reopening non-existent task returns 404."""
        # Act
        response = self.client.post("/api/v1/tasks/999/reopen")

        # Assert
        self.assertEqual(response.status_code, 404)

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
