"""Tests for TaskFormDialog."""

from datetime import datetime

from taskdog.tui.dialogs.task_form_dialog import TaskFormDialog
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.entities.task import TaskStatus


def create_mock_task(
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
    """Create a mock TaskDetailDto for testing."""
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


class TestTaskFormDialogInitialization:
    """Test cases for TaskFormDialog initialization."""

    def test_init_without_task_sets_add_mode(self) -> None:
        """Test that initializing without task sets add mode."""
        dialog = TaskFormDialog(task=None)

        assert dialog.task_to_edit is None
        assert dialog.is_edit_mode is False

    def test_init_with_task_sets_edit_mode(self) -> None:
        """Test that initializing with task sets edit mode."""
        task = create_mock_task()
        dialog = TaskFormDialog(task=task)

        assert dialog.task_to_edit is task
        assert dialog.is_edit_mode is True

    def test_init_stores_task_reference(self) -> None:
        """Test that task reference is stored correctly."""
        task = create_mock_task(name="Specific Task", priority=100)
        dialog = TaskFormDialog(task=task)

        assert dialog.task_to_edit.name == "Specific Task"
        assert dialog.task_to_edit.priority == 100

    def test_init_with_complex_task(self) -> None:
        """Test initialization with task containing all fields."""
        task = create_mock_task(
            name="Complex Task",
            priority=75,
            deadline=datetime(2025, 12, 31, 18, 0),
            estimated_duration=8.5,
            planned_start=datetime(2025, 1, 1, 9, 0),
            planned_end=datetime(2025, 1, 5, 17, 0),
            is_fixed=True,
            depends_on=[2, 3],
            tags=["urgent", "work"],
        )
        dialog = TaskFormDialog(task=task)

        assert dialog.is_edit_mode is True
        assert dialog.task_to_edit.name == "Complex Task"
        assert dialog.task_to_edit.is_fixed is True
        assert dialog.task_to_edit.depends_on == [2, 3]


class TestTaskFormDialogBindings:
    """Test cases for TaskFormDialog key bindings."""

    def test_has_escape_binding(self) -> None:
        """Test that escape binding is defined."""
        bindings = {b.key for b in TaskFormDialog.BINDINGS}
        assert "escape" in bindings

    def test_has_submit_binding(self) -> None:
        """Test that submit binding (ctrl+s) is defined."""
        bindings = {b.key for b in TaskFormDialog.BINDINGS}
        assert "ctrl+s" in bindings

    def test_has_focus_next_binding(self) -> None:
        """Test that focus next binding (ctrl+j) is defined."""
        bindings = {b.key for b in TaskFormDialog.BINDINGS}
        assert "ctrl+j" in bindings

    def test_has_focus_previous_binding(self) -> None:
        """Test that focus previous binding (ctrl+k) is defined."""
        bindings = {b.key for b in TaskFormDialog.BINDINGS}
        assert "ctrl+k" in bindings


class TestTaskFormDialogActions:
    """Test cases for TaskFormDialog action methods."""

    def test_action_focus_next_exists(self) -> None:
        """Test that action_focus_next method exists."""
        dialog = TaskFormDialog(task=None)
        assert hasattr(dialog, "action_focus_next")
        assert callable(dialog.action_focus_next)

    def test_action_focus_previous_exists(self) -> None:
        """Test that action_focus_previous method exists."""
        dialog = TaskFormDialog(task=None)
        assert hasattr(dialog, "action_focus_previous")
        assert callable(dialog.action_focus_previous)

    def test_action_submit_exists(self) -> None:
        """Test that action_submit method exists."""
        dialog = TaskFormDialog(task=None)
        assert hasattr(dialog, "action_submit")
        assert callable(dialog.action_submit)

    def test_action_cancel_inherited(self) -> None:
        """Test that action_cancel is inherited from base class."""
        dialog = TaskFormDialog(task=None)
        assert hasattr(dialog, "action_cancel")
        assert callable(dialog.action_cancel)


class TestTaskFormDialogAvailableTags:
    """Test cases for available_tags parameter."""

    def test_init_without_available_tags(self) -> None:
        """Test that available_tags defaults to None."""
        dialog = TaskFormDialog(task=None)
        assert dialog._available_tags is None

    def test_init_with_available_tags(self) -> None:
        """Test that available_tags is stored."""
        tags = ["work", "urgent", "client"]
        dialog = TaskFormDialog(task=None, available_tags=tags)
        assert dialog._available_tags == tags

    def test_init_with_empty_available_tags(self) -> None:
        """Test that empty available_tags list is stored."""
        dialog = TaskFormDialog(task=None, available_tags=[])
        assert dialog._available_tags == []

    def test_edit_mode_with_available_tags(self) -> None:
        """Test that available_tags works in edit mode."""
        task = create_mock_task(tags=["existing"])
        tags = ["work", "urgent", "existing"]
        dialog = TaskFormDialog(task=task, available_tags=tags)
        assert dialog._available_tags == tags
        assert dialog.is_edit_mode is True


class TestTaskFormDialogModeDetection:
    """Test cases for dialog mode detection logic."""

    def test_edit_mode_true_when_task_provided(self) -> None:
        """Test is_edit_mode is True when task is provided."""
        task = create_mock_task()
        dialog = TaskFormDialog(task=task)
        assert dialog.is_edit_mode is True

    def test_edit_mode_false_when_no_task(self) -> None:
        """Test is_edit_mode is False when no task provided."""
        dialog = TaskFormDialog(task=None)
        assert dialog.is_edit_mode is False

    def test_task_to_edit_matches_provided_task(self) -> None:
        """Test task_to_edit matches the provided task."""
        task = create_mock_task(task_id=42, name="Unique Task")
        dialog = TaskFormDialog(task=task)

        assert dialog.task_to_edit.id == 42
        assert dialog.task_to_edit.name == "Unique Task"

    def test_multiple_dialogs_independent(self) -> None:
        """Test that multiple dialog instances are independent."""
        task1 = create_mock_task(name="Task 1")
        task2 = create_mock_task(name="Task 2")

        dialog1 = TaskFormDialog(task=task1)
        dialog2 = TaskFormDialog(task=task2)
        dialog3 = TaskFormDialog(task=None)

        assert dialog1.is_edit_mode is True
        assert dialog1.task_to_edit.name == "Task 1"

        assert dialog2.is_edit_mode is True
        assert dialog2.task_to_edit.name == "Task 2"

        assert dialog3.is_edit_mode is False
        assert dialog3.task_to_edit is None
