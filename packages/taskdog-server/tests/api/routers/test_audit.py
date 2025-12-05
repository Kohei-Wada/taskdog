"""Tests for audit logs router."""

from datetime import datetime

from taskdog_core.application.dto.audit_log_dto import AuditEvent


class TestAuditLogsRouter:
    """Test cases for audit logs router endpoints."""

    def test_list_audit_logs_empty(self, client, audit_log_repository):
        """Test listing audit logs when there are none."""
        response = client.get("/api/v1/audit-logs")

        assert response.status_code == 200
        data = response.json()
        assert data["logs"] == []
        assert data["total_count"] == 0
        assert data["limit"] == 100
        assert data["offset"] == 0

    def test_list_audit_logs_after_task_creation(self, client, audit_log_repository):
        """Test that task creation generates an audit log."""
        # Arrange - create a task via API (which generates an audit log)
        response = client.post(
            "/api/v1/tasks",
            json={"name": "Audit Test Task", "priority": 5},
        )
        assert response.status_code == 201

        # Act - list audit logs
        response = client.get("/api/v1/audit-logs")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1

        # Find the create_task log
        create_logs = [log for log in data["logs"] if log["operation"] == "create_task"]
        assert len(create_logs) >= 1

        log = create_logs[0]
        assert log["resource_type"] == "task"
        assert log["success"] is True

    def test_list_audit_logs_filter_by_operation(
        self, client, task_factory, audit_log_repository
    ):
        """Test filtering audit logs by operation type."""
        # Arrange - create a specific audit log
        audit_log_repository.save(
            AuditEvent(
                timestamp=datetime.now(),
                client_name="test-client",
                operation="complete_task",
                resource_type="task",
                resource_id=100,
                resource_name="Test Task",
                old_values={"status": "IN_PROGRESS"},
                new_values={"status": "COMPLETED"},
                success=True,
                error_message=None,
            )
        )

        # Act - filter by operation
        response = client.get("/api/v1/audit-logs?operation=complete_task")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(log["operation"] == "complete_task" for log in data["logs"])

    def test_list_audit_logs_filter_by_client(self, client, audit_log_repository):
        """Test filtering audit logs by client name."""
        # Arrange - create audit logs with different clients
        audit_log_repository.save(
            AuditEvent(
                timestamp=datetime.now(),
                client_name="claude-code",
                operation="create_task",
                resource_type="task",
                resource_id=1,
                resource_name="Task 1",
                old_values=None,
                new_values={"name": "Task 1"},
                success=True,
                error_message=None,
            )
        )
        audit_log_repository.save(
            AuditEvent(
                timestamp=datetime.now(),
                client_name="web-ui",
                operation="create_task",
                resource_type="task",
                resource_id=2,
                resource_name="Task 2",
                old_values=None,
                new_values={"name": "Task 2"},
                success=True,
                error_message=None,
            )
        )

        # Act - filter by client
        response = client.get("/api/v1/audit-logs?client=claude-code")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(log["client_name"] == "claude-code" for log in data["logs"])

    def test_list_audit_logs_filter_by_resource_id(self, client, audit_log_repository):
        """Test filtering audit logs by resource ID."""
        # Arrange - create audit logs with different resource IDs
        for i in range(3):
            audit_log_repository.save(
                AuditEvent(
                    timestamp=datetime.now(),
                    client_name="test",
                    operation="update_task",
                    resource_type="task",
                    resource_id=200 + i,
                    resource_name=f"Task {200 + i}",
                    old_values=None,
                    new_values={"updated": True},
                    success=True,
                    error_message=None,
                )
            )

        # Act - filter by resource_id
        response = client.get("/api/v1/audit-logs?resource_id=201")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(log["resource_id"] == 201 for log in data["logs"])

    def test_list_audit_logs_pagination(self, client, audit_log_repository):
        """Test audit logs pagination."""
        # Arrange - create multiple audit logs
        for i in range(15):
            audit_log_repository.save(
                AuditEvent(
                    timestamp=datetime.now(),
                    client_name="test",
                    operation="test_operation",
                    resource_type="test",
                    resource_id=300 + i,
                    resource_name=f"Test {i}",
                    old_values=None,
                    new_values=None,
                    success=True,
                    error_message=None,
                )
            )

        # Act - get first page
        response1 = client.get("/api/v1/audit-logs?limit=5&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["logs"]) == 5
        assert data1["limit"] == 5
        assert data1["offset"] == 0

        # Act - get second page
        response2 = client.get("/api/v1/audit-logs?limit=5&offset=5")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["logs"]) == 5
        assert data2["offset"] == 5

        # Ensure different logs on different pages
        page1_ids = {log["id"] for log in data1["logs"]}
        page2_ids = {log["id"] for log in data2["logs"]}
        assert page1_ids.isdisjoint(page2_ids)

    def test_list_audit_logs_filter_by_success(self, client, audit_log_repository):
        """Test filtering audit logs by success status."""
        # Arrange - create success and failure logs
        audit_log_repository.save(
            AuditEvent(
                timestamp=datetime.now(),
                client_name="test",
                operation="success_op",
                resource_type="task",
                resource_id=400,
                resource_name="Success Task",
                old_values=None,
                new_values=None,
                success=True,
                error_message=None,
            )
        )
        audit_log_repository.save(
            AuditEvent(
                timestamp=datetime.now(),
                client_name="test",
                operation="failed_op",
                resource_type="task",
                resource_id=401,
                resource_name="Failed Task",
                old_values=None,
                new_values=None,
                success=False,
                error_message="Something went wrong",
            )
        )

        # Act - filter for failed only
        response = client.get("/api/v1/audit-logs?success=false")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(log["success"] is False for log in data["logs"])

    def test_get_audit_log_by_id(self, client, audit_log_repository):
        """Test getting a single audit log by ID."""
        # Arrange - create an audit log
        audit_log_repository.save(
            AuditEvent(
                timestamp=datetime.now(),
                client_name="test-client",
                operation="get_by_id_test",
                resource_type="task",
                resource_id=500,
                resource_name="Test Task",
                old_values={"old": "value"},
                new_values={"new": "value"},
                success=True,
                error_message=None,
            )
        )

        # Get the log to find its ID
        list_response = client.get("/api/v1/audit-logs?operation=get_by_id_test")
        logs = list_response.json()["logs"]
        assert len(logs) >= 1
        log_id = logs[0]["id"]

        # Act
        response = client.get(f"/api/v1/audit-logs/{log_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == log_id
        assert data["operation"] == "get_by_id_test"
        assert data["resource_id"] == 500
        assert data["old_values"] == {"old": "value"}
        assert data["new_values"] == {"new": "value"}

    def test_get_audit_log_nonexistent_returns_null(self, client):
        """Test getting a non-existent audit log returns null."""
        response = client.get("/api/v1/audit-logs/999999")

        # The endpoint returns None/null for non-existent logs
        assert response.status_code == 200
        assert response.json() is None
