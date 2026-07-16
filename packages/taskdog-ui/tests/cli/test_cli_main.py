"""Tests for CLI main entry point and global options."""

import importlib
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from taskdog.cli_main import LAZY_SUBCOMMANDS, cli


class TestCliGlobalOptions:
    """Test cases for CLI global options (--host, --port)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_default_connection(self, mock_load_config, mock_api_client):
        """Test default connection uses config values."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_config.api.api_key = None
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute - invoke with a subcommand that triggers context setup
        # Using --help on a subcommand still triggers the group callback
        self.runner.invoke(cli, ["list", "--help"])

        # Verify
        mock_api_client.assert_called_once_with(
            base_url="http://127.0.0.1:8000", api_key=None
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_host_option_override(self, mock_load_config, mock_api_client):
        """Test --host option overrides config."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_config.api.api_key = None
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute
        self.runner.invoke(cli, ["--host", "192.168.1.100", "list", "--help"])

        # Verify - host should be overridden, port should use config
        mock_api_client.assert_called_once_with(
            base_url="http://192.168.1.100:8000", api_key=None
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_port_option_override(self, mock_load_config, mock_api_client):
        """Test --port option overrides config."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_config.api.api_key = None
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute
        self.runner.invoke(cli, ["--port", "3000", "list", "--help"])

        # Verify - port should be overridden, host should use config
        mock_api_client.assert_called_once_with(
            base_url="http://127.0.0.1:3000", api_key=None
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_both_options_override(self, mock_load_config, mock_api_client):
        """Test --host and --port options both override config."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_config.api.api_key = None
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute
        self.runner.invoke(
            cli, ["--host", "192.168.1.100", "--port", "3000", "list", "--help"]
        )

        # Verify
        mock_api_client.assert_called_once_with(
            base_url="http://192.168.1.100:3000", api_key=None
        )

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

    def test_port_validation_too_low(self):
        """Test that port 0 is rejected."""
        # Execute
        result = self.runner.invoke(cli, ["--port", "0", "list"])

        # Verify - Click returns exit code 2 for usage errors
        assert result.exit_code == 2
        assert "is not in the range 1<=x<=65535" in result.output

    def test_port_validation_too_high(self):
        """Test that port > 65535 is rejected."""
        # Execute
        result = self.runner.invoke(cli, ["--port", "65536", "list"])

        # Verify - Click returns exit code 2 for usage errors
        assert result.exit_code == 2
        assert "is not in the range 1<=x<=65535" in result.output

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_port_validation_valid_boundary(self, mock_load_config, mock_api_client):
        """Test that valid boundary ports (1, 65535) are accepted."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_config.api.api_key = None
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute - test port 1
        self.runner.invoke(cli, ["--port", "1", "list", "--help"])
        mock_api_client.assert_called_with(base_url="http://127.0.0.1:1", api_key=None)

        # Reset mock
        mock_api_client.reset_mock()

        # Execute - test port 65535
        self.runner.invoke(cli, ["--port", "65535", "list", "--help"])
        mock_api_client.assert_called_with(
            base_url="http://127.0.0.1:65535", api_key=None
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_api_key_option_override(self, mock_load_config, mock_api_client):
        """Test --api-key option overrides config."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_config.api.api_key = "config-key"
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute
        self.runner.invoke(cli, ["--api-key", "cli-key", "list", "--help"])

        # Verify - api_key should be overridden
        mock_api_client.assert_called_once_with(
            base_url="http://127.0.0.1:8000", api_key="cli-key"
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_api_key_from_config(self, mock_load_config, mock_api_client):
        """Test api_key from config is used when --api-key not provided."""
        # Setup
        mock_config = MagicMock()
        mock_config.api.host = "127.0.0.1"
        mock_config.api.port = 8000
        mock_config.api.api_key = "config-key"
        mock_load_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance

        # Execute
        self.runner.invoke(cli, ["list", "--help"])

        # Verify - api_key from config should be used
        mock_api_client.assert_called_once_with(
            base_url="http://127.0.0.1:8000", api_key="config-key"
        )

    def test_help_shows_api_key_option(self):
        """Test that --help displays --api-key option."""
        # Execute
        result = self.runner.invoke(cli, ["--help"])

        # Verify
        assert result.exit_code == 0
        assert "--api-key" in result.output
        assert "API key for authentication" in result.output


class TestLazySubcommands:
    """Guards for the lazy command registry (see LAZY_SUBCOMMANDS)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.runner = CliRunner()

    def test_help_lists_every_command(self):
        """--help must list every registered command."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        for name in LAZY_SUBCOMMANDS:
            assert name in result.output

    def test_help_does_not_import_heavy_subcommand_modules(self):
        """--help lists commands from static summaries, importing none of them.

        This is the whole point of the registry: rendering help must not drag in
        heavy per-command deps (rich.markdown, markdown_it, Textual via ``tui``).
        """
        import sys

        for path, _ in LAZY_SUBCOMMANDS.values():
            sys.modules.pop(path.rsplit(".", 1)[0], None)
        sys.modules.pop("textual", None)

        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "textual" not in sys.modules

    @pytest.mark.parametrize("name", sorted(LAZY_SUBCOMMANDS))
    def test_each_command_loads_and_summary_matches(self, name):
        """Each command imports cleanly and its static summary stays in sync."""
        import_path, summary = LAZY_SUBCOMMANDS[name]
        modname, attr = import_path.rsplit(".", 1)
        command = getattr(importlib.import_module(modname), attr)

        assert isinstance(command, click.Command)
        assert command.name == name
        # The registry summary must not drift from the command's own help.
        assert command.get_short_help_str(10**6) == summary

    def test_alias_resolves_to_canonical_command(self):
        """Aliases dispatch to their canonical command and stay hidden from help."""
        from taskdog.cli_main import COMMAND_ALIASES

        result = self.runner.invoke(cli, ["--help"])
        for alias, canonical in COMMAND_ALIASES.items():
            assert canonical in result.output
            # Aliases must not clutter the command listing.
            assert f"  {alias} " not in result.output


# Noun subgroups (dep/tag/db/audit) are themselves lazy groups; guard their
# leaf registries the same way the top-level registry is guarded.
NOUN_GROUPS = ["dep", "tag", "db", "audit"]


class TestNounSubgroups:
    """Guards for the lazy noun subgroups."""

    @pytest.mark.parametrize("group_name", NOUN_GROUPS)
    def test_subcommands_load_and_summaries_match(self, group_name):
        """Every subcommand in a group imports cleanly with a matching summary."""
        import_path = LAZY_SUBCOMMANDS[group_name][0]
        modname, attr = import_path.rsplit(".", 1)
        group = getattr(importlib.import_module(modname), attr)

        assert isinstance(group, click.Group)
        for sub_name, (sub_path, summary) in group.lazy_subcommands.items():
            sub_modname, sub_attr = sub_path.rsplit(".", 1)
            command = getattr(importlib.import_module(sub_modname), sub_attr)
            assert isinstance(command, click.Command)
            assert command.name == sub_name
            assert command.get_short_help_str(10**6) == summary
