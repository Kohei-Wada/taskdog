"""Tests for BaseApiClient."""

import unittest
from unittest.mock import Mock, patch

import httpx
from parameterized import parameterized

from taskdog.infrastructure.api.base_client import BaseApiClient
from taskdog_core.domain.exceptions.task_exceptions import (
    ServerConnectionError,
    TaskNotFoundException,
    TaskValidationError,
)


class TestBaseApiClient(unittest.TestCase):
    """Test cases for BaseApiClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "http://test.example.com"
        self.timeout = 10.0

    def test_init(self):
        """Test client initialization."""
        client = BaseApiClient(self.base_url, self.timeout)

        self.assertEqual(client.base_url, self.base_url)
        self.assertIsInstance(client.client, httpx.Client)

    def test_init_strips_trailing_slash(self):
        """Test base URL trailing slash is stripped."""
        client = BaseApiClient("http://test.example.com/", self.timeout)

        self.assertEqual(client.base_url, "http://test.example.com")

    def test_context_manager(self):
        """Test context manager protocol."""
        with BaseApiClient(self.base_url, self.timeout) as client:
            self.assertIsInstance(client, BaseApiClient)

    @patch("taskdog.infrastructure.api.base_client.httpx.Client")
    def test_close(self, mock_client_class):
        """Test close method closes underlying client."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        client = BaseApiClient(self.base_url, self.timeout)
        client.close()

        mock_client_instance.close.assert_called_once()

    @parameterized.expand(
        [
            ("404_error", 404, TaskNotFoundException, "Task not found"),
            ("400_error", 400, TaskValidationError, "Validation failed"),
        ]
    )
    def test_handle_error_status_codes(
        self, scenario, status_code, expected_exception, detail_message
    ):
        """Test _handle_error raises appropriate exceptions for error status codes."""
        client = BaseApiClient(self.base_url, self.timeout)
        response = Mock()
        response.status_code = status_code
        response.json.return_value = {"detail": detail_message}

        with self.assertRaises(expected_exception) as cm:
            client._handle_error(response)

        self.assertIn(detail_message, str(cm.exception))

    def test_handle_error_other_status(self):
        """Test _handle_error calls raise_for_status for other errors."""
        client = BaseApiClient(self.base_url, self.timeout)
        response = Mock()
        response.status_code = 500
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=response
        )

        with self.assertRaises(httpx.HTTPStatusError):
            client._handle_error(response)

        response.raise_for_status.assert_called_once()

    @patch.object(BaseApiClient, "_handle_error")
    def test_safe_request_success(self, mock_handle_error):
        """Test _safe_request executes successful request."""
        client = BaseApiClient(self.base_url, self.timeout)
        mock_response = Mock()
        mock_response.status_code = 200
        client.client.get = Mock(return_value=mock_response)

        response = client._safe_request("get", "/test")

        self.assertEqual(response, mock_response)
        mock_handle_error.assert_not_called()

    @parameterized.expand(
        [
            ("connect_error", httpx.ConnectError("Connection failed"), True),
            ("timeout_error", httpx.TimeoutException("Timeout"), False),
            ("request_error", httpx.RequestError("Request failed"), False),
        ]
    )
    def test_safe_request_connection_errors(
        self, scenario, exception_to_raise, should_check_base_url
    ):
        """Test _safe_request raises ServerConnectionError on connection failures."""
        client = BaseApiClient(self.base_url, self.timeout)
        client.client.get = Mock(side_effect=exception_to_raise)

        with self.assertRaises(ServerConnectionError) as cm:
            client._safe_request("get", "/test")

        if should_check_base_url:
            self.assertIn(self.base_url, str(cm.exception))

    def test_safe_request_calls_correct_method(self):
        """Test _safe_request calls the specified HTTP method."""
        client = BaseApiClient(self.base_url, self.timeout)

        for method in ["get", "post", "patch", "delete", "put"]:
            mock_response = Mock()
            setattr(client.client, method, Mock(return_value=mock_response))

            client._safe_request(method, "/test", param="value")

            getattr(client.client, method).assert_called_once_with(
                "/test", param="value"
            )


if __name__ == "__main__":
    unittest.main()
