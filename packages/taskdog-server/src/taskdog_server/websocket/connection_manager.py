"""WebSocket connection manager for real-time task updates.

This module manages active WebSocket connections and broadcasts
task change events to all connected clients.
"""

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events to clients."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self.active_connections: dict[str, WebSocket] = {}  # client_id -> WebSocket
        self.client_user_names: dict[str, str] = {}  # client_id -> user_name

    async def connect(
        self, client_id: str, websocket: WebSocket, user_name: str | None = None
    ) -> None:
        """Accept a new WebSocket connection.

        Args:
            client_id: Unique client identifier
            websocket: The WebSocket connection to accept
            user_name: Optional user name from X-User-Name header
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        if user_name:
            self.client_user_names[client_id] = user_name
        logger.info(
            f"WebSocket client connected: {client_id} (user: {user_name or 'anonymous'}, total: {len(self.active_connections)})"
        )

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection.

        Args:
            client_id: Client identifier to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            if client_id in self.client_user_names:
                del self.client_user_names[client_id]
            logger.info(
                f"WebSocket client disconnected: {client_id} (remaining: {
                    len(self.active_connections)
                })"
            )

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: The message dictionary to broadcast
        """
        # Remove disconnected clients while broadcasting
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except (ConnectionError, RuntimeError) as e:
                # Connection is broken, mark for removal
                logger.warning(
                    f"Failed to send message to client {client_id}: {e}. Marking for disconnection."
                )
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    async def send_personal_message(
        self, message: dict[str, Any], client_id: str
    ) -> None:
        """Send a message to a specific client.

        Args:
            message: The message dictionary to send
            client_id: The target client identifier
        """
        if client_id not in self.active_connections:
            return

        try:
            await self.active_connections[client_id].send_json(message)
        except (ConnectionError, RuntimeError) as e:
            # Connection is broken, remove it
            logger.warning(
                f"Failed to send personal message to client {client_id}: {e}. Disconnecting."
            )
            self.disconnect(client_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections.

        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)
