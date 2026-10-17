"""Tests for the server entry point."""

from unittest.mock import patch

import pytest

from taskdog_server.config.server_config_manager import AuthConfig, ServerConfig
from taskdog_server.main import main


def _run_main(host: str, auth_enabled: bool) -> None:
    config = ServerConfig(auth=AuthConfig(enabled=auth_enabled))
    with (
        patch("sys.argv", ["taskdog-server", "--host", host]),
        patch("taskdog_server.main.ServerConfigManager.load", return_value=config),
        patch("uvicorn.run"),
    ):
        main()


class TestExposureWarning:
    """Test the warning for non-loopback binds without auth."""

    @pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.10", "::"])
    def test_warns_on_non_loopback_without_auth(self, capsys, host):
        _run_main(host, auth_enabled=False)

        assert "authentication is disabled" in capsys.readouterr().err

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
    def test_no_warning_on_loopback(self, capsys, host):
        _run_main(host, auth_enabled=False)

        assert capsys.readouterr().err == ""

    def test_no_warning_when_auth_enabled(self, capsys):
        _run_main("0.0.0.0", auth_enabled=True)

        assert capsys.readouterr().err == ""
