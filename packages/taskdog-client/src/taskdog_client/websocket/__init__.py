"""WebSocket client infrastructure for Taskdog server communication."""

from taskdog_client.websocket.websocket_client import (
    ConnectionState,
    WebSocketClient,
)

__all__ = ["ConnectionState", "WebSocketClient"]
