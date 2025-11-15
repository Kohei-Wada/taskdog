"""WebSocket client for real-time task notifications.

This module provides a WebSocket client that connects to the taskdog-server
and receives real-time notifications about task changes.
"""

import asyncio
import contextlib
import json
from collections.abc import Callable
from typing import Any

from textual import log

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

    def __init__(self, ws_url: str, on_message: Callable[[dict[str, Any]], None]):
        """Initialize the WebSocket client.

        Args:
            ws_url: WebSocket URL (e.g., "ws://127.0.0.1:8000/ws")
            on_message: Callback function called when a message is received
        """
        if not WEBSOCKETS_AVAILABLE:
            log.warning("websockets library not available, real-time sync disabled")

        self.ws_url = ws_url
        self.on_message = on_message
        self._websocket: Any = None
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        """Connect to the WebSocket server and start listening.

        This method starts a background task that maintains the WebSocket
        connection and processes incoming messages.
        """
        if not WEBSOCKETS_AVAILABLE:
            log.warning("Cannot connect: websockets library not available")
            return

        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run())

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server.

        Stops the background task and closes the WebSocket connection.
        """
        self._running = False

        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._websocket and WEBSOCKETS_AVAILABLE:
            with contextlib.suppress(Exception):
                await self._websocket.close()
            self._websocket = None

    async def _run(self) -> None:
        """Main loop for WebSocket connection.

        Maintains the connection and processes incoming messages.
        Automatically reconnects if the connection is lost.
        """
        reconnect_delay = 1.0
        max_reconnect_delay = 30.0

        while self._running:
            try:
                async with websockets.connect(self.ws_url) as websocket:  # type: ignore
                    self._websocket = websocket
                    # Connection successful, reset reconnect delay
                    reconnect_delay = 1.0
                    log.info("WebSocket connected")

                    # Process messages
                    async for message_str in websocket:
                        if not self._running:
                            break

                        try:
                            message = json.loads(message_str)
                            self.on_message(message)
                        except json.JSONDecodeError:
                            log.warning(f"Invalid JSON received: {message_str!r}")
                        except Exception as e:
                            log.error(f"Error processing message: {e}")

            except Exception as e:
                self._websocket = None
                if self._running:
                    log.warning(f"WebSocket error: {e}, reconnecting...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                else:
                    break

    def is_connected(self) -> bool:
        """Check if the WebSocket is currently connected.

        Returns:
            True if connected, False otherwise
        """
        return self._running and self._websocket is not None
