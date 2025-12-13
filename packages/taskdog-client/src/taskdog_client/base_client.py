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

    def _extract_validation_error_detail(self, response: httpx.Response) -> str:
        """Extract validation error detail from response.

        Handles both simple {"detail": "message"} and FastAPI's Pydantic format:
        {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}

        Args:
            response: HTTP response with validation error

        Returns:
            Human-readable error message
        """
        try:
            data = response.json()
            detail = data.get("detail", "Validation error")

            # Handle FastAPI's Pydantic validation error format (list of errors)
            if isinstance(detail, list) and len(detail) > 0:
                messages = []
                for error in detail:
                    if isinstance(error, dict):
                        msg = error.get("msg", "")
                        loc = error.get("loc", [])
                        # Format: "field: message"
                        field = loc[-1] if loc else "field"
                        messages.append(f"{field}: {msg}")
                    else:
                        messages.append(str(error))
                return "; ".join(messages)

            return str(detail)
        except Exception:
            return "Validation error"

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses.

        Args:
            response: HTTP response

        Raises:
            TaskNotFoundException: If status is 404
            TaskValidationError: If status is 400 or 422
            Exception: For other errors
        """
        if response.status_code == 404:
            detail = response.json().get("detail", "Task not found")
            raise TaskNotFoundException(detail)
        elif response.status_code in (400, 422):
            detail = self._extract_validation_error_detail(response)
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

    def _request_json(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Execute HTTP request and return JSON response, handling errors.

        Combines _safe_request + error check + JSON parsing into one call.

        Args:
            method: HTTP method name ('get', 'post', 'patch', 'delete', 'put')
            *args: Positional arguments for the request
            **kwargs: Keyword arguments for the request

        Returns:
            Parsed JSON response (dict, list, or primitive)

        Raises:
            ServerConnectionError: If connection to server fails
            TaskNotFoundException: If status is 404
            TaskValidationError: If status is 400 or 422
            AuthenticationError: If status is 401
            ServerError: If status >= 500
        """
        response = self._safe_request(method, *args, **kwargs)
        if not response.is_success:
            self._handle_error(response)
        return response.json()

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
