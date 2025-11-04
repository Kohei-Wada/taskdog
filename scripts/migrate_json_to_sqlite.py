#!/usr/bin/env python3
"""Migration script to move tasks from JSON to SQLite database.

This script:
1. Reads all tasks from the existing JSON file
2. Creates a backup of the JSON file
3. Migrates all tasks to SQLite database
4. Verifies the migration was successful
5. Provides rollback instructions if needed

Usage:
    PYTHONPATH=src python scripts/migrate_json_to_sqlite.py [--database-url URL]

Options:
    --database-url URL    Custom SQLite database URL (default: XDG data directory)
    --dry-run            Show what would be migrated without making changes
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


class MigrationError(Exception):
    """Raised when migration fails."""

    pass


def create_backup(json_file: Path) -> Path:
    """Create a timestamped backup of the JSON file.

    Args:
        json_file: Path to the JSON tasks file

    Returns:
        Path to the backup file

    Raises:
        MigrationError: If backup creation fails
    """
    if not json_file.exists():
        raise MigrationError(f"JSON file not found: {json_file}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = json_file.with_suffix(f".{timestamp}.backup.json")

    try:
        shutil.copy2(json_file, backup_file)
        print(f"✓ Created backup: {backup_file}")
        return backup_file
    except Exception as e:
        raise MigrationError(f"Failed to create backup: {e}")


def load_json_tasks(json_file: Path) -> list:
    """Load all tasks from JSON repository.

    Args:
        json_file: Path to the JSON tasks file

    Returns:
        List of Task entities

    Raises:
        MigrationError: If loading fails
    """
    try:
        mapper = TaskJsonMapper()
        repository = JsonTaskRepository(str(json_file), mapper)
        tasks = repository.get_all()
        print(f"✓ Loaded {len(tasks)} tasks from JSON")
        return tasks
    except Exception as e:
        raise MigrationError(f"Failed to load tasks from JSON: {e}")


def migrate_to_sqlite(tasks: list, database_url: str) -> None:
    """Migrate tasks to SQLite database.

    Args:
        tasks: List of Task entities to migrate
        database_url: SQLite database URL

    Raises:
        MigrationError: If migration fails
    """
    try:
        mapper = TaskDbMapper()
        repository = SqliteTaskRepository(database_url, mapper)

        # Save all tasks
        repository.save_all(tasks)
        print(f"✓ Migrated {len(tasks)} tasks to SQLite")

        # Verify migration
        migrated_tasks = repository.get_all()
        if len(migrated_tasks) != len(tasks):
            raise MigrationError(
                f"Verification failed: Expected {len(tasks)} tasks, found {len(migrated_tasks)}"
            )

        print(f"✓ Verified: {len(migrated_tasks)} tasks in SQLite database")
        repository.close()

    except Exception as e:
        raise MigrationError(f"Failed to migrate to SQLite: {e}")


def verify_migration(json_file: Path, database_url: str) -> bool:
    """Verify that migration was successful by comparing task counts and IDs.

    Args:
        json_file: Path to the JSON tasks file
        database_url: SQLite database URL

    Returns:
        True if verification passes

    Raises:
        MigrationError: If verification fails
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
            missing_in_db = json_ids - db_ids
            extra_in_db = db_ids - json_ids
            error_msg = "Task ID mismatch:\n"
            if missing_in_db:
                error_msg += f"  Missing in DB: {missing_in_db}\n"
            if extra_in_db:
                error_msg += f"  Extra in DB: {extra_in_db}\n"
            raise MigrationError(error_msg)

        print(f"✓ Verification passed: All {len(json_tasks)} task IDs match")
        return True

    except Exception as e:
        raise MigrationError(f"Verification failed: {e}")


def main() -> int:
    """Main migration script entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Migrate tasks from JSON to SQLite database",
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
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Taskdog: JSON → SQLite Migration")
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

    print(f"Source (JSON):  {json_file}")
    print(f"Target (SQLite): {database_url}")
    print()

    # Check if JSON file exists
    if not json_file.exists():
        print("✗ Error: No JSON tasks file found")
        print(f"  Expected location: {json_file}")
        print()
        print("Nothing to migrate. Exiting.")
        return 0

    # Load tasks to show what will be migrated
    try:
        tasks = load_json_tasks(json_file)
    except MigrationError as e:
        print(f"✗ Error: {e}")
        return 1

    if len(tasks) == 0:
        print("No tasks found in JSON file. Nothing to migrate.")
        return 0

    print()
    print(f"This will migrate {len(tasks)} tasks from JSON to SQLite.")
    print()

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print()
        print("Tasks to be migrated:")
        for i, task in enumerate(tasks[:5], 1):
            print(f"  {i}. [{task.id}] {task.name} (status: {task.status.value})")
        if len(tasks) > 5:
            print(f"  ... and {len(tasks) - 5} more tasks")
        print()
        print("Run without --dry-run to perform the migration.")
        return 0

    # Confirmation prompt
    if not args.force:
        print("⚠️  WARNING: This will create a new SQLite database.")
        print("   Your JSON file will be backed up but not modified.")
        print()
        response = input("Continue with migration? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("Migration cancelled.")
            return 0
        print()

    # Perform migration
    try:
        # Step 1: Create backup
        backup_file = create_backup(json_file)

        # Step 2: Migrate to SQLite
        migrate_to_sqlite(tasks, database_url)

        # Step 3: Verify migration
        verify_migration(json_file, database_url)

        print()
        print("=" * 70)
        print("✓ Migration completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Update your config file (~/.config/taskdog/config.toml):")
        print("   [storage]")
        print('   backend = "sqlite"')
        print()
        print("2. Test the new SQLite backend:")
        print("   taskdog table")
        print()
        print("3. If everything works, you can delete the backup:")
        print(f"   rm {backup_file}")
        print()
        print("To rollback, run:")
        print("   PYTHONPATH=src python scripts/rollback_sqlite_to_json.py")
        print()

        return 0

    except MigrationError as e:
        print()
        print("=" * 70)
        print("✗ Migration failed!")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        print("Your JSON file is unchanged. No data has been lost.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
