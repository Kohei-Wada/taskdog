"""WebSocket client infrastructure.

This module re-exports WebSocket classes from taskdog_client
for backward compatibility.
"""

from taskdog_client import (  # type: ignore[import-not-found]
    ConnectionState,
    WebSocketClient,
)

__all__ = ["ConnectionState", "WebSocketClient"]
