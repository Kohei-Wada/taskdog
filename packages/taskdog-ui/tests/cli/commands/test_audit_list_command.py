"""Tests for audit list command date filters."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.audit.list import list_command


class TestAuditListDateFilters:
    """Test cases for --since / --until parsing."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.api_client = MagicMock()
        self.api_client.list_audit_logs.return_value = MagicMock(logs=[], total_count=0)
        self.cli_context = MagicMock()
        self.cli_context.console_writer = MagicMock()
        self.cli_context.api_client = self.api_client

    def _invoke(self, args):
        result = self.runner.invoke(list_command, args, obj=self.cli_context)
        assert result.exit_code == 0, result.output
        return self.api_client.list_audit_logs.call_args.kwargs

    def test_until_date_only_covers_whole_day(self):
        """A bare --until date must include logs recorded later that day."""
        kwargs = self._invoke(["--until", "2025-12-31"])
        assert kwargs["end_date"] == datetime(2025, 12, 31, 23, 59, 59, 999999)

    def test_until_with_explicit_time_is_preserved(self):
        """An explicit --until time must be passed through unchanged."""
        kwargs = self._invoke(["--until", "2025-12-31T09:00:00"])
        assert kwargs["end_date"] == datetime(2025, 12, 31, 9, 0, 0)

    def test_since_date_only_starts_at_midnight(self):
        """A bare --since date must start at the beginning of that day."""
        kwargs = self._invoke(["--since", "2025-12-01"])
        assert kwargs["start_date"] == datetime(2025, 12, 1, 0, 0, 0)
