"""Base test class for CLI batch command tests."""

import unittest
from unittest.mock import MagicMock

from click.testing import CliRunner


class BaseBatchCommandTest(unittest.TestCase):
    """Base test class with common setup for batch CLI commands.

    Provides common fixtures for testing commands that process multiple tasks
    (start, done, pause, cancel, etc.).
    """

    def setUp(self):
        """Set up common test fixtures."""
        self.runner = CliRunner()
        self.repository = MagicMock()
        self.time_tracker = MagicMock()
        self.console_writer = MagicMock()
        self.config = MagicMock()

        # Set up CLI context with all dependencies
        self.cli_context = MagicMock()
        self.cli_context.repository = self.repository
        self.cli_context.time_tracker = self.time_tracker
        self.cli_context.console_writer = self.console_writer
        self.cli_context.config = self.config
