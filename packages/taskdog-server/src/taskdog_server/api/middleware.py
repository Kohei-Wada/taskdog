"""FastAPI middleware for request/response logging."""

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("taskdog_server.api.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses.

    Logs:
    - Request method and path
    - Response status code
    - Request processing time in milliseconds
    - Error details with stack trace for 5xx responses
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and log details.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response: The HTTP response
        """
        # Record start time
        start_time = time.time()

        # Extract request details
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = (time.time() - start_time) * 1000  # Convert to ms

            # Log successful request
            logger.info(
                f"{method} {path} - {response.status_code} - {process_time:.2f}ms",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time, 2),
                    "client_host": client_host,
                },
            )

            return response

        except Exception as exc:
            # Calculate processing time
            process_time = (time.time() - start_time) * 1000

            # Log error with stack trace
            logger.error(
                f"{method} {path} - ERROR - {process_time:.2f}ms",
                exc_info=True,
                extra={
                    "method": method,
                    "path": path,
                    "process_time_ms": round(process_time, 2),
                    "client_host": client_host,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )

            # Re-raise the exception to let FastAPI's exception handlers deal with it
            raise
