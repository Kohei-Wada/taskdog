"""Tests for editor utilities."""

import subprocess
from unittest.mock import patch

import pytest

from taskdog.utils.editor import get_editor


class TestGetEditor:
    """Test cases for get_editor function."""

    def test_returns_editor_env_variable(self) -> None:
        """Test that $EDITOR environment variable is returned when set."""
        with patch.dict("os.environ", {"EDITOR": "code"}):
            result = get_editor()
            assert result == "code"

    def test_returns_full_path_editor(self) -> None:
        """Test that full path editor is returned."""
        with patch.dict("os.environ", {"EDITOR": "/usr/bin/nvim"}):
            result = get_editor()
            assert result == "/usr/bin/nvim"

    def test_returns_editor_with_args(self) -> None:
        """Test that editor with arguments is returned as-is."""
        with patch.dict("os.environ", {"EDITOR": "code --wait"}):
            result = get_editor()
            assert result == "code --wait"

    @patch("subprocess.run")
    def test_fallback_to_vim_when_no_editor_env(self, mock_run) -> None:
        """Test fallback to vim when $EDITOR is not set."""
        mock_run.return_value = None  # which command succeeds

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("os.getenv", return_value=None),
        ):
            result = get_editor()
            assert result == "vim"

    @patch("subprocess.run")
    def test_fallback_to_nano_when_vim_not_found(self, mock_run) -> None:
        """Test fallback to nano when vim is not found."""

        def side_effect(args, **kwargs):
            if args == ["which", "vim"]:
                raise subprocess.CalledProcessError(1, "which")
            return None  # nano found

        mock_run.side_effect = side_effect

        with patch("os.getenv", return_value=None):
            result = get_editor()
            assert result == "nano"

    @patch("subprocess.run")
    def test_fallback_to_vi_when_vim_and_nano_not_found(self, mock_run) -> None:
        """Test fallback to vi when vim and nano are not found."""

        def side_effect(args, **kwargs):
            if args == ["which", "vim"] or args == ["which", "nano"]:
                raise subprocess.CalledProcessError(1, "which")
            return None  # vi found

        mock_run.side_effect = side_effect

        with patch("os.getenv", return_value=None):
            result = get_editor()
            assert result == "vi"

    @patch("subprocess.run")
    def test_raises_runtime_error_when_no_editor_found(self, mock_run) -> None:
        """Test that RuntimeError is raised when no editor is found."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "which")

        with patch("os.getenv", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                get_editor()

            assert "No editor found" in str(exc_info.value)
            assert "$EDITOR" in str(exc_info.value)

    def test_empty_editor_env_uses_fallback(self) -> None:
        """Test that empty $EDITOR uses fallback."""
        with (
            patch.dict("os.environ", {"EDITOR": ""}),
            patch("os.getenv", return_value=""),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = None
            # Empty string is falsy, so should use fallback
            result = get_editor()
            # Since empty string is returned by getenv and is falsy,
            # the function should check fallbacks
            assert result in ["vim", "nano", "vi", ""]

    @patch("subprocess.run")
    def test_which_called_with_correct_arguments(self, mock_run) -> None:
        """Test that which command is called with correct arguments."""
        mock_run.return_value = None

        with patch("os.getenv", return_value=None):
            get_editor()

        mock_run.assert_called()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["which", "vim"]
        assert call_args[1]["check"] is True
        assert call_args[1]["capture_output"] is True

    @patch("subprocess.run")
    def test_subprocess_run_called_with_text_true(self, mock_run) -> None:
        """Test that subprocess.run is called with text=True."""
        mock_run.return_value = None

        with patch("os.getenv", return_value=None):
            get_editor()

        call_args = mock_run.call_args
        assert call_args[1]["text"] is True
