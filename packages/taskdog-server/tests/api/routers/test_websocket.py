"""Tests for WebSocket router endpoint."""

import uuid

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from taskdog_server.config.server_config_manager import (
    AuthConfig,
    ServerConfig,
)

# Re-use the test API key from conftest
TEST_API_KEY = "test-api-key-12345"
TEST_CLIENT_NAME = "test-client"


class TestWebSocketAuthentication:
    """Test WebSocket authentication via query parameter token."""

    def test_connect_with_valid_api_key(self, session_client):
        """Valid token should allow connection and receive welcome message."""
        with session_client.websocket_connect(f"/ws?token={TEST_API_KEY}") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert data["user_name"] == TEST_CLIENT_NAME

    def test_connect_with_invalid_api_key(self, session_client):
        """Invalid token should close connection with code 1008."""
        with (
            pytest.raises(WebSocketDisconnect),
            session_client.websocket_connect("/ws?token=invalid-key") as ws,
        ):
            ws.receive_json()

    def test_connect_without_api_key(self, session_client):
        """Missing token should close connection with code 1008."""
        with (
            pytest.raises(WebSocketDisconnect),
            session_client.websocket_connect("/ws") as ws,
        ):
            ws.receive_json()

    def test_connect_with_auth_disabled(self, app):
        """When auth is disabled, connection should succeed without token."""
        # Override server_config with auth disabled
        original_config = app.state.server_config
        app.state.server_config = ServerConfig(
            auth=AuthConfig(enabled=False, api_keys=())
        )
        try:
            no_auth_client = TestClient(app)
            with no_auth_client.websocket_connect("/ws") as ws:
                data = ws.receive_json()
                assert data["type"] == "connected"
                assert data["user_name"] == "anonymous"
        finally:
            app.state.server_config = original_config


class TestWebSocketWelcomeMessage:
    """Test the welcome message sent upon connection."""

    def test_welcome_message_contains_client_id(self, session_client):
        """Welcome message should include a valid UUID client_id."""
        with session_client.websocket_connect(f"/ws?token={TEST_API_KEY}") as ws:
            data = ws.receive_json()
            assert "client_id" in data
            # Validate it's a proper UUID
            uuid.UUID(data["client_id"])

    def test_welcome_message_contains_user_name(self, session_client):
        """Welcome message should include the authenticated user name."""
        with session_client.websocket_connect(f"/ws?token={TEST_API_KEY}") as ws:
            data = ws.receive_json()
            assert data["user_name"] == TEST_CLIENT_NAME

    def test_welcome_message_contains_connection_count(self, session_client):
        """Welcome message should include the current connection count."""
        with session_client.websocket_connect(f"/ws?token={TEST_API_KEY}") as ws:
            data = ws.receive_json()
            assert "connections" in data
            assert isinstance(data["connections"], int)
            assert data["connections"] >= 1


class TestWebSocketMessaging:
    """Test message exchange over WebSocket."""

    def test_ping_pong(self, session_client):
        """Sending a ping should receive a pong with the same timestamp."""
        with session_client.websocket_connect(f"/ws?token={TEST_API_KEY}") as ws:
            # Consume welcome message
            ws.receive_json()

            # Send ping
            ws.send_json({"type": "ping", "timestamp": 1234567890})
            pong = ws.receive_json()
            assert pong["type"] == "pong"
            assert pong["timestamp"] == 1234567890


class TestWebSocketDisconnect:
    """Test WebSocket disconnection behavior."""

    def test_disconnect_removes_from_manager(self, app, session_client):
        """After disconnect, the client should be removed from ConnectionManager."""
        manager = app.state.connection_manager
        count_before = manager.get_connection_count()

        with session_client.websocket_connect(f"/ws?token={TEST_API_KEY}") as ws:
            ws.receive_json()
            # Connection is active
            assert manager.get_connection_count() == count_before + 1

        # After context manager exits (disconnect), count should return to previous
        assert manager.get_connection_count() == count_before
