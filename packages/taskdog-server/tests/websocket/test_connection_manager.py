"""Tests for WebSocket connection manager."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import WebSocket

from taskdog_server.websocket.connection_manager import ConnectionManager


class TestConnectionManager:
    """Test cases for ConnectionManager."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.manager = ConnectionManager()

    async def test_initialize_connection_manager(self):
        """Test initializing connection manager."""
        # Assert
        assert self.manager.get_connection_count() == 0
        assert len(self.manager.active_connections) == 0

    async def test_connect_single_client(self):
        """Test connecting a single WebSocket client."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "client-1"

        # Act
        await self.manager.connect(client_id, mock_websocket)

        # Assert
        assert self.manager.get_connection_count() == 1
        assert client_id in self.manager.active_connections
        assert self.manager.active_connections[client_id] == mock_websocket
        mock_websocket.accept.assert_called_once()

    async def test_connect_multiple_clients(self):
        """Test connecting multiple WebSocket clients."""
        # Arrange
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket3 = AsyncMock(spec=WebSocket)

        # Act
        await self.manager.connect("client-1", mock_websocket1)
        await self.manager.connect("client-2", mock_websocket2)
        await self.manager.connect("client-3", mock_websocket3)

        # Assert
        assert self.manager.get_connection_count() == 3
        assert "client-1" in self.manager.active_connections
        assert "client-2" in self.manager.active_connections
        assert "client-3" in self.manager.active_connections

    async def test_disconnect_existing_client(self):
        """Test disconnecting an existing client."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "client-1"
        await self.manager.connect(client_id, mock_websocket)

        # Act
        self.manager.disconnect(client_id)

        # Assert
        assert self.manager.get_connection_count() == 0
        assert client_id not in self.manager.active_connections

    async def test_disconnect_non_existing_client(self):
        """Test disconnecting a non-existing client does not raise error."""
        # Act & Assert - should not raise any exception
        self.manager.disconnect("non-existing-client")
        assert self.manager.get_connection_count() == 0

    async def test_broadcast_to_all_clients(self):
        """Test broadcasting message to all connected clients."""
        # Arrange
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket3 = AsyncMock(spec=WebSocket)

        await self.manager.connect("client-1", mock_websocket1)
        await self.manager.connect("client-2", mock_websocket2)
        await self.manager.connect("client-3", mock_websocket3)

        message = {"type": "task_updated", "task_id": 123}

        # Act
        await self.manager.broadcast(message)

        # Assert
        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)
        mock_websocket3.send_json.assert_called_once_with(message)

    async def test_broadcast_with_excluded_client(self):
        """Test broadcasting message excluding one client."""
        # Arrange
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket3 = AsyncMock(spec=WebSocket)

        await self.manager.connect("client-1", mock_websocket1)
        await self.manager.connect("client-2", mock_websocket2)
        await self.manager.connect("client-3", mock_websocket3)

        message = {"type": "task_updated", "task_id": 123}

        # Act
        await self.manager.broadcast(message, exclude_client_id="client-2")

        # Assert
        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_not_called()
        mock_websocket3.send_json.assert_called_once_with(message)

    async def test_broadcast_removes_disconnected_clients(self):
        """Test that broadcast removes clients with broken connections."""
        # Arrange
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket3 = AsyncMock(spec=WebSocket)

        await self.manager.connect("client-1", mock_websocket1)
        await self.manager.connect("client-2", mock_websocket2)
        await self.manager.connect("client-3", mock_websocket3)

        # Simulate connection failure for client-2
        mock_websocket2.send_json.side_effect = Exception("Connection broken")

        message = {"type": "task_updated", "task_id": 123}

        # Act
        await self.manager.broadcast(message)

        # Assert
        assert self.manager.get_connection_count() == 2
        assert "client-2" not in self.manager.active_connections
        assert "client-1" in self.manager.active_connections
        assert "client-3" in self.manager.active_connections

    async def test_send_personal_message_to_existing_client(self):
        """Test sending personal message to existing client."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "client-1"
        await self.manager.connect(client_id, mock_websocket)

        message = {"type": "task_detail", "task_id": 123}

        # Act
        await self.manager.send_personal_message(message, client_id)

        # Assert
        mock_websocket.send_json.assert_called_once_with(message)

    async def test_send_personal_message_to_non_existing_client(self):
        """Test sending personal message to non-existing client does nothing."""
        # Arrange
        message = {"type": "task_detail", "task_id": 123}

        # Act & Assert - should not raise any exception
        await self.manager.send_personal_message(message, "non-existing-client")

    async def test_send_personal_message_removes_client_on_error(self):
        """Test that personal message removes client on connection error."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "client-1"
        await self.manager.connect(client_id, mock_websocket)

        # Simulate connection failure
        mock_websocket.send_json.side_effect = Exception("Connection broken")

        message = {"type": "task_detail", "task_id": 123}

        # Act
        await self.manager.send_personal_message(message, client_id)

        # Assert
        assert self.manager.get_connection_count() == 0
        assert client_id not in self.manager.active_connections

    async def test_get_connection_count_returns_correct_value(self):
        """Test that get_connection_count returns correct number."""
        # Arrange
        assert self.manager.get_connection_count() == 0

        # Act & Assert
        mock_websocket1 = AsyncMock(spec=WebSocket)
        await self.manager.connect("client-1", mock_websocket1)
        assert self.manager.get_connection_count() == 1

        mock_websocket2 = AsyncMock(spec=WebSocket)
        await self.manager.connect("client-2", mock_websocket2)
        assert self.manager.get_connection_count() == 2

        self.manager.disconnect("client-1")
        assert self.manager.get_connection_count() == 1

        self.manager.disconnect("client-2")
        assert self.manager.get_connection_count() == 0

    async def test_broadcast_to_empty_connections(self):
        """Test broadcasting when no clients are connected."""
        # Arrange
        message = {"type": "task_updated", "task_id": 123}

        # Act & Assert - should not raise any exception
        await self.manager.broadcast(message)

    async def test_connect_same_client_id_overwrites_previous(self):
        """Test that connecting with same client ID overwrites previous connection."""
        # Arrange
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        client_id = "client-1"

        # Act
        await self.manager.connect(client_id, mock_websocket1)
        await self.manager.connect(client_id, mock_websocket2)

        # Assert
        assert self.manager.get_connection_count() == 1
        assert self.manager.active_connections[client_id] == mock_websocket2

    @patch("taskdog_server.websocket.connection_manager.logger")
    async def test_connect_logs_connection(self, mock_logger):
        """Test that connecting a client logs the event."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "client-1"

        # Act
        await self.manager.connect(client_id, mock_websocket)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert client_id in call_args
        assert "connected" in call_args.lower()

    @patch("taskdog_server.websocket.connection_manager.logger")
    async def test_disconnect_logs_disconnection(self, mock_logger):
        """Test that disconnecting a client logs the event."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "client-1"
        await self.manager.connect(client_id, mock_websocket)

        mock_logger.reset_mock()

        # Act
        self.manager.disconnect(client_id)

        # Assert
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert client_id in call_args
        assert "disconnected" in call_args.lower()

    @patch("taskdog_server.websocket.connection_manager.logger")
    async def test_broadcast_failure_logs_warning(self, mock_logger):
        """Test that broadcast failure logs a warning."""
        # Arrange
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_json.side_effect = Exception("Connection error")
        client_id = "client-1"
        await self.manager.connect(client_id, mock_websocket)

        mock_logger.reset_mock()

        # Act
        await self.manager.broadcast({"type": "test"})

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert client_id in call_args
