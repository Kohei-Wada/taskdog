"""Tests for ConnectionStatusManager."""

from datetime import datetime

import pytest

from taskdog.tui.state.connection_status import ConnectionStatus
from taskdog.tui.state.connection_status_manager import ConnectionStatusManager


class TestConnectionStatus:
    """Test cases for ConnectionStatus dataclass."""

    def test_immutable(self):
        """Test ConnectionStatus is immutable (frozen)."""
        status = ConnectionStatus(
            is_api_connected=True,
            is_websocket_connected=False,
            last_update=datetime.now(),
        )
        with pytest.raises(AttributeError):
            status.is_api_connected = False  # type: ignore[misc]


class TestConnectionStatusManager:
    """Test cases for ConnectionStatusManager class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.manager = ConnectionStatusManager()

    def test_default_values(self):
        """Test default status values are correctly initialized."""
        assert self.manager.is_api_connected is False
        assert self.manager.is_websocket_connected is False
        assert self.manager.status.last_update is not None

    def test_status_property(self):
        """Test status property returns current ConnectionStatus."""
        status = self.manager.status
        assert isinstance(status, ConnectionStatus)
        assert status.is_api_connected is False
        assert status.is_websocket_connected is False

    @pytest.mark.parametrize(
        "api_connected,ws_connected",
        [
            (True, True),
            (True, False),
            (False, True),
        ],
        ids=["both_connected", "api_only", "websocket_only"],
    )
    def test_update(self, api_connected, ws_connected):
        """Test update with different connection states."""
        self.manager.update(api_connected=api_connected, ws_connected=ws_connected)

        assert self.manager.is_api_connected == api_connected
        assert self.manager.is_websocket_connected == ws_connected

    def test_update_updates_last_update(self):
        """Test update changes the last_update timestamp."""
        initial_time = self.manager.status.last_update

        # Small delay to ensure timestamp difference
        self.manager.update(api_connected=True, ws_connected=True)

        # last_update should be >= initial_time
        assert self.manager.status.last_update >= initial_time

    def test_subscribe_receives_updates(self):
        """Test subscribers receive updates when status changes."""
        received_statuses: list[ConnectionStatus] = []

        def callback(status: ConnectionStatus) -> None:
            received_statuses.append(status)

        self.manager.subscribe(callback)
        self.manager.update(api_connected=True, ws_connected=False)

        assert len(received_statuses) == 1
        assert received_statuses[0].is_api_connected is True
        assert received_statuses[0].is_websocket_connected is False

    def test_multiple_subscribers(self):
        """Test multiple subscribers all receive updates."""
        call_counts = {"cb1": 0, "cb2": 0}

        def callback1(status: ConnectionStatus) -> None:
            call_counts["cb1"] += 1

        def callback2(status: ConnectionStatus) -> None:
            call_counts["cb2"] += 1

        self.manager.subscribe(callback1)
        self.manager.subscribe(callback2)
        self.manager.update(api_connected=True, ws_connected=True)

        assert call_counts["cb1"] == 1
        assert call_counts["cb2"] == 1

    def test_unsubscribe_stops_updates(self):
        """Test unsubscribed callbacks no longer receive updates."""
        received_statuses: list[ConnectionStatus] = []

        def callback(status: ConnectionStatus) -> None:
            received_statuses.append(status)

        self.manager.subscribe(callback)
        self.manager.update(api_connected=True, ws_connected=False)
        assert len(received_statuses) == 1

        self.manager.unsubscribe(callback)
        self.manager.update(api_connected=False, ws_connected=False)

        # Should still be 1 (no new updates after unsubscribe)
        assert len(received_statuses) == 1

    def test_unsubscribe_nonexistent_callback(self):
        """Test unsubscribe with non-existent callback does not raise."""

        def callback(status: ConnectionStatus) -> None:
            pass

        # Should not raise
        self.manager.unsubscribe(callback)

    def test_multiple_updates(self):
        """Test multiple sequential updates."""
        received_statuses: list[ConnectionStatus] = []

        def callback(status: ConnectionStatus) -> None:
            received_statuses.append(status)

        self.manager.subscribe(callback)

        self.manager.update(api_connected=False, ws_connected=False)
        self.manager.update(api_connected=True, ws_connected=False)
        self.manager.update(api_connected=True, ws_connected=True)

        assert len(received_statuses) == 3
        assert received_statuses[0].is_api_connected is False
        assert received_statuses[1].is_api_connected is True
        assert received_statuses[2].is_websocket_connected is True

    def test_exception_in_callback_does_not_break_chain(self):
        """Test that exception in one callback doesn't prevent others from being called."""
        call_counts = {"cb1": 0, "cb2": 0, "cb3": 0}

        def callback1(status: ConnectionStatus) -> None:
            call_counts["cb1"] += 1

        def callback2_raises(status: ConnectionStatus) -> None:
            call_counts["cb2"] += 1
            raise ValueError("Test exception")

        def callback3(status: ConnectionStatus) -> None:
            call_counts["cb3"] += 1

        self.manager.subscribe(callback1)
        self.manager.subscribe(callback2_raises)
        self.manager.subscribe(callback3)

        # Should not raise, and all callbacks should be attempted
        self.manager.update(api_connected=True, ws_connected=True)

        assert call_counts["cb1"] == 1
        assert call_counts["cb2"] == 1  # Called but raised
        assert call_counts["cb3"] == 1  # Still called despite cb2 exception
