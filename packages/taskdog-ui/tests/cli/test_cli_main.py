"""Tests for CLI main entry point and global options."""

import importlib
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from taskdog.cli_main import LAZY_SUBCOMMANDS, cli


class TestCliGlobalOptions:
    """Test cases for CLI global options (--base-url, --api-key)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def _mock_config(self, base_url="http://127.0.0.1:8000", api_key=None):
        mock_config = MagicMock()
        mock_config.api.base_url = base_url
        mock_config.api.api_key = api_key
        return mock_config

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_default_connection(self, mock_load_config, mock_api_client):
        """Test default connection uses the configured base_url."""
        mock_load_config.return_value = self._mock_config()

        # Using --help on a subcommand still triggers the group callback
        self.runner.invoke(cli, ["list", "--help"])

        mock_api_client.assert_called_once_with(
            base_url="http://127.0.0.1:8000", api_key=None
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_base_url_from_config(self, mock_load_config, mock_api_client):
        """Test base_url from config is used when --base-url is not given."""
        mock_load_config.return_value = self._mock_config("https://tasks.example.com")

        self.runner.invoke(cli, ["list", "--help"])

        mock_api_client.assert_called_once_with(
            base_url="https://tasks.example.com", api_key=None
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_base_url_option_override(self, mock_load_config, mock_api_client):
        """Test --base-url overrides the configured base_url."""
        mock_load_config.return_value = self._mock_config("https://config.example.com")

        self.runner.invoke(
            cli, ["--base-url", "https://cli.example.com", "list", "--help"]
        )

        mock_api_client.assert_called_once_with(
            base_url="https://cli.example.com", api_key=None
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_api_key_option_override(self, mock_load_config, mock_api_client):
        """Test --api-key option overrides config."""
        mock_load_config.return_value = self._mock_config(api_key="config-key")

        self.runner.invoke(cli, ["--api-key", "cli-key", "list", "--help"])

        mock_api_client.assert_called_once_with(
            base_url="http://127.0.0.1:8000", api_key="cli-key"
        )

    @patch("taskdog_client.TaskdogApiClient")
    @patch("taskdog.cli_main.load_cli_config")
    def test_api_key_from_config(self, mock_load_config, mock_api_client):
        """Test api_key from config is used when --api-key not provided."""
        mock_load_config.return_value = self._mock_config(api_key="config-key")

        self.runner.invoke(cli, ["list", "--help"])

        mock_api_client.assert_called_once_with(
            base_url="http://127.0.0.1:8000", api_key="config-key"
        )

    def test_help_shows_base_url_option(self):
        """Test that --help displays --base-url option."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "--base-url" in result.output

    def test_help_shows_api_key_option(self):
        """Test that --help displays --api-key option."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "--api-key" in result.output
        assert "API key for authentication" in result.output

    def test_host_and_port_options_are_gone(self):
        """Test the client-side --host/--port options were removed."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--host" not in result.output
        assert "--port" not in result.output

        result = self.runner.invoke(cli, ["--host", "192.168.1.100", "list"])
        assert result.exit_code == 2


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
