"""Connection monitoring service for TUI."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taskdog_client import TaskdogApiClient, WebSocketClient

    from taskdog.tui.app import TaskdogTUI
    from taskdog.tui.state.connection_status_manager import ConnectionStatusManager


class ConnectionMonitor:
    """Monitors API and WebSocket connection status without blocking the UI.

    Uses run_worker to execute health checks in a background thread,
    preventing synchronous HTTP requests from freezing the event loop.
    """

    def __init__(
        self,
        app: TaskdogTUI,
        api_client: TaskdogApiClient,
        websocket_client: WebSocketClient,
        connection_manager: ConnectionStatusManager,
    ) -> None:
        self._app = app
        self._api_client = api_client
        self._websocket_client = websocket_client
        self._connection_manager = connection_manager

    def check(self) -> None:
        """Dispatch connection check to a background thread."""
        self._app.run_worker(self._check_worker(), exclusive=True)

    async def _check_worker(self) -> None:
        """Check API and WebSocket connection status in background."""
        api_connected = await asyncio.to_thread(self._api_client.check_health)
        ws_connected = self._websocket_client.is_connected()
        self._connection_manager.update(api_connected, ws_connected)
