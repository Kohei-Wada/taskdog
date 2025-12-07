"""Tests for AuditClient."""

from datetime import datetime
from unittest.mock import Mock

import pytest
from taskdog_client.audit_client import AuditClient


class TestAuditClientListAuditLogs:
    """Test cases for AuditClient.list_audit_logs."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = AuditClient(self.mock_base)

    def test_list_audit_logs_with_default_params(self) -> None:
        """Test list_audit_logs with only default parameters."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "logs": [],
            "total_count": 0,
            "limit": 100,
            "offset": 0,
        }
        self.mock_base._safe_request.return_value = mock_response

        result = self.client.list_audit_logs()

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        assert call_args[0][0] == "get"
        assert call_args[0][1] == "/api/v1/audit-logs"
        assert call_args[1]["params"]["limit"] == 100
        assert call_args[1]["params"]["offset"] == 0
        assert result.total_count == 0

    def test_list_audit_logs_with_all_filters(self) -> None:
        """Test list_audit_logs with all filter parameters."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "logs": [],
            "total_count": 0,
            "limit": 50,
            "offset": 10,
        }
        self.mock_base._safe_request.return_value = mock_response

        start_date = datetime(2025, 1, 1, 0, 0, 0)
        end_date = datetime(2025, 12, 31, 23, 59, 59)

        self.client.list_audit_logs(
            client_filter="test-client",
            operation="CREATE",
            resource_type="task",
            resource_id=123,
            success=True,
            start_date=start_date,
            end_date=end_date,
            limit=50,
            offset=10,
        )

        call_args = self.mock_base._safe_request.call_args
        params = call_args[1]["params"]

        assert params["client"] == "test-client"
        assert params["operation"] == "CREATE"
        assert params["resource_type"] == "task"
        assert params["resource_id"] == 123
        assert params["success"] == "true"
        assert params["start_date"] == start_date.isoformat()
        assert params["end_date"] == end_date.isoformat()
        assert params["limit"] == 50
        assert params["offset"] == 10

    def test_list_audit_logs_success_false_converted_to_lowercase(self) -> None:
        """Test that success=False is converted to 'false' string."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "logs": [],
            "total_count": 0,
            "limit": 100,
            "offset": 0,
        }
        self.mock_base._safe_request.return_value = mock_response

        self.client.list_audit_logs(success=False)

        call_args = self.mock_base._safe_request.call_args
        params = call_args[1]["params"]
        assert params["success"] == "false"

    def test_list_audit_logs_handles_error_response(self) -> None:
        """Test that error responses trigger error handler."""
        mock_response = Mock()
        mock_response.is_success = False
        self.mock_base._safe_request.return_value = mock_response
        self.mock_base._handle_error.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            self.client.list_audit_logs()

        self.mock_base._handle_error.assert_called_once_with(mock_response)

    def test_list_audit_logs_returns_logs(self) -> None:
        """Test that logs are correctly returned."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "logs": [
                {
                    "id": 1,
                    "timestamp": "2025-01-15T10:30:00",
                    "client_name": "cli",
                    "operation": "CREATE",
                    "resource_type": "task",
                    "resource_id": 42,
                    "resource_name": "Test Task",
                    "old_values": None,
                    "new_values": {"name": "Test Task"},
                    "success": True,
                    "error_message": None,
                },
                {
                    "id": 2,
                    "timestamp": "2025-01-15T11:00:00",
                    "client_name": "api",
                    "operation": "UPDATE",
                    "resource_type": "task",
                    "resource_id": 42,
                    "resource_name": "Test Task",
                    "old_values": {"priority": 50},
                    "new_values": {"priority": 100},
                    "success": True,
                    "error_message": None,
                },
            ],
            "total_count": 2,
            "limit": 100,
            "offset": 0,
        }
        self.mock_base._safe_request.return_value = mock_response

        result = self.client.list_audit_logs()

        assert len(result.logs) == 2
        assert result.logs[0].id == 1
        assert result.logs[0].operation == "CREATE"
        assert result.logs[1].id == 2
        assert result.logs[1].operation == "UPDATE"
        assert result.total_count == 2


class TestAuditClientGetAuditLog:
    """Test cases for AuditClient.get_audit_log."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = AuditClient(self.mock_base)

    def test_get_audit_log_success(self) -> None:
        """Test successful retrieval of audit log."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": 1,
            "timestamp": "2025-01-15T10:30:00",
            "client_name": "cli",
            "operation": "CREATE",
            "resource_type": "task",
            "resource_id": 42,
            "resource_name": "Test Task",
            "old_values": None,
            "new_values": {"name": "Test Task"},
            "success": True,
            "error_message": None,
        }
        self.mock_base._safe_request.return_value = mock_response

        result = self.client.get_audit_log(1)

        self.mock_base._safe_request.assert_called_once_with(
            "get", "/api/v1/audit-logs/1"
        )
        assert result is not None
        assert result.id == 1
        assert result.operation == "CREATE"

    def test_get_audit_log_not_found(self) -> None:
        """Test get_audit_log returns None for 404."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.is_success = False
        self.mock_base._safe_request.return_value = mock_response

        result = self.client.get_audit_log(999)

        assert result is None
        self.mock_base._handle_error.assert_not_called()

    def test_get_audit_log_handles_other_errors(self) -> None:
        """Test get_audit_log handles non-404 errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.is_success = False
        self.mock_base._safe_request.return_value = mock_response
        self.mock_base._handle_error.side_effect = Exception("Server Error")

        with pytest.raises(Exception, match="Server Error"):
            self.client.get_audit_log(1)

        self.mock_base._handle_error.assert_called_once_with(mock_response)

    def test_get_audit_log_returns_none_for_null_data(self) -> None:
        """Test get_audit_log returns None when response data is None."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = None
        self.mock_base._safe_request.return_value = mock_response

        result = self.client.get_audit_log(1)

        assert result is None


