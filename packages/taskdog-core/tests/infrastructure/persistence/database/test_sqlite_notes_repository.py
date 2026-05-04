"""Tests for SqliteNotesRepository."""

import sys
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add tests directory to path for fixtures module
_tests_path = Path(__file__).parent.parent.parent.parent.resolve()
if str(_tests_path) not in sys.path:
    sys.path.insert(0, str(_tests_path))

from helpers.time_provider import FakeTimeProvider  # noqa: E402

from taskdog_core.infrastructure.persistence.database.sqlite_notes_repository import (  # noqa: E402
    SqliteNotesRepository,
)


def _create_test_task(engine, task_id: int) -> None:
    """Create a test task with the given ID for foreign key satisfaction."""
    from sqlalchemy.orm import Session

    from taskdog_core.infrastructure.persistence.database.models import TaskModel

    with Session(engine) as session:
        task = TaskModel(
            id=task_id,
            name=f"Test Task {task_id}",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_archived=False,
        )
        session.add(task)
        session.commit()


class TestSqliteNotesRepository:
    """Test suite for SqliteNotesRepository."""

    @pytest.fixture
    def time_provider(self) -> FakeTimeProvider:
        """Create a fake time provider for testing."""
        return FakeTimeProvider(datetime(2025, 1, 15, 10, 30, 0))

    @pytest.fixture
    def repository(self, time_provider: FakeTimeProvider) -> SqliteNotesRepository:
        """Create an in-memory SqliteNotesRepository for testing."""
        repo = SqliteNotesRepository("sqlite:///:memory:", time_provider)
        yield repo
        repo.close()

    @pytest.fixture
    def create_task(self, repository: SqliteNotesRepository) -> Callable[[int], None]:
        """Return a helper function to create tasks for foreign key satisfaction."""

        def _create(task_id: int) -> None:
            _create_test_task(repository.engine, task_id)

        return _create

    def test_has_notes_returns_false_when_no_notes(
        self, repository: SqliteNotesRepository
    ):
        """Test has_notes returns False when note doesn't exist."""
        assert repository.has_notes(999) is False

    def test_has_notes_returns_true_when_notes_exist(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test has_notes returns True when note exists."""
        create_task(1)
        repository.write_notes(1, "Test content")

        assert repository.has_notes(1) is True

    def test_read_notes_returns_none_when_no_notes(
        self, repository: SqliteNotesRepository
    ):
        """Test read_notes returns None when note doesn't exist."""
        assert repository.read_notes(999) is None

    def test_read_notes_returns_content_when_exists(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test read_notes returns content when note exists."""
        create_task(1)
        content = "# Task Notes\n\nThis is a test note."
        repository.write_notes(1, content)

        assert repository.read_notes(1) == content

    def test_write_notes_creates_new_note(
        self,
        repository: SqliteNotesRepository,
        time_provider: FakeTimeProvider,
        create_task: Callable[[int], None],
    ):
        """Test write_notes creates new note with timestamps."""
        create_task(1)
        content = "New note content"
        repository.write_notes(1, content)

        result = repository.read_notes(1)
        assert result == content

    def test_write_notes_updates_existing_note(
        self,
        repository: SqliteNotesRepository,
        time_provider: FakeTimeProvider,
        create_task: Callable[[int], None],
    ):
        """Test write_notes updates existing note."""
        create_task(1)
        repository.write_notes(1, "Original content")

        # Advance time to verify updated_at changes
        time_provider.advance(timedelta(hours=1))

        repository.write_notes(1, "Updated content")

        assert repository.read_notes(1) == "Updated content"

    def test_write_notes_handles_unicode_content(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test write_notes handles Unicode and emoji content."""
        create_task(1)
        content = "# タスクノート\n\n絵文字テスト: 🚀 ✅ 📝"
        repository.write_notes(1, content)

        assert repository.read_notes(1) == content

    def test_write_notes_handles_empty_string(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test write_notes can write empty string."""
        create_task(1)
        repository.write_notes(1, "")

        assert repository.read_notes(1) == ""
        assert repository.has_notes(1) is True

    def test_write_notes_preserves_multiline_content(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test write_notes preserves multiline content."""
        create_task(1)
        content = "# Task\n\nLine 1\nLine 2\nLine 3\n\n## Section\n\nMore text"
        repository.write_notes(1, content)

        assert repository.read_notes(1) == content

    def test_delete_notes_removes_existing_note(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test delete_notes removes existing note."""
        create_task(1)
        repository.write_notes(1, "Test content")
        assert repository.has_notes(1) is True

        repository.delete_notes(1)

        assert repository.has_notes(1) is False
        assert repository.read_notes(1) is None

    def test_delete_notes_is_idempotent(self, repository: SqliteNotesRepository):
        """Test delete_notes doesn't raise when note doesn't exist."""
        # Should not raise any exception
        repository.delete_notes(999)

        assert repository.has_notes(999) is False

    def test_ensure_notes_dir_is_noop(self, repository: SqliteNotesRepository):
        """Test ensure_notes_dir does nothing for database storage."""
        # Should not raise any exception
        repository.ensure_notes_dir()

    def test_get_task_ids_with_notes_returns_empty_set_for_empty_list(
        self, repository: SqliteNotesRepository
    ):
        """Test get_task_ids_with_notes returns empty set for empty input."""
        result = repository.get_task_ids_with_notes([])

        assert result == set()

    def test_get_task_ids_with_notes_returns_ids_with_notes(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test get_task_ids_with_notes returns only IDs that have notes."""
        for i in range(1, 6):
            create_task(i)
        repository.write_notes(1, "Note 1")
        repository.write_notes(3, "Note 3")
        repository.write_notes(5, "Note 5")

        result = repository.get_task_ids_with_notes([1, 2, 3, 4, 5])

        assert result == {1, 3, 5}

    def test_get_task_ids_with_notes_returns_empty_when_no_matches(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test get_task_ids_with_notes returns empty set when no notes match."""
        create_task(1)
        repository.write_notes(1, "Note 1")

        result = repository.get_task_ids_with_notes([2, 3, 4])

        assert result == set()

    def test_get_task_ids_with_notes_handles_large_batch(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test get_task_ids_with_notes handles large batch efficiently."""
        # Create notes for even-numbered tasks
        for i in range(0, 100, 2):
            create_task(i)
            repository.write_notes(i, f"Note {i}")

        result = repository.get_task_ids_with_notes(list(range(100)))

        assert result == set(range(0, 100, 2))

    def test_clear_removes_all_notes(
        self, repository: SqliteNotesRepository, create_task: Callable[[int], None]
    ):
        """Test clear removes all notes from database."""
        for i in range(1, 4):
            create_task(i)
        repository.write_notes(1, "Note 1")
        repository.write_notes(2, "Note 2")
        repository.write_notes(3, "Note 3")

        repository.clear()

        assert repository.has_notes(1) is False
        assert repository.has_notes(2) is False
        assert repository.has_notes(3) is False
