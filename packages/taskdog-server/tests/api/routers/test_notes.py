"""Tests for notes router (CRUD operations for markdown notes)."""

import pytest


class TestNotesRouter:
    """Test cases for notes router endpoints."""

    def test_get_notes_for_existing_task_with_no_notes(self, client, task_factory):
        """Test getting notes for a task that has no notes."""
        # Arrange - create task without notes
        task = task_factory.create(name="Test Task", priority=1)

        # Act
        response = client.get(f"/api/v1/tasks/{task.id}/notes")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task.id
        assert data["content"] == ""
        assert data["has_notes"] is False

    def test_get_notes_for_existing_task_with_notes(
        self, client, task_factory, notes_repository
    ):
        """Test getting notes for a task that has notes."""
        # Arrange - create task with notes
        task = task_factory.create(name="Test Task", priority=1)
        notes_repository.write_notes(task.id, "# Test Notes\n\nSome content here.")

        # Act
        response = client.get(f"/api/v1/tasks/{task.id}/notes")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task.id
        assert data["content"] == "# Test Notes\n\nSome content here."
        assert data["has_notes"] is True

    @pytest.mark.parametrize(
        "operation,method,endpoint,payload",
        [
            ("get_notes", "GET", "/api/v1/tasks/999/notes", None),
            (
                "update_notes",
                "PUT",
                "/api/v1/tasks/999/notes",
                {"content": "Some notes"},
            ),
            ("delete_notes", "DELETE", "/api/v1/tasks/999/notes", None),
        ],
    )
    def test_notes_operation_not_found_returns_404(
        self, client, operation, method, endpoint, payload
    ):
        """Test notes operations on non-existent task return 404."""
        if method == "GET":
            response = client.get(endpoint)
        elif method == "PUT":
            response = client.put(endpoint, json=payload)
        elif method == "DELETE":
            response = client.delete(endpoint)

        assert response.status_code == 404
        if method != "DELETE":  # DELETE returns 204 with no content on success
            assert "detail" in response.json()

    # ===== PUT /{task_id}/notes Tests =====

    def test_update_notes_for_existing_task(
        self, client, task_factory, notes_repository
    ):
        """Test updating notes for an existing task."""
        # Arrange - create task
        task = task_factory.create(name="Test Task", priority=1)

        request_data = {"content": "# Updated Notes\n\nNew content."}

        # Act
        response = client.put(f"/api/v1/tasks/{task.id}/notes", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task.id
        assert data["content"] == "# Updated Notes\n\nNew content."
        assert data["has_notes"] is True

        # Verify notes were actually saved
        saved_notes = notes_repository.read_notes(task.id)
        assert saved_notes == "# Updated Notes\n\nNew content."

    def test_update_notes_with_empty_content(self, client, task_factory):
        """Test updating notes with empty content."""
        # Arrange - create task
        task = task_factory.create(name="Test Task", priority=1)

        request_data = {"content": ""}

        # Act
        response = client.put(f"/api/v1/tasks/{task.id}/notes", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == ""
        assert data["has_notes"] is False

    def test_update_notes_replace_existing(
        self, client, task_factory, notes_repository
    ):
        """Test updating notes replaces existing content."""
        # Arrange - create task with existing notes
        task = task_factory.create(name="Test Task", priority=1)
        notes_repository.write_notes(task.id, "Old content")

        request_data = {"content": "New content"}

        # Act
        response = client.put(f"/api/v1/tasks/{task.id}/notes", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "New content"

        # Verify old content is replaced
        saved_notes = notes_repository.read_notes(task.id)
        assert saved_notes == "New content"

    def test_update_notes_with_markdown_formatting(self, client, task_factory):
        """Test updating notes with markdown formatting."""
        # Arrange - create task
        task = task_factory.create(name="Test Task", priority=1)

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
        response = client.put(f"/api/v1/tasks/{task.id}/notes", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == markdown_content

    # ===== DELETE /{task_id}/notes Tests =====

    def test_delete_notes_for_existing_task_with_notes(
        self, client, task_factory, notes_repository
    ):
        """Test deleting notes for a task that has notes."""
        # Arrange - create task with notes
        task = task_factory.create(name="Test Task", priority=1)
        notes_repository.write_notes(task.id, "Some notes to delete")

        # Act
        response = client.delete(f"/api/v1/tasks/{task.id}/notes")

        # Assert
        assert response.status_code == 204

        # Verify notes were deleted
        saved_notes = notes_repository.read_notes(task.id)
        assert saved_notes == ""

    def test_delete_notes_for_existing_task_without_notes(self, client, task_factory):
        """Test deleting notes for a task that has no notes."""
        # Arrange - create task without notes
        task = task_factory.create(name="Test Task", priority=1)

        # Act
        response = client.delete(f"/api/v1/tasks/{task.id}/notes")

        # Assert
        assert response.status_code == 204

    def test_delete_notes_then_get_returns_empty(
        self, client, task_factory, notes_repository
    ):
        """Test that getting notes after deletion returns empty content."""
        # Arrange - create task with notes
        task = task_factory.create(name="Test Task", priority=1)
        notes_repository.write_notes(task.id, "Notes to be deleted")

        # Act - delete notes
        delete_response = client.delete(f"/api/v1/tasks/{task.id}/notes")
        assert delete_response.status_code == 204

        # Act - get notes after deletion
        get_response = client.get(f"/api/v1/tasks/{task.id}/notes")

        # Assert
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["content"] == ""
        assert data["has_notes"] is False

    # ===== Integration Tests =====

    def test_notes_crud_workflow(self, client, task_factory):
        """Test complete CRUD workflow for notes."""
        # Arrange - create task
        task = task_factory.create(name="Test Task", priority=1)

        # 1. Create notes (PUT)
        create_response = client.put(
            f"/api/v1/tasks/{task.id}/notes", json={"content": "Initial notes"}
        )
        assert create_response.status_code == 200
        assert create_response.json()["content"] == "Initial notes"

        # 2. Read notes (GET)
        read_response = client.get(f"/api/v1/tasks/{task.id}/notes")
        assert read_response.status_code == 200
        assert read_response.json()["content"] == "Initial notes"

        # 3. Update notes (PUT)
        update_response = client.put(
            f"/api/v1/tasks/{task.id}/notes", json={"content": "Updated notes"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["content"] == "Updated notes"

        # 4. Verify update (GET)
        verify_response = client.get(f"/api/v1/tasks/{task.id}/notes")
        assert verify_response.status_code == 200
        assert verify_response.json()["content"] == "Updated notes"

        # 5. Delete notes (DELETE)
        delete_response = client.delete(f"/api/v1/tasks/{task.id}/notes")
        assert delete_response.status_code == 204

        # 6. Verify deletion (GET)
        final_response = client.get(f"/api/v1/tasks/{task.id}/notes")
        assert final_response.status_code == 200
        assert final_response.json()["content"] == ""
