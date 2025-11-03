"""Tests for JsonTaskStorage."""

import json
import tempfile
import unittest
from pathlib import Path

from domain.entities.task import Task
from domain.exceptions.task_exceptions import CorruptedDataError
from infrastructure.persistence.json_task_storage import JsonTaskStorage
from shared.constants.file_management import BACKUP_FILE_SUFFIX


class TestJsonTaskStorage(unittest.TestCase):
    """Test suite for JsonTaskStorage."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.storage = JsonTaskStorage()
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = str(Path(self.temp_dir) / "tasks.json")
        self.task1 = Task(id=1, name="Test Task 1", priority=1)
        self.task2 = Task(id=2, name="Test Task 2", priority=2)

    def tearDown(self) -> None:
        """Clean up test files."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_load_returns_empty_list_when_file_does_not_exist(self) -> None:
        """Test load returns empty list when file doesn't exist."""
        result = self.storage.load(self.test_file)

        self.assertEqual(result, [])

    def test_load_returns_empty_list_when_file_is_empty(self) -> None:
        """Test load returns empty list when file is empty."""
        Path(self.test_file).write_text("", encoding="utf-8")

        result = self.storage.load(self.test_file)

        self.assertEqual(result, [])

    def test_load_returns_empty_list_when_file_has_only_whitespace(self) -> None:
        """Test load returns empty list when file contains only whitespace."""
        Path(self.test_file).write_text("  \n\t  \n", encoding="utf-8")

        result = self.storage.load(self.test_file)

        self.assertEqual(result, [])

    def test_load_returns_tasks_when_file_has_valid_json(self) -> None:
        """Test load returns tasks when file contains valid JSON."""
        tasks_data = [self.task1.to_dict(), self.task2.to_dict()]
        Path(self.test_file).write_text(
            json.dumps(tasks_data, indent=4, ensure_ascii=False), encoding="utf-8"
        )

        result = self.storage.load(self.test_file)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "Test Task 1")
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[1].name, "Test Task 2")

    def test_load_raises_os_error_when_json_is_corrupted_and_no_backup(self) -> None:
        """Test load raises OSError when JSON is corrupted and no backup exists."""
        Path(self.test_file).write_text("{invalid json", encoding="utf-8")

        with self.assertRaises(OSError) as cm:
            self.storage.load(self.test_file)

        self.assertIn("corrupted data file", str(cm.exception))

    def test_load_falls_back_to_backup_when_main_file_is_corrupted(self) -> None:
        """Test load loads from backup when main file is corrupted."""
        # Create valid backup
        backup_file = Path(self.test_file).with_suffix(BACKUP_FILE_SUFFIX)
        tasks_data = [self.task1.to_dict()]
        backup_file.write_text(
            json.dumps(tasks_data, indent=4, ensure_ascii=False), encoding="utf-8"
        )

        # Create corrupted main file
        Path(self.test_file).write_text("{corrupted", encoding="utf-8")

        result = self.storage.load(self.test_file)

        # Should load from backup and restore main file
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "Test Task 1")
        # Main file should be restored from backup
        self.assertTrue(Path(self.test_file).exists())

    def test_load_raises_os_error_when_both_main_and_backup_are_corrupted(
        self,
    ) -> None:
        """Test load raises OSError when both main and backup are corrupted."""
        # Create corrupted main file
        Path(self.test_file).write_text("{corrupted", encoding="utf-8")

        # Create corrupted backup
        backup_file = Path(self.test_file).with_suffix(BACKUP_FILE_SUFFIX)
        backup_file.write_text("{also corrupted", encoding="utf-8")

        with self.assertRaises(OSError):
            self.storage.load(self.test_file)

    def test_load_raises_corrupted_data_error_when_task_validation_fails(self) -> None:
        """Test load raises CorruptedDataError when task data is invalid."""
        # Create invalid task data (empty name violates entity invariant)
        invalid_task_data = [{"id": 1, "name": "", "priority": 1}]
        Path(self.test_file).write_text(json.dumps(invalid_task_data, indent=4), encoding="utf-8")

        with self.assertRaises(CorruptedDataError) as cm:
            self.storage.load(self.test_file)

        # Should include error details
        self.assertTrue(len(cm.exception.corrupted_tasks) > 0)

    def test_save_creates_file_with_tasks(self) -> None:
        """Test save creates file with task data."""
        tasks = [self.task1, self.task2]

        self.storage.save(self.test_file, tasks)

        # Verify file exists and has correct content
        self.assertTrue(Path(self.test_file).exists())
        loaded_tasks = self.storage.load(self.test_file)
        self.assertEqual(len(loaded_tasks), 2)
        self.assertEqual(loaded_tasks[0].id, 1)
        self.assertEqual(loaded_tasks[1].id, 2)

    def test_save_creates_parent_directory_if_not_exists(self) -> None:
        """Test save creates parent directories if they don't exist."""
        nested_file = str(Path(self.temp_dir) / "nested" / "dir" / "tasks.json")

        self.storage.save(nested_file, [self.task1])

        self.assertTrue(Path(nested_file).exists())

    def test_save_creates_backup_of_existing_file(self) -> None:
        """Test save creates backup before overwriting existing file."""
        # Create initial file
        self.storage.save(self.test_file, [self.task1])
        initial_content = Path(self.test_file).read_text(encoding="utf-8")

        # Update with new data
        self.storage.save(self.test_file, [self.task2])

        # Verify backup contains old data
        backup_file = Path(self.test_file).with_suffix(BACKUP_FILE_SUFFIX)
        self.assertTrue(backup_file.exists())
        self.assertEqual(backup_file.read_text(encoding="utf-8"), initial_content)

    def test_save_overwrites_existing_file(self) -> None:
        """Test save overwrites existing file with new data."""
        # Create initial file
        self.storage.save(self.test_file, [self.task1])

        # Update with new data
        new_task = Task(id=99, name="Updated Task", priority=5)
        self.storage.save(self.test_file, [new_task])

        # Verify file has new data
        loaded_tasks = self.storage.load(self.test_file)
        self.assertEqual(len(loaded_tasks), 1)
        self.assertEqual(loaded_tasks[0].id, 99)
        self.assertEqual(loaded_tasks[0].name, "Updated Task")

    def test_save_preserves_unicode_characters(self) -> None:
        """Test save preserves Unicode and emoji characters."""
        task_with_unicode = Task(id=1, name="タスク 🚀 Test", priority=1)

        self.storage.save(self.test_file, [task_with_unicode])

        loaded_tasks = self.storage.load(self.test_file)
        self.assertEqual(loaded_tasks[0].name, "タスク 🚀 Test")

    def test_save_formats_json_with_indentation(self) -> None:
        """Test save formats JSON with proper indentation for readability."""
        self.storage.save(self.test_file, [self.task1])

        content = Path(self.test_file).read_text(encoding="utf-8")
        # Check that JSON is indented (contains newlines and spaces)
        self.assertIn("\n", content)
        self.assertIn("    ", content)

    def test_save_with_empty_list(self) -> None:
        """Test save handles empty task list."""
        self.storage.save(self.test_file, [])

        loaded_tasks = self.storage.load(self.test_file)
        self.assertEqual(loaded_tasks, [])

    def test_save_cleans_up_temp_file_on_error(self) -> None:
        """Test save cleans up temporary file when write fails."""
        # Create a file path that will cause write to fail
        invalid_file = "/nonexistent/directory/tasks.json"

        with self.assertRaises(OSError):
            self.storage.save(invalid_file, [self.task1])

        # Note: This test mainly ensures the cleanup code path is exercised
        # We can't reliably verify temp file cleanup in temp directory due to other processes

    def test_save_and_load_round_trip_with_all_task_fields(self) -> None:
        """Test save/load round-trip preserves all task fields."""
        # Save task2 which has all fields populated
        self.storage.save(self.test_file, [self.task2])
        loaded_tasks = self.storage.load(self.test_file)

        loaded_task = loaded_tasks[0]
        self.assertEqual(loaded_task.id, self.task2.id)
        self.assertEqual(loaded_task.name, self.task2.name)
        self.assertEqual(loaded_task.priority, self.task2.priority)

    def test_save_handles_none_values_correctly(self) -> None:
        """Test save handles None values in task fields."""
        task_with_nones = Task(
            id=1,
            name="Task with Nones",
            priority=1,
            planned_start=None,
            planned_end=None,
            deadline=None,
            estimated_duration=None,
        )

        self.storage.save(self.test_file, [task_with_nones])
        loaded_tasks = self.storage.load(self.test_file)

        loaded_task = loaded_tasks[0]
        self.assertIsNone(loaded_task.planned_start)
        self.assertIsNone(loaded_task.planned_end)
        self.assertIsNone(loaded_task.deadline)
        self.assertIsNone(loaded_task.estimated_duration)

    def test_load_from_backup_when_backup_is_empty(self) -> None:
        """Test load handles empty backup file gracefully."""
        # Create empty backup
        backup_file = Path(self.test_file).with_suffix(BACKUP_FILE_SUFFIX)
        backup_file.write_text("", encoding="utf-8")

        # Create corrupted main file
        Path(self.test_file).write_text("{corrupted", encoding="utf-8")

        result = self.storage.load(self.test_file)

        # Should return empty list from backup
        self.assertEqual(result, [])

    def test_parse_tasks_with_mixed_valid_and_invalid_data(self) -> None:
        """Test _parse_tasks collects all corrupted tasks."""
        tasks_data = [
            {"id": 1, "name": "Valid Task", "priority": 1},
            {"id": 2, "name": "", "priority": 2},  # Invalid: empty name
            {"id": 3, "name": "Another Valid", "priority": 3},
            {"id": 4, "name": "Invalid Priority", "priority": -1},  # Invalid: negative priority
        ]

        with self.assertRaises(CorruptedDataError) as cm:
            self.storage._parse_tasks(tasks_data)

        # Should report both corrupted tasks
        self.assertEqual(len(cm.exception.corrupted_tasks), 2)
        corrupted_ids = [t["data"]["id"] for t in cm.exception.corrupted_tasks]
        self.assertIn(2, corrupted_ids)
        self.assertIn(4, corrupted_ids)


if __name__ == "__main__":
    unittest.main()
