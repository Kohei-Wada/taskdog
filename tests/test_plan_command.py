"""Test cases for plan command"""

import unittest
import tempfile
import os
from unittest.mock import MagicMock
from click.testing import CliRunner
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from domain.entities.task import Task
from presentation.cli.commands.plan import plan_command


class TestPlanCommand(unittest.TestCase):
    """Test cases for plan command"""

    def setUp(self):
        """Create temporary file and initialize repository for each test"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.runner = CliRunner()

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_plan_with_duration_only(self):
        """Test planning with only estimated duration"""
        # Create a task
        created_task = self.repository.create(name="Test Task", priority=1)

        # Run plan command with duration only
        result = self.runner.invoke(
            plan_command,
            [str(created_task.id), "2.5"],
            obj={"console": MagicMock(), "repository": self.repository},
        )

        self.assertEqual(result.exit_code, 0)

        # Verify the task was updated
        updated_task = self.repository.get_by_id(created_task.id)
        self.assertEqual(updated_task.estimated_duration, 2.5)
        self.assertIsNone(updated_task.planned_start)
        self.assertIsNone(updated_task.planned_end)

    def test_plan_with_duration_and_start(self):
        """Test planning with duration and start date"""
        # Create a task
        created_task = self.repository.create(name="Test Task", priority=1)

        # Run plan command with duration and start
        result = self.runner.invoke(
            plan_command,
            [str(created_task.id), "3.0", "2025-10-15"],
            obj={"console": MagicMock(), "repository": self.repository},
        )

        self.assertEqual(result.exit_code, 0)

        # Verify the task was updated
        updated_task = self.repository.get_by_id(created_task.id)
        self.assertEqual(updated_task.estimated_duration, 3.0)
        self.assertEqual(updated_task.planned_start, "2025-10-15 18:00:00")
        self.assertIsNone(updated_task.planned_end)

    def test_plan_with_all_arguments(self):
        """Test planning with all arguments"""
        # Create a task
        created_task = self.repository.create(name="Test Task", priority=1)

        # Run plan command with all arguments
        result = self.runner.invoke(
            plan_command,
            [str(created_task.id), "4.5", "2025-10-15", "2025-10-17"],
            obj={"console": MagicMock(), "repository": self.repository},
        )

        self.assertEqual(result.exit_code, 0)

        # Verify the task was updated
        updated_task = self.repository.get_by_id(created_task.id)
        self.assertEqual(updated_task.estimated_duration, 4.5)
        self.assertEqual(updated_task.planned_start, "2025-10-15 18:00:00")
        self.assertEqual(updated_task.planned_end, "2025-10-17 18:00:00")

    def test_plan_with_datetime_strings(self):
        """Test planning with full datetime strings"""
        # Create a task
        created_task = self.repository.create(name="Test Task", priority=1)

        # Run plan command with full datetime strings
        result = self.runner.invoke(
            plan_command,
            [
                str(created_task.id),
                "2.0",
                "2025-10-15 09:00:00",
                "2025-10-15 17:00:00",
            ],
            obj={"console": MagicMock(), "repository": self.repository},
        )

        self.assertEqual(result.exit_code, 0)

        # Verify the task was updated
        updated_task = self.repository.get_by_id(created_task.id)
        self.assertEqual(updated_task.estimated_duration, 2.0)
        self.assertEqual(updated_task.planned_start, "2025-10-15 09:00:00")
        self.assertEqual(updated_task.planned_end, "2025-10-15 17:00:00")

    def test_plan_with_invalid_task_id(self):
        """Test planning with non-existent task ID"""
        # Run plan command with invalid task ID
        result = self.runner.invoke(
            plan_command,
            ["999", "2.5"],
            obj={"console": MagicMock(), "repository": self.repository},
        )

        # Error handler catches the exception and prints error message
        # Exit code is 0 since error is handled gracefully
        self.assertEqual(result.exit_code, 0)

    def test_plan_updates_existing_values(self):
        """Test that plan command can update existing planning values"""
        # Create a task with initial planning values
        created_task = self.repository.create(
            name="Test Task",
            priority=1,
            estimated_duration=1.0,
            planned_start="2025-10-10 18:00:00",
        )

        # Run plan command to update values
        result = self.runner.invoke(
            plan_command,
            [str(created_task.id), "5.0", "2025-10-20"],
            obj={"console": MagicMock(), "repository": self.repository},
        )

        self.assertEqual(result.exit_code, 0)

        # Verify the values were updated
        updated_task = self.repository.get_by_id(created_task.id)
        self.assertEqual(updated_task.estimated_duration, 5.0)
        self.assertEqual(updated_task.planned_start, "2025-10-20 18:00:00")


if __name__ == "__main__":
    unittest.main()
