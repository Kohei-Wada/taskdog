"""Tests for note command."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from taskdog.cli.commands.note import note_command
from taskdog.cli.context import CliContext


class TestNoteCommand:
    """Test cases for note command."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.console_writer = MagicMock()
        self.api_client = MagicMock()
        self.config = MagicMock()

        self.cli_context = CliContext(
            console_writer=self.console_writer,
            api_client=self.api_client,
            config=self.config,
        )

        # Setup mock task - just use a simple Mock object
        self.mock_task = Mock(id=1, name="Test Task")
        self.api_client.get_task_by_id.return_value = Mock(task=self.mock_task)

    def test_stdin_input(self):
        """Test providing note content via stdin."""
        # Setup
        content = "Note from stdin"
        self.api_client.get_task_notes.return_value = ("", False)

        # Mock the helper function to return stdin content
        with patch("taskdog.cli.commands.note._read_content_from_source") as mock_read:
            mock_read.return_value = content

            # Execute
            result = self.runner.invoke(
                note_command,
                ["1"],
                obj=self.cli_context,
            )

            # Verify
            assert result.exit_code == 0
            mock_read.assert_called_once_with(None, None, self.console_writer)
            self.api_client.update_task_notes.assert_called_once_with(1, content)
            self.console_writer.success.assert_called_once()

    def test_content_option(self):
        """Test providing note content via --content option."""
        # Setup
        content = "Note from option"
        self.api_client.get_task_notes.return_value = ("", False)

        # Execute
        result = self.runner.invoke(
            note_command,
            ["1", "--content", content],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.update_task_notes.assert_called_once_with(1, content)
        self.console_writer.success.assert_called_once()

    def test_content_option_short_flag(self):
        """Test providing note content via -c short flag."""
        # Setup
        content = "Note from short flag"
        self.api_client.get_task_notes.return_value = ("", False)

        # Execute
        result = self.runner.invoke(
            note_command,
            ["1", "-c", content],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        self.api_client.update_task_notes.assert_called_once_with(1, content)
        self.console_writer.success.assert_called_once()

    def test_file_option(self):
        """Test providing note content via --file option."""
        # Setup
        content = "Note from file"
        self.api_client.get_task_notes.return_value = ("", False)

        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            # Execute
            result = self.runner.invoke(
                note_command,
                ["1", "--file", str(tmp_path)],
                obj=self.cli_context,
            )

            # Verify
            assert result.exit_code == 0
            self.api_client.update_task_notes.assert_called_once_with(1, content)
            self.console_writer.success.assert_called_once()
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_file_option_short_flag(self):
        """Test providing note content via -f short flag."""
        # Setup
        content = "Note from file (short)"
        self.api_client.get_task_notes.return_value = ("", False)

        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            # Execute
            result = self.runner.invoke(
                note_command,
                ["1", "-f", str(tmp_path)],
                obj=self.cli_context,
            )

            # Verify
            assert result.exit_code == 0
            self.api_client.update_task_notes.assert_called_once_with(1, content)
            self.console_writer.success.assert_called_once()
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_append_mode_with_existing_notes(self):
        """Test appending to existing notes."""
        # Setup
        existing_content = "Existing note"
        new_content = "New note"
        self.api_client.get_task_notes.return_value = (existing_content, True)

        # Execute
        result = self.runner.invoke(
            note_command,
            ["1", "--content", new_content, "--append"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        expected_content = f"{existing_content}\n\n{new_content}"
        self.api_client.update_task_notes.assert_called_once_with(1, expected_content)
        self.console_writer.success.assert_called_once()

    def test_append_mode_short_flag(self):
        """Test appending with -a short flag."""
        # Setup
        existing_content = "Existing note"
        new_content = "New note"
        self.api_client.get_task_notes.return_value = (existing_content, True)

        # Execute
        result = self.runner.invoke(
            note_command,
            ["1", "-c", new_content, "-a"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        expected_content = f"{existing_content}\n\n{new_content}"
        self.api_client.update_task_notes.assert_called_once_with(1, expected_content)

    def test_append_mode_without_existing_notes(self):
        """Test appending when no existing notes exist."""
        # Setup
        new_content = "First note"
        self.api_client.get_task_notes.return_value = ("", False)

        # Execute
        result = self.runner.invoke(
            note_command,
            ["1", "--content", new_content, "--append"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        # When no existing notes, should just save new content
        self.api_client.update_task_notes.assert_called_once_with(1, new_content)
        self.console_writer.success.assert_called_once()

    def test_append_strips_whitespace_correctly(self):
        """Test that append mode handles whitespace correctly."""
        # Setup
        existing_content = "Existing note\n\n  "
        new_content = "  \nNew note"
        self.api_client.get_task_notes.return_value = (existing_content, True)

        # Execute
        result = self.runner.invoke(
            note_command,
            ["1", "--content", new_content, "--append"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        expected_content = "Existing note\n\nNew note"
        self.api_client.update_task_notes.assert_called_once_with(1, expected_content)

    def test_replace_mode_default(self):
        """Test that replace mode is default (overwrites existing notes)."""
        # Setup
        existing_content = "Old note"
        new_content = "New note"
        self.api_client.get_task_notes.return_value = (existing_content, True)

        # Execute (no --append flag)
        result = self.runner.invoke(
            note_command,
            ["1", "--content", new_content],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        # Should replace, not append
        self.api_client.update_task_notes.assert_called_once_with(1, new_content)
        self.console_writer.success.assert_called_once()

    def test_empty_content_warning(self):
        """Test warning when content is empty."""
        # Setup
        self.api_client.get_task_notes.return_value = ("", False)

        # Execute with empty content
        result = self.runner.invoke(
            note_command,
            ["1", "--content", "   "],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.warning.assert_called_once_with("Note content is empty")
        self.api_client.update_task_notes.assert_called_once()

    def test_multiple_input_sources_error(self):
        """Test error when multiple input sources are specified."""
        # Setup
        self.api_client.get_task_notes.return_value = ("", False)

        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write("content")
            tmp_path = Path(tmp.name)

        try:
            # Execute with both --content and --file
            result = self.runner.invoke(
                note_command,
                ["1", "--content", "text", "--file", str(tmp_path)],
                obj=self.cli_context,
            )

            # Verify
            assert result.exit_code == 0
            self.console_writer.validation_error.assert_called_once()
            error_msg = self.console_writer.validation_error.call_args[0][0]
            assert "multiple input sources" in error_msg
            self.api_client.update_task_notes.assert_not_called()
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_file_not_found_error(self):
        """Test error handling when file doesn't exist."""
        # Execute with non-existent file
        result = self.runner.invoke(
            note_command,
            ["1", "--file", "/nonexistent/file.md"],
            obj=self.cli_context,
        )

        # Verify - Click should catch this before our code
        assert result.exit_code != 0
        self.api_client.update_task_notes.assert_not_called()

    def test_editor_mode_when_no_input(self):
        """Test that editor opens when no input source is provided."""
        # Setup
        self.api_client.get_task_notes.return_value = ("Existing note", True)

        # Mock _read_content_from_source to return None (no stdin/file/content)
        with (
            patch("taskdog.cli.commands.note._read_content_from_source") as mock_read,
            patch("taskdog.cli.commands.note._edit_with_editor") as mock_edit,
        ):
            mock_read.return_value = None

            # Execute (no input options)
            result = self.runner.invoke(
                note_command,
                ["1"],
                obj=self.cli_context,
            )

            # Verify editor mode was called
            assert result.exit_code == 0
            mock_read.assert_called_once_with(None, None, self.console_writer)
            mock_edit.assert_called_once()
            # Verify it was called with correct arguments
            call_args = mock_edit.call_args[0]
            assert call_args[0] == 1  # task_id
            assert call_args[1] == self.mock_task  # task
            assert call_args[2] == self.api_client  # api_client
            assert call_args[3] == self.console_writer  # console_writer

    def test_api_error_handling(self):
        """Test error handling when API call fails."""
        # Setup
        self.api_client.get_task_notes.return_value = ("", False)
        self.api_client.update_task_notes.side_effect = Exception("API Error")

        # Execute
        result = self.runner.invoke(
            note_command,
            ["1", "--content", "test"],
            obj=self.cli_context,
        )

        # Verify
        assert result.exit_code == 0
        self.console_writer.error.assert_called_once()
        error_args = self.console_writer.error.call_args[0]
        assert error_args[0] == "saving notes"

    def test_task_not_found(self):
        """Test error when task doesn't exist."""

        # Setup - task not found
        self.api_client.get_task_by_id.return_value = Mock(task=None)

        # Execute
        result = self.runner.invoke(
            note_command,
            ["999", "--content", "test"],
            obj=self.cli_context,
        )

        # Verify - handle_task_errors catches TaskNotFoundException
        assert result.exit_code == 0
        self.console_writer.validation_error.assert_called_once()

    def test_file_read_oserror(self):
        """Test error handling when file read fails with OSError."""
        from taskdog.cli.commands.note import _read_content_from_source

        # Create a mock file path that will fail to read
        with patch("taskdog.cli.commands.note.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.read_text.side_effect = OSError("Permission denied")
            mock_path_cls.return_value = mock_path

            # Execute
            result = _read_content_from_source(None, "/fake/path", self.console_writer)

            # Verify
            assert result is None
            self.console_writer.error.assert_called_once()

    def test_file_read_unicode_error(self):
        """Test error handling when file has encoding issues."""
        from taskdog.cli.commands.note import _read_content_from_source

        with patch("taskdog.cli.commands.note.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.read_text.side_effect = UnicodeDecodeError(
                "utf-8", b"", 0, 1, "invalid"
            )
            mock_path_cls.return_value = mock_path

            # Execute
            result = _read_content_from_source(None, "/fake/path", self.console_writer)

            # Verify
            assert result is None
            self.console_writer.error.assert_called_once()

    def test_editor_not_found(self):
        """Test error when $EDITOR is not found."""
        from taskdog.cli.commands.note import _edit_with_editor

        self.api_client.get_task_notes.return_value = ("", False)

        with patch("taskdog.cli.commands.note.get_editor") as mock_get_editor:
            mock_get_editor.side_effect = RuntimeError("No editor found")

            # Execute
            _edit_with_editor(
                1, self.mock_task, self.api_client, self.console_writer, None
            )

            # Verify
            self.console_writer.error.assert_called_once()
            assert "finding editor" in self.console_writer.error.call_args[0][0]

    def test_editor_execution_error(self):
        """Test error when editor returns non-zero exit code."""
        import subprocess

        from taskdog.cli.commands.note import _edit_with_editor

        self.api_client.get_task_notes.return_value = ("existing content", True)

        with (
            patch("taskdog.cli.commands.note.get_editor") as mock_get_editor,
            patch("taskdog.cli.commands.note.subprocess.run") as mock_run,
            patch("taskdog.cli.commands.note.tempfile.NamedTemporaryFile") as mock_tmp,
            patch("taskdog.cli.commands.note.Path") as mock_path_cls,
        ):
            mock_get_editor.return_value = "vim"
            mock_run.side_effect = subprocess.CalledProcessError(1, "vim")

            # Setup temp file mock
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.name = "/tmp/test.md"
            mock_tmp.return_value = mock_file

            mock_path = MagicMock()
            mock_path_cls.return_value = mock_path

            # Execute
            _edit_with_editor(
                1, self.mock_task, self.api_client, self.console_writer, None
            )

            # Verify
            self.console_writer.error.assert_called()

    def test_editor_keyboard_interrupt(self):
        """Test handling of keyboard interrupt during editing."""
        from taskdog.cli.commands.note import _edit_with_editor

        self.api_client.get_task_notes.return_value = ("existing content", True)

        with (
            patch("taskdog.cli.commands.note.get_editor") as mock_get_editor,
            patch("taskdog.cli.commands.note.subprocess.run") as mock_run,
            patch("taskdog.cli.commands.note.tempfile.NamedTemporaryFile") as mock_tmp,
            patch("taskdog.cli.commands.note.Path") as mock_path_cls,
        ):
            mock_get_editor.return_value = "vim"
            mock_run.side_effect = KeyboardInterrupt()

            # Setup temp file mock
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.name = "/tmp/test.md"
            mock_tmp.return_value = mock_file

            mock_path = MagicMock()
            mock_path_cls.return_value = mock_path

            # Execute
            _edit_with_editor(
                1, self.mock_task, self.api_client, self.console_writer, None
            )

            # Verify
            self.console_writer.warning.assert_called_once_with("Editor interrupted")

    def test_editor_save_oserror(self):
        """Test error handling when saving edited content fails."""
        from taskdog.cli.commands.note import _edit_with_editor

        self.api_client.get_task_notes.return_value = ("existing content", True)

        with (
            patch("taskdog.cli.commands.note.get_editor") as mock_get_editor,
            patch("taskdog.cli.commands.note.subprocess.run") as mock_run,
            patch("taskdog.cli.commands.note.tempfile.NamedTemporaryFile") as mock_tmp,
            patch("taskdog.cli.commands.note.Path") as mock_path_cls,
        ):
            mock_get_editor.return_value = "vim"
            mock_run.return_value = MagicMock(returncode=0)

            # Setup temp file mock
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.name = "/tmp/test.md"
            mock_tmp.return_value = mock_file

            mock_path = MagicMock()
            mock_path.read_text.side_effect = OSError("Cannot read file")
            mock_path_cls.return_value = mock_path

            # Execute
            _edit_with_editor(
                1, self.mock_task, self.api_client, self.console_writer, None
            )

            # Verify
            self.console_writer.error.assert_called()
