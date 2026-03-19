"""Tests for ConnectionMonitor."""

from unittest.mock import Mock, patch

import pytest

from taskdog.tui.services.connection_monitor import ConnectionMonitor


class TestConnectionMonitor:
    """Test cases for ConnectionMonitor."""

    def setup_method(self):
        self.mock_app = Mock()
        self.mock_api_client = Mock()
        self.mock_ws_client = Mock()
        self.mock_connection_manager = Mock()
        self.monitor = ConnectionMonitor(
            app=self.mock_app,
            api_client=self.mock_api_client,
            websocket_client=self.mock_ws_client,
            connection_manager=self.mock_connection_manager,
        )

    def test_check_dispatches_worker(self):
        self.monitor.check()
        self.mock_app.run_worker.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_worker_updates_connection_status(self):
        self.mock_api_client.check_health.return_value = True
        self.mock_ws_client.is_connected.return_value = True

        with patch("asyncio.to_thread", return_value=True):
            await self.monitor._check_worker()

        self.mock_connection_manager.update.assert_called_once_with(True, True)

    @pytest.mark.asyncio
    async def test_check_worker_when_disconnected(self):
        self.mock_api_client.check_health.return_value = False
        self.mock_ws_client.is_connected.return_value = False

        with patch("asyncio.to_thread", return_value=False):
            await self.monitor._check_worker()

        self.mock_connection_manager.update.assert_called_once_with(False, False)
