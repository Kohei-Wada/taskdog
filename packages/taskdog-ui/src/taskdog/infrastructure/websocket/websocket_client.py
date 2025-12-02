"""WebSocket client for real-time task notifications.

This module provides a WebSocket client that connects to the taskdog-server
and receives real-time notifications about task changes.
"""

import asyncio
import contextlib
import json
from collections.abc import Callable
from enum import Enum, auto
from typing import Any

from textual import log


class ConnectionState(Enum):
    """WebSocket connection state."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()


try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None  # type: ignore


class WebSocketClient:
    """WebSocket client for receiving real-time task notifications.

    This client connects to the taskdog-server's WebSocket endpoint and
    listens for task change events. When events are received, it calls
    the registered callback function.
    """

    def __init__(
        self,
        ws_url: str,
        on_message: Callable[[dict[str, Any]], None],
        api_key: str | None = None,
    ):
        """Initialize the WebSocket client.

        Args:
            ws_url: WebSocket URL (e.g., "ws://127.0.0.1:8000/ws")
            on_message: Callback function called when a message is received
            api_key: Optional API key for authentication (sent as X-Api-Key header)
        """
        if not WEBSOCKETS_AVAILABLE:
            log.warning("websockets library not available, real-time sync disabled")

        self.ws_url = ws_url
        self.on_message = on_message
        self.api_key = api_key
        self._websocket: Any = None
        self._state = ConnectionState.DISCONNECTED
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        self.client_id: str | None = None  # Received from server on connection

    async def connect(self) -> None:
        """Connect to the WebSocket server and start listening.

        This method starts a background task that maintains the WebSocket
        connection and processes incoming messages.
        """
        if not WEBSOCKETS_AVAILABLE:
            log.warning("Cannot connect: websockets library not available")
            return

        async with self._lock:
            if self._state != ConnectionState.DISCONNECTED:
                return

            self._state = ConnectionState.CONNECTING
            self._task = asyncio.create_task(self._run())

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server.

        Stops the background task and closes the WebSocket connection.
        """
        task_to_cancel: asyncio.Task[None] | None = None
        websocket_to_close: Any = None

        async with self._lock:
            if self._state == ConnectionState.DISCONNECTED:
                return

            self._state = ConnectionState.DISCONNECTED
            task_to_cancel = self._task
            self._task = None
            websocket_to_close = self._websocket
            self._websocket = None

        # Cancel task and close websocket outside the lock to avoid deadlock
        if task_to_cancel:
            task_to_cancel.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task_to_cancel

        if websocket_to_close and WEBSOCKETS_AVAILABLE:
            with contextlib.suppress(Exception):
                await websocket_to_close.close()

    def _process_message(self, message_str: str | bytes) -> None:
        """Process a single WebSocket message."""
        try:
            message = json.loads(message_str)

            # Store client ID from connection message
            if message.get("type") == "connected":
                self.client_id = message.get("client_id")
                log.info(f"Received client ID: {self.client_id}")

            self.on_message(message)
        except json.JSONDecodeError:
            log.warning(f"Invalid JSON received: {message_str!r}")
        except Exception as e:
            log.error(f"Error processing message: {e}")

    async def _handle_connection_error(
        self, error: Exception, reconnect_delay: float, max_reconnect_delay: float
    ) -> tuple[bool, float]:
        """Handle connection error and determine if reconnection should occur."""
        self._websocket = None
        should_reconnect = False
        async with self._lock:
            if self._state != ConnectionState.DISCONNECTED:
                self._state = ConnectionState.RECONNECTING
                should_reconnect = True
        if should_reconnect:
            log.warning(f"WebSocket error: {error}, reconnecting...")
            await asyncio.sleep(reconnect_delay)
            return True, min(reconnect_delay * 2, max_reconnect_delay)
        return False, reconnect_delay

    async def _run(self) -> None:
        """Main loop for WebSocket connection.

        Maintains the connection and processes incoming messages.
        Automatically reconnects if the connection is lost.
        """
        reconnect_delay = 1.0
        max_reconnect_delay = 30.0

        while self._state != ConnectionState.DISCONNECTED:
            try:
                # Build extra headers for authentication
                extra_headers = {}
                if self.api_key:
                    extra_headers["X-Api-Key"] = self.api_key

                async with websockets.connect(
                    self.ws_url, extra_headers=extra_headers or None
                ) as websocket:  # type: ignore[attr-defined]
                    self._websocket = websocket
                    async with self._lock:
                        # State may have changed to DISCONNECTED during connection
                        if self._state != ConnectionState.DISCONNECTED:  # type: ignore[comparison-overlap]
                            self._state = ConnectionState.CONNECTED
                    reconnect_delay = 1.0
                    log.info("WebSocket connected")

                    async for message_str in websocket:
                        if self._state == ConnectionState.DISCONNECTED:
                            break
                        self._process_message(message_str)

            except Exception as e:
                should_continue, reconnect_delay = await self._handle_connection_error(
                    e, reconnect_delay, max_reconnect_delay
                )
                if not should_continue:
                    break

    def is_connected(self) -> bool:
        """Check if the WebSocket is currently connected.

        Returns:
            True if connected, False otherwise
        """
        return self._state == ConnectionState.CONNECTED
