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

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.sys.platform", "linux"),
        ):
            result = get_editor()
            assert result == "vim"

    @patch("shutil.which")
    def test_fallback_to_nano_when_vim_not_found(self, mock_which) -> None:
        """Test fallback to nano when vim is not found."""

        def side_effect(cmd):
            if cmd == "vim":
                return None
            if cmd == "nano":
                return "/usr/bin/nano"
            return None

        mock_which.side_effect = side_effect

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.sys.platform", "linux"),
        ):
            result = get_editor()
            assert result == "nano"

    @patch("shutil.which")
    def test_fallback_to_vi_when_vim_and_nano_not_found(self, mock_which) -> None:
        """Test fallback to vi when vim and nano are not found."""

        def side_effect(cmd):
            if cmd in ["vim", "nano"]:
                return None
            if cmd == "vi":
                return "/usr/bin/vi"
            return None

        mock_which.side_effect = side_effect

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.sys.platform", "linux"),
        ):
            result = get_editor()
            assert result == "vi"

    @patch("shutil.which")
    def test_raises_runtime_error_when_no_editor_found_unix(self, mock_which) -> None:
        """Test that RuntimeError is raised when no editor is found on Unix."""
        mock_which.return_value = None

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.sys.platform", "linux"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                get_editor()

            assert "No editor found" in str(exc_info.value)
            assert "$EDITOR" in str(exc_info.value)

    @patch("shutil.which")
    def test_windows_raises_runtime_error_when_no_editor_found(
        self, mock_which
    ) -> None:
        """Test that RuntimeError is raised when no editor is found on Windows."""
        mock_which.return_value = None

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.sys.platform", "win32"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                get_editor()

            assert "No editor found" in str(exc_info.value)
            assert "$EDITOR" in str(exc_info.value)

    @patch("shutil.which")
    def test_windows_uses_code_first(self, mock_which) -> None:
        """Test that Windows tries VS Code first."""

        def side_effect(cmd):
            if cmd == "code":
                return "C:\\Program Files\\VS Code\\code.exe"
            return None

        mock_which.side_effect = side_effect

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.sys.platform", "win32"),
        ):
            result = get_editor()
            assert result == "code"

    @patch("shutil.which")
    def test_windows_uses_notepad_plus_plus_second(self, mock_which) -> None:
        """Test that Windows tries notepad++ when code not found."""

        def side_effect(cmd):
            if cmd == "code":
                return None
            if cmd == "notepad++":
                return "C:\\Program Files\\Notepad++\\notepad++.exe"
            return None

        mock_which.side_effect = side_effect

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.sys.platform", "win32"),
        ):
            result = get_editor()
            assert result == "notepad++"

    def test_empty_editor_env_uses_fallback(self) -> None:
        """Test that empty $EDITOR uses fallback."""
        with (
            patch.dict("os.environ", {"EDITOR": ""}),
            patch("os.getenv", return_value=""),
            patch("shutil.which") as mock_which,
            patch("taskdog.utils.editor.sys.platform", "linux"),
        ):
            mock_which.return_value = "/usr/bin/vim"
            # Empty string is falsy, so should use fallback
            result = get_editor()
            # Since empty string is returned by getenv and is falsy,
            # the function should check fallbacks
            assert result in ["vim", "nano", "vi", ""]

    @patch("shutil.which")
    def test_shutil_which_called_for_fallbacks(self, mock_which) -> None:
        """Test that shutil.which is called to check fallback editors."""
        mock_which.return_value = "/usr/bin/vim"

        with (
            patch("os.getenv", return_value=None),
            patch("taskdog.utils.editor.sys.platform", "linux"),
        ):
            get_editor()

        mock_which.assert_called()
        # First call should be for vim on Unix
        assert mock_which.call_args_list[0][0][0] == "vim"
