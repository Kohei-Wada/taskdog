"""Tests for WebSocketClient."""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from taskdog.infrastructure.websocket.websocket_client import (
    ConnectionState,
    WebSocketClient,
)


class TestConnectionState(unittest.TestCase):
    """Tests for ConnectionState enum."""

    def test_states_exist(self) -> None:
        """Test that all expected states exist."""
        self.assertIsNotNone(ConnectionState.DISCONNECTED)
        self.assertIsNotNone(ConnectionState.CONNECTING)
        self.assertIsNotNone(ConnectionState.CONNECTED)
        self.assertIsNotNone(ConnectionState.RECONNECTING)


class TestWebSocketClientInit(unittest.TestCase):
    """Tests for WebSocketClient initialization."""

    def test_initial_state_is_disconnected(self) -> None:
        """Test that initial state is DISCONNECTED."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        self.assertEqual(client._state, ConnectionState.DISCONNECTED)

    def test_initial_websocket_is_none(self) -> None:
        """Test that initial websocket is None."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        self.assertIsNone(client._websocket)

    def test_initial_task_is_none(self) -> None:
        """Test that initial task is None."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        self.assertIsNone(client._task)

    def test_lock_is_initialized(self) -> None:
        """Test that asyncio.Lock is initialized."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        self.assertIsInstance(client._lock, asyncio.Lock)


class TestWebSocketClientConnect(unittest.IsolatedAsyncioTestCase):
    """Tests for WebSocketClient.connect()."""

    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", True
    )
    async def test_connect_changes_state_to_connecting(self) -> None:
        """Test that connect() changes state to CONNECTING."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        # Mock _run to avoid actual connection
        async def mock_run() -> None:
            await asyncio.sleep(10)

        with patch.object(client, "_run", mock_run):
            await client.connect()
            # State should be CONNECTING (or CONNECTED if _run completes quickly)
            self.assertIn(
                client._state,
                [ConnectionState.CONNECTING, ConnectionState.CONNECTED],
            )
            # Clean up
            await client.disconnect()

    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", True
    )
    async def test_duplicate_connect_is_no_op(self) -> None:
        """Test that calling connect() twice doesn't create duplicate tasks."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        run_count = 0

        async def mock_run() -> None:
            nonlocal run_count
            run_count += 1
            await asyncio.sleep(10)

        with patch.object(client, "_run", mock_run):
            await client.connect()
            first_task = client._task

            # Second connect should be a no-op
            await client.connect()
            second_task = client._task

            self.assertIs(first_task, second_task)
            await client.disconnect()

    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", False
    )
    async def test_connect_without_websockets_library(self) -> None:
        """Test that connect() does nothing when websockets is not available."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        await client.connect()
        self.assertEqual(client._state, ConnectionState.DISCONNECTED)
        self.assertIsNone(client._task)


class TestWebSocketClientDisconnect(unittest.IsolatedAsyncioTestCase):
    """Tests for WebSocketClient.disconnect()."""

    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", True
    )
    async def test_disconnect_changes_state_to_disconnected(self) -> None:
        """Test that disconnect() changes state to DISCONNECTED."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        async def mock_run() -> None:
            while client._state != ConnectionState.DISCONNECTED:
                await asyncio.sleep(0.1)

        with patch.object(client, "_run", mock_run):
            await client.connect()
            await client.disconnect()
            self.assertEqual(client._state, ConnectionState.DISCONNECTED)

    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", True
    )
    async def test_disconnect_when_already_disconnected_is_no_op(self) -> None:
        """Test that disconnect() on disconnected client is a no-op."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        # Should not raise
        await client.disconnect()
        self.assertEqual(client._state, ConnectionState.DISCONNECTED)

    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", True
    )
    async def test_disconnect_cancels_task(self) -> None:
        """Test that disconnect() cancels the background task."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        async def mock_run() -> None:
            while client._state != ConnectionState.DISCONNECTED:
                await asyncio.sleep(0.1)

        with patch.object(client, "_run", mock_run):
            await client.connect()
            self.assertIsNotNone(client._task)

            await client.disconnect()
            self.assertIsNone(client._task)


class TestWebSocketClientIsConnected(unittest.TestCase):
    """Tests for WebSocketClient.is_connected()."""

    def test_is_connected_when_disconnected(self) -> None:
        """Test is_connected() returns False when disconnected."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        self.assertFalse(client.is_connected())

    def test_is_connected_when_connecting(self) -> None:
        """Test is_connected() returns False when connecting."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        client._state = ConnectionState.CONNECTING
        self.assertFalse(client.is_connected())

    def test_is_connected_when_connected(self) -> None:
        """Test is_connected() returns True when connected."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        client._state = ConnectionState.CONNECTED
        self.assertTrue(client.is_connected())

    def test_is_connected_when_reconnecting(self) -> None:
        """Test is_connected() returns False when reconnecting."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        client._state = ConnectionState.RECONNECTING
        self.assertFalse(client.is_connected())


class TestWebSocketClientConcurrency(unittest.IsolatedAsyncioTestCase):
    """Tests for WebSocketClient concurrent access."""

    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", True
    )
    async def test_concurrent_connect_disconnect(self) -> None:
        """Test that concurrent connect/disconnect calls are properly serialized."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        connect_started = asyncio.Event()

        async def slow_run() -> None:
            connect_started.set()
            while client._state != ConnectionState.DISCONNECTED:
                await asyncio.sleep(0.01)

        with patch.object(client, "_run", slow_run):
            # Start connect
            connect_task = asyncio.create_task(client.connect())

            # Wait for connect to acquire lock and start
            await connect_started.wait()

            # Try to disconnect concurrently
            disconnect_task = asyncio.create_task(client.disconnect())

            await asyncio.gather(connect_task, disconnect_task)

            # Should end up disconnected
            self.assertEqual(client._state, ConnectionState.DISCONNECTED)


if __name__ == "__main__":
    unittest.main()
