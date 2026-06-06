"""Tests for backup and restore-db commands."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.backup import backup_command
from taskdog.cli.commands.restore_db import restore_db_command


class TestBackupCommand:
    """Test cases for the backup command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_backup_with_explicit_output(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                backup_command, ["-o", "out.db"], obj=self.cli_context
            )

        assert result.exit_code == 0
        (path,) = self.api_client.backup.call_args.args
        assert path == Path("out.db")
        self.console_writer.success.assert_called_once()

    def test_backup_defaults_to_timestamped_cwd_file(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(backup_command, [], obj=self.cli_context)

        assert result.exit_code == 0
        (path,) = self.api_client.backup.call_args.args
        assert path.name.startswith("taskdog-backup-")
        assert path.suffix == ".db"

    def test_backup_reports_error(self):
        self.api_client.backup.side_effect = RuntimeError("nope")

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                backup_command, ["-o", "out.db"], obj=self.cli_context
            )

        assert result.exit_code != 0
        self.console_writer.error.assert_called_once()


class TestRestoreDbCommand:
    """Test cases for the restore-db command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.api_client.restore.return_value = MagicMock(
            status="pending", message="restart required"
        )
        self.cli_context = MagicMock()
        self.cli_context.console_writer = self.console_writer
        self.cli_context.api_client = self.api_client

    def test_restore_requires_confirmation(self):
        with self.runner.isolated_filesystem():
            Path("snap.db").write_bytes(b"db")
            result = self.runner.invoke(
                restore_db_command, ["snap.db"], obj=self.cli_context, input="n\n"
            )

        assert result.exit_code == 0
        self.api_client.restore.assert_not_called()
        self.console_writer.info.assert_called_once()

    def test_restore_with_yes_skips_prompt(self):
        with self.runner.isolated_filesystem():
            Path("snap.db").write_bytes(b"db")
            result = self.runner.invoke(
                restore_db_command, ["snap.db", "--yes"], obj=self.cli_context
            )

        assert result.exit_code == 0
        (path,) = self.api_client.restore.call_args.args
        assert path == Path("snap.db")
        self.console_writer.success.assert_called_once()

    def test_restore_missing_file_errors(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                restore_db_command, ["missing.db", "--yes"], obj=self.cli_context
            )

        assert result.exit_code != 0
        self.api_client.restore.assert_not_called()
