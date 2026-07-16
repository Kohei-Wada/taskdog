"""Tests for EditCommand."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from taskdog.tui.commands.edit import EditCommand
from taskdog.tui.forms.task_form_fields import TaskFormData
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.entities.task import TaskStatus


def create_task_detail_dto(
    task_id: int = 1,
    name: str = "Test Task",
    priority: int = 50,
    deadline: datetime | None = None,
    estimated_duration: float | None = None,
    planned_start: datetime | None = None,
    planned_end: datetime | None = None,
    is_fixed: bool = False,
    depends_on: list[int] | None = None,
    tags: list[str] | None = None,
) -> TaskDetailDto:
    """Helper to create TaskDetailDto with defaults."""
    return TaskDetailDto(
        id=task_id,
        name=name,
        priority=priority,
        status=TaskStatus.PENDING,
        planned_start=planned_start,
        planned_end=planned_end,
        deadline=deadline,
        actual_start=None,
        actual_end=None,
        actual_duration=None,
        estimated_duration=estimated_duration,
        daily_allocations={},
        is_fixed=is_fixed,
        depends_on=depends_on or [],
        tags=tags or [],
        is_archived=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        actual_duration_hours=None,
        is_active=False,
        is_finished=False,
        can_be_modified=True,
        is_schedulable=True,
    )


def create_form_data(
    name: str = "Test Task",
    priority: int = 50,
    deadline: datetime | None = None,
    estimated_duration: float | None = None,
    planned_start: datetime | None = None,
    planned_end: datetime | None = None,
    is_fixed: bool = False,
    depends_on: list[int] | None = None,
    tags: list[str] | None = None,
) -> TaskFormData:
    """Helper to create TaskFormData with defaults.

    Note: TaskFormData stores datetime fields as strings in YYYY-MM-DD HH:MM:SS format.
    """
    # Convert datetime to string format if provided
    deadline_str = deadline.strftime("%Y-%m-%d %H:%M:%S") if deadline else None
    planned_start_str = (
        planned_start.strftime("%Y-%m-%d %H:%M:%S") if planned_start else None
    )
    planned_end_str = planned_end.strftime("%Y-%m-%d %H:%M:%S") if planned_end else None

    return TaskFormData(
        name=name,
        priority=priority,
        deadline=deadline_str,
        estimated_duration=estimated_duration,
        planned_start=planned_start_str,
        planned_end=planned_end_str,
        is_fixed=is_fixed,
        depends_on=depends_on or [],
        tags=tags or [],
    )


class TestEditCommandDetectChanges:
    """Test cases for EditCommand._detect_changes method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = EditCommand(self.mock_app, self.mock_context)

    def test_no_changes_detected(self) -> None:
        """Test that identical task and form data returns no changes."""
        task = create_task_detail_dto(
            name="Test Task",
            priority=50,
            deadline=datetime(2025, 12, 31, 18, 0),
            tags=["tag1"],
        )
        form_data = create_form_data(
            name="Test Task",
            priority=50,
            deadline=datetime(2025, 12, 31, 18, 0),
            tags=["tag1"],
        )

        fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is False
        assert deps_changed is False

    def test_name_change_detected(self) -> None:
        """Test that name change is detected."""
        task = create_task_detail_dto(name="Old Name")
        form_data = create_form_data(name="New Name")

        fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True
        assert deps_changed is False

    def test_priority_change_detected(self) -> None:
        """Test that priority change is detected."""
        task = create_task_detail_dto(priority=50)
        form_data = create_form_data(priority=100)

        fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True
        assert deps_changed is False

    def test_deadline_change_detected(self) -> None:
        """Test that deadline change is detected."""
        task = create_task_detail_dto(deadline=datetime(2025, 1, 1, 18, 0))
        form_data = create_form_data(deadline=datetime(2025, 12, 31, 18, 0))

        fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True
        assert deps_changed is False

    def test_deadline_added_detected(self) -> None:
        """Test that adding deadline is detected."""
        task = create_task_detail_dto(deadline=None)
        form_data = create_form_data(deadline=datetime(2025, 12, 31, 18, 0))

        fields_changed, _deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True

    def test_deadline_removed_detected(self) -> None:
        """Test that removing deadline is detected."""
        task = create_task_detail_dto(deadline=datetime(2025, 12, 31, 18, 0))
        form_data = create_form_data(deadline=None)

        fields_changed, _deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True

    def test_estimated_duration_change_detected(self) -> None:
        """Test that estimated duration change is detected."""
        task = create_task_detail_dto(estimated_duration=5.0)
        form_data = create_form_data(estimated_duration=10.0)

        fields_changed, _deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True

    def test_planned_start_change_detected(self) -> None:
        """Test that planned start change is detected."""
        task = create_task_detail_dto(planned_start=datetime(2025, 1, 1, 9, 0))
        form_data = create_form_data(planned_start=datetime(2025, 1, 15, 9, 0))

        fields_changed, _deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True

    def test_planned_end_change_detected(self) -> None:
        """Test that planned end change is detected."""
        task = create_task_detail_dto(planned_end=datetime(2025, 1, 5, 17, 0))
        form_data = create_form_data(planned_end=datetime(2025, 1, 20, 17, 0))

        fields_changed, _deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True

    def test_is_fixed_change_detected(self) -> None:
        """Test that is_fixed change is detected."""
        task = create_task_detail_dto(is_fixed=False)
        form_data = create_form_data(is_fixed=True)

        fields_changed, _deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True

    def test_tags_change_detected(self) -> None:
        """Test that tags change is detected."""
        task = create_task_detail_dto(tags=["tag1"])
        form_data = create_form_data(tags=["tag1", "tag2"])

        fields_changed, _deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True

    def test_tags_removed_detected(self) -> None:
        """Test that removing tags is detected."""
        task = create_task_detail_dto(tags=["tag1", "tag2"])
        form_data = create_form_data(tags=[])

        fields_changed, _deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True

    def test_dependency_added_detected(self) -> None:
        """Test that adding dependency is detected."""
        task = create_task_detail_dto(depends_on=[])
        form_data = create_form_data(depends_on=[2])

        _fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert deps_changed is True

    def test_dependency_removed_detected(self) -> None:
        """Test that removing dependency is detected."""
        task = create_task_detail_dto(depends_on=[2, 3])
        form_data = create_form_data(depends_on=[2])

        _fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert deps_changed is True

    def test_dependency_changed_detected(self) -> None:
        """Test that changing dependencies is detected."""
        task = create_task_detail_dto(depends_on=[2])
        form_data = create_form_data(depends_on=[3])

        _fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert deps_changed is True

    def test_dependency_order_does_not_matter(self) -> None:
        """Test that dependency order doesn't affect comparison."""
        task = create_task_detail_dto(depends_on=[3, 2])
        form_data = create_form_data(depends_on=[2, 3])

        _fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert deps_changed is False

    def test_both_fields_and_deps_changed(self) -> None:
        """Test that both field and dependency changes are detected."""
        task = create_task_detail_dto(name="Old Name", depends_on=[2])
        form_data = create_form_data(name="New Name", depends_on=[3])

        fields_changed, deps_changed = self.command._detect_changes(task, form_data)

        assert fields_changed is True
        assert deps_changed is True


