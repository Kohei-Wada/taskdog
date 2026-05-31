"""Tests for editor utilities."""

from unittest.mock import call, patch

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

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Linux"),
        ):
            result = get_editor()
            assert result == "vim"

    @patch("shutil.which")
    def test_fallback_to_nano_when_vim_not_found(self, mock_which) -> None:
        """Test fallback to nano when vim is not found."""
        mock_which.side_effect = lambda cmd: "/usr/bin/nano" if cmd == "nano" else None

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Linux"),
        ):
            result = get_editor()
            assert result == "nano"

    @patch("shutil.which")
    def test_fallback_to_vi_when_vim_and_nano_not_found(self, mock_which) -> None:
        """Test fallback to vi when vim and nano are not found."""
        mock_which.side_effect = lambda cmd: "/usr/bin/vi" if cmd == "vi" else None

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Linux"),
        ):
            result = get_editor()
            assert result == "vi"

    @patch("shutil.which")
    def test_windows_fallback_to_code_when_no_editor_env(self, mock_which) -> None:
        """Test Windows fallback to VS Code when $EDITOR is not set."""
        mock_which.side_effect = lambda cmd: (
            "C:/Tools/code.exe" if cmd == "code" else None
        )

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Windows"),
        ):
            result = get_editor()
            assert result == "code"

        mock_which.assert_called_once_with("code")

    @patch("shutil.which")
    def test_windows_fallback_to_notepad_when_code_not_found(self, mock_which) -> None:
        """Test Windows fallback to notepad when code is not found."""
        mock_which.side_effect = lambda cmd: (
            "C:/Windows/System32/notepad.exe" if cmd == "notepad" else None
        )

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Windows"),
        ):
            result = get_editor()
            assert result == "notepad"

        assert mock_which.call_args_list == [call("code"), call("notepad")]

    @patch("shutil.which")
    def test_windows_fallback_to_vim_when_code_and_notepad_not_found(
        self, mock_which
    ) -> None:
        """Test Windows fallback to vim when code and notepad are not found."""
        mock_which.side_effect = lambda cmd: (
            "C:/Tools/vim.exe" if cmd == "vim" else None
        )

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Windows"),
        ):
            result = get_editor()
            assert result == "vim"

        assert mock_which.call_args_list == [call("code"), call("notepad"), call("vim")]

    @patch("shutil.which", return_value=None)
    def test_raises_runtime_error_when_no_editor_found(self, mock_which) -> None:
        """Test that RuntimeError is raised when no editor is found."""
        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Linux"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                get_editor()

            assert "No editor found" in str(exc_info.value)
            assert "$EDITOR" in str(exc_info.value)
            assert "vim, nano, vi" in str(exc_info.value)

    @patch("shutil.which", return_value=None)
    def test_windows_runtime_error_mentions_windows_fallbacks(self, mock_which) -> None:
        """Test that Windows errors mention Windows-specific fallback editors."""
        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Windows"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                get_editor()

            assert "code, notepad, vim" in str(exc_info.value)

    @patch("shutil.which", return_value="/usr/bin/vim")
    def test_empty_editor_env_uses_fallback(self, mock_which) -> None:
        """Test that empty $EDITOR uses fallback."""
        with (
            patch("os.getenv", return_value=""),
            patch("taskdog.utils.editor.platform.system", return_value="Linux"),
        ):
            result = get_editor()
            assert result == "vim"

    @patch("shutil.which")
    def test_which_called_with_correct_arguments(self, mock_which) -> None:
        """Test that shutil.which is called with correct arguments."""
        mock_which.return_value = "/usr/bin/vim"

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.platform.system", return_value="Linux"),
        ):
            get_editor()

        mock_which.assert_called()
        mock_which.assert_any_call("vim")
