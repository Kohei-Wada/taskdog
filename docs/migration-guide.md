# Migration Guide: JSON to SQLite

This guide explains how to migrate your task data from JSON storage to SQLite database.

## Why Migrate to SQLite?

**Benefits of SQLite**:
- **Performance**: Faster queries with database indexes (O(1) lookups)
- **Reliability**: ACID transactions ensure data consistency
- **Scalability**: Handles 1000+ tasks efficiently
- **Concurrency**: Better support for concurrent access
- **Data Integrity**: Database constraints prevent invalid data

**When to Migrate**:
- You have a large number of tasks (100+)
- You want better performance
- You need concurrent access (multiple processes/terminals)
- You want database-level data validation

**When to Stay on JSON**:
- You have a small number of tasks (<50)
- You prefer simple file-based storage
- You want easy manual editing of task data
- Current performance is sufficient

## Prerequisites

1. **Backup Your Data** (automatically done by migration script)
2. **Install Taskdog** with SQLite support (already included)
3. **Stop All Taskdog Instances** (close any running terminals with taskdog)

## Migration Process

### Step 1: Dry Run (Optional but Recommended)

First, run the migration in dry-run mode to see what will be migrated:

```bash
PYTHONPATH=src python scripts/migrate_json_to_sqlite.py --dry-run
```

This shows:
- Number of tasks to be migrated
- Sample of tasks (first 5)
- Source and target locations

### Step 2: Run Migration

Execute the migration script:

```bash
PYTHONPATH=src python scripts/migrate_json_to_sqlite.py
```

The script will:
1. ✓ Create backup of your JSON file (`tasks.YYYYMMDD_HHMMSS.backup.json`)
2. ✓ Load all tasks from JSON
3. ✓ Migrate tasks to SQLite database
4. ✓ Verify migration success (compare task IDs and counts)
5. ✓ Display next steps

**Interactive Confirmation**:
```
Source (JSON):  /home/user/.local/share/taskdog/tasks.json
Target (SQLite): sqlite:////home/user/.local/share/taskdog/tasks.db

This will migrate 42 tasks from JSON to SQLite.

⚠️  WARNING: This will create a new SQLite database.
   Your JSON file will be backed up but not modified.

Continue with migration? [y/N]:
```

Type `y` and press Enter to proceed.

### Step 3: Update Configuration

After successful migration, update your config file:

```bash
# Create config if it doesn't exist
mkdir -p ~/.config/taskdog
nano ~/.config/taskdog/config.toml
```

Add:
```toml
[storage]
backend = "sqlite"
```

### Step 4: Test SQLite Backend

Verify everything works with the new backend:

```bash
# List all tasks
taskdog table

# Show a specific task
taskdog show 1

# Create a test task
taskdog add "Test SQLite Task"

# Remove test task
taskdog rm <id>
```

If everything works correctly, your migration is complete!

### Step 5: Clean Up (Optional)

Once you've verified the SQLite backend works:

```bash
# Remove the JSON backup (only if everything works!)
rm ~/.local/share/taskdog/tasks.*.backup.json

# Keep the original tasks.json as a backup
# You can delete it later when you're confident
```

## Advanced Options

### Custom Database Location

Migrate to a custom database location:

```bash
PYTHONPATH=src python scripts/migrate_json_to_sqlite.py \
  --database-url "sqlite:////custom/path/tasks.db"
```

Then update your config:
```toml
[storage]
backend = "sqlite"
database_url = "sqlite:////custom/path/tasks.db"
```

### Skip Confirmation

For automated/scripted migrations:

```bash
PYTHONPATH=src python scripts/migrate_json_to_sqlite.py --force
```

## Rollback to JSON

If you need to rollback to JSON storage:

### Step 1: Run Rollback Script

```bash
PYTHONPATH=src python scripts/rollback_sqlite_to_json.py
```

This will:
1. ✓ Backup current JSON file (if exists)
2. ✓ Export all tasks from SQLite to JSON
3. ✓ Verify export success

### Step 2: Update Configuration

```toml
[storage]
backend = "json"
```

### Step 3: Test JSON Backend

```bash
taskdog table
```

## Troubleshooting

### Migration Failed: "JSON file not found"

**Problem**: No existing JSON file to migrate.

