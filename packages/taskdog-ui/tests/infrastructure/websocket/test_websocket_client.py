"""Tests for WebSocketClient."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from taskdog.infrastructure.websocket.websocket_client import (
    ConnectionState,
    WebSocketClient,
)


class TestConnectionState:
    """Tests for ConnectionState enum."""

    def test_states_exist(self) -> None:
        """Test that all expected states exist."""
        assert ConnectionState.DISCONNECTED is not None
        assert ConnectionState.CONNECTING is not None
        assert ConnectionState.CONNECTED is not None
        assert ConnectionState.RECONNECTING is not None


class TestWebSocketClientInit:
    """Tests for WebSocketClient initialization."""

    def test_initial_state_is_disconnected(self) -> None:
        """Test that initial state is DISCONNECTED."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        assert client._state == ConnectionState.DISCONNECTED

    def test_initial_websocket_is_none(self) -> None:
        """Test that initial websocket is None."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        assert client._websocket is None

    def test_initial_task_is_none(self) -> None:
        """Test that initial task is None."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        assert client._task is None

    def test_lock_is_initialized(self) -> None:
        """Test that asyncio.Lock is initialized."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        assert isinstance(client._lock, asyncio.Lock)


class TestWebSocketClientConnect:
    """Tests for WebSocketClient.connect()."""

    @pytest.mark.asyncio
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
            assert client._state in [
                ConnectionState.CONNECTING,
                ConnectionState.CONNECTED,
            ]
            # Clean up
            await client.disconnect()

    @pytest.mark.asyncio
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

            assert first_task is second_task
            await client.disconnect()

    @pytest.mark.asyncio
    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", False
    )
    async def test_connect_without_websockets_library(self) -> None:
        """Test that connect() does nothing when websockets is not available."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        await client.connect()
        assert client._state == ConnectionState.DISCONNECTED
        assert client._task is None


class TestWebSocketClientDisconnect:
    """Tests for WebSocketClient.disconnect()."""

    @pytest.mark.asyncio
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
            assert client._state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    @patch(
        "taskdog.infrastructure.websocket.websocket_client.WEBSOCKETS_AVAILABLE", True
    )
    async def test_disconnect_when_already_disconnected_is_no_op(self) -> None:
        """Test that disconnect() on disconnected client is a no-op."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)

        # Should not raise
        await client.disconnect()
        assert client._state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
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
            assert client._task is not None

            await client.disconnect()
            assert client._task is None


class TestWebSocketClientIsConnected:
    """Tests for WebSocketClient.is_connected()."""

    @pytest.mark.parametrize(
        "state,expected",
        [
            (ConnectionState.DISCONNECTED, False),
            (ConnectionState.CONNECTING, False),
            (ConnectionState.CONNECTED, True),
            (ConnectionState.RECONNECTING, False),
        ],
        ids=["disconnected", "connecting", "connected", "reconnecting"],
    )
    def test_is_connected(self, state, expected) -> None:
        """Test is_connected() returns correct value for each state."""
        callback = MagicMock()
        client = WebSocketClient("ws://localhost:8000/ws", callback)
        client._state = state
        assert client.is_connected() == expected


class TestWebSocketClientConcurrency:
    """Tests for WebSocketClient concurrent access."""

    @pytest.mark.asyncio
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
            assert client._state == ConnectionState.DISCONNECTED
