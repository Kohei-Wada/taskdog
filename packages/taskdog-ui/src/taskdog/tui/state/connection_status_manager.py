"""Connection status manager with observer pattern."""

import logging
from collections.abc import Callable
from datetime import datetime

from .connection_status import ConnectionStatus

logger = logging.getLogger(__name__)


class ConnectionStatusManager:
    """Manages connection status with observer pattern.

    This class is responsible for tracking API and WebSocket connection states
    and notifying observers when the status changes.
    """

    def __init__(self) -> None:
        """Initialize with disconnected status."""
        self._status = ConnectionStatus(
            is_api_connected=False,
            is_websocket_connected=False,
            last_update=datetime.now(),
        )
        self._observers: list[Callable[[ConnectionStatus], None]] = []

    @property
    def status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self._status

    @property
    def is_api_connected(self) -> bool:
        """Check if API is connected."""
        return self._status.is_api_connected

    @property
    def is_websocket_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._status.is_websocket_connected

    def subscribe(self, callback: Callable[[ConnectionStatus], None]) -> None:
        """Subscribe to connection status changes.

        Args:
            callback: Function to call when status changes.
        """
        self._observers.append(callback)

    def unsubscribe(self, callback: Callable[[ConnectionStatus], None]) -> None:
        """Unsubscribe from connection status changes.

        Args:
            callback: Previously subscribed callback to remove.
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def update(self, api_connected: bool, ws_connected: bool) -> None:
        """Update connection status and notify observers.

        Args:
            api_connected: Whether API server is connected.
            ws_connected: Whether WebSocket is connected.
        """
        self._status = ConnectionStatus(
            is_api_connected=api_connected,
            is_websocket_connected=ws_connected,
            last_update=datetime.now(),
        )
        self._notify_observers()

    def _notify_observers(self) -> None:
        """Notify all observers of the current status.

        Exceptions in individual callbacks are caught and logged
        to ensure all observers receive notifications.
        """
        for callback in self._observers:
            try:
                callback(self._status)
            except Exception:
                logger.exception("Error in connection status observer callback")
