"""Tests for MCP server entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestMain:
    """Test main module entry point."""

    def test_version_flag(self) -> None:
        """Test --version flag outputs version and exits."""

        with patch.object(sys, "argv", ["taskdog-mcp", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                from taskdog_mcp.main import main

                main()

            assert exc_info.value.code == 0

    def test_main_creates_and_runs_server(self) -> None:
        """Test main creates and runs the MCP server."""
        mock_mcp = MagicMock()

        with (
            patch.object(sys, "argv", ["taskdog-mcp"]),
            patch(
                "taskdog_mcp.main.create_mcp_server", return_value=mock_mcp
            ) as mock_create,
        ):
            from taskdog_mcp.main import main

            main()

            mock_create.assert_called_once()
            mock_mcp.run.assert_called_once()

    def test_main_parses_args(self) -> None:
        """Test main parses command line arguments."""
        mock_mcp = MagicMock()

        with (
            patch.object(sys, "argv", ["taskdog-mcp"]),
            patch("taskdog_mcp.main.create_mcp_server", return_value=mock_mcp),
        ):
            from taskdog_mcp.main import main

            # Should not raise any exceptions
            main()
