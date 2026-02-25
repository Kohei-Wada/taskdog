"""Tests for NotesClient."""

from unittest.mock import Mock

import pytest
from taskdog_client.notes_client import NotesClient

from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException


class TestNotesClient:
    """Test cases for NotesClient."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.client = NotesClient(self.mock_base)

    def test_get_task_notes(self):
        """Test get_task_notes makes correct API call."""
        self.mock_base._request_json.return_value = {
            "content": "# Notes\n\nSome content",
            "has_notes": True,
        }

        content, has_notes = self.client.get_task_notes(task_id=1)

        self.mock_base._request_json.assert_called_once_with(
            "get", "/api/v1/tasks/1/notes"
        )
        assert content == "# Notes\n\nSome content"
        assert has_notes is True

    def test_get_task_notes_error(self):
        """Test get_task_notes handles errors."""
        self.mock_base._request_json.side_effect = TaskNotFoundException("Not found")

        with pytest.raises(TaskNotFoundException):
            self.client.get_task_notes(task_id=999)

    def test_update_task_notes(self):
        """Test update_task_notes makes correct API call."""
        self.mock_base._request_json.return_value = {"status": "ok"}

        self.client.update_task_notes(task_id=1, content="New notes")

        self.mock_base._request_json.assert_called_once_with(
            "put", "/api/v1/tasks/1/notes", json={"content": "New notes"}
        )

    def test_delete_task_notes(self):
        """Test delete_task_notes makes correct API call."""
        mock_response = Mock()
        mock_response.is_success = True
        self.mock_base._safe_request.return_value = mock_response

        self.client.delete_task_notes(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "delete", "/api/v1/tasks/1/notes"
        )
