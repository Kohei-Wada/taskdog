"""Tests for editor utilities."""

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

    @patch("shutil.which")
    def test_fallback_to_vim_when_no_editor_env(self, mock_which) -> None:
        """Test fallback to vim when $EDITOR is not set."""
        mock_which.return_value = "/usr/bin/vim"

        with patch("os.getenv", return_value=None):
            result = get_editor()
            assert result == "vim"

    @patch("shutil.which")
    def test_fallback_to_nano_when_vim_not_found(self, mock_which) -> None:
        """Test fallback to nano when vim is not found."""
        mock_which.side_effect = lambda cmd: "/usr/bin/nano" if cmd == "nano" else None

        with patch("os.getenv", return_value=None):
            result = get_editor()
            assert result == "nano"

    @patch("shutil.which")
    def test_fallback_to_vi_when_vim_and_nano_not_found(self, mock_which) -> None:
        """Test fallback to vi when vim and nano are not found."""
        mock_which.side_effect = lambda cmd: "/usr/bin/vi" if cmd == "vi" else None

        with patch("os.getenv", return_value=None):
            result = get_editor()
            assert result == "vi"

    @patch("shutil.which", return_value=None)
    def test_raises_runtime_error_when_no_editor_found(self, mock_which) -> None:
        """Test that RuntimeError is raised when no editor is found."""
        with patch("os.getenv", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                get_editor()

            assert "No editor found" in str(exc_info.value)
            assert "$EDITOR" in str(exc_info.value)

    @patch("shutil.which", return_value="/usr/bin/vim")
    def test_empty_editor_env_uses_fallback(self, mock_which) -> None:
        """Test that empty $EDITOR uses fallback."""
        with patch("os.getenv", return_value=""):
            result = get_editor()
            assert result == "vim"

    @patch("shutil.which")
    def test_which_called_with_correct_arguments(self, mock_which) -> None:
        """Test that shutil.which is called with correct arguments."""
        mock_which.return_value = "/usr/bin/vim"

        with patch("os.getenv", return_value=None):
            get_editor()

        mock_which.assert_called()
        mock_which.assert_any_call("vim")
