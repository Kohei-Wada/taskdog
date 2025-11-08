"""Tests for lifecycle router (status change endpoints)."""

import os
import tempfile
import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)
from taskdog_server.api.context import ApiContext
from taskdog_server.api.dependencies import set_api_context


class TestLifecycleRouter(unittest.TestCase):
    """Test cases for lifecycle router endpoints."""

    def setUp(self):
        """Set up test fixtures with real dependencies."""
        # Create temporary database file
        self.test_db = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db")
        self.test_db.close()
        self.test_db_path = self.test_db.name

        # Create temporary notes directory
        self.test_notes_dir = tempfile.mkdtemp()

        # Initialize repositories
        self.repository = SqliteTaskRepository(f"sqlite:///{self.test_db_path}")
        self.notes_repository = FileNotesRepository()

        # ID counter for test tasks
        self._next_task_id = 1

        # Initialize API context with real controllers
        from unittest.mock import MagicMock

        from taskdog_core.controllers.query_controller import QueryController
        from taskdog_core.controllers.task_analytics_controller import (
            TaskAnalyticsController,
        )
        from taskdog_core.controllers.task_crud_controller import TaskCrudController
        from taskdog_core.controllers.task_lifecycle_controller import (
            TaskLifecycleController,
        )
        from taskdog_core.controllers.task_relationship_controller import (
            TaskRelationshipController,
        )

        # Mock config with defaults
        self.config = MagicMock()
        self.config.task.default_priority = 3
        self.config.scheduling.max_hours_per_day = 8.0
        self.config.scheduling.default_algorithm = "greedy"
        self.config.region.country = None

        # Create controllers
        query_controller = QueryController(self.repository, self.notes_repository)
        lifecycle_controller = TaskLifecycleController(self.repository, self.config)
        relationship_controller = TaskRelationshipController(
            self.repository, self.config
        )
        analytics_controller = TaskAnalyticsController(
            self.repository, self.config, None
        )
        crud_controller = TaskCrudController(self.repository, self.config)

        # Create API context
        api_context = ApiContext(
            repository=self.repository,
            config=self.config,
            notes_repository=self.notes_repository,
            query_controller=query_controller,
            lifecycle_controller=lifecycle_controller,
            relationship_controller=relationship_controller,
            analytics_controller=analytics_controller,
            crud_controller=crud_controller,
            holiday_checker=None,
        )

        # Set context BEFORE creating app
        set_api_context(api_context)

        # Create test client with app (lifespan will use the context we just set)
        from fastapi import FastAPI

        # Create app without lifespan to avoid reinitializing context
        app = FastAPI(
            title="Taskdog API Test",
            description="Test instance",
            version="1.0.0",
        )

        # Import and register routers
        from taskdog_server.api.routers import (
            analytics_router,
            lifecycle_router,
            notes_router,
            relationships_router,
            tasks_router,
        )

        app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
        app.include_router(lifecycle_router, prefix="/api/v1/tasks", tags=["lifecycle"])
        app.include_router(
            relationships_router, prefix="/api/v1/tasks", tags=["relationships"]
        )
        app.include_router(notes_router, prefix="/api/v1/tasks", tags=["notes"])
        app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

        self.client = TestClient(app)

    def _get_next_id(self):
        """Get next available task ID for tests."""
        task_id = self._next_task_id
        self._next_task_id += 1
        return task_id

    def tearDown(self):
        """Clean up temporary files after each test."""
        if hasattr(self, "repository"):
            self.repository.close()
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
        # Clean up notes directory
        import shutil

        if os.path.exists(self.test_notes_dir):
            shutil.rmtree(self.test_notes_dir)

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
