"""Tests for tags router (tag management)."""

from taskdog_core.domain.entities.task import TaskStatus


class TestTagsRouter:
    """Test cases for tags router endpoints."""

    def test_delete_tag_success(self, client, repository, task_factory):
        """Test deleting a tag from the system."""
        # Arrange
        task_factory.create(
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent", "work"],
        )
        task_factory.create(
            name="Task 2", priority=1, status=TaskStatus.PENDING, tags=["urgent"]
        )

        # Act
        response = client.delete("/api/v1/tags/urgent")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tag_name"] == "urgent"
        assert data["affected_task_count"] == 2

    def test_delete_tag_preserves_other_tags(self, client, repository, task_factory):
        """Test deleting a tag preserves other tags on tasks."""
        # Arrange
        task = task_factory.create(
            name="Task 1",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent", "work"],
        )

        # Act
        client.delete("/api/v1/tags/urgent")

        # Assert - verify in database
        updated_task = repository.get_by_id(task.id)
        assert "work" in updated_task.tags
        assert "urgent" not in updated_task.tags

    def test_delete_tag_not_found(self, client):
        """Test deleting a non-existent tag returns 404."""
        # Act
        response = client.delete("/api/v1/tags/nonexistent")

        # Assert
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_delete_tag_single_task(self, client, repository, task_factory):
        """Test deleting a tag with single task association."""
        # Arrange
        task_factory.create(
            name="Task 1", priority=1, status=TaskStatus.PENDING, tags=["unique-tag"]
        )

        # Act
        response = client.delete("/api/v1/tags/unique-tag")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["affected_task_count"] == 1
