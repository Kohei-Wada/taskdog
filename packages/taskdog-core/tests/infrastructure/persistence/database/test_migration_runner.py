"""Tests for database migration runner."""

from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from taskdog_core.infrastructure.persistence.database.migration_runner import (
    get_current_revision,
    get_migrations_dir,
    run_migrations,
)
from taskdog_core.infrastructure.persistence.database.models.task_model import Base


class TestGetMigrationsDir:
    """Tests for get_migrations_dir function."""

    def test_returns_path_to_migrations(self) -> None:
        """Test that get_migrations_dir returns the correct path."""
        migrations_dir = get_migrations_dir()

        assert migrations_dir.exists()
        assert migrations_dir.is_dir()
        assert migrations_dir.name == "migrations"
        assert (migrations_dir / "env.py").exists()
        assert (migrations_dir / "versions").is_dir()


class TestRunMigrations:
    """Tests for run_migrations function."""

    def test_creates_all_tables_on_fresh_database(self) -> None:
        """Test migrations run correctly on a new in-memory database."""
        engine = create_engine("sqlite:///:memory:")
        try:
            run_migrations(engine)

            inspector = inspect(engine)
            tables = set(inspector.get_table_names())

            # Check all expected tables exist
            assert "tasks" in tables
            assert "tags" in tables
            assert "task_tags" in tables
            assert "audit_logs" in tables
            assert "alembic_version" in tables
        finally:
            engine.dispose()

    def test_creates_alembic_version_table(self) -> None:
        """Test that alembic_version table is created."""
        engine = create_engine("sqlite:///:memory:")
        try:
            run_migrations(engine)

            inspector = inspect(engine)
            assert "alembic_version" in inspector.get_table_names()
        finally:
            engine.dispose()

    def test_stamps_existing_database_without_alembic_version(
        self, tmp_path: Path
    ) -> None:
        """Test migrations on existing database without alembic_version.

        Simulates bringing a pre-migration database under version control.
        """
        db_path = tmp_path / "test.db"
        database_url = f"sqlite:///{db_path}"

        # Create existing schema using create_all (simulating pre-migration DB)
        engine = create_engine(database_url)
        try:
            Base.metadata.create_all(engine)

            # Verify no alembic_version yet
            inspector = inspect(engine)
            assert "alembic_version" not in inspector.get_table_names()
            assert "tasks" in inspector.get_table_names()

            # Run migrations - should stamp, not recreate
            run_migrations(engine)

            # Should now have alembic_version stamped
            inspector = inspect(engine)
            assert "alembic_version" in inspector.get_table_names()
            assert get_current_revision(engine) == "001_initial"
        finally:
            engine.dispose()

    def test_migrations_are_idempotent(self) -> None:
        """Test running migrations multiple times is safe."""
        engine = create_engine("sqlite:///:memory:")
        try:
            # Run migrations multiple times
            run_migrations(engine)
            run_migrations(engine)
            run_migrations(engine)

            # Should still work and have correct revision
            assert get_current_revision(engine) == "001_initial"
        finally:
            engine.dispose()

    def test_creates_tasks_table_with_correct_schema(self) -> None:
        """Test that tasks table has the correct columns."""
        engine = create_engine("sqlite:///:memory:")
        try:
            run_migrations(engine)

            inspector = inspect(engine)
            columns = {col["name"] for col in inspector.get_columns("tasks")}

            expected_columns = {
                "id",
                "name",
                "priority",
                "status",
                "created_at",
                "updated_at",
                "planned_start",
                "planned_end",
                "deadline",
                "actual_start",
                "actual_end",
                "actual_duration",
                "estimated_duration",
                "is_fixed",
                "daily_allocations",
                "actual_daily_hours",
                "depends_on",
                "is_archived",
            }
            assert columns == expected_columns
        finally:
            engine.dispose()

    def test_creates_tasks_table_indexes(self) -> None:
        """Test that tasks table has the correct indexes."""
        engine = create_engine("sqlite:///:memory:")
        try:
            run_migrations(engine)

            inspector = inspect(engine)
            indexes = {idx["name"] for idx in inspector.get_indexes("tasks")}

            expected_indexes = {
                "idx_status",
                "idx_is_archived",
                "idx_deadline",
                "idx_planned_start",
                "idx_priority",
            }
            assert expected_indexes.issubset(indexes)
        finally:
            engine.dispose()

    def test_creates_tags_table_with_correct_schema(self) -> None:
        """Test that tags table has the correct columns."""
        engine = create_engine("sqlite:///:memory:")
        try:
            run_migrations(engine)

            inspector = inspect(engine)
            columns = {col["name"] for col in inspector.get_columns("tags")}

            expected_columns = {"id", "name", "created_at"}
            assert columns == expected_columns
        finally:
            engine.dispose()

    def test_creates_task_tags_junction_table(self) -> None:
        """Test that task_tags junction table is created correctly."""
        engine = create_engine("sqlite:///:memory:")
        try:
            run_migrations(engine)

            inspector = inspect(engine)
            columns = {col["name"] for col in inspector.get_columns("task_tags")}

            expected_columns = {"task_id", "tag_id"}
            assert columns == expected_columns
        finally:
            engine.dispose()

    def test_creates_audit_logs_table_with_correct_schema(self) -> None:
        """Test that audit_logs table has the correct columns."""
        engine = create_engine("sqlite:///:memory:")
        try:
            run_migrations(engine)

            inspector = inspect(engine)
            columns = {col["name"] for col in inspector.get_columns("audit_logs")}

            expected_columns = {
                "id",
                "timestamp",
                "client_name",
                "operation",
                "resource_type",
                "resource_id",
                "resource_name",
                "old_values",
                "new_values",
                "success",
                "error_message",
            }
            assert columns == expected_columns
        finally:
            engine.dispose()


class TestGetCurrentRevision:
    """Tests for get_current_revision function."""

    def test_returns_none_for_unversioned_database(self) -> None:
        """Test get_current_revision returns None for unversioned DB."""
        engine = create_engine("sqlite:///:memory:")
        try:
            assert get_current_revision(engine) is None
        finally:
            engine.dispose()

    def test_returns_revision_after_migrations(self) -> None:
        """Test get_current_revision returns correct revision after migrations."""
        engine = create_engine("sqlite:///:memory:")
        try:
            run_migrations(engine)

            assert get_current_revision(engine) == "001_initial"
        finally:
            engine.dispose()

    def test_returns_none_for_empty_alembic_version(self) -> None:
        """Test returns None if alembic_version table exists but is empty."""
        engine = create_engine("sqlite:///:memory:")
        try:
            # Create empty alembic_version table manually
            with engine.connect() as conn:
                conn.execute(
                    text("CREATE TABLE alembic_version (version_num VARCHAR(32))")
                )
                conn.commit()

            assert get_current_revision(engine) is None
        finally:
            engine.dispose()
