"""Tests for table_helpers module."""

from unittest.mock import MagicMock, patch

import pytest

from taskdog.cli.commands.table_helpers import render_table
from taskdog.cli.context import CliContext


class TestRenderTable:
    """Test cases for render_table helper function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.config = MagicMock()

        self.cli_context = CliContext(
            console_writer=self.console_writer,
            api_client=self.api_client,
            config=self.config,
        )

    def test_render_table_basic(self):
        """Test basic table rendering."""
        # Setup
        mock_output = MagicMock()
        mock_view_models = [MagicMock(), MagicMock()]

        with (
            patch(
                "taskdog.cli.commands.table_helpers.TablePresenter"
            ) as mock_presenter_cls,
            patch(
                "taskdog.cli.commands.table_helpers.RichTableRenderer"
            ) as mock_renderer_cls,
        ):
            mock_presenter = MagicMock()
            mock_presenter.present.return_value = mock_view_models
            mock_presenter_cls.return_value = mock_presenter

            mock_renderer = MagicMock()
            mock_renderer_cls.return_value = mock_renderer

            # Execute
            render_table(self.cli_context, mock_output)

            # Verify
            mock_presenter_cls.assert_called_once_with()
            mock_presenter.present.assert_called_once_with(mock_output)
            mock_renderer_cls.assert_called_once_with(self.console_writer)
            mock_renderer.render.assert_called_once_with(mock_view_models, fields=None)

    def test_render_table_with_fields(self):
        """Test table rendering with specific fields."""
        # Setup
        mock_output = MagicMock()
        mock_view_models = [MagicMock()]
        fields = ["id", "name", "status"]

        with (
            patch(
                "taskdog.cli.commands.table_helpers.TablePresenter"
            ) as mock_presenter_cls,
            patch(
                "taskdog.cli.commands.table_helpers.RichTableRenderer"
            ) as mock_renderer_cls,
        ):
            mock_presenter = MagicMock()
            mock_presenter.present.return_value = mock_view_models
            mock_presenter_cls.return_value = mock_presenter

            mock_renderer = MagicMock()
            mock_renderer_cls.return_value = mock_renderer

            # Execute
            render_table(self.cli_context, mock_output, fields=fields)

            # Verify
            mock_renderer.render.assert_called_once_with(
                mock_view_models, fields=fields
            )

    def test_render_table_empty(self):
        """Test table rendering with empty task list."""
        # Setup
        mock_output = MagicMock()
        mock_view_models = []  # Empty list

        with (
            patch(
                "taskdog.cli.commands.table_helpers.TablePresenter"
            ) as mock_presenter_cls,
            patch(
                "taskdog.cli.commands.table_helpers.RichTableRenderer"
            ) as mock_renderer_cls,
        ):
            mock_presenter = MagicMock()
            mock_presenter.present.return_value = mock_view_models
            mock_presenter_cls.return_value = mock_presenter

            mock_renderer = MagicMock()
            mock_renderer_cls.return_value = mock_renderer

            # Execute
            render_table(self.cli_context, mock_output)

            # Verify - should still render (empty table)
            mock_renderer.render.assert_called_once_with(mock_view_models, fields=None)
