"""Tests for tasks router (CRUD endpoints)."""

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


class TestTasksRouter(unittest.TestCase):
    """Test cases for tasks router endpoints."""

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

    def test_create_task_success(self):
        """Test creating a new task successfully."""
        # Arrange
        request_data = {
            "name": "Test Task",
            "priority": 2,
            "tags": ["test", "api"],
        }

        # Act
        response = self.client.post("/api/v1/tasks", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Test Task")
        self.assertEqual(data["priority"], 2)
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["tags"], ["test", "api"])
        self.assertIsNotNone(data["id"])

    def test_create_task_with_minimal_data(self):
        """Test creating task with only required fields."""
        # Arrange
        request_data = {"name": "Minimal Task"}

        # Act
        response = self.client.post("/api/v1/tasks", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Minimal Task")
        self.assertEqual(data["priority"], 3)  # Default from config

    def test_create_task_validation_error_empty_name(self):
        """Test creating task with empty name returns 400 or 422."""
        # Arrange
        request_data = {"name": ""}

        # Act
        response = self.client.post("/api/v1/tasks", json=request_data)

        # Assert
        self.assertIn(
            response.status_code, [400, 422]
        )  # 422 from Pydantic, 400 from business logic
        self.assertIn("detail", response.json())

    def test_create_task_validation_error_invalid_priority(self):
        """Test creating task with invalid priority returns 400 or 422."""
        # Arrange
        request_data = {"name": "Test Task", "priority": 0}

        # Act
        response = self.client.post("/api/v1/tasks", json=request_data)

        # Assert
        self.assertIn(response.status_code, [400, 422])

    def test_list_tasks_empty(self):
        """Test listing tasks when none exist."""
        # Act
        response = self.client.get("/api/v1/tasks")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tasks"], [])
        self.assertEqual(data["total_count"], 0)
        self.assertEqual(data["filtered_count"], 0)

    def test_list_tasks_returns_all_non_archived(self):
        """Test listing tasks returns all non-archived tasks."""
        # Arrange - Create tasks (assign IDs manually to avoid collision)
        task1 = Task(name="Task 1", priority=1, status=TaskStatus.PENDING)
        task1.id = 1
        task2 = Task(name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS)
        task2.id = 2
        task3 = Task(
            name="Archived Task",
            priority=3,
            status=TaskStatus.PENDING,
            is_archived=True,
        )
        task3.id = 3

        self.repository.save(task1)
        self.repository.save(task2)
        self.repository.save(task3)

        # Verify tasks were saved
        all_tasks = self.repository.get_all()
        self.assertEqual(
            len(all_tasks), 3, f"Expected 3 tasks in repo, got {len(all_tasks)}"
        )

        # Act
        response = self.client.get("/api/v1/tasks")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Debug: print response if test fails
        if len(data["tasks"]) != 2:
            print(f"DEBUG: Response data: {data}")
            print(f"DEBUG: All tasks in repo: {[t.name for t in all_tasks]}")
        self.assertEqual(len(data["tasks"]), 2)
        self.assertEqual(data["total_count"], 3)
        self.assertEqual(data["filtered_count"], 2)

    def test_list_tasks_with_all_flag_includes_archived(self):
        """Test listing tasks with all=true includes archived tasks."""
        # Arrange
        task1 = Task(name="Task 1", priority=1, status=TaskStatus.PENDING)
        task1.id = self._get_next_id()
        task2 = Task(
            name="Archived Task",
            priority=2,
            status=TaskStatus.PENDING,
            is_archived=True,
        )
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act
        response = self.client.get("/api/v1/tasks?all=true")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 2)

    def test_list_tasks_filter_by_status(self):
        """Test filtering tasks by status."""
        # Arrange
        task1 = Task(name="Pending Task", priority=1, status=TaskStatus.PENDING)
        task1.id = self._get_next_id()
        task2 = Task(name="Active Task", priority=2, status=TaskStatus.IN_PROGRESS)
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act
        response = self.client.get("/api/v1/tasks?status=PENDING")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["name"], "Pending Task")

    def test_list_tasks_filter_by_tags(self):
        """Test filtering tasks by tags."""
        # Arrange
        task1 = Task(
            name="Task 1", priority=1, status=TaskStatus.PENDING, tags=["urgent", "bug"]
        )
        task1.id = self._get_next_id()
        task2 = Task(
            name="Task 2", priority=2, status=TaskStatus.PENDING, tags=["feature"]
        )
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act
        response = self.client.get("/api/v1/tasks?tags=urgent")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["name"], "Task 1")

    def test_list_tasks_sort_by_priority(self):
        """Test sorting tasks by priority."""
        # Arrange
        task1 = Task(name="Low Priority", priority=3, status=TaskStatus.PENDING)
        task1.id = self._get_next_id()
        task2 = Task(name="High Priority", priority=1, status=TaskStatus.PENDING)
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act
        response = self.client.get("/api/v1/tasks?sort=priority")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Default sort is ascending (low to high priority numbers)
        self.assertEqual(len(data["tasks"]), 2)
        self.assertEqual(data["tasks"][0]["priority"], 3)
        self.assertEqual(data["tasks"][1]["priority"], 1)

    def test_get_task_success(self):
        """Test getting a task by ID."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.get(f"/api/v1/tasks/{task.id}")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], task.id)
        self.assertEqual(data["name"], "Test Task")

    def test_get_task_not_found(self):
        """Test getting non-existent task returns 404."""
        # Act
        response = self.client.get("/api/v1/tasks/999")

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_update_task_success(self):
        """Test updating task fields."""
        # Arrange
        task = Task(name="Original Name", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.patch(
            f"/api/v1/tasks/{task.id}", json={"name": "Updated Name", "priority": 5}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Updated Name")
        self.assertEqual(data["priority"], 5)
        self.assertIn("updated_fields", data)
        self.assertIn("name", data["updated_fields"])
        self.assertIn("priority", data["updated_fields"])

    def test_update_task_not_found(self):
        """Test updating non-existent task returns 404."""
        # Act
        response = self.client.patch("/api/v1/tasks/999", json={"name": "New Name"})

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_update_task_validation_error(self):
        """Test updating task with invalid data returns 400 or 422."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act - Try to set invalid priority
        response = self.client.patch(f"/api/v1/tasks/{task.id}", json={"priority": 0})

        # Assert
        self.assertIn(response.status_code, [400, 422])

    def test_archive_task_success(self):
        """Test archiving a task."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/archive")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["is_archived"], True)

        # Verify in database
        updated_task = self.repository.get_by_id(task.id)
        self.assertTrue(updated_task.is_archived)

    def test_archive_task_not_found(self):
        """Test archiving non-existent task returns 404."""
        # Act
        response = self.client.post("/api/v1/tasks/999/archive")

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_restore_task_success(self):
        """Test restoring an archived task."""
        # Arrange
        task = Task(
            name="Archived Task",
            priority=1,
            status=TaskStatus.PENDING,
            is_archived=True,
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/restore")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["is_archived"], False)

    def test_restore_task_not_archived_returns_error(self):
        """Test restoring non-archived task returns 400."""
        # Arrange
        task = Task(
            name="Active Task", priority=1, status=TaskStatus.PENDING, is_archived=False
        )
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.post(f"/api/v1/tasks/{task.id}/restore")

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_delete_task_success(self):
        """Test permanently deleting a task."""
        # Arrange
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self._get_next_id()
        self.repository.save(task)

        # Act
        response = self.client.delete(f"/api/v1/tasks/{task.id}")

        # Assert
        self.assertEqual(response.status_code, 204)

        # Verify task is deleted
        deleted_task = self.repository.get_by_id(task.id)
        self.assertIsNone(deleted_task)

    def test_delete_task_not_found(self):
        """Test deleting non-existent task returns 404."""
        # Act
        response = self.client.delete("/api/v1/tasks/999")

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_list_tasks_with_date_range_filter(self):
        """Test filtering tasks by date range."""
        # Arrange
        task1 = Task(
            name="Early Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=date(2025, 1, 1),
            planned_end=date(2025, 1, 5),
        )
        task1.id = self._get_next_id()
        task2 = Task(
            name="Late Task",
            priority=2,
            status=TaskStatus.PENDING,
            planned_start=date(2025, 2, 1),
            planned_end=date(2025, 2, 5),
        )
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act - Filter for January
        response = self.client.get(
            "/api/v1/tasks?start_date=2025-01-01&end_date=2025-01-31"
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["name"], "Early Task")

    def test_list_tasks_with_reverse_sort(self):
        """Test reverse sorting."""
        # Arrange
        task1 = Task(name="Task A", priority=1, status=TaskStatus.PENDING)
        task1.id = self._get_next_id()
        task2 = Task(name="Task B", priority=2, status=TaskStatus.PENDING)
        task2.id = self._get_next_id()

        self.repository.save(task1)
        self.repository.save(task2)

        # Act
        response = self.client.get("/api/v1/tasks?sort=priority&reverse=true")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tasks"]), 2)
        # Verify reverse order by checking priorities
        self.assertEqual(data["tasks"][0]["priority"], 1)
        self.assertEqual(data["tasks"][1]["priority"], 2)


if __name__ == "__main__":
    unittest.main()
