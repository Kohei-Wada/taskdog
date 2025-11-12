"""Tests for FileNotesRepository."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from taskdog_core.domain.constants import MIN_FILE_SIZE_FOR_CONTENT
from taskdog_core.infrastructure.persistence.file_notes_repository import (
    FileNotesRepository,
)


class TestFileNotesRepository(unittest.TestCase):
    """Test suite for FileNotesRepository."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.repo = FileNotesRepository()
        self.temp_dir = tempfile.mkdtemp()
        self.task_id = 123

    def tearDown(self) -> None:
        """Clean up test files."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_get_notes_path_returns_correct_path(self, mock_xdg: MagicMock) -> None:
        """Test get_notes_path returns path from XDG utilities."""
        expected_path = Path(self.temp_dir) / "notes" / "123.md"
        mock_xdg.get_note_file.return_value = expected_path

        result = self.repo.get_notes_path(self.task_id)

        self.assertEqual(result, expected_path)
        mock_xdg.get_note_file.assert_called_once_with(self.task_id)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_has_notes_returns_false_when_file_does_not_exist(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test has_notes returns False when file doesn't exist."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.has_notes(self.task_id)

        self.assertFalse(result)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_has_notes_returns_false_when_file_is_empty(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test has_notes returns False for empty file."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text("", encoding="utf-8")
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.has_notes(self.task_id)

        self.assertFalse(result)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_has_notes_returns_false_when_file_is_too_small(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test has_notes returns False when file size is below minimum."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        # Write content smaller than MIN_FILE_SIZE_FOR_CONTENT
        content = "x" * (MIN_FILE_SIZE_FOR_CONTENT - 1)
        notes_path.write_text(content, encoding="utf-8")
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.has_notes(self.task_id)

        self.assertFalse(result)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_has_notes_returns_true_when_file_has_sufficient_content(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test has_notes returns True when file has sufficient content."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        # Write content larger than MIN_FILE_SIZE_FOR_CONTENT
        content = "x" * (MIN_FILE_SIZE_FOR_CONTENT + 1)
        notes_path.write_text(content, encoding="utf-8")
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.has_notes(self.task_id)

        self.assertTrue(result)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_read_notes_returns_none_when_file_does_not_exist(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test read_notes returns None when file doesn't exist."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.read_notes(self.task_id)

        self.assertIsNone(result)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_read_notes_returns_content_when_file_exists(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test read_notes returns file content when file exists."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        expected_content = "# Task Notes\n\nThis is a test note."
        notes_path.write_text(expected_content, encoding="utf-8")
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.read_notes(self.task_id)

        self.assertEqual(result, expected_content)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_read_notes_handles_unicode_content(self, mock_xdg: MagicMock) -> None:
        """Test read_notes handles Unicode and emoji content correctly."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        expected_content = "# タスクノート\n\n絵文字テスト: 🚀 ✅ 📝"
        notes_path.write_text(expected_content, encoding="utf-8")
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.read_notes(self.task_id)

        self.assertEqual(result, expected_content)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_read_notes_returns_none_on_permission_error(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test read_notes returns None when permission denied."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text("test content", encoding="utf-8")
        # Make file unreadable
        notes_path.chmod(0o000)
        mock_xdg.get_note_file.return_value = notes_path

        try:
            result = self.repo.read_notes(self.task_id)
            self.assertIsNone(result)
        finally:
            # Restore permissions for cleanup
            notes_path.chmod(0o644)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_read_notes_returns_none_on_unicode_decode_error(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test read_notes returns None when file has invalid UTF-8."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        # Write invalid UTF-8 bytes
        notes_path.write_bytes(b"\x80\x81\x82")
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.read_notes(self.task_id)

        self.assertIsNone(result)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_write_notes_creates_file_with_content(self, mock_xdg: MagicMock) -> None:
        """Test write_notes creates file with correct content."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        mock_xdg.get_note_file.return_value = notes_path
        content = "# New Task Note\n\nThis is a new note."

        self.repo.write_notes(self.task_id, content)

        self.assertTrue(notes_path.exists())
        self.assertEqual(notes_path.read_text(encoding="utf-8"), content)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_write_notes_overwrites_existing_file(self, mock_xdg: MagicMock) -> None:
        """Test write_notes overwrites existing file."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text("Old content", encoding="utf-8")
        mock_xdg.get_note_file.return_value = notes_path
        new_content = "New content"

        self.repo.write_notes(self.task_id, new_content)

        self.assertEqual(notes_path.read_text(encoding="utf-8"), new_content)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_write_notes_handles_unicode_content(self, mock_xdg: MagicMock) -> None:
        """Test write_notes handles Unicode and emoji content correctly."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        mock_xdg.get_note_file.return_value = notes_path
        content = "# 日本語タイトル\n\n絵文字: 🎯 📊 ✨"

        self.repo.write_notes(self.task_id, content)

        self.assertEqual(notes_path.read_text(encoding="utf-8"), content)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_write_notes_raises_os_error_on_write_failure(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test write_notes raises OSError when write fails."""
        # Point to a directory that doesn't exist and can't be created
        notes_path = Path("/nonexistent/notes/123.md")
        mock_xdg.get_note_file.return_value = notes_path

        with self.assertRaises(OSError):
            self.repo.write_notes(self.task_id, "test content")

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_write_notes_creates_parent_directory_if_needed(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test write_notes works when parent directory is created separately."""
        notes_path = Path(self.temp_dir) / "new_notes" / "123.md"
        mock_xdg.get_note_file.return_value = notes_path
        # Manually create parent directory to simulate ensure_notes_dir call
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        content = "test content"

        self.repo.write_notes(self.task_id, content)

        self.assertTrue(notes_path.exists())
        self.assertEqual(notes_path.read_text(encoding="utf-8"), content)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_ensure_notes_dir_calls_xdg_get_notes_dir(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test ensure_notes_dir calls XDG utilities to create directory."""
        self.repo.ensure_notes_dir()

        mock_xdg.get_notes_dir.assert_called_once()

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_write_notes_with_empty_string(self, mock_xdg: MagicMock) -> None:
        """Test write_notes can write empty string."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        mock_xdg.get_note_file.return_value = notes_path

        self.repo.write_notes(self.task_id, "")

        self.assertTrue(notes_path.exists())
        self.assertEqual(notes_path.read_text(encoding="utf-8"), "")

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_read_notes_with_multiline_content(self, mock_xdg: MagicMock) -> None:
        """Test read_notes preserves multiline content."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        expected_content = "# Task\n\nLine 1\nLine 2\nLine 3\n\n## Section\n\nMore text"
        notes_path.write_text(expected_content, encoding="utf-8")
        mock_xdg.get_note_file.return_value = notes_path

        result = self.repo.read_notes(self.task_id)

        self.assertEqual(result, expected_content)

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_delete_notes_removes_existing_file(self, mock_xdg: MagicMock) -> None:
        """Test delete_notes removes existing notes file."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text("# Test Note\n\nContent", encoding="utf-8")
        mock_xdg.get_note_file.return_value = notes_path

        # Verify file exists before deletion
        self.assertTrue(notes_path.exists())

        self.repo.delete_notes(self.task_id)

        # Verify file was deleted
        self.assertFalse(notes_path.exists())

    @patch(
        "taskdog_core.infrastructure.persistence.file_notes_repository.XDGDirectories"
    )
    def test_delete_notes_does_not_raise_when_file_not_exists(
        self, mock_xdg: MagicMock
    ) -> None:
        """Test delete_notes is idempotent and doesn't fail if file doesn't exist."""
        notes_path = Path(self.temp_dir) / "notes" / "123.md"
        mock_xdg.get_note_file.return_value = notes_path

        # Verify file doesn't exist
        self.assertFalse(notes_path.exists())

        # Should not raise any exception
        self.repo.delete_notes(self.task_id)

        # Still should not exist
        self.assertFalse(notes_path.exists())


if __name__ == "__main__":
    unittest.main()
