#!/usr/bin/env python3
"""Migration script for Issue #228 Phase 5: Migrate tags from JSON to normalized schema.

This script migrates task tags from the legacy JSON column to the normalized
tags/task_tags tables introduced in Phase 1.

Usage:
    python scripts/migrate_tags_to_normalized_schema.py [database_url]

If database_url is not provided, uses the default taskdog database location.

The migration is idempotent - it can be run multiple times safely.
Tasks that have already been migrated (have tag_models populated) are skipped.

Phase 6 Update: Since tags column was removed from TaskModel ORM, the script now
reads the legacy tags column directly via raw SQL queries.
"""

import json
import sys
from pathlib import Path

# Add taskdog-core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "taskdog-core" / "src"))

from sqlalchemy import select, text

from taskdog_core.infrastructure.persistence.database.models import TagModel, TaskModel
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.mappers.tag_resolver import TagResolver
from taskdog_core.shared.xdg_utils import XDGDirectories


def migrate_tags_to_normalized_schema(
    database_url: str | None = None, verbose: bool = True
) -> dict[str, int]:
    """Migrate tags from JSON column to normalized schema.

    Args:
        database_url: Optional SQLAlchemy database URL. If None, uses default location.
        verbose: If True, print progress messages. If False, run silently (useful for tests).

    Returns:
        Dictionary with migration statistics:
        - migrated: Number of tasks migrated
        - skipped: Number of tasks skipped (already migrated or no tags)
        - errors: Number of tasks with errors

    Raises:
        Exception: If migration fails catastrophically
    """
    # Use default database if not specified
    if database_url is None:
        db_path = XDGDirectories.get_data_home() / "tasks.db"
        database_url = f"sqlite:///{db_path}"

    if verbose:
        print(f"Starting migration for database: {database_url}")
        print("=" * 60)

    # Create repository
    repository = SqliteTaskRepository(database_url)

    stats = {"migrated": 0, "skipped": 0, "errors": 0}

    # Track if we should return early
    should_skip = False

    try:
        with repository.Session() as session:
            # Check if tags column exists before attempting migration
            result = session.execute(text("PRAGMA table_info(tasks)"))
            columns = [row[1] for row in result]  # column name is at index 1

            if "tags" not in columns:
                if verbose:
                    print("Legacy tags column does not exist - migration already completed.")
                    print("Skipping migration.")
                # Count all tasks as skipped since migration is already done
                stmt = select(TaskModel)
                tasks = session.scalars(stmt).all()
                stats["skipped"] = len(tasks)
                # Mark for early return
                should_skip = True

            # Skip migration if tags column doesn't exist
            if not should_skip:
                # Create TagResolver for this session
                tag_resolver = TagResolver(session)

                # Query all tasks
                stmt = select(TaskModel)
                tasks = session.scalars(stmt).all()

                total_tasks = len(tasks)
                if verbose:
                    print(f"Found {total_tasks} tasks in database")
                    print()

                # Phase 6: Read legacy tags column directly from database
                # (tags column no longer exists in TaskModel ORM)
                tags_map = {}
                result = session.execute(text("SELECT id, tags FROM tasks"))
                for row in result:
                    tags_map[row[0]] = row[1]  # task_id -> tags JSON string

                for i, task_model in enumerate(tasks, 1):
                    task_id = task_model.id
                    task_name = task_model.name

                    # Progress indicator
                    if verbose and (i % 100 == 0 or i == total_tasks):
                        print(f"Progress: {i}/{total_tasks} tasks processed...")

                    try:
                        # Check if already migrated (has tag_models)
                        if task_model.tag_models:
                            stats["skipped"] += 1
                            continue

                        # Get JSON tags from raw SQL query result
                        json_tags = tags_map.get(task_id, "[]")
                        if not json_tags or json_tags == "[]":
                            # No tags to migrate
                            stats["skipped"] += 1
                            continue

                        try:
                            tag_names = json.loads(json_tags)
                        except json.JSONDecodeError as e:
                            if verbose:
                                print(
                                    f"  WARNING: Task {task_id} ({task_name}) has invalid JSON: {e}"
                                )
                                print(f"           JSON content: {json_tags[:100]}")
                            stats["errors"] += 1
                            continue

                        if not tag_names:
                            # Empty tag list
                            stats["skipped"] += 1
                            continue

                        # Migrate tags to normalized schema
                        tag_ids = tag_resolver.resolve_tag_names_to_ids(tag_names)

                        # Fetch TagModel instances
                        tag_stmt = select(TagModel).where(TagModel.id.in_(tag_ids))
                        tag_models = session.scalars(tag_stmt).all()

                        # Associate tags with task
                        task_model.tag_models.extend(tag_models)

                        stats["migrated"] += 1

                    except Exception as e:
                        if verbose:
                            print(f"  ERROR: Failed to migrate task {task_id} ({task_name}): {e}")
                        stats["errors"] += 1
                        continue

                # Commit all changes
                session.commit()
                if verbose:
                    print()
                    print("Migration committed successfully!")

                # Phase 7: Drop the legacy tags column from tasks table
                # (Safe to do after data migration is complete)
                if verbose:
                    print()
                    print("Dropping legacy tags column from tasks table...")

                try:
                    # Check if tags column still exists
                    result = session.execute(text("PRAGMA table_info(tasks)"))
                    columns = [row[1] for row in result]  # column name is at index 1

                    if "tags" in columns:
                        # Drop the column
                        session.execute(text("ALTER TABLE tasks DROP COLUMN tags"))
                        session.commit()
                        if verbose:
                            print("✓ Legacy tags column dropped successfully")
                    else:
                        if verbose:
                            print("  (tags column already removed, skipping)")
                except Exception as e:
                    if verbose:
                        print(f"  WARNING: Could not drop tags column: {e}")
                        print("  This is not critical - the column can be removed manually later")
                    # Don't fail the entire migration if column drop fails
                    pass

    except Exception as e:
        if verbose:
            print(f"\nFATAL ERROR: Migration failed: {e}")
        raise

    finally:
        repository.close()

    # Print summary
    if verbose:
        print()
        print("=" * 60)
        print("Migration Summary:")
        print(f"  Total tasks:     {total_tasks}")
        print(f"  Migrated:        {stats['migrated']}")
        print(f"  Skipped:         {stats['skipped']}")
        print(f"  Errors:          {stats['errors']}")
        print("=" * 60)

    return stats


def main() -> int:
    """Main entry point for command-line execution.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    database_url = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        stats = migrate_tags_to_normalized_schema(database_url)
        return 0 if stats["errors"] == 0 else 1
    except Exception as e:
        print(f"\nMigration failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
