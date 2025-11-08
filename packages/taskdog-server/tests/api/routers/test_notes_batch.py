"""Tests for batch notes endpoint."""

import unittest

from fastapi.testclient import TestClient

from taskdog_server.api.app import create_app


class TestBatchNotesEndpoint(unittest.TestCase):
    """Test cases for batch notes endpoint."""

    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_batch_notes_endpoint_exists(self):
        """Test that the batch notes endpoint is registered."""
        # Get all routes
        routes = [route.path for route in self.app.routes if hasattr(route, "path")]

        # Check that the batch endpoint exists
        self.assertIn("/api/v1/tasks/notes/batch", routes)

    def test_batch_notes_empty_list(self):
        """Test batch notes with empty task list."""
        # No ids parameter should return validation error
        response = self.client.get("/api/v1/tasks/notes/batch")
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_batch_notes_endpoint_format(self):
        """Test batch notes endpoint returns correct format."""
        # This test requires a running database, so we'll just check the route exists
        # and returns the expected structure (even if tasks don't exist)
        response = self.client.get("/api/v1/tasks/notes/batch?ids=999")

        # Should return 200 with notes_status field
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("notes_status", data)
        self.assertIsInstance(data["notes_status"], dict)


if __name__ == "__main__":
    unittest.main()