class TestAuditClientConvertToOutput:
    """Test cases for AuditClient._convert_to_output."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = AuditClient(self.mock_base)

    def test_converts_complete_data(self) -> None:
        """Test conversion of complete audit log data."""
        data = {
            "id": 1,
            "timestamp": "2025-01-15T10:30:00",
            "client_name": "test-client",
            "operation": "CREATE",
            "resource_type": "task",
            "resource_id": 42,
            "resource_name": "Test Task",
            "old_values": {"status": "PENDING"},
            "new_values": {"status": "COMPLETED"},
            "success": True,
            "error_message": None,
        }

        result = self.client._convert_to_output(data)

        assert result.id == 1
        assert result.timestamp == datetime(2025, 1, 15, 10, 30, 0)
        assert result.client_name == "test-client"
        assert result.operation == "CREATE"
        assert result.resource_type == "task"
        assert result.resource_id == 42
        assert result.resource_name == "Test Task"
        assert result.old_values == {"status": "PENDING"}
        assert result.new_values == {"status": "COMPLETED"}
        assert result.success is True
        assert result.error_message is None

    def test_converts_minimal_data(self) -> None:
        """Test conversion with minimal required fields."""
        data = {
            "id": 1,
            "timestamp": "2025-01-15T10:30:00",
            "operation": "DELETE",
            "resource_type": "task",
            "success": False,
        }

        result = self.client._convert_to_output(data)

        assert result.id == 1
        assert result.operation == "DELETE"
        assert result.resource_type == "task"
        assert result.success is False
        assert result.client_name is None
        assert result.resource_id is None
        assert result.resource_name is None
        assert result.old_values is None
        assert result.new_values is None
        assert result.error_message is None

    def test_handles_invalid_timestamp(self) -> None:
        """Test that invalid timestamp falls back to current time."""
        data = {
            "id": 1,
            "timestamp": "invalid-timestamp",
            "operation": "CREATE",
            "resource_type": "task",
            "success": True,
        }

        result = self.client._convert_to_output(data)

        # Should not raise, and should have a timestamp close to now
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)

    def test_handles_missing_timestamp(self) -> None:
        """Test that missing timestamp falls back to current time."""
        data = {
            "id": 1,
            "operation": "CREATE",
            "resource_type": "task",
            "success": True,
        }

        result = self.client._convert_to_output(data)

        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)

    def test_preserves_error_message(self) -> None:
        """Test that error message is preserved."""
        data = {
            "id": 1,
            "timestamp": "2025-01-15T10:30:00",
            "operation": "CREATE",
            "resource_type": "task",
            "success": False,
            "error_message": "Task not found",
        }

        result = self.client._convert_to_output(data)

        assert result.success is False
        assert result.error_message == "Task not found"


class TestAuditClientConvertToListOutput:
    """Test cases for AuditClient._convert_to_list_output."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = AuditClient(self.mock_base)

    def test_converts_list_with_pagination(self) -> None:
        """Test conversion of list output with pagination info."""
        data = {
            "logs": [
                {
                    "id": 1,
                    "timestamp": "2025-01-15T10:30:00",
                    "operation": "CREATE",
                    "resource_type": "task",
                    "success": True,
                },
                {
                    "id": 2,
                    "timestamp": "2025-01-15T11:00:00",
                    "operation": "UPDATE",
                    "resource_type": "task",
                    "success": True,
                },
            ],
            "total_count": 100,
            "limit": 50,
            "offset": 0,
        }

        result = self.client._convert_to_list_output(data)

        assert len(result.logs) == 2
        assert result.total_count == 100
        assert result.limit == 50
        assert result.offset == 0

    def test_converts_empty_list(self) -> None:
        """Test conversion of empty logs list."""
        data = {
            "logs": [],
            "total_count": 0,
            "limit": 100,
            "offset": 0,
        }

        result = self.client._convert_to_list_output(data)

        assert len(result.logs) == 0
        assert result.total_count == 0

    def test_all_logs_converted(self) -> None:
        """Test that all logs in list are converted."""
        data = {
            "logs": [
                {
                    "id": i,
                    "timestamp": "2025-01-15T10:30:00",
                    "operation": "CREATE",
                    "resource_type": "task",
                    "success": True,
                }
                for i in range(10)
            ],
            "total_count": 10,
            "limit": 100,
            "offset": 0,
        }

        result = self.client._convert_to_list_output(data)

        assert len(result.logs) == 10
        for i, log in enumerate(result.logs):
            assert log.id == i
