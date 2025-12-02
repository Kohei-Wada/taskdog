"""Base HTTP client infrastructure for Taskdog API."""

import contextlib
from collections.abc import Callable
from typing import Any

import httpx  # type: ignore[import-not-found]

from taskdog_core.domain.exceptions.task_exceptions import (
    AuthenticationError,
    ServerConnectionError,
    ServerError,
    TaskNotFoundException,
    TaskValidationError,
)


class BaseApiClient:
    """Base HTTP client with error handling and lifecycle management.

    Provides:
    - HTTP client initialization and lifecycle
    - Context manager support
    - Error mapping to domain exceptions
    - Safe request execution with connection handling
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 30.0,
        api_key: str | None = None,
    ):
        """Initialize base API client.

        Args:
            base_url: Base URL of the API server
            timeout: Request timeout in seconds
            api_key: API key for authentication (sent as X-Api-Key header)
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)
        self.client_id: str | None = None  # Set by WebSocket connection
        self.api_key = api_key

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "BaseApiClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses.

        Args:
            response: HTTP response

        Raises:
            TaskNotFoundException: If status is 404
            TaskValidationError: If status is 400
            Exception: For other errors
        """
        if response.status_code == 404:
            detail = response.json().get("detail", "Task not found")
            raise TaskNotFoundException(detail)
        elif response.status_code == 400:
            detail = response.json().get("detail", "Validation error")
            raise TaskValidationError(detail)
        elif response.status_code == 401:
            raise AuthenticationError("Authentication failed. Check your API key.")
        elif response.status_code >= 500:
            detail = "Server error occurred"
            with contextlib.suppress(Exception):
                detail = response.json().get("detail", detail)
            raise ServerError(response.status_code, detail)
        else:
            response.raise_for_status()

    def _safe_request(self, method: str, *args: Any, **kwargs: Any) -> httpx.Response:
        """Execute HTTP request with connection error handling.

        Args:
            method: HTTP method name ('get', 'post', 'patch', 'delete', 'put')
            *args: Positional arguments for the request
            **kwargs: Keyword arguments for the request

        Returns:
            HTTP response

        Raises:
            ServerConnectionError: If connection to server fails
            TaskNotFoundException: If status is 404
            TaskValidationError: If status is 400
            Exception: For other errors
        """
        try:
            headers = kwargs.get("headers", {})

            # Add X-Client-ID header if client_id is set
            if self.client_id:
                headers["X-Client-ID"] = self.client_id

            # Add X-Api-Key header if api_key is set
            if self.api_key:
                headers["X-Api-Key"] = self.api_key

            if headers:
                kwargs["headers"] = headers

            request_method: Callable[..., httpx.Response] = getattr(self.client, method)
            return request_method(*args, **kwargs)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            raise ServerConnectionError(self.base_url, e) from e
