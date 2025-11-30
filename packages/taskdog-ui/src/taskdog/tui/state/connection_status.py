"""Connection status data class."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConnectionStatus:
    """Immutable connection status snapshot.

    Attributes:
        is_api_connected: Whether API server is connected and reachable.
        is_websocket_connected: Whether WebSocket connection is active.
        last_update: Timestamp of the last status update.
    """

    is_api_connected: bool
    is_websocket_connected: bool
    last_update: datetime
