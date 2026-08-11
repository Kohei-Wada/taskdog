"""Tests for the tui command helpers."""

from taskdog.cli.commands.tui import _get_websocket_url


class TestGetWebsocketUrl:
    """Test WebSocket URL derivation from the API base URL."""

    def test_http_base_url_uses_ws(self):
        assert _get_websocket_url("http://127.0.0.1:8000") == "ws://127.0.0.1:8000/ws"

    def test_https_base_url_uses_wss(self):
        assert (
            _get_websocket_url("https://tasks.example.com")
            == "wss://tasks.example.com/ws"
        )

    def test_path_prefix_is_preserved(self):
        assert (
            _get_websocket_url("https://example.com/taskdog")
            == "wss://example.com/taskdog/ws"
        )
