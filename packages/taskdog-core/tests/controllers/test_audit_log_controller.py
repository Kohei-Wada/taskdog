"""Tests for AuditLogController."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from taskdog_core.application.dto.audit_log_dto import (
    AuditLogListOutput,
    AuditLogOutput,
)
from taskdog_core.controllers.audit_log_controller import AuditLogController
from taskdog_core.domain.entities.audit_log import AuditLog, AuditQuery
from taskdog_core.domain.repositories.audit_log_repository import AuditLogRepository
from taskdog_core.domain.services.time_provider import ITimeProvider


class TestAuditLogController:
    """Test cases for AuditLogController."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=AuditLogRepository)
        self.time_provider = Mock(spec=ITimeProvider)
        self.controller = AuditLogController(self.repository, self.time_provider)

    def test_save_delegates_to_repository(self):
        """Test that save delegates to repository.save."""
        log = AuditLog(
            timestamp=datetime(2026, 1, 1, 12, 0),
            operation="create_task",
            resource_type="task",
            success=True,
            resource_id=1,
        )

        self.controller.save(log)

        self.repository.save.assert_called_once_with(log)

    @patch("taskdog_core.controllers.audit_log_controller.logger")
    def test_save_logs_debug_message(self, mock_logger):
        """Test that save calls logger.debug."""
        log = AuditLog(
            timestamp=datetime(2026, 1, 1, 12, 0),
            operation="create_task",
            resource_type="task",
            success=True,
            resource_id=42,
        )

        self.controller.save(log)

        mock_logger.debug.assert_called_once()
        log_message = mock_logger.debug.call_args[0][0]
        assert "create_task" in log_message
        assert "task" in log_message
        assert "42" in log_message

    def test_log_operation_creates_log_with_correct_fields(self):
        """Test that log_operation constructs an AuditLog with correct fields."""
        fixed_time = datetime(2026, 2, 19, 10, 30)
        self.time_provider.now.return_value = fixed_time

        self.controller.log_operation(
            operation="complete_task",
            resource_type="task",
            success=True,
            client_name="test-client",
            resource_id=5,
            resource_name="My Task",
            old_values={"status": "IN_PROGRESS"},
            new_values={"status": "COMPLETED"},
        )

        saved = self.repository.save.call_args[0][0]
        assert isinstance(saved, AuditLog)
        assert saved.id is None
        assert saved.timestamp == fixed_time
        assert saved.operation == "complete_task"
        assert saved.resource_type == "task"
        assert saved.success is True
        assert saved.client_name == "test-client"
        assert saved.resource_id == 5
        assert saved.resource_name == "My Task"
        assert saved.old_values == {"status": "IN_PROGRESS"}
        assert saved.new_values == {"status": "COMPLETED"}
        assert saved.error_message is None

    def test_log_operation_uses_time_provider(self):
        """Test that log_operation uses time_provider.now(), not datetime.now()."""
        injected_time = datetime(2000, 1, 1, 0, 0)
        self.time_provider.now.return_value = injected_time

        self.controller.log_operation(
            operation="create_task",
            resource_type="task",
            success=True,
        )

        self.time_provider.now.assert_called_once()
        saved = self.repository.save.call_args[0][0]
        assert saved.timestamp == injected_time

    def test_log_operation_optional_fields_default_to_none(self):
        """Test that optional fields are None when omitted."""
        self.time_provider.now.return_value = datetime(2026, 1, 1)

        self.controller.log_operation(
            operation="delete_task",
            resource_type="task",
            success=False,
        )

        saved = self.repository.save.call_args[0][0]
        assert saved.client_name is None
        assert saved.resource_id is None
        assert saved.resource_name is None
        assert saved.old_values is None
        assert saved.new_values is None
        assert saved.error_message is None

    def test_get_logs_maps_entities_to_output(self):
        """get_logs maps repository entities into a paginated output DTO."""
        query = AuditQuery(operation="create_task", limit=50)
        self.repository.get_logs.return_value = [
            AuditLog(
                id=1,
                timestamp=datetime(2026, 1, 1),
                operation="create_task",
                resource_type="task",
                success=True,
                resource_id=1,
                resource_name="Task 1",
            )
        ]
        self.repository.count_logs.return_value = 1

        result = self.controller.get_logs(query)

        self.repository.get_logs.assert_called_once_with(query)
        self.repository.count_logs.assert_called_once_with(query)
        assert isinstance(result, AuditLogListOutput)
        assert result.total_count == 1
        assert result.limit == 50
        assert result.offset == 0
        assert len(result.logs) == 1
        assert isinstance(result.logs[0], AuditLogOutput)
        assert result.logs[0].id == 1
        assert result.logs[0].operation == "create_task"

    def test_get_by_id_maps_entity_to_output(self):
        """get_by_id maps the repository entity to an output DTO."""
        self.repository.get_by_id.return_value = AuditLog(
            id=7,
            timestamp=datetime(2026, 1, 1),
            operation="start_task",
            resource_type="task",
            success=True,
            client_name="cli",
            resource_id=3,
            resource_name="Task 3",
        )

        result = self.controller.get_by_id(7)

        self.repository.get_by_id.assert_called_once_with(7)
        assert isinstance(result, AuditLogOutput)
        assert result.id == 7
        assert result.operation == "start_task"

    def test_get_by_id_returns_none_when_not_found(self):
        """Test that get_by_id returns None when log is not found."""
        self.repository.get_by_id.return_value = None

        result = self.controller.get_by_id(999)

        self.repository.get_by_id.assert_called_once_with(999)
        assert result is None

    def test_count_logs_delegates_to_repository(self):
        """Test that count_logs delegates to repository."""
        query = AuditQuery(resource_type="task")
        self.repository.count_logs.return_value = 42

        result = self.controller.count_logs(query)

        self.repository.count_logs.assert_called_once_with(query)
        assert result == 42
