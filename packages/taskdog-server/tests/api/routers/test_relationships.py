"""Tests for relationships router (dependencies, tags, hours logging)."""

import os
import tempfile
import unittest
from datetime import date

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


class TestRelationshipsRouter(unittest.TestCase):
    """Test cases for relationships router endpoints."""

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

    def test_add_dependency_success(self):
        """Test adding a dependency to a task."""
        # Arrange
        task1 = Task(name="Dependent Task", priority=1, status=TaskStatus.PENDING)
        task1.id = self._get_next_id()
        task2 = Task(name="Dependency Task", priority=1, status=TaskStatus.PENDING)
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act
        response = self.client.post(
            f"/api/v1/tasks/{task1.id}/dependencies", json={"depends_on_id": task2.id}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(task2.id, data["depends_on"])

        # Verify in database
        updated_task = self.repository.get_by_id(task1.id)
        self.assertIn(task2.id, updated_task.depends_on)

    def test_add_dependency_not_found(self):
        """Test adding dependency when task not found returns 404."""
        # Act
        response = self.client.post(
            "/api/v1/tasks/999/dependencies", json={"depends_on_id": 1}
        )

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_add_dependency_circular_returns_error(self):
        """Test adding circular dependency returns 400."""
        # Arrange - Create chain: task1 -> task2
        task1 = Task(name="Task 1", priority=1, status=TaskStatus.PENDING)
        task1.id = self._get_next_id()
        task2 = Task(
            name="Task 2", priority=1, status=TaskStatus.PENDING, depends_on=[task1.id]
        )
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act - Try to add task2 as dependency of task1 (creates cycle)
        response = self.client.post(
            f"/api/v1/tasks/{task1.id}/dependencies", json={"depends_on_id": task2.id}
        )

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_add_dependency_self_reference_returns_error(self):
        """Test adding self as dependency returns 400."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(
            f"/api/v1/tasks/{task.id}/dependencies", json={"depends_on_id": task.id}
        )

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_remove_dependency_success(self):
        """Test removing a dependency from a task."""
        # Arrange
        task1 = Task(name="Dependency Task", priority=1, status=TaskStatus.PENDING)
        task1.id = self._get_next_id()
        task2 = Task(
            name="Dependent Task",
            priority=1,
            status=TaskStatus.PENDING,
            depends_on=[task1.id],
        )
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act
        response = self.client.delete(
            f"/api/v1/tasks/{task2.id}/dependencies/{task1.id}"
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn(task1.id, data["depends_on"])

        # Verify in database
        updated_task = self.repository.get_by_id(task2.id)
        self.assertNotIn(task1.id, updated_task.depends_on)

    def test_remove_dependency_not_found(self):
        """Test removing dependency when task not found returns 404."""
        # Act
        response = self.client.delete("/api/v1/tasks/999/dependencies/1")

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_remove_nonexistent_dependency_returns_error(self):
        """Test removing non-existent dependency returns 400."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act - Try to remove dependency that doesn't exist
        response = self.client.delete(f"/api/v1/tasks/{task.id}/dependencies/999")

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_set_task_tags_success(self):
        """Test setting task tags."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING, tags=[])
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.put(
            f"/api/v1/tasks/{task.id}/tags", json={"tags": ["urgent", "bug"]}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(sorted(data["tags"]), ["bug", "urgent"])

        # Verify in database
        updated_task = self.repository.get_by_id(task.id)
        self.assertEqual(sorted(updated_task.tags), ["bug", "urgent"])

    def test_set_task_tags_replaces_existing(self):
        """Test setting tags replaces existing tags."""
        # Arrange
        task = Task(
            name="Test Task", priority=1, status=TaskStatus.PENDING, tags=["old", "tag"]
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.put(
            f"/api/v1/tasks/{task.id}/tags", json={"tags": ["new", "tags"]}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(sorted(data["tags"]), ["new", "tags"])
        self.assertNotIn("old", data["tags"])

    def test_set_task_tags_empty_clears_tags(self):
        """Test setting empty tags list clears all tags."""
        # Arrange
        task = Task(
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["tag1", "tag2"],
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.put(f"/api/v1/tasks/{task.id}/tags", json={"tags": []})

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tags"], [])

    def test_set_task_tags_not_found(self):
        """Test setting tags when task not found returns 404."""
        # Act
        response = self.client.put("/api/v1/tasks/999/tags", json={"tags": ["test"]})

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_set_task_tags_validation_error_empty_tag(self):
        """Test setting tags with empty tag name returns 400 or 422."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.put(f"/api/v1/tasks/{task.id}/tags", json={"tags": [""]})

        # Assert
        self.assertIn(response.status_code, [400, 422])

    def test_log_hours_success(self):
        """Test logging hours for a task."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(
            f"/api/v1/tasks/{task.id}/log-hours",
            json={"hours": 4.5, "date": "2025-01-15"},
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("2025-01-15", data["actual_daily_hours"])
        self.assertEqual(data["actual_daily_hours"]["2025-01-15"], 4.5)

        # Verify in database
        updated_task = self.repository.get_by_id(task.id)
        self.assertIn(date(2025, 1, 15), updated_task.actual_daily_hours)
        self.assertEqual(updated_task.actual_daily_hours[date(2025, 1, 15)], 4.5)

    def test_log_hours_default_date_today(self):
        """Test logging hours without date uses today."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        today = date.today()

        # Act
        response = self.client.post(
            f"/api/v1/tasks/{task.id}/log-hours", json={"hours": 3.0}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(today.isoformat(), data["actual_daily_hours"])
        self.assertEqual(data["actual_daily_hours"][today.isoformat()], 3.0)

    def test_log_hours_not_found(self):
        """Test logging hours when task not found returns 404."""
        # Act
        response = self.client.post("/api/v1/tasks/999/log-hours", json={"hours": 2.0})

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_log_hours_validation_error_negative_hours(self):
        """Test logging negative hours returns 400 or 422."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(
            f"/api/v1/tasks/{task.id}/log-hours", json={"hours": -1.0}
        )

        # Assert
        self.assertIn(response.status_code, [400, 422])

    def test_log_hours_updates_existing_date(self):
        """Test logging hours for existing date updates the value."""
        # Arrange
        task = Task(
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            actual_daily_hours={date(2025, 1, 15): 2.0},
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(
            f"/api/v1/tasks/{task.id}/log-hours",
            json={"hours": 5.0, "date": "2025-01-15"},
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["actual_daily_hours"]["2025-01-15"], 5.0)


if __name__ == "__main__":
    unittest.main()
