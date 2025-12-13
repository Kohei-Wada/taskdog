"""Tests for relationships router (dependency and tag management)."""

import pytest

from taskdog_core.domain.entities.task import TaskStatus


class TestRelationshipsRouter:
    """Test cases for relationships router endpoints."""

    def test_add_dependency_success(self, client, repository, task_factory):
        """Test adding a dependency to a task."""
        # Arrange
        task1 = task_factory.create(
            name="Dependent Task", priority=1, status=TaskStatus.PENDING
        )
        task2 = task_factory.create(
            name="Dependency Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.post(
            f"/api/v1/tasks/{task1.id}/dependencies", json={"depends_on_id": task2.id}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert task2.id in data["depends_on"]

        # Verify in database
        updated_task = repository.get_by_id(task1.id)
        assert task2.id in updated_task.depends_on

    @pytest.mark.parametrize(
        "operation,method,endpoint,payload",
        [
            (
                "add_dependency",
                "POST",
                "/api/v1/tasks/999/dependencies",
                {"depends_on_id": 1},
            ),
            ("remove_dependency", "DELETE", "/api/v1/tasks/999/dependencies/1", None),
            ("set_tags", "PUT", "/api/v1/tasks/999/tags", {"tags": ["test"]}),
        ],
    )
    def test_relationship_operation_not_found(
        self, client, operation, method, endpoint, payload
    ):
        """Test relationship operations on non-existent task return 404."""
        if method == "POST":
            response = client.post(endpoint, json=payload)
        elif method == "DELETE":
            response = client.delete(endpoint)
        elif method == "PUT":
            response = client.put(endpoint, json=payload)

        assert response.status_code == 404

    def test_add_dependency_circular_returns_error(
        self, client, repository, task_factory
    ):
        """Test adding circular dependency returns 400."""
        # Arrange - Create chain: task1 -> task2
        task1 = task_factory.create(
            name="Task 1", priority=1, status=TaskStatus.PENDING
        )
        task2 = task_factory.create(
            name="Task 2", priority=1, status=TaskStatus.PENDING, depends_on=[task1.id]
        )

        # Act - Try to add task2 as dependency of task1 (creates cycle)
        response = client.post(
            f"/api/v1/tasks/{task1.id}/dependencies", json={"depends_on_id": task2.id}
        )

        # Assert
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_add_dependency_self_reference_returns_error(self, client, task_factory):
        """Test adding self as dependency returns 400."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.post(
            f"/api/v1/tasks/{task.id}/dependencies", json={"depends_on_id": task.id}
        )

        # Assert
        assert response.status_code == 400

    def test_remove_dependency_success(self, client, repository, task_factory):
        """Test removing a dependency from a task."""
        # Arrange
        task1 = task_factory.create(
            name="Dependency Task", priority=1, status=TaskStatus.PENDING
        )
        task2 = task_factory.create(
            name="Dependent Task",
            priority=1,
            status=TaskStatus.PENDING,
            depends_on=[task1.id],
        )

        # Act
        response = client.delete(f"/api/v1/tasks/{task2.id}/dependencies/{task1.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert task1.id not in data["depends_on"]

        # Verify in database
        updated_task = repository.get_by_id(task2.id)
        assert task1.id not in updated_task.depends_on

    def test_remove_nonexistent_dependency_returns_error(self, client, task_factory):
        """Test removing non-existent dependency returns 400."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act - Try to remove dependency that doesn't exist
        response = client.delete(f"/api/v1/tasks/{task.id}/dependencies/999")

        # Assert
        assert response.status_code == 400

    def test_set_task_tags_success(self, client, repository, task_factory):
        """Test setting task tags."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING, tags=[]
        )

        # Act
        response = client.put(
            f"/api/v1/tasks/{task.id}/tags", json={"tags": ["urgent", "bug"]}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert sorted(data["tags"]) == ["bug", "urgent"]

        # Verify in database
        updated_task = repository.get_by_id(task.id)
        assert sorted(updated_task.tags) == ["bug", "urgent"]

    def test_set_task_tags_replaces_existing(self, client, task_factory):
        """Test setting tags replaces existing tags."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING, tags=["old", "tag"]
        )

        # Act
        response = client.put(
            f"/api/v1/tasks/{task.id}/tags", json={"tags": ["new", "tags"]}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert sorted(data["tags"]) == ["new", "tags"]
        assert "old" not in data["tags"]

    def test_set_task_tags_empty_clears_tags(self, client, task_factory):
        """Test setting empty tags list clears all tags."""
        # Arrange
        task = task_factory.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["tag1", "tag2"],
        )

        # Act
        response = client.put(f"/api/v1/tasks/{task.id}/tags", json={"tags": []})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == []

    def test_set_task_tags_validation_error_empty_tag(self, client, task_factory):
        """Test setting tags with empty tag name returns 400 or 422."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.put(f"/api/v1/tasks/{task.id}/tags", json={"tags": [""]})

        # Assert
        assert response.status_code in [400, 422]
