"""Tests for AuditLogController."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from taskdog_core.application.dto.audit_log_dto import (
    AuditEvent,
    AuditLogListOutput,
    AuditLogOutput,
    AuditQuery,
)
from taskdog_core.controllers.audit_log_controller import AuditLogController
from taskdog_core.domain.repositories.audit_log_repository import AuditLogRepository
from taskdog_core.domain.services.logger import Logger
from taskdog_core.domain.services.time_provider import ITimeProvider


class TestAuditLogController:
    """Test cases for AuditLogController."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=AuditLogRepository)
        self.logger = Mock(spec=Logger)
        self.time_provider = Mock(spec=ITimeProvider)
        self.controller = AuditLogController(
            self.repository, self.logger, self.time_provider
        )

    def test_save_delegates_to_repository(self):
        """Test that save delegates to repository.save."""
        event = AuditEvent(
            timestamp=datetime(2026, 1, 1, 12, 0),
            operation="create_task",
            resource_type="task",
            success=True,
            resource_id=1,
        )

        self.controller.save(event)

        self.repository.save.assert_called_once_with(event)

    def test_save_logs_debug_message(self):
        """Test that save calls logger.debug."""
        event = AuditEvent(
            timestamp=datetime(2026, 1, 1, 12, 0),
            operation="create_task",
            resource_type="task",
            success=True,
            resource_id=42,
        )

        self.controller.save(event)

        self.logger.debug.assert_called_once()
        log_message = self.logger.debug.call_args[0][0]
        assert "create_task" in log_message
        assert "task" in log_message
        assert "42" in log_message

    def test_log_operation_creates_event_with_correct_fields(self):
        """Test that log_operation constructs AuditEvent with correct fields."""
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

        saved_event = self.repository.save.call_args[0][0]
        assert saved_event.timestamp == fixed_time
        assert saved_event.operation == "complete_task"
        assert saved_event.resource_type == "task"
        assert saved_event.success is True
        assert saved_event.client_name == "test-client"
        assert saved_event.resource_id == 5
        assert saved_event.resource_name == "My Task"
        assert saved_event.old_values == {"status": "IN_PROGRESS"}
        assert saved_event.new_values == {"status": "COMPLETED"}
        assert saved_event.error_message is None

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
        saved_event = self.repository.save.call_args[0][0]
        assert saved_event.timestamp == injected_time

    def test_log_operation_optional_fields_default_to_none(self):
        """Test that optional fields are None when omitted."""
        self.time_provider.now.return_value = datetime(2026, 1, 1)

        self.controller.log_operation(
            operation="delete_task",
            resource_type="task",
            success=False,
        )

        saved_event = self.repository.save.call_args[0][0]
        assert saved_event.client_name is None
        assert saved_event.resource_id is None
        assert saved_event.resource_name is None
        assert saved_event.old_values is None
        assert saved_event.new_values is None
        assert saved_event.error_message is None

    def test_get_logs_delegates_to_repository(self):
        """Test that get_logs delegates to repository and returns its result."""
        query = AuditQuery(operation="create_task", limit=50)
        expected_output = AuditLogListOutput(
            logs=[
                AuditLogOutput(
                    id=1,
                    timestamp=datetime(2026, 1, 1),
                    client_name=None,
                    operation="create_task",
                    resource_type="task",
                    resource_id=1,
                    resource_name="Task 1",
                    old_values=None,
                    new_values=None,
                    success=True,
                    error_message=None,
                )
            ],
            total_count=1,
            limit=50,
            offset=0,
        )
        self.repository.get_logs.return_value = expected_output

        result = self.controller.get_logs(query)

        self.repository.get_logs.assert_called_once_with(query)
        assert result is expected_output

    def test_get_by_id_delegates_to_repository(self):
        """Test that get_by_id delegates to repository."""
        expected_output = AuditLogOutput(
            id=7,
            timestamp=datetime(2026, 1, 1),
            client_name="cli",
            operation="start_task",
            resource_type="task",
            resource_id=3,
            resource_name="Task 3",
            old_values=None,
            new_values=None,
            success=True,
            error_message=None,
        )
        self.repository.get_by_id.return_value = expected_output

        result = self.controller.get_by_id(7)

        self.repository.get_by_id.assert_called_once_with(7)
        assert result is expected_output

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
