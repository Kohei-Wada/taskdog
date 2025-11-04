#!/usr/bin/env python3
"""Rollback script to move tasks from SQLite back to JSON.

This script:
1. Reads all tasks from the SQLite database
2. Creates a backup of the current JSON file (if exists)
3. Exports all tasks to JSON format
4. Verifies the rollback was successful

Usage:
    PYTHONPATH=src python scripts/rollback_sqlite_to_json.py [--database-url URL]

Options:
    --database-url URL    Custom SQLite database URL (default: XDG data directory)
    --dry-run            Show what would be exported without making changes
    --force              Skip confirmation prompt
    --help               Show this help message
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.persistence.database.sqlite_task_repository import SqliteTaskRepository
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper
from infrastructure.persistence.mappers.task_json_mapper import TaskJsonMapper
from shared.xdg_utils import XDGDirectories


class RollbackError(Exception):
    """Raised when rollback fails."""

    pass


def create_backup(json_file: Path) -> Path | None:
    """Create a timestamped backup of the JSON file if it exists.

    Args:
        json_file: Path to the JSON tasks file

    Returns:
        Path to the backup file, or None if file doesn't exist
    """
    if not json_file.exists():
        print("  (No existing JSON file to backup)")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = json_file.with_suffix(f".{timestamp}.backup.json")

    try:
        shutil.copy2(json_file, backup_file)
        print(f"✓ Created backup: {backup_file}")
        return backup_file
    except Exception as e:
        raise RollbackError(f"Failed to create backup: {e}")


def load_sqlite_tasks(database_url: str) -> list:
    """Load all tasks from SQLite repository.

    Args:
        database_url: SQLite database URL

    Returns:
        List of Task entities

    Raises:
        RollbackError: If loading fails
    """
    try:
        mapper = TaskDbMapper()
        repository = SqliteTaskRepository(database_url, mapper)
        tasks = repository.get_all()
        repository.close()
        print(f"✓ Loaded {len(tasks)} tasks from SQLite")
        return tasks
    except Exception as e:
        raise RollbackError(f"Failed to load tasks from SQLite: {e}")


def export_to_json(tasks: list, json_file: Path) -> None:
    """Export tasks to JSON file.

    Args:
        tasks: List of Task entities to export
        json_file: Path to the JSON tasks file

    Raises:
        RollbackError: If export fails
    """
    try:
        mapper = TaskJsonMapper()
        repository = JsonTaskRepository(str(json_file), mapper)

        # Save all tasks
        repository.save_all(tasks)
        print(f"✓ Exported {len(tasks)} tasks to JSON")

        # Verify export
        exported_tasks = repository.get_all()
        if len(exported_tasks) != len(tasks):
            raise RollbackError(
                f"Verification failed: Expected {len(tasks)} tasks, found {len(exported_tasks)}"
            )

        print(f"✓ Verified: {len(exported_tasks)} tasks in JSON file")

    except Exception as e:
        raise RollbackError(f"Failed to export to JSON: {e}")


def verify_rollback(json_file: Path, database_url: str) -> bool:
    """Verify that rollback was successful by comparing task counts and IDs.

    Args:
        json_file: Path to the JSON tasks file
        database_url: SQLite database URL

    Returns:
        True if verification passes

    Raises:
        RollbackError: If verification fails
    """
    try:
        # Load from JSON
        json_mapper = TaskJsonMapper()
        json_repo = JsonTaskRepository(str(json_file), json_mapper)
        json_tasks = json_repo.get_all()
        json_ids = {task.id for task in json_tasks}

        # Load from SQLite
        db_mapper = TaskDbMapper()
        db_repo = SqliteTaskRepository(database_url, db_mapper)
        db_tasks = db_repo.get_all()
        db_ids = {task.id for task in db_tasks}
        db_repo.close()

        # Compare
        if json_ids != db_ids:
            missing_in_json = db_ids - json_ids
            extra_in_json = json_ids - db_ids
            error_msg = "Task ID mismatch:\n"
            if missing_in_json:
                error_msg += f"  Missing in JSON: {missing_in_json}\n"
            if extra_in_json:
                error_msg += f"  Extra in JSON: {extra_in_json}\n"
            raise RollbackError(error_msg)

        print(f"✓ Verification passed: All {len(json_tasks)} task IDs match")
        return True

    except Exception as e:
        raise RollbackError(f"Verification failed: {e}")


def main() -> int:
    """Main rollback script entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Rollback tasks from SQLite to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--database-url",
        help="Custom SQLite database URL (default: XDG data directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Taskdog: SQLite → JSON Rollback")
    print("=" * 70)
    print()

    # Determine paths
    json_file = XDGDirectories.get_tasks_file()

    if args.database_url:
        database_url = args.database_url
    else:
        data_dir = XDGDirectories.get_data_home()
        db_file = data_dir / "tasks.db"
        database_url = f"sqlite:///{db_file}"

    print(f"Source (SQLite): {database_url}")
    print(f"Target (JSON):   {json_file}")
    print()

    # Check if SQLite database exists
    if args.database_url:
        # Custom URL, assume it exists
        pass
    else:
        data_dir = XDGDirectories.get_data_home()
        db_file = data_dir / "tasks.db"
        if not db_file.exists():
            print("✗ Error: No SQLite database found")
            print(f"  Expected location: {db_file}")
            print()
            print("Nothing to rollback. Exiting.")
            return 0

    # Load tasks to show what will be exported
    try:
        tasks = load_sqlite_tasks(database_url)
    except RollbackError as e:
        print(f"✗ Error: {e}")
        return 1

    if len(tasks) == 0:
        print("No tasks found in SQLite database. Nothing to rollback.")
        return 0

    print()
    print(f"This will export {len(tasks)} tasks from SQLite to JSON.")
    print()

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print()
        print("Tasks to be exported:")
        for i, task in enumerate(tasks[:5], 1):
            print(f"  {i}. [{task.id}] {task.name} (status: {task.status.value})")
        if len(tasks) > 5:
            print(f"  ... and {len(tasks) - 5} more tasks")
        print()
        print("Run without --dry-run to perform the rollback.")
        return 0

    # Confirmation prompt
    if not args.force:
        print("⚠️  WARNING: This will overwrite your JSON file.")
        print("   Any existing JSON data will be backed up.")
        print()
        response = input("Continue with rollback? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("Rollback cancelled.")
            return 0
        print()

    # Perform rollback
    try:
        # Step 1: Create backup if JSON file exists
        backup_file = create_backup(json_file)

        # Step 2: Export to JSON
        export_to_json(tasks, json_file)

        # Step 3: Verify rollback
        verify_rollback(json_file, database_url)

        print()
        print("=" * 70)
        print("✓ Rollback completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Update your config file (~/.config/taskdog/config.toml):")
        print("   [storage]")
        print('   backend = "json"')
        print()
        print("2. Test the JSON backend:")
        print("   taskdog table")
        print()
        if backup_file:
            print("3. If everything works, you can delete the backup:")
            print(f"   rm {backup_file}")
            print()
        print("Your SQLite database is preserved if you need to migrate again.")
        print()

        return 0

    except RollbackError as e:
        print()
        print("=" * 70)
        print("✗ Rollback failed!")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        if backup_file:
            print("Your previous JSON file backup is available:")
            print(f"  {backup_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
