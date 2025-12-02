"""Tests for NotesClient."""

from unittest.mock import Mock

import pytest

from taskdog.infrastructure.api.notes_client import NotesClient
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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "# Notes\n\nSome content",
            "has_notes": True,
        }
        self.mock_base._safe_request.return_value = mock_response

        content, has_notes = self.client.get_task_notes(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "get", "/api/v1/tasks/1/notes"
        )
        assert content == "# Notes\n\nSome content"
        assert has_notes is True

    def test_get_task_notes_error(self):
        """Test get_task_notes handles errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        self.mock_base._safe_request.return_value = mock_response
        self.mock_base._handle_error.side_effect = TaskNotFoundException("Not found")

        with pytest.raises(TaskNotFoundException):
            self.client.get_task_notes(task_id=999)

        self.mock_base._handle_error.assert_called_once_with(mock_response)

    def test_update_task_notes(self):
        """Test update_task_notes makes correct API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_base._safe_request.return_value = mock_response

        self.client.update_task_notes(task_id=1, content="New notes")

        self.mock_base._safe_request.assert_called_once()
        call_args = self.mock_base._safe_request.call_args
        assert call_args[0][0] == "put"
        assert call_args[0][1] == "/api/v1/tasks/1/notes"
        assert call_args[1]["json"] == {"content": "New notes"}

    def test_delete_task_notes(self):
        """Test delete_task_notes makes correct API call."""
        mock_response = Mock()
        mock_response.status_code = 204
        self.mock_base._safe_request.return_value = mock_response

        self.client.delete_task_notes(task_id=1)

        self.mock_base._safe_request.assert_called_once_with(
            "delete", "/api/v1/tasks/1/notes"
        )

    def test_has_task_notes_from_cache(self):
        """Test has_task_notes uses cache."""
        self.client._has_notes_cache[1] = True

        result = self.client.has_task_notes(task_id=1)

        assert result is True
        self.mock_base._safe_request.assert_not_called()

    def test_has_task_notes_from_api(self):
        """Test has_task_notes queries API when not cached."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": "Notes", "has_notes": True}
        self.mock_base._safe_request.return_value = mock_response

        result = self.client.has_task_notes(task_id=1)

        assert result is True
        # Should be cached now
        assert self.client._has_notes_cache[1] is True

    def test_cache_notes_info(self):
        """Test cache_notes_info stores info."""
        self.client.cache_notes_info(task_id=1, has_notes=True)

        assert self.client._has_notes_cache[1] is True

    def test_clear_cache(self):
        """Test clear_cache empties cache."""
        self.client._has_notes_cache[1] = True
        self.client._has_notes_cache[2] = False

        self.client.clear_cache()

        assert len(self.client._has_notes_cache) == 0