**Solution**: Nothing to migrate. You can start fresh with SQLite:
```toml
[storage]
backend = "sqlite"
```

### Migration Failed: "Verification failed"

**Problem**: Task counts or IDs don't match after migration.

**Solution**:
1. Check the error message for specific mismatches
2. Your JSON file is unchanged (safe to retry)
3. Report the issue with error details

### "No such table: tasks" Error

**Problem**: SQLite database wasn't initialized properly.

**Solution**: Delete the database and retry:
```bash
rm ~/.local/share/taskdog/tasks.db
PYTHONPATH=src python scripts/migrate_json_to_sqlite.py
```

### Tasks Not Showing After Migration

**Problem**: Config file still points to JSON backend.

**Solution**: Update config:
```toml
[storage]
backend = "sqlite"
```

### Want to Migrate Again After Changes

**Problem**: Made changes in JSON, want to re-migrate.

**Solution**:
1. Delete existing SQLite database:
   ```bash
   rm ~/.local/share/taskdog/tasks.db
   ```
2. Run migration again:
   ```bash
   PYTHONPATH=src python scripts/migrate_json_to_sqlite.py --force
   ```

## Hybrid Mode (Advanced)

For a transition period, you can use both backends:

1. **Keep JSON as primary**: `backend = "json"` (default)
2. **Test SQLite separately**: Use custom database URL for testing
3. **Switch when ready**: Change config to `backend = "sqlite"`

## Data Safety

### Backups

The migration script automatically creates backups:
- `tasks.YYYYMMDD_HHMMSS.backup.json` - Timestamped JSON backup

### No Data Loss

- ✓ Original JSON file is **never modified** during migration
- ✓ Automatic backups created before any changes
- ✓ Verification step ensures all data was migrated
- ✓ Rollback script available if needed

### What Gets Migrated

**All task fields**:
- ID, name, priority, status
- Timestamps (created_at, updated_at)
- Schedule (planned_start, planned_end, deadline)
- Time tracking (actual_start, actual_end)
- Estimated duration and is_fixed flag
- Daily allocations and actual hours
- Dependencies (depends_on list)
- Tags
- Archive status

**Format**:
- Complex fields (daily_allocations, tags, etc.) stored as JSON TEXT columns
- All datetime fields preserved with precision
- Task IDs preserved (no renumbering)

## Performance Comparison

### JSON Backend
- **Load time**: O(n) - reads entire file
- **Query**: O(n) - scans all tasks
- **Save**: O(n) - writes entire file
- **Good for**: <50 tasks

### SQLite Backend
- **Load time**: O(1) with caching
- **Query**: O(1) with indexes
- **Save**: O(1) with transactions
- **Good for**: Any size, especially 100+ tasks

## FAQ

**Q: Can I use both JSON and SQLite?**
A: Not simultaneously. Choose one backend via config. You can switch anytime.

**Q: Will my JSON file be deleted?**
A: No. Migration only reads from JSON. You can delete it manually later.

**Q: Can I edit SQLite database manually?**
A: Yes, with any SQLite client (sqlite3, DB Browser for SQLite, etc.)

**Q: Does migration preserve task IDs?**
A: Yes. All IDs are preserved exactly as they were.

**Q: Can I migrate back to JSON after using SQLite?**
A: Yes. Use the rollback script to export from SQLite to JSON.

**Q: What if migration is interrupted?**
A: Your JSON file is unchanged. Simply run the migration script again.

**Q: Do I need to re-migrate after updates?**
A: No. Once migrated, all changes are saved to SQLite automatically.

## Getting Help

If you encounter issues:

1. Check this guide's troubleshooting section
2. Run with `--dry-run` to see what would happen
3. Examine the backup file to ensure your data is safe
4. Report issues at: https://github.com/Kohei-Wada/taskdog/issues

## Summary

**Migration Steps**:
1. ✓ Run dry-run (optional): `--dry-run`
2. ✓ Run migration: `migrate_json_to_sqlite.py`
3. ✓ Update config: `backend = "sqlite"`
4. ✓ Test: `taskdog table`
5. ✓ Clean up backups (optional)

**Rollback Steps**:
1. ✓ Run rollback: `rollback_sqlite_to_json.py`
2. ✓ Update config: `backend = "json"`
3. ✓ Test: `taskdog table`

Your data is always safe with automatic backups and verification!