class TestEditCommandSyncDependencies:
    """Test cases for EditCommand._sync_dependencies method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = EditCommand(self.mock_app, self.mock_context)
        # Mock manage_dependencies to return no failures
        self.command.manage_dependencies = MagicMock(return_value=[])

    def test_adds_new_dependencies(self) -> None:
        """Test that new dependencies are added."""
        task = create_task_detail_dto(depends_on=[])
        form_data = create_form_data(depends_on=[2, 3])

        self.command._sync_dependencies(task, form_data)

        self.command.manage_dependencies.assert_called_once()
        call_args = self.command.manage_dependencies.call_args
        assert set(call_args[1]["add_deps"]) == {2, 3}
        assert call_args[1]["remove_deps"] == []

    def test_removes_old_dependencies(self) -> None:
        """Test that old dependencies are removed."""
        task = create_task_detail_dto(depends_on=[2, 3])
        form_data = create_form_data(depends_on=[])

        self.command._sync_dependencies(task, form_data)

        call_args = self.command.manage_dependencies.call_args
        assert call_args[1]["add_deps"] == []
        assert set(call_args[1]["remove_deps"]) == {2, 3}

    def test_adds_and_removes_dependencies(self) -> None:
        """Test that dependencies can be added and removed simultaneously."""
        task = create_task_detail_dto(depends_on=[2, 3])
        form_data = create_form_data(depends_on=[3, 4])

        self.command._sync_dependencies(task, form_data)

        call_args = self.command.manage_dependencies.call_args
        assert set(call_args[1]["add_deps"]) == {4}
        assert set(call_args[1]["remove_deps"]) == {2}

    def test_notifies_on_failure(self) -> None:
        """Test that failures trigger warning notification."""
        task = create_task_detail_dto(depends_on=[])
        form_data = create_form_data(depends_on=[2])
        self.command.manage_dependencies.return_value = ["Failed to add #2"]
        self.command.notify_warning = MagicMock()

        self.command._sync_dependencies(task, form_data)

        self.command.notify_warning.assert_called_once()
        assert "failed" in self.command.notify_warning.call_args[0][0].lower()


class TestEditCommandHandleTaskUpdate:
    """Test cases for EditCommand._handle_task_update method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = EditCommand(self.mock_app, self.mock_context)
        self.command.notify_warning = MagicMock()
        self.command._update_task_fields = MagicMock()
        self.command._sync_dependencies = MagicMock()

    def test_no_changes_shows_warning(self) -> None:
        """Test that no changes shows warning message."""
        task = create_task_detail_dto()
        form_data = create_form_data()

        self.command._handle_task_update(task, form_data)

        self.command.notify_warning.assert_called_once()
        assert "no changes" in self.command.notify_warning.call_args[0][0].lower()
        self.command._update_task_fields.assert_not_called()

    def test_field_changes_calls_update(self) -> None:
        """Test that field changes call _update_task_fields."""
        task = create_task_detail_dto(name="Old Name")
        form_data = create_form_data(name="New Name")
        mock_updated_task = MagicMock()
        mock_updated_task.id = 1
        self.command._update_task_fields.return_value = (mock_updated_task, ["name"])

        self.command._handle_task_update(task, form_data)

        self.command._update_task_fields.assert_called_once()
        self.mock_app.post_message.assert_called_once()

    def test_dependency_changes_calls_sync(self) -> None:
        """Test that dependency changes call _sync_dependencies."""
        task = create_task_detail_dto(depends_on=[])
        form_data = create_form_data(depends_on=[2])

        self.command._handle_task_update(task, form_data)

        self.command._sync_dependencies.assert_called_once()
        self.mock_app.post_message.assert_called_once()
