"""Tests for LifecycleClient."""

from unittest.mock import Mock

import pytest
from taskdog_client.lifecycle_client import LifecycleClient


class TestLifecycleClient:
    """Test cases for LifecycleClient."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = LifecycleClient(self.mock_base)

    @pytest.mark.parametrize(
        "method_name,expected_operation",
        [
            ("start_task", "start"),
            ("complete_task", "complete"),
            ("pause_task", "pause"),
            ("cancel_task", "cancel"),
            ("reopen_task", "reopen"),
        ],
        ids=["start_task", "complete_task", "pause_task", "cancel_task", "reopen_task"],
    )
    def test_lifecycle_operation_delegates_to_base(
        self, method_name, expected_operation
    ):
        """Test lifecycle operations delegate to base client."""
        mock_output = Mock()
        self.mock_base.lifecycle_operation.return_value = mock_output

        method = getattr(self.client, method_name)
        result = method(task_id=1)

        self.mock_base.lifecycle_operation.assert_called_once_with(
            1, expected_operation
        )
        assert result == mock_output

    def test_lifecycle_operation_error_handling(self):
        """Test lifecycle operations propagate errors from base client."""
        from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException

        self.mock_base.lifecycle_operation.side_effect = TaskNotFoundException(
            "Task not found"
        )

        with pytest.raises(TaskNotFoundException):
            self.client.start_task(task_id=999)
