"""Tests for template_loader utility."""

from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

from taskdog.utils.template_loader import _expand_template_variables, load_note_template
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.entities.task import TaskStatus


def create_mock_task(
    task_id: int = 1,
    name: str = "Test Task",
    priority: int = 50,
    status: TaskStatus = TaskStatus.PENDING,
    deadline: datetime | None = None,
    estimated_duration: float | None = None,
    tags: list[str] | None = None,
) -> TaskDetailDto:
    """Create a mock TaskDetailDto for testing."""
    return TaskDetailDto(
        id=task_id,
        name=name,
        priority=priority,
        status=status,
        planned_start=None,
        planned_end=None,
        deadline=deadline,
        actual_start=None,
        actual_end=None,
        estimated_duration=estimated_duration,
        daily_allocations={},
        is_fixed=False,
        depends_on=[],
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


class TestLoadNoteTemplate:
    """Test cases for load_note_template function."""

    def test_returns_none_when_config_is_none(self) -> None:
        """Test that None config returns None."""
        task = create_mock_task()
        result = load_note_template(None, task)
        assert result is None

    def test_returns_none_when_template_path_is_none(self) -> None:
        """Test that None template path returns None."""
        config = MagicMock()
        config.notes.template = None
        task = create_mock_task()

        result = load_note_template(config, task)

        assert result is None

    @patch("os.path.isfile")
    @patch("os.path.expanduser")
    def test_returns_none_when_file_not_found(
        self, mock_expanduser: MagicMock, mock_isfile: MagicMock
    ) -> None:
        """Test that non-existent file returns None."""
        config = MagicMock()
        config.notes.template = "~/template.md"
        mock_expanduser.return_value = "/home/user/template.md"
        mock_isfile.return_value = False
        task = create_mock_task()

        result = load_note_template(config, task)

        assert result is None

    @patch("builtins.open", mock_open(read_data="# Task: {{task_name}}"))
    @patch("os.path.isfile")
    @patch("os.path.expanduser")
    def test_loads_and_expands_template(
        self, mock_expanduser: MagicMock, mock_isfile: MagicMock
    ) -> None:
        """Test successful template loading and expansion."""
        config = MagicMock()
        config.notes.template = "~/template.md"
        mock_expanduser.return_value = "/home/user/template.md"
        mock_isfile.return_value = True
        task = create_mock_task(name="My Task")

        result = load_note_template(config, task)

        assert result is not None
        assert "My Task" in result

    @patch("builtins.open")
    @patch("os.path.isfile")
    @patch("os.path.expanduser")
    def test_returns_none_on_oserror(
        self, mock_expanduser: MagicMock, mock_isfile: MagicMock, mock_file: MagicMock
    ) -> None:
        """Test that OSError returns None."""
        config = MagicMock()
        config.notes.template = "~/template.md"
        mock_expanduser.return_value = "/home/user/template.md"
        mock_isfile.return_value = True
        mock_file.side_effect = OSError("Permission denied")
        task = create_mock_task()

        result = load_note_template(config, task)

        assert result is None

    @patch("builtins.open")
    @patch("os.path.isfile")
    @patch("os.path.expanduser")
    def test_returns_none_on_unicode_decode_error(
        self, mock_expanduser: MagicMock, mock_isfile: MagicMock, mock_file: MagicMock
    ) -> None:
        """Test that UnicodeDecodeError returns None."""
        config = MagicMock()
        config.notes.template = "~/template.md"
        mock_expanduser.return_value = "/home/user/template.md"
        mock_isfile.return_value = True
        mock_file.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        task = create_mock_task()

        result = load_note_template(config, task)

        assert result is None

    @patch("os.path.expanduser")
    def test_expands_user_home_in_path(self, mock_expanduser: MagicMock) -> None:
        """Test that ~ is expanded in path."""
        config = MagicMock()
        config.notes.template = "~/notes/template.md"
        mock_expanduser.return_value = "/home/user/notes/template.md"
        task = create_mock_task()

        with patch("os.path.isfile", return_value=False):
            load_note_template(config, task)

        mock_expanduser.assert_called_once_with("~/notes/template.md")


class TestExpandTemplateVariables:
    """Test cases for _expand_template_variables function."""

    def test_expands_task_id(self) -> None:
        """Test {{task_id}} variable expansion."""
        task = create_mock_task(task_id=42)
        result = _expand_template_variables("ID: {{task_id}}", task)
        assert result == "ID: 42"

    def test_expands_task_name(self) -> None:
        """Test {{task_name}} variable expansion."""
        task = create_mock_task(name="Important Task")
        result = _expand_template_variables("Name: {{task_name}}", task)
        assert result == "Name: Important Task"

    def test_expands_priority(self) -> None:
        """Test {{priority}} variable expansion."""
        task = create_mock_task(priority=100)
        result = _expand_template_variables("Priority: {{priority}}", task)
        assert result == "Priority: 100"

    def test_expands_status(self) -> None:
        """Test {{status}} variable expansion."""
        task = create_mock_task(status=TaskStatus.IN_PROGRESS)
        result = _expand_template_variables("Status: {{status}}", task)
        assert result == "Status: IN_PROGRESS"

    def test_expands_deadline_when_set(self) -> None:
        """Test {{deadline}} variable expansion with value."""
        task = create_mock_task(deadline=datetime(2025, 12, 31, 18, 0))
        result = _expand_template_variables("Deadline: {{deadline}}", task)
        assert result == "Deadline: 2025-12-31"

    def test_expands_deadline_empty_when_not_set(self) -> None:
        """Test {{deadline}} variable expansion without value."""
        task = create_mock_task(deadline=None)
        result = _expand_template_variables("Deadline: {{deadline}}", task)
        assert result == "Deadline: "

    def test_expands_estimated_duration_when_set(self) -> None:
        """Test {{estimated_duration}} variable expansion with value."""
        task = create_mock_task(estimated_duration=8.5)
        result = _expand_template_variables("Duration: {{estimated_duration}}", task)
        assert result == "Duration: 8.5"

    def test_expands_estimated_duration_empty_when_not_set(self) -> None:
        """Test {{estimated_duration}} variable expansion without value."""
        task = create_mock_task(estimated_duration=None)
        result = _expand_template_variables("Duration: {{estimated_duration}}", task)
        assert result == "Duration: "

    def test_expands_tags_when_set(self) -> None:
        """Test {{tags}} variable expansion with values."""
        task = create_mock_task(tags=["urgent", "work", "client"])
        result = _expand_template_variables("Tags: {{tags}}", task)
        assert result == "Tags: urgent, work, client"

    def test_expands_tags_empty_when_not_set(self) -> None:
        """Test {{tags}} variable expansion without values."""
        task = create_mock_task(tags=[])
        result = _expand_template_variables("Tags: {{tags}}", task)
        assert result == "Tags: "

    def test_expands_created_at(self) -> None:
        """Test {{created_at}} variable expansion."""
        task = create_mock_task()
        result = _expand_template_variables("Created: {{created_at}}", task)
        # Should contain datetime format
        assert "Created: " in result
        assert "-" in result  # Date separator
        assert ":" in result  # Time separator

    def test_expands_multiple_variables(self) -> None:
        """Test multiple variables in one template."""
        task = create_mock_task(
            task_id=99,
            name="Multi Test",
            priority=75,
            tags=["test"],
        )
        template = (
            "# {{task_name}} (ID: {{task_id}})\nPriority: {{priority}}\nTags: {{tags}}"
        )
        result = _expand_template_variables(template, task)

        assert "Multi Test" in result
        assert "99" in result
        assert "75" in result
        assert "test" in result

    def test_preserves_unrecognized_placeholders(self) -> None:
        """Test that unrecognized placeholders are preserved."""
        task = create_mock_task()
        result = _expand_template_variables("Custom: {{custom_field}}", task)
        assert result == "Custom: {{custom_field}}"

    def test_handles_empty_template(self) -> None:
        """Test empty template returns empty string."""
        task = create_mock_task()
        result = _expand_template_variables("", task)
        assert result == ""

    def test_handles_template_without_variables(self) -> None:
        """Test template without variables returns unchanged."""
        task = create_mock_task()
        template = "This is plain text without any variables."
        result = _expand_template_variables(template, task)
        assert result == template
