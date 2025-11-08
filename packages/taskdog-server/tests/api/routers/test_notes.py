"""Tests for notes router (CRUD operations for markdown notes)."""

import unittest

from taskdog_core.domain.entities.task import Task
from tests.test_base import BaseApiRouterTest


class TestNotesRouter(BaseApiRouterTest):
    """Test cases for notes router endpoints."""

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
