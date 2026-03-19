"""Tests for update_helpers."""

from unittest.mock import Mock

from taskdog.cli.commands.update_helpers import execute_single_field_update


class TestExecuteSingleFieldUpdate:
    """Test cases for execute_single_field_update."""

    def test_calls_api_client_with_correct_field(self):
        mock_task = Mock()
        mock_result = Mock()
        mock_result.task = mock_task

        mock_api_client = Mock()
        mock_api_client.update_task.return_value = mock_result

        mock_ctx_obj = Mock()
        mock_ctx_obj.api_client = mock_api_client

        mock_ctx = Mock()
        mock_ctx.obj = mock_ctx_obj

        result = execute_single_field_update(
            mock_ctx, task_id=5, field_name="priority", field_value=3
        )

        mock_api_client.update_task.assert_called_once_with(task_id=5, priority=3)
        assert result == mock_task

    def test_calls_with_deadline_field(self):
        from datetime import datetime

        deadline = datetime(2026, 6, 1, 18, 0)
        mock_task = Mock()
        mock_result = Mock()
        mock_result.task = mock_task

        mock_api_client = Mock()
        mock_api_client.update_task.return_value = mock_result

        mock_ctx_obj = Mock()
        mock_ctx_obj.api_client = mock_api_client

        mock_ctx = Mock()
        mock_ctx.obj = mock_ctx_obj

        result = execute_single_field_update(
            mock_ctx, task_id=1, field_name="deadline", field_value=deadline
        )

        mock_api_client.update_task.assert_called_once_with(
            task_id=1, deadline=deadline
        )
        assert result == mock_task
