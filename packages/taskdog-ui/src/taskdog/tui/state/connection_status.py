"""Connection status data class."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionStatus:
    """Immutable connection status snapshot.

    Attributes:
        is_api_connected: Whether API server is connected and reachable.
        is_websocket_connected: Whether WebSocket connection is active.
    """

    is_api_connected: bool
    is_websocket_connected: bool
