"""Tests for tasks router (CRUD endpoints)."""

from datetime import date

import pytest

from taskdog_core.domain.entities.task import TaskStatus


class TestTasksRouter:
    """Test cases for tasks router endpoints."""

    def test_create_task_success(self, client):
        """Test creating a new task successfully."""
        # Arrange
        request_data = {
            "name": "Test Task",
            "priority": 2,
            "tags": ["test", "api"],
        }

        # Act
        response = client.post("/api/v1/tasks", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Task"
        assert data["priority"] == 2
        assert data["status"] == "PENDING"
        assert set(data["tags"]) == {"test", "api"}
        assert data["id"] is not None

    def test_create_task_with_minimal_data(self, client):
        """Test creating task with only required fields."""
        # Arrange
        request_data = {"name": "Minimal Task"}

        # Act
        response = client.post("/api/v1/tasks", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Task"
        assert data["priority"] == 3  # Default from config

    def test_create_task_validation_error_empty_name(self, client):
        """Test creating task with empty name returns 400 or 422."""
        # Arrange
        request_data = {"name": ""}

        # Act
        response = client.post("/api/v1/tasks", json=request_data)

        # Assert
        assert response.status_code in [
            400,
            422,
        ]  # 422 from Pydantic, 400 from business logic
        assert "detail" in response.json()

    def test_create_task_validation_error_invalid_priority(self, client):
        """Test creating task with invalid priority returns 400 or 422."""
        # Arrange
        request_data = {"name": "Test Task", "priority": 0}

        # Act
        response = client.post("/api/v1/tasks", json=request_data)

        # Assert
        assert response.status_code in [400, 422]

    def test_list_tasks_empty(self, client):
        """Test listing tasks when none exist."""
        # Act
        response = client.get("/api/v1/tasks")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total_count"] == 0
        assert data["filtered_count"] == 0

    def test_list_tasks_returns_all_non_archived(self, client, task_factory):
        """Test listing tasks returns all non-archived tasks."""
        # Arrange
        task_factory.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        task_factory.create(name="Task 2", priority=2, status=TaskStatus.IN_PROGRESS)
        task_factory.create(
            name="Archived Task",
            priority=3,
            status=TaskStatus.PENDING,
            is_archived=True,
        )

        # Act
        response = client.get("/api/v1/tasks")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total_count"] == 3
        assert data["filtered_count"] == 2

    def test_list_tasks_with_all_flag_includes_archived(self, client, task_factory):
        """Test listing tasks with all=true includes archived tasks."""
        # Arrange
        task_factory.create(name="Task 1", priority=1, status=TaskStatus.PENDING)
        task_factory.create(
            name="Archived Task",
            priority=2,
            status=TaskStatus.PENDING,
            is_archived=True,
        )

        # Act
        response = client.get("/api/v1/tasks?all=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2

    def test_list_tasks_filter_by_status(self, client, task_factory):
        """Test filtering tasks by status."""
        # Arrange
        task_factory.create(name="Pending Task", priority=1, status=TaskStatus.PENDING)
        task_factory.create(
            name="Active Task", priority=2, status=TaskStatus.IN_PROGRESS
        )

        # Act
        response = client.get("/api/v1/tasks?status=PENDING")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["name"] == "Pending Task"

    def test_list_tasks_filter_by_tags(self, client, task_factory):
        """Test filtering tasks by tags."""
        # Arrange
        task_factory.create(
            name="Task 1", priority=1, status=TaskStatus.PENDING, tags=["urgent", "bug"]
        )
        task_factory.create(
            name="Task 2", priority=2, status=TaskStatus.PENDING, tags=["feature"]
        )

        # Act
        response = client.get("/api/v1/tasks?tags=urgent")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["name"] == "Task 1"

    def test_list_tasks_sort_by_priority(self, client, task_factory):
        """Test sorting tasks by priority."""
        # Arrange
        task_factory.create(name="Low Priority", priority=3, status=TaskStatus.PENDING)
        task_factory.create(name="High Priority", priority=1, status=TaskStatus.PENDING)

        # Act
        response = client.get("/api/v1/tasks?sort=priority")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Default sort is ascending (low to high priority numbers)
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["priority"] == 3
        assert data["tasks"][1]["priority"] == 1

    def test_get_task_success(self, client, task_factory):
        """Test getting a task by ID."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.get(f"/api/v1/tasks/{task.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task.id
        assert data["name"] == "Test Task"

    @pytest.mark.parametrize(
        "operation,method,endpoint,payload",
        [
            ("get_task", "GET", "/api/v1/tasks/999", None),
            ("update_task", "PATCH", "/api/v1/tasks/999", {"name": "New Name"}),
            ("archive_task", "POST", "/api/v1/tasks/999/archive", None),
            ("delete_task", "DELETE", "/api/v1/tasks/999", None),
        ],
    )
    def test_operation_not_found_returns_404(
        self, client, operation, method, endpoint, payload
    ):
        """Test operations on non-existent task return 404."""
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint)
        elif method == "PATCH":
            response = client.patch(endpoint, json=payload)
        elif method == "DELETE":
            response = client.delete(endpoint)

        assert response.status_code == 404
        if method != "DELETE":  # DELETE returns 204 with no content
            assert "detail" in response.json()

    def test_update_task_success(self, client, task_factory):
        """Test updating task fields."""
        # Arrange
        task = task_factory.create(
            name="Original Name", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.patch(
            f"/api/v1/tasks/{task.id}", json={"name": "Updated Name", "priority": 5}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["priority"] == 5
        assert "updated_fields" in data
        assert "name" in data["updated_fields"]
        assert "priority" in data["updated_fields"]

    def test_update_task_validation_error(self, client, task_factory):
        """Test updating task with invalid data returns 400 or 422."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act - Try to set invalid priority
        response = client.patch(f"/api/v1/tasks/{task.id}", json={"priority": 0})

        # Assert
        assert response.status_code in [400, 422]

    def test_archive_task_success(self, client, task_factory):
        """Test archiving a task."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.post(f"/api/v1/tasks/{task.id}/archive")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is True

    def test_restore_task_success(self, client, task_factory):
        """Test restoring an archived task."""
        # Arrange
        task = task_factory.create(
            name="Archived Task",
            priority=1,
            status=TaskStatus.PENDING,
            is_archived=True,
        )

        # Act
        response = client.post(f"/api/v1/tasks/{task.id}/restore")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is False

    def test_restore_task_not_archived_returns_error(self, client, task_factory):
        """Test restoring non-archived task returns 400."""
        # Arrange
        task = task_factory.create(
            name="Active Task", priority=1, status=TaskStatus.PENDING, is_archived=False
        )

        # Act
        response = client.post(f"/api/v1/tasks/{task.id}/restore")

        # Assert
        assert response.status_code == 400

    def test_delete_task_success(self, client, repository, task_factory):
        """Test permanently deleting a task."""
        # Arrange
        task = task_factory.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        response = client.delete(f"/api/v1/tasks/{task.id}")

        # Assert
        assert response.status_code == 204

        # Verify task is deleted
        deleted_task = repository.get_by_id(task.id)
        assert deleted_task is None

    def test_list_tasks_with_date_range_filter(self, client, task_factory):
        """Test filtering tasks by date range."""
        # Arrange
        task_factory.create(
            name="Early Task",
            priority=1,
            status=TaskStatus.PENDING,
            planned_start=date(2025, 1, 1),
            planned_end=date(2025, 1, 5),
        )
        task_factory.create(
            name="Late Task",
            priority=2,
            status=TaskStatus.PENDING,
            planned_start=date(2025, 2, 1),
            planned_end=date(2025, 2, 5),
        )

        # Act - Filter for January
        response = client.get("/api/v1/tasks?start_date=2025-01-01&end_date=2025-01-31")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["name"] == "Early Task"

    def test_list_tasks_with_reverse_sort(self, client, task_factory):
        """Test reverse sorting."""
        # Arrange
        task_factory.create(name="Task A", priority=1, status=TaskStatus.PENDING)
        task_factory.create(name="Task B", priority=2, status=TaskStatus.PENDING)

        # Act
        response = client.get("/api/v1/tasks?sort=priority&reverse=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        # Verify reverse order by checking priorities
        assert data["tasks"][0]["priority"] == 1
        assert data["tasks"][1]["priority"] == 2
