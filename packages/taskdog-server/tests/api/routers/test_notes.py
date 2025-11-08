"""Tests for notes router (CRUD operations for markdown notes)."""

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from taskdog_core.domain.entities.task import Task
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)
from taskdog_server.api.context import ApiContext
from taskdog_server.api.dependencies import set_api_context


class TestNotesRouter(unittest.TestCase):
    """Test cases for notes router endpoints."""

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

        # Create test client with app
        from fastapi import FastAPI

        app = FastAPI(
            title="Taskdog API Test",
            description="Test instance",
            version="1.0.0",
        )

        # Import and register routers
        from taskdog_server.api.routers import notes_router

        app.include_router(notes_router, prefix="/api/v1/tasks", tags=["notes"])

        self.client = TestClient(app)

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

    # ===== GET /{task_id}/notes Tests =====

    def test_get_notes_for_existing_task_with_no_notes(self):
        """Test getting notes for a task that has no notes."""
        # Arrange - create task without notes
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)

        # Act
        response = self.client.get("/api/v1/tasks/1/notes")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["task_id"], 1)
        self.assertEqual(data["content"], "")
        self.assertEqual(data["has_notes"], False)

    def test_get_notes_for_existing_task_with_notes(self):
        """Test getting notes for a task that has notes."""
        # Arrange - create task with notes
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)
        self.notes_repository.write_notes(1, "# Test Notes\n\nSome content here.")

        # Act
        response = self.client.get("/api/v1/tasks/1/notes")

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["task_id"], 1)
        self.assertEqual(data["content"], "# Test Notes\n\nSome content here.")
        self.assertEqual(data["has_notes"], True)

    def test_get_notes_for_nonexistent_task(self):
        """Test getting notes for a task that doesn't exist."""
        # Act
        response = self.client.get("/api/v1/tasks/999/notes")

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    # ===== PUT /{task_id}/notes Tests =====

    def test_update_notes_for_existing_task(self):
        """Test updating notes for an existing task."""
        # Arrange - create task
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)

        request_data = {"content": "# Updated Notes\n\nNew content."}

        # Act
        response = self.client.put("/api/v1/tasks/1/notes", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["task_id"], 1)
        self.assertEqual(data["content"], "# Updated Notes\n\nNew content.")
        self.assertEqual(data["has_notes"], True)

        # Verify notes were actually saved
        saved_notes = self.notes_repository.read_notes(1)
        self.assertEqual(saved_notes, "# Updated Notes\n\nNew content.")

    def test_update_notes_with_empty_content(self):
        """Test updating notes with empty content."""
        # Arrange - create task
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)

        request_data = {"content": ""}

        # Act
        response = self.client.put("/api/v1/tasks/1/notes", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["content"], "")
        self.assertEqual(data["has_notes"], False)

    def test_update_notes_for_nonexistent_task(self):
        """Test updating notes for a task that doesn't exist."""
        # Arrange
        request_data = {"content": "Some notes"}

        # Act
        response = self.client.put("/api/v1/tasks/999/notes", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_update_notes_replace_existing(self):
        """Test updating notes replaces existing content."""
        # Arrange - create task with existing notes
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)
        self.notes_repository.write_notes(1, "Old content")

        request_data = {"content": "New content"}

        # Act
        response = self.client.put("/api/v1/tasks/1/notes", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["content"], "New content")

        # Verify old content is replaced
        saved_notes = self.notes_repository.read_notes(1)
        self.assertEqual(saved_notes, "New content")

    def test_update_notes_with_markdown_formatting(self):
        """Test updating notes with markdown formatting."""
        # Arrange - create task
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)

        markdown_content = """# Title

## Subtitle

- Item 1
- Item 2

**Bold text** and *italic text*.

```python
def hello():
    print("Hello, World!")
```
"""
        request_data = {"content": markdown_content}

        # Act
        response = self.client.put("/api/v1/tasks/1/notes", json=request_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["content"], markdown_content)

    # ===== DELETE /{task_id}/notes Tests =====

    def test_delete_notes_for_existing_task_with_notes(self):
        """Test deleting notes for a task that has notes."""
        # Arrange - create task with notes
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)
        self.notes_repository.write_notes(1, "Some notes to delete")

        # Act
        response = self.client.delete("/api/v1/tasks/1/notes")

        # Assert
        self.assertEqual(response.status_code, 204)

        # Verify notes were deleted
        saved_notes = self.notes_repository.read_notes(1)
        self.assertEqual(saved_notes, "")

    def test_delete_notes_for_existing_task_without_notes(self):
        """Test deleting notes for a task that has no notes."""
        # Arrange - create task without notes
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)

        # Act
        response = self.client.delete("/api/v1/tasks/1/notes")

        # Assert
        self.assertEqual(response.status_code, 204)

    def test_delete_notes_for_nonexistent_task(self):
        """Test deleting notes for a task that doesn't exist."""
        # Act
        response = self.client.delete("/api/v1/tasks/999/notes")

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_delete_notes_then_get_returns_empty(self):
        """Test that getting notes after deletion returns empty content."""
        # Arrange - create task with notes
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)
        self.notes_repository.write_notes(1, "Notes to be deleted")

        # Act - delete notes
        delete_response = self.client.delete("/api/v1/tasks/1/notes")
        self.assertEqual(delete_response.status_code, 204)

        # Act - get notes after deletion
        get_response = self.client.get("/api/v1/tasks/1/notes")

        # Assert
        self.assertEqual(get_response.status_code, 200)
        data = get_response.json()
        self.assertEqual(data["content"], "")
        self.assertEqual(data["has_notes"], False)

    # ===== Integration Tests =====

    def test_notes_crud_workflow(self):
        """Test complete CRUD workflow for notes."""
        # Arrange - create task
        task = Task(id=1, name="Test Task", priority=1)
        self.repository.save(task)

        # 1. Create notes (PUT)
        create_response = self.client.put(
            "/api/v1/tasks/1/notes", json={"content": "Initial notes"}
        )
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(create_response.json()["content"], "Initial notes")

        # 2. Read notes (GET)
        read_response = self.client.get("/api/v1/tasks/1/notes")
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()["content"], "Initial notes")

        # 3. Update notes (PUT)
        update_response = self.client.put(
            "/api/v1/tasks/1/notes", json={"content": "Updated notes"}
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["content"], "Updated notes")

        # 4. Verify update (GET)
        verify_response = self.client.get("/api/v1/tasks/1/notes")
        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(verify_response.json()["content"], "Updated notes")

        # 5. Delete notes (DELETE)
        delete_response = self.client.delete("/api/v1/tasks/1/notes")
        self.assertEqual(delete_response.status_code, 204)

        # 6. Verify deletion (GET)
        final_response = self.client.get("/api/v1/tasks/1/notes")
        self.assertEqual(final_response.status_code, 200)
        self.assertEqual(final_response.json()["content"], "")


if __name__ == "__main__":
    unittest.main()
