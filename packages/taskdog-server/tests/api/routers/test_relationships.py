"""Tests for relationships router (dependency and tag management)."""

import unittest
from datetime import date

from parameterized import parameterized

from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.test_base import BaseApiRouterTest


class TestRelationshipsRouter(BaseApiRouterTest):
    """Test cases for relationships router endpoints."""

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

    @parameterized.expand(
        [
            (
                "add_dependency",
                "POST",
                "/api/v1/tasks/999/dependencies",
                {"depends_on_id": 1},
            ),
            ("remove_dependency", "DELETE", "/api/v1/tasks/999/dependencies/1", None),
            ("set_tags", "PUT", "/api/v1/tasks/999/tags", {"tags": ["test"]}),
            ("log_hours", "POST", "/api/v1/tasks/999/log-hours", {"hours": 2.0}),
        ]
    )
    def test_relationship_operation_not_found(
        self, operation, method, endpoint, payload
    ):
        """Test relationship operations on non-existent task return 404."""
        if method == "POST":
            response = self.client.post(endpoint, json=payload)
        elif method == "DELETE":
            response = self.client.delete(endpoint)
        elif method == "PUT":
            response = self.client.put(endpoint, json=payload)

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
