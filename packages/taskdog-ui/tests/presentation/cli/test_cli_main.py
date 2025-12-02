"""Tests for CLI main entry point and global options."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from taskdog.cli_main import cli


class TestCliGlobalOptions:
    """Test cases for CLI global options (--host, --port)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("taskdog.infrastructure.api_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_default_connection(self, mock_load_config, mock_api_client):
        """Test default connection uses config values."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute - invoke with a subcommand that triggers context setup
        # Using --help on a subcommand still triggers the group callback
        self.runner.invoke(cli, ["table", "--help"])

        # Verify
        mock_api_client.assert_called_once_with(base_url="http://127.0.0.1:8000")

    @patch("taskdog.infrastructure.api_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_host_option_override(self, mock_load_config, mock_api_client):
        """Test --host option overrides config."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute
        self.runner.invoke(cli, ["--host", "192.168.1.100", "table", "--help"])

        # Verify - host should be overridden, port should use config
        mock_api_client.assert_called_once_with(base_url="http://192.168.1.100:8000")

    @patch("taskdog.infrastructure.api_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_port_option_override(self, mock_load_config, mock_api_client):
        """Test --port option overrides config."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute
        self.runner.invoke(cli, ["--port", "3000", "table", "--help"])

        # Verify - port should be overridden, host should use config
        mock_api_client.assert_called_once_with(base_url="http://127.0.0.1:3000")

    @patch("taskdog.infrastructure.api_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_both_options_override(self, mock_load_config, mock_api_client):
        """Test --host and --port options both override config."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute
        self.runner.invoke(
            cli, ["--host", "192.168.1.100", "--port", "3000", "table", "--help"]
        )

        # Verify
        mock_api_client.assert_called_once_with(base_url="http://192.168.1.100:3000")

    def test_help_shows_global_options(self):
        """Test that --help displays --host and --port options."""
        # Execute
        result = self.runner.invoke(cli, ["--help"])

        # Verify
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output
        assert "API server host" in result.output
        assert "API server port" in result.output

    @patch("taskdog.infrastructure.api_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_connection_error_shows_overridden_host_port(
        self, mock_load_config, mock_api_client
    ):
        """Test connection error message uses overridden host/port."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_client_instance.client.get.side_effect = Exception("Connection refused")
        mock_api_client.return_value = mock_client_instance

        # Execute
        result = self.runner.invoke(
            cli, ["--host", "192.168.1.100", "--port", "3000", "table"]
        )

        # Verify - error message should show overridden values
        assert result.exit_code == 1
        assert "192.168.1.100:3000" in result.output
