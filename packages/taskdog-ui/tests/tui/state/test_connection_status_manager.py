"""Tests for ConnectionStatusManager."""

import unittest
from datetime import datetime

from taskdog.tui.state.connection_status import ConnectionStatus
from taskdog.tui.state.connection_status_manager import ConnectionStatusManager


class TestConnectionStatus(unittest.TestCase):
    """Test cases for ConnectionStatus dataclass."""

    def test_immutable(self):
        """Test ConnectionStatus is immutable (frozen)."""
        status = ConnectionStatus(
            is_api_connected=True,
            is_websocket_connected=False,
            last_update=datetime.now(),
        )
        with self.assertRaises(AttributeError):
            status.is_api_connected = False  # type: ignore[misc]


class TestConnectionStatusManager(unittest.TestCase):
    """Test cases for ConnectionStatusManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ConnectionStatusManager()

    def test_default_values(self):
        """Test default status values are correctly initialized."""
        self.assertFalse(self.manager.is_api_connected)
        self.assertFalse(self.manager.is_websocket_connected)
        self.assertIsNotNone(self.manager.status.last_update)

    def test_status_property(self):
        """Test status property returns current ConnectionStatus."""
        status = self.manager.status
        self.assertIsInstance(status, ConnectionStatus)
        self.assertFalse(status.is_api_connected)
        self.assertFalse(status.is_websocket_connected)

    def test_update_both_connected(self):
        """Test update when both connections are established."""
        self.manager.update(api_connected=True, ws_connected=True)

        self.assertTrue(self.manager.is_api_connected)
        self.assertTrue(self.manager.is_websocket_connected)

    def test_update_api_only(self):
        """Test update when only API is connected."""
        self.manager.update(api_connected=True, ws_connected=False)

        self.assertTrue(self.manager.is_api_connected)
        self.assertFalse(self.manager.is_websocket_connected)

    def test_update_websocket_only(self):
        """Test update when only WebSocket is connected."""
        self.manager.update(api_connected=False, ws_connected=True)

        self.assertFalse(self.manager.is_api_connected)
        self.assertTrue(self.manager.is_websocket_connected)

    def test_update_updates_last_update(self):
        """Test update changes the last_update timestamp."""
        initial_time = self.manager.status.last_update

        # Small delay to ensure timestamp difference
        self.manager.update(api_connected=True, ws_connected=True)

        # last_update should be >= initial_time
        self.assertGreaterEqual(self.manager.status.last_update, initial_time)

    def test_subscribe_receives_updates(self):
        """Test subscribers receive updates when status changes."""
        received_statuses: list[ConnectionStatus] = []

        def callback(status: ConnectionStatus) -> None:
            received_statuses.append(status)

        self.manager.subscribe(callback)
        self.manager.update(api_connected=True, ws_connected=False)

        self.assertEqual(len(received_statuses), 1)
        self.assertTrue(received_statuses[0].is_api_connected)
        self.assertFalse(received_statuses[0].is_websocket_connected)

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

        self.assertEqual(call_counts["cb1"], 1)
        self.assertEqual(call_counts["cb2"], 1)

    def test_unsubscribe_stops_updates(self):
        """Test unsubscribed callbacks no longer receive updates."""
        received_statuses: list[ConnectionStatus] = []

        def callback(status: ConnectionStatus) -> None:
            received_statuses.append(status)

        self.manager.subscribe(callback)
        self.manager.update(api_connected=True, ws_connected=False)
        self.assertEqual(len(received_statuses), 1)

        self.manager.unsubscribe(callback)
        self.manager.update(api_connected=False, ws_connected=False)

        # Should still be 1 (no new updates after unsubscribe)
        self.assertEqual(len(received_statuses), 1)

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

        self.assertEqual(len(received_statuses), 3)
        self.assertFalse(received_statuses[0].is_api_connected)
        self.assertTrue(received_statuses[1].is_api_connected)
        self.assertTrue(received_statuses[2].is_websocket_connected)


if __name__ == "__main__":
    unittest.main()
