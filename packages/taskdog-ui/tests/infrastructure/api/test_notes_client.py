"""Tests for NotesClient."""

import unittest
from unittest.mock import Mock

from taskdog.infrastructure.api.notes_client import NotesClient


class TestNotesClient(unittest.TestCase):
    """Test cases for NotesClient."""

    def setUp(self):
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
        self.assertEqual(content, "# Notes\n\nSome content")
        self.assertTrue(has_notes)

    def test_get_task_notes_error(self):
        """Test get_task_notes handles errors."""
        from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        self.mock_base._safe_request.return_value = mock_response
        self.mock_base._handle_error.side_effect = TaskNotFoundException("Not found")

        with self.assertRaises(TaskNotFoundException):
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
        self.assertEqual(call_args[0][0], "put")
        self.assertEqual(call_args[0][1], "/api/v1/tasks/1/notes")
        self.assertEqual(call_args[1]["json"], {"content": "New notes"})

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

        self.assertTrue(result)
        self.mock_base._safe_request.assert_not_called()

    def test_has_task_notes_from_api(self):
        """Test has_task_notes queries API when not cached."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": "Notes", "has_notes": True}
        self.mock_base._safe_request.return_value = mock_response

        result = self.client.has_task_notes(task_id=1)

        self.assertTrue(result)
        # Should be cached now
        self.assertTrue(self.client._has_notes_cache[1])

    def test_cache_notes_info(self):
        """Test cache_notes_info stores info."""
        self.client.cache_notes_info(task_id=1, has_notes=True)

        self.assertTrue(self.client._has_notes_cache[1])

    def test_clear_cache(self):
        """Test clear_cache empties cache."""
        self.client._has_notes_cache[1] = True
        self.client._has_notes_cache[2] = False

        self.client.clear_cache()

        self.assertEqual(len(self.client._has_notes_cache), 0)


if __name__ == "__main__":
    unittest.main()
