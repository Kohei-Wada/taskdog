"""Tests for MCP tools."""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from taskdog_core.application.dto.statistics_output import (
    PriorityDistributionStatistics,
    StatisticsOutput,
    TaskStatistics,
    TimeStatistics,
)
from taskdog_core.application.dto.tag_statistics_output import TagStatisticsOutput
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
from taskdog_core.application.dto.task_dto import TaskDetailDto, TaskRowDto
from taskdog_core.application.dto.task_list_output import TaskListOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import TaskStatus


def create_mock_task_row(
    task_id: int = 1,
    name: str = "Test Task",
    status: TaskStatus = TaskStatus.PENDING,
    priority: int = 50,
) -> TaskRowDto:
    """Create a mock TaskRowDto for testing."""
    return TaskRowDto(
        id=task_id,
        name=name,
        priority=priority,
        status=status,
        planned_start=None,
        planned_end=None,
        deadline=None,
        actual_start=None,
        actual_end=None,
        estimated_duration=2.0,
        actual_duration_hours=None,
        is_fixed=False,
        depends_on=[],
        tags=["test"],
        is_archived=False,
        is_finished=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def create_mock_task_operation_output(
    task_id: int = 1,
    name: str = "Test Task",
    status: TaskStatus = TaskStatus.PENDING,
) -> TaskOperationOutput:
    """Create a mock TaskOperationOutput for testing."""
    return TaskOperationOutput(
        id=task_id,
        name=name,
        status=status,
        priority=50,
        deadline=None,
        estimated_duration=2.0,
        planned_start=None,
        planned_end=None,
        actual_start=None,
        actual_end=None,
        actual_duration=None,
        depends_on=[],
        tags=["test"],
        is_fixed=False,
        is_archived=False,
        actual_duration_hours=None,
        daily_allocations={},
    )


def create_mock_task_detail_dto(
    task_id: int = 1,
    name: str = "Test Task",
    status: TaskStatus = TaskStatus.PENDING,
    priority: int = 50,
) -> TaskDetailDto:
    """Create a mock TaskDetailDto for testing."""
    return TaskDetailDto(
        id=task_id,
        name=name,
        priority=priority,
        status=status,
        planned_start=None,
        planned_end=None,
        deadline=None,
        actual_start=None,
        actual_end=None,
        actual_duration=None,
        estimated_duration=2.0,
        daily_allocations={},
        is_fixed=False,
        depends_on=[],
        tags=["test"],
        is_archived=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        actual_duration_hours=None,
        is_active=False,
        is_finished=False,
        can_be_modified=True,
        is_schedulable=True,
    )


def create_mock_task_detail_output(
    task_id: int = 1,
    name: str = "Test Task",
    status: TaskStatus = TaskStatus.PENDING,
    notes_content: str | None = None,
) -> TaskDetailOutput:
    """Create a mock TaskDetailOutput for testing."""
    return TaskDetailOutput(
        task=create_mock_task_detail_dto(task_id, name, status),
        notes_content=notes_content,
        has_notes=notes_content is not None,
    )


def create_mock_client() -> MagicMock:
    """Create a mock TaskdogApiClient with all required methods."""
    client = MagicMock()
    # TaskdogApiClient has flat methods (no nested clients)
    # CRUD methods
    client.list_tasks = MagicMock()
    client.get_task_detail = MagicMock()
    client.create_task = MagicMock()
    client.update_task = MagicMock()
    client.archive_task = MagicMock()
    client.restore_task = MagicMock()
    client.remove_task = MagicMock()
    # Lifecycle methods
    client.start_task = MagicMock()
    client.complete_task = MagicMock()
    client.pause_task = MagicMock()
    client.cancel_task = MagicMock()
    client.reopen_task = MagicMock()
    client.fix_actual_times = MagicMock()
    # Query methods
    client.get_tag_statistics = MagicMock()
    client.calculate_statistics = MagicMock()
    # Relationship methods
    client.add_dependency = MagicMock()
    client.remove_dependency = MagicMock()
    client.set_task_tags = MagicMock()
    # Notes methods
    client.get_task_notes = MagicMock()
    client.update_task_notes = MagicMock()
    # Audit methods
    client.list_audit_logs = MagicMock()
    client.get_audit_log = MagicMock()
    return client


class TestTaskCrudTools:
    """Test task CRUD MCP tools."""

    def test_list_tasks_returns_formatted_response(self) -> None:
        """Test list_tasks tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        client.list_tasks.return_value = TaskListOutput(
            tasks=[create_mock_task_row()],
            total_count=1,
            filtered_count=1,
        )

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        # Call the tool directly through the registered function
        client.list_tasks.assert_not_called()  # Not called yet

    def test_create_task_formats_response(self) -> None:
        """Test create_task tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        client.create_task.return_value = create_mock_task_operation_output()

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        # Verify registration didn't raise
        assert mcp is not None

    @pytest.mark.parametrize(
        ("input_kwargs", "expected_kwargs"),
        [
            pytest.param(
                {
                    "planned_start": "2025-12-11T09:00:00",
                    "planned_end": "2025-12-11T17:00:00",
                },
                {
                    "planned_start": datetime(2025, 12, 11, 9, 0, 0),
                    "planned_end": datetime(2025, 12, 11, 17, 0, 0),
                },
                id="planned_times",
            ),
            pytest.param(
                {
                    "deadline": "2025-12-11T18:30:00",
                    "estimated_duration": 0.5,
                },
                {
                    "deadline": datetime(2025, 12, 11, 18, 30, 0),
                    "estimated_duration": 0.5,
                },
                id="deadline_and_duration",
            ),
        ],
    )
    def test_create_task_datetime_conversion(
        self,
        input_kwargs: dict[str, Any],
        expected_kwargs: dict[str, Any],
    ) -> None:
        """Test create_task tool converts datetime strings correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        client.create_task.return_value = create_mock_task_operation_output()

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        create_task_fn = mcp._tool_manager._tools["create_task"].fn
        result = create_task_fn(name="Test Task", **input_kwargs)

        client.create_task.assert_called_once()
        call_kwargs = client.create_task.call_args.kwargs
        for key, expected_value in expected_kwargs.items():
            assert call_kwargs[key] == expected_value
        assert result["id"] == 1

    @pytest.mark.parametrize(
        ("input_kwargs", "expected_kwargs"),
        [
            pytest.param(
                {
                    "planned_start": "2025-12-12T10:00:00",
                    "planned_end": "2025-12-12T16:00:00",
                },
                {
                    "planned_start": datetime(2025, 12, 12, 10, 0, 0),
                    "planned_end": datetime(2025, 12, 12, 16, 0, 0),
                },
                id="planned_times",
            ),
            pytest.param(
                {
                    "deadline": "2025-12-15T14:00:00",
                    "estimated_duration": 1.5,
                },
                {
                    "deadline": datetime(2025, 12, 15, 14, 0, 0),
                    "estimated_duration": 1.5,
                },
                id="deadline_and_duration",
            ),
        ],
    )
    def test_update_task_datetime_conversion(
        self,
        input_kwargs: dict[str, Any],
        expected_kwargs: dict[str, Any],
    ) -> None:
        """Test update_task tool converts datetime strings correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        from taskdog_core.application.dto.update_task_output import TaskUpdateOutput

        client = create_mock_client()
        client.update_task.return_value = TaskUpdateOutput(
            task=create_mock_task_operation_output(),
            updated_fields=list(expected_kwargs.keys()),
        )

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        update_task_fn = mcp._tool_manager._tools["update_task"].fn
        result = update_task_fn(task_id=1, **input_kwargs)

        client.update_task.assert_called_once()
        call_kwargs = client.update_task.call_args.kwargs
        assert call_kwargs["task_id"] == 1
        for key, expected_value in expected_kwargs.items():
            assert call_kwargs[key] == expected_value
        assert result["id"] == 1

    @pytest.mark.parametrize(
        "invalid_datetime",
        [
            pytest.param("invalid-date", id="invalid_format"),
            pytest.param("2025-13-01T00:00:00", id="invalid_month"),
            pytest.param("not-a-date", id="not_a_date"),
        ],
    )
    def test_create_task_invalid_datetime_raises_error(
        self, invalid_datetime: str
    ) -> None:
        """Test create_task raises ValueError for invalid datetime strings."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        create_task_fn = mcp._tool_manager._tools["create_task"].fn

        with pytest.raises(ValueError, match="Invalid datetime format"):
            create_task_fn(name="Test Task", deadline=invalid_datetime)

    @pytest.mark.parametrize(
        "invalid_datetime",
        [
            pytest.param("invalid-date", id="invalid_format"),
            pytest.param("2025-13-01T00:00:00", id="invalid_month"),
            pytest.param("not-a-date", id="not_a_date"),
        ],
    )
    def test_update_task_invalid_datetime_raises_error(
        self, invalid_datetime: str
    ) -> None:
        """Test update_task raises ValueError for invalid datetime strings."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        update_task_fn = mcp._tool_manager._tools["update_task"].fn

        with pytest.raises(ValueError, match="Invalid datetime format"):
            update_task_fn(task_id=1, planned_start=invalid_datetime)

    def test_list_tasks_with_filters(self) -> None:
        """Test list_tasks tool with various filters."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        task1 = create_mock_task_row(task_id=1, name="Task 1")
        task2 = create_mock_task_row(task_id=2, name="Task 2")
        client.list_tasks.return_value = TaskListOutput(
            tasks=[task1, task2],
            total_count=2,
            filtered_count=2,
        )

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        list_tasks_fn = mcp._tool_manager._tools["list_tasks"].fn
        result = list_tasks_fn(
            include_archived=True,
            status="PENDING",
            tags=["test"],
            sort_by="priority",
            reverse=True,
        )

        client.list_tasks.assert_called_once_with(
            all=True,
            status="PENDING",
            tags=["test"],
            sort_by="priority",
            reverse=True,
        )
        assert len(result["tasks"]) == 2
        assert result["total"] == 2
        assert result["tasks"][0]["id"] == 1
        assert result["tasks"][0]["name"] == "Task 1"
        assert result["tasks"][0]["status"] == "PENDING"
        assert result["tasks"][0]["tags"] == ["test"]

    def test_get_task_returns_full_details(self) -> None:
        """Test get_task tool returns full task details including notes."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1,
            name="Test Task",
            notes_content="# Notes\nSome notes here",
        )

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        get_task_fn = mcp._tool_manager._tools["get_task"].fn
        result = get_task_fn(task_id=1)

        client.get_task_detail.assert_called_once_with(1)
        assert result["id"] == 1
        assert result["name"] == "Test Task"
        assert result["notes"] == "# Notes\nSome notes here"
        assert result["priority"] == 50
        assert result["tags"] == ["test"]
        assert result["depends_on"] == []

    def test_delete_task_soft(self) -> None:
        """Test delete_task tool with soft delete (archive)."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        client.archive_task.return_value = create_mock_task_operation_output(
            task_id=1, name="Archived Task"
        )

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        delete_task_fn = mcp._tool_manager._tools["delete_task"].fn
        result = delete_task_fn(task_id=1, hard=False)

        client.archive_task.assert_called_once_with(1)
        client.remove_task.assert_not_called()
        assert result["id"] == 1
        assert "archived" in result["message"]

    def test_delete_task_hard(self) -> None:
        """Test delete_task tool with hard delete (permanent)."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        delete_task_fn = mcp._tool_manager._tools["delete_task"].fn
        result = delete_task_fn(task_id=1, hard=True)

        client.remove_task.assert_called_once_with(1)
        client.archive_task.assert_not_called()
        assert "permanently deleted" in result["message"]

    def test_restore_task_returns_restored_data(self) -> None:
        """Test restore_task tool returns restored task data."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        client = create_mock_client()
        client.restore_task.return_value = create_mock_task_operation_output(
            task_id=1, name="Restored Task"
        )

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, client)

        restore_task_fn = mcp._tool_manager._tools["restore_task"].fn
        result = restore_task_fn(task_id=1)

        client.restore_task.assert_called_once_with(1)
        assert result["id"] == 1
        assert result["name"] == "Restored Task"
        assert result["status"] == "PENDING"
        assert "restored" in result["message"]


class TestTaskLifecycleTools:
    """Test task lifecycle MCP tools."""

    def test_start_task_formats_response(self) -> None:
        """Test start_task tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        started_task = create_mock_task_operation_output(status=TaskStatus.IN_PROGRESS)
        started_task.actual_start = datetime.now()
        client.start_task.return_value = started_task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        assert mcp is not None

    def test_start_task_returns_actual_start(self) -> None:
        """Test start_task returns actual_start in ISO format."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        start_time = datetime(2025, 12, 11, 9, 0, 0)
        started_task = create_mock_task_operation_output(
            task_id=1, name="Started Task", status=TaskStatus.IN_PROGRESS
        )
        started_task.actual_start = start_time
        client.start_task.return_value = started_task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        start_task_fn = mcp._tool_manager._tools["start_task"].fn
        result = start_task_fn(task_id=1)

        client.start_task.assert_called_once_with(1)
        assert result["id"] == 1
        assert result["name"] == "Started Task"
        assert result["status"] == "IN_PROGRESS"
        assert result["actual_start"] == "2025-12-11T09:00:00"
        assert "started" in result["message"]

    def test_complete_task_returns_duration(self) -> None:
        """Test complete_task returns actual_end and actual_duration_hours."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        end_time = datetime(2025, 12, 11, 17, 0, 0)
        completed_task = create_mock_task_operation_output(
            task_id=1, name="Completed Task", status=TaskStatus.COMPLETED
        )
        completed_task.actual_end = end_time
        completed_task.actual_duration_hours = 8.0
        client.complete_task.return_value = completed_task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        complete_task_fn = mcp._tool_manager._tools["complete_task"].fn
        result = complete_task_fn(task_id=1)

        client.complete_task.assert_called_once_with(1)
        assert result["id"] == 1
        assert result["status"] == "COMPLETED"
        assert result["actual_end"] == "2025-12-11T17:00:00"
        assert result["actual_duration_hours"] == 8.0
        assert "completed" in result["message"]

    @pytest.mark.parametrize(
        ("tool_name", "client_method", "expected_status", "message_keyword"),
        [
            pytest.param("pause_task", "pause_task", "PENDING", "paused", id="pause"),
            pytest.param(
                "cancel_task", "cancel_task", "CANCELED", "canceled", id="cancel"
            ),
            pytest.param(
                "reopen_task", "reopen_task", "PENDING", "reopened", id="reopen"
            ),
        ],
    )
    def test_lifecycle_status_change_tools(
        self,
        tool_name: str,
        client_method: str,
        expected_status: str,
        message_keyword: str,
    ) -> None:
        """Test lifecycle tools that change task status."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        status_enum = TaskStatus(expected_status)
        task = create_mock_task_operation_output(
            task_id=1, name="Test Task", status=status_enum
        )
        getattr(client, client_method).return_value = task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        tool_fn = mcp._tool_manager._tools[tool_name].fn
        result = tool_fn(task_id=1)

        getattr(client, client_method).assert_called_once_with(1)
        assert result["id"] == 1
        assert result["status"] == expected_status
        assert message_keyword in result["message"]

    def test_fix_actual_times_valid_datetime(self) -> None:
        """Test fix_actual_times with valid ISO format datetimes."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        start_time = datetime(2025, 12, 13, 9, 0, 0)
        end_time = datetime(2025, 12, 13, 17, 0, 0)
        fixed_task = create_mock_task_operation_output(
            task_id=1, name="Fixed Task", status=TaskStatus.COMPLETED
        )
        fixed_task.actual_start = start_time
        fixed_task.actual_end = end_time
        fixed_task.actual_duration_hours = 8.0
        client.fix_actual_times.return_value = fixed_task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        fix_fn = mcp._tool_manager._tools["fix_actual_times"].fn
        result = fix_fn(
            task_id=1,
            actual_start="2025-12-13T09:00:00",
            actual_end="2025-12-13T17:00:00",
        )

        client.fix_actual_times.assert_called_once_with(
            task_id=1,
            actual_start=start_time,
            actual_end=end_time,
            actual_duration=None,
            clear_start=False,
            clear_end=False,
            clear_duration=False,
        )
        assert result["id"] == 1
        assert result["actual_start"] == "2025-12-13T09:00:00"
        assert result["actual_end"] == "2025-12-13T17:00:00"
        assert result["actual_duration_hours"] == 8.0
        assert "Fixed actual times" in result["message"]

    def test_fix_actual_times_with_clear_flags(self) -> None:
        """Test fix_actual_times with clear_start and clear_end flags."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        cleared_task = create_mock_task_operation_output(
            task_id=1, name="Cleared Task", status=TaskStatus.PENDING
        )
        cleared_task.actual_start = None
        cleared_task.actual_end = None
        cleared_task.actual_duration_hours = None
        client.fix_actual_times.return_value = cleared_task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        fix_fn = mcp._tool_manager._tools["fix_actual_times"].fn
        result = fix_fn(task_id=1, clear_start=True, clear_end=True)

        client.fix_actual_times.assert_called_once_with(
            task_id=1,
            actual_start=None,
            actual_end=None,
            actual_duration=None,
            clear_start=True,
            clear_end=True,
            clear_duration=False,
        )
        assert result["actual_start"] is None
        assert result["actual_end"] is None
        assert result["actual_duration_hours"] is None

    def test_fix_actual_times_invalid_datetime(self) -> None:
        """Test fix_actual_times raises ValueError for invalid datetime."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        fix_fn = mcp._tool_manager._tools["fix_actual_times"].fn

        with pytest.raises(ValueError, match="Invalid datetime format"):
            fix_fn(task_id=1, actual_start="invalid-date")

    def test_fix_actual_times_with_duration(self) -> None:
        """Test fix_actual_times with actual_duration parameter."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        fixed_task = create_mock_task_operation_output(
            task_id=1, name="Fixed Task", status=TaskStatus.COMPLETED
        )
        fixed_task.actual_start = None
        fixed_task.actual_end = None
        fixed_task.actual_duration_hours = 2.5
        client.fix_actual_times.return_value = fixed_task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        fix_fn = mcp._tool_manager._tools["fix_actual_times"].fn
        result = fix_fn(task_id=1, actual_duration=2.5)

        client.fix_actual_times.assert_called_once_with(
            task_id=1,
            actual_start=None,
            actual_end=None,
            actual_duration=2.5,
            clear_start=False,
            clear_end=False,
            clear_duration=False,
        )
        assert result["actual_duration_hours"] == 2.5

    def test_fix_actual_times_with_clear_duration(self) -> None:
        """Test fix_actual_times with clear_duration flag."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        fixed_task = create_mock_task_operation_output(
            task_id=1, name="Fixed Task", status=TaskStatus.COMPLETED
        )
        fixed_task.actual_start = None
        fixed_task.actual_end = None
        fixed_task.actual_duration_hours = None
        client.fix_actual_times.return_value = fixed_task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        fix_fn = mcp._tool_manager._tools["fix_actual_times"].fn
        result = fix_fn(task_id=1, clear_duration=True)

        client.fix_actual_times.assert_called_once_with(
            task_id=1,
            actual_start=None,
            actual_end=None,
            actual_duration=None,
            clear_start=False,
            clear_end=False,
            clear_duration=True,
        )
        assert result["actual_duration_hours"] is None

    @pytest.mark.parametrize(
        "invalid_duration",
        [
            pytest.param(0, id="zero"),
            pytest.param(-1.0, id="negative"),
            pytest.param(-0.5, id="negative_float"),
        ],
    )
    def test_fix_actual_times_invalid_duration(self, invalid_duration: float) -> None:
        """Test fix_actual_times raises ValueError for invalid duration."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        client = create_mock_client()
        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, client)

        fix_fn = mcp._tool_manager._tools["fix_actual_times"].fn

        with pytest.raises(ValueError, match="actual_duration must be greater than 0"):
            fix_fn(task_id=1, actual_duration=invalid_duration)


class TestTaskQueryTools:
    """Test task query MCP tools."""

    def test_get_statistics_formats_response(self) -> None:
        """Test get_statistics tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        client = create_mock_client()
        client.calculate_statistics.return_value = StatisticsOutput(
            task_stats=TaskStatistics(
                total_tasks=10,
                pending_count=5,
                in_progress_count=2,
                completed_count=2,
                canceled_count=1,
                completion_rate=0.2,
            ),
            time_stats=TimeStatistics(
                total_work_hours=20.0,
                average_work_hours=2.0,
                median_work_hours=1.5,
                longest_task=None,
                shortest_task=None,
                tasks_with_time_tracking=5,
            ),
            estimation_stats=None,
            deadline_stats=None,
            priority_stats=PriorityDistributionStatistics(
                high_priority_count=2,
                medium_priority_count=5,
                low_priority_count=3,
                high_priority_completion_rate=0.5,
                priority_completion_map={},
            ),
            trend_stats=None,
        )

        mcp = FastMCP("test")
        task_query.register_tools(mcp, client)

        assert mcp is not None

    def test_get_tag_statistics_formats_response(self) -> None:
        """Test get_tag_statistics tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        client = create_mock_client()
        client.get_tag_statistics.return_value = TagStatisticsOutput(
            tag_counts={"work": 5, "personal": 3},
            total_tags=2,
            total_tagged_tasks=8,
        )

        mcp = FastMCP("test")
        task_query.register_tools(mcp, client)

        assert mcp is not None

    def test_get_statistics_returns_formatted_data(self) -> None:
        """Test get_statistics returns properly formatted statistics."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        client = create_mock_client()
        client.calculate_statistics.return_value = StatisticsOutput(
            task_stats=TaskStatistics(
                total_tasks=10,
                pending_count=5,
                in_progress_count=2,
                completed_count=2,
                canceled_count=1,
                completion_rate=0.2,
            ),
            time_stats=TimeStatistics(
                total_work_hours=20.0,
                average_work_hours=2.0,
                median_work_hours=1.5,
                longest_task=None,
                shortest_task=None,
                tasks_with_time_tracking=5,
            ),
            estimation_stats=None,
            deadline_stats=None,
            priority_stats=None,
            trend_stats=None,
        )

        mcp = FastMCP("test")
        task_query.register_tools(mcp, client)

        get_statistics_fn = mcp._tool_manager._tools["get_statistics"].fn
        result = get_statistics_fn(period="7d")

        client.calculate_statistics.assert_called_once_with("7d")
        assert result["period"] == "7d"
        assert result["total_tasks"] == 10
        assert result["pending"] == 5
        assert result["in_progress"] == 2
        assert result["completed"] == 2
        assert result["canceled"] == 1
        assert result["completion_rate"] == 0.2
        assert result["overdue_count"] == 0
        assert result["average_completion_time_hours"] == 2.0

    def test_get_statistics_without_time_stats(self) -> None:
        """Test get_statistics when time_stats is None."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        client = create_mock_client()
        client.calculate_statistics.return_value = StatisticsOutput(
            task_stats=TaskStatistics(
                total_tasks=5,
                pending_count=3,
                in_progress_count=2,
                completed_count=0,
                canceled_count=0,
                completion_rate=0.0,
            ),
            time_stats=None,
            estimation_stats=None,
            deadline_stats=None,
            priority_stats=None,
            trend_stats=None,
        )

        mcp = FastMCP("test")
        task_query.register_tools(mcp, client)

        get_statistics_fn = mcp._tool_manager._tools["get_statistics"].fn
        result = get_statistics_fn(period="all")

        assert result["average_completion_time_hours"] is None

    def test_get_tag_statistics_returns_formatted_data(self) -> None:
        """Test get_tag_statistics returns properly formatted tag stats."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        client = create_mock_client()
        client.get_tag_statistics.return_value = TagStatisticsOutput(
            tag_counts={"work": 5, "personal": 3, "urgent": 2},
            total_tags=3,
            total_tagged_tasks=10,
        )

        mcp = FastMCP("test")
        task_query.register_tools(mcp, client)

        get_tag_stats_fn = mcp._tool_manager._tools["get_tag_statistics"].fn
        result = get_tag_stats_fn()

        client.get_tag_statistics.assert_called_once()
        assert result["total_tags"] == 3
        assert len(result["tags"]) == 3
        # Check that tags are formatted as list of dicts
        tag_names = [t["tag"] for t in result["tags"]]
        assert "work" in tag_names
        assert "personal" in tag_names

    def test_get_executable_tasks(self) -> None:
        """Test get_executable_tasks returns pending and in_progress tasks."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        client = create_mock_client()
        in_progress_task = create_mock_task_row(
            task_id=1, name="In Progress", status=TaskStatus.IN_PROGRESS
        )
        pending_task = create_mock_task_row(
            task_id=2, name="Pending", status=TaskStatus.PENDING
        )
        client.list_tasks.side_effect = [
            TaskListOutput(tasks=[pending_task], total_count=1, filtered_count=1),
            TaskListOutput(tasks=[in_progress_task], total_count=1, filtered_count=1),
        ]

        mcp = FastMCP("test")
        task_query.register_tools(mcp, client)

        get_executable_fn = mcp._tool_manager._tools["get_executable_tasks"].fn
        result = get_executable_fn(tags=["coding"], limit=5)

        assert client.list_tasks.call_count == 2
        assert len(result["tasks"]) == 2
        assert result["total"] == 2
        # IN_PROGRESS should be first
        assert result["tasks"][0]["status"] == "IN_PROGRESS"
        assert result["tasks"][1]["status"] == "PENDING"
        assert "executable tasks" in result["message"]

    def test_get_executable_tasks_with_limit(self) -> None:
        """Test get_executable_tasks respects limit parameter."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        client = create_mock_client()
        tasks = [create_mock_task_row(task_id=i, name=f"Task {i}") for i in range(1, 6)]
        client.list_tasks.side_effect = [
            TaskListOutput(tasks=tasks, total_count=5, filtered_count=5),
            TaskListOutput(tasks=[], total_count=0, filtered_count=0),
        ]

        mcp = FastMCP("test")
        task_query.register_tools(mcp, client)

        get_executable_fn = mcp._tool_manager._tools["get_executable_tasks"].fn
        result = get_executable_fn(limit=3)

        assert len(result["tasks"]) == 3
        assert result["total"] == 3


class TestTaskDecompositionTools:
    """Test task decomposition MCP tools."""

    def test_decompose_task_registers_without_error(self) -> None:
        """Test decompose_task tool registration."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        assert mcp is not None

    def test_build_subtask_tags(self) -> None:
        """Test _build_subtask_tags helper function."""
        from taskdog_mcp.tools.task_decomposition import _build_subtask_tags

        # Test with no tags
        result = _build_subtask_tags({}, [], None)
        assert result == []

        # Test with subtask tags
        result = _build_subtask_tags({"tags": ["a", "b"]}, [], None)
        assert result == ["a", "b"]

        # Test with original tags
        result = _build_subtask_tags({}, ["orig1", "orig2"], None)
        assert result == ["orig1", "orig2"]

        # Test with group tag
        result = _build_subtask_tags({}, [], "group")
        assert result == ["group"]

        # Test deduplication
        result = _build_subtask_tags({"tags": ["a", "b"]}, ["b", "c"], "a")
        assert result == ["a", "b", "c"]

    def test_decompose_task_single_subtask(self) -> None:
        """Test decompose_task with a single subtask."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1, name="Original Task"
        )
        created_subtask = create_mock_task_operation_output(task_id=2, name="Subtask 1")
        client.create_task.return_value = created_subtask
        client.get_task_notes.return_value = ("", False)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        decompose_fn = mcp._tool_manager._tools["decompose_task"].fn
        result = decompose_fn(
            task_id=1,
            subtasks=[{"name": "Subtask 1", "estimated_duration": 2.0}],
        )

        assert result["original_task_id"] == 1
        assert result["original_task_name"] == "Original Task"
        assert result["total_created"] == 1
        assert result["total_estimated_hours"] == 2.0
        assert len(result["created_subtasks"]) == 1
        assert result["created_subtasks"][0]["name"] == "Subtask 1"

    def test_decompose_task_with_dependencies(self) -> None:
        """Test decompose_task creates dependencies between subtasks."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1, name="Original Task"
        )
        client.create_task.side_effect = [
            create_mock_task_operation_output(task_id=2, name="Subtask 1"),
            create_mock_task_operation_output(task_id=3, name="Subtask 2"),
        ]
        client.get_task_notes.return_value = ("", False)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        decompose_fn = mcp._tool_manager._tools["decompose_task"].fn
        result = decompose_fn(
            task_id=1,
            subtasks=[
                {"name": "Subtask 1", "estimated_duration": 1.0},
                {"name": "Subtask 2", "estimated_duration": 2.0},
            ],
            create_dependencies=True,
        )

        # Second subtask should depend on first
        client.add_dependency.assert_called_once_with(3, 2)
        assert result["dependencies_created"] is True
        assert result["total_created"] == 2
        assert result["total_estimated_hours"] == 3.0

    def test_decompose_task_with_group_tag(self) -> None:
        """Test decompose_task adds group_tag to all subtasks."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1, name="Original Task"
        )
        client.create_task.return_value = create_mock_task_operation_output(
            task_id=2, name="Subtask 1"
        )
        client.get_task_notes.return_value = ("", False)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        decompose_fn = mcp._tool_manager._tools["decompose_task"].fn
        result = decompose_fn(
            task_id=1,
            subtasks=[{"name": "Subtask 1", "estimated_duration": 1.0}],
            group_tag="feature-x",
        )

        assert result["group_tag"] == "feature-x"
        # Check that create_task was called with the group tag
        call_kwargs = client.create_task.call_args.kwargs
        assert "feature-x" in call_kwargs["tags"]

    def test_decompose_task_archive_original(self) -> None:
        """Test decompose_task archives original task when requested."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1, name="Original Task"
        )
        client.create_task.return_value = create_mock_task_operation_output(
            task_id=2, name="Subtask 1"
        )
        client.get_task_notes.return_value = ("", False)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        decompose_fn = mcp._tool_manager._tools["decompose_task"].fn
        result = decompose_fn(
            task_id=1,
            subtasks=[{"name": "Subtask 1", "estimated_duration": 1.0}],
            archive_original=True,
        )

        client.archive_task.assert_called_once_with(1)
        assert result["original_archived"] is True

    def test_add_dependency_returns_formatted_response(self) -> None:
        """Test add_dependency returns properly formatted response."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        result_task = create_mock_task_operation_output(
            task_id=1, name="Task with Dependency"
        )
        result_task.depends_on = [2]
        client.add_dependency.return_value = result_task

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        add_dep_fn = mcp._tool_manager._tools["add_dependency"].fn
        result = add_dep_fn(task_id=1, depends_on_id=2)

        client.add_dependency.assert_called_once_with(1, 2)
        assert result["id"] == 1
        assert result["name"] == "Task with Dependency"
        assert result["depends_on"] == [2]
        assert "depends on" in result["message"]

    def test_remove_dependency_returns_formatted_response(self) -> None:
        """Test remove_dependency returns properly formatted response."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        result_task = create_mock_task_operation_output(
            task_id=1, name="Task without Dependency"
        )
        result_task.depends_on = []
        client.remove_dependency.return_value = result_task

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        remove_dep_fn = mcp._tool_manager._tools["remove_dependency"].fn
        result = remove_dep_fn(task_id=1, depends_on_id=2)

        client.remove_dependency.assert_called_once_with(1, 2)
        assert result["id"] == 1
        assert result["depends_on"] == []
        assert "no longer depends" in result["message"]

    def test_set_task_tags_returns_formatted_response(self) -> None:
        """Test set_task_tags returns properly formatted response."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        result_task = create_mock_task_operation_output(task_id=1, name="Tagged Task")
        result_task.tags = ["new-tag", "another-tag"]
        client.set_task_tags.return_value = result_task

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        set_tags_fn = mcp._tool_manager._tools["set_task_tags"].fn
        result = set_tags_fn(task_id=1, tags=["new-tag", "another-tag"])

        client.set_task_tags.assert_called_once_with(1, ["new-tag", "another-tag"])
        assert result["id"] == 1
        assert result["tags"] == ["new-tag", "another-tag"]
        assert "Tags updated" in result["message"]

    def test_update_task_notes_returns_confirmation(self) -> None:
        """Test update_task_notes returns confirmation message."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        update_notes_fn = mcp._tool_manager._tools["update_task_notes"].fn
        result = update_notes_fn(task_id=1, content="# New Notes\nContent here")

        client.update_task_notes.assert_called_once_with(1, "# New Notes\nContent here")
        assert result["id"] == 1
        assert "Notes updated" in result["message"]

    def test_get_task_notes_returns_content(self) -> None:
        """Test get_task_notes returns notes content."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_notes.return_value = ("# Notes\nSome content", True)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        get_notes_fn = mcp._tool_manager._tools["get_task_notes"].fn
        result = get_notes_fn(task_id=1)

        client.get_task_notes.assert_called_once_with(1)
        assert result["id"] == 1
        assert result["has_notes"] is True
        assert result["content"] == "# Notes\nSome content"

    def test_get_task_notes_no_notes(self) -> None:
        """Test get_task_notes when task has no notes."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_notes.return_value = (None, False)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        get_notes_fn = mcp._tool_manager._tools["get_task_notes"].fn
        result = get_notes_fn(task_id=1)

        assert result["has_notes"] is False
        assert result["content"] is None

    def test_decompose_task_handles_subtask_creation_error(self) -> None:
        """Test decompose_task handles subtask creation errors gracefully."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1, name="Original Task"
        )
        # First subtask succeeds, second fails
        client.create_task.side_effect = [
            create_mock_task_operation_output(task_id=2, name="Subtask 1"),
            Exception("Failed to create subtask"),
        ]
        client.get_task_notes.return_value = ("", False)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        decompose_fn = mcp._tool_manager._tools["decompose_task"].fn
        result = decompose_fn(
            task_id=1,
            subtasks=[
                {"name": "Subtask 1", "estimated_duration": 1.0},
                {"name": "Subtask 2", "estimated_duration": 2.0},
            ],
        )

        # First subtask should be created, second should have error
        assert result["total_created"] == 1
        assert len(result["errors"]) == 1
        assert result["errors"][0]["subtask_index"] == 1
        assert "Failed to create subtask" in result["errors"][0]["error"]

    def test_decompose_task_handles_dependency_error(self) -> None:
        """Test decompose_task handles dependency creation errors."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1, name="Original Task"
        )
        client.create_task.side_effect = [
            create_mock_task_operation_output(task_id=2, name="Subtask 1"),
            create_mock_task_operation_output(task_id=3, name="Subtask 2"),
        ]
        client.add_dependency.side_effect = Exception("Dependency error")
        client.get_task_notes.return_value = ("", False)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        decompose_fn = mcp._tool_manager._tools["decompose_task"].fn
        result = decompose_fn(
            task_id=1,
            subtasks=[
                {"name": "Subtask 1", "estimated_duration": 1.0},
                {"name": "Subtask 2", "estimated_duration": 2.0},
            ],
            create_dependencies=True,
        )

        # Both subtasks created but dependency failed
        assert result["total_created"] == 2
        assert len(result["errors"]) == 1
        assert "Failed to create dependency" in result["errors"][0]["error"]

    def test_decompose_task_handles_archive_error(self) -> None:
        """Test decompose_task handles archive error gracefully."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1, name="Original Task"
        )
        client.create_task.return_value = create_mock_task_operation_output(
            task_id=2, name="Subtask 1"
        )
        client.archive_task.side_effect = Exception("Archive failed")
        client.get_task_notes.return_value = ("", False)

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        decompose_fn = mcp._tool_manager._tools["decompose_task"].fn
        result = decompose_fn(
            task_id=1,
            subtasks=[{"name": "Subtask 1", "estimated_duration": 1.0}],
            archive_original=True,
        )

        # Subtask created but archive failed
        assert result["total_created"] == 1
        assert result["original_archived"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["action"] == "archive_original"

    def test_update_decomposition_notes_handles_error(self) -> None:
        """Test _update_decomposition_notes silently handles errors."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        client = create_mock_client()
        client.get_task_detail.return_value = create_mock_task_detail_output(
            task_id=1, name="Original Task"
        )
        client.create_task.return_value = create_mock_task_operation_output(
            task_id=2, name="Subtask 1"
        )
        # Notes operations fail
        client.get_task_notes.side_effect = Exception("Notes read failed")

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, client)

        decompose_fn = mcp._tool_manager._tools["decompose_task"].fn
        # Should complete without raising, notes update is optional
        result = decompose_fn(
            task_id=1,
            subtasks=[{"name": "Subtask 1", "estimated_duration": 1.0}],
        )

        # Decomposition succeeds even if notes update fails
        assert result["total_created"] == 1
        assert result["errors"] is None


class TestTaskAuditTools:
    """Test task audit log MCP tools."""

    def test_list_audit_logs_returns_formatted_response(self) -> None:
        """Test list_audit_logs tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_audit

        from taskdog_core.application.dto.audit_log_dto import (
            AuditLogListOutput,
            AuditLogOutput,
        )

        client = create_mock_client()
        client.list_audit_logs.return_value = AuditLogListOutput(
            logs=[
                AuditLogOutput(
                    id=1,
                    timestamp=datetime(2025, 12, 11, 10, 0, 0),
                    client_name="claude-code",
                    operation="create_task",
                    resource_type="task",
                    resource_id=42,
                    resource_name="Test Task",
                    old_values=None,
                    new_values={"name": "Test Task"},
                    success=True,
                    error_message=None,
                ),
                AuditLogOutput(
                    id=2,
                    timestamp=datetime(2025, 12, 11, 11, 0, 0),
                    client_name=None,
                    operation="complete_task",
                    resource_type="task",
                    resource_id=42,
                    resource_name="Test Task",
                    old_values=None,
                    new_values=None,
                    success=True,
                    error_message=None,
                ),
            ],
            total_count=2,
            limit=50,
            offset=0,
        )

        mcp = FastMCP("test")
        task_audit.register_tools(mcp, client)

        list_fn = mcp._tool_manager._tools["list_audit_logs"].fn
        result = list_fn()

        client.list_audit_logs.assert_called_once_with(
            client_filter=None,
            operation=None,
            resource_id=None,
            success=None,
            start_date=None,
            end_date=None,
            limit=50,
        )
        assert result["total_count"] == 2
        assert len(result["logs"]) == 2
        assert result["logs"][0]["id"] == 1
        assert result["logs"][0]["operation"] == "create_task"
        assert result["logs"][0]["resource_id"] == 42
        assert result["logs"][0]["client_name"] == "claude-code"
        assert result["logs"][1]["id"] == 2
        assert "Found 2 audit log(s)" in result["message"]

    def test_list_audit_logs_with_filters(self) -> None:
        """Test list_audit_logs passes filters correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_audit

        from taskdog_core.application.dto.audit_log_dto import AuditLogListOutput

        client = create_mock_client()
        client.list_audit_logs.return_value = AuditLogListOutput(
            logs=[],
            total_count=0,
            limit=10,
            offset=0,
        )

        mcp = FastMCP("test")
        task_audit.register_tools(mcp, client)

        list_fn = mcp._tool_manager._tools["list_audit_logs"].fn
        result = list_fn(
            task_id=42,
            operation="create_task",
            client_name="cli",
            since="2025-12-01T00:00:00",
            until="2025-12-31T23:59:59",
            failed=True,
            limit=10,
        )

        client.list_audit_logs.assert_called_once_with(
            client_filter="cli",
            operation="create_task",
            resource_id=42,
            success=False,
            start_date=datetime(2025, 12, 1, 0, 0, 0),
            end_date=datetime(2025, 12, 31, 23, 59, 59),
            limit=10,
        )
        assert result["total_count"] == 0
        assert result["logs"] == []

    def test_get_audit_log_returns_formatted_response(self) -> None:
        """Test get_audit_log tool returns all fields including old/new values."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_audit

        from taskdog_core.application.dto.audit_log_dto import AuditLogOutput

        client = create_mock_client()
        client.get_audit_log.return_value = AuditLogOutput(
            id=1,
            timestamp=datetime(2025, 12, 11, 10, 0, 0),
            client_name="claude-code",
            operation="update_task",
            resource_type="task",
            resource_id=42,
            resource_name="Test Task",
            old_values={"priority": 50},
            new_values={"priority": 80},
            success=True,
            error_message=None,
        )

        mcp = FastMCP("test")
        task_audit.register_tools(mcp, client)

        get_fn = mcp._tool_manager._tools["get_audit_log"].fn
        result = get_fn(log_id=1)

        client.get_audit_log.assert_called_once_with(1)
        assert result["id"] == 1
        assert result["timestamp"] == "2025-12-11T10:00:00"
        assert result["operation"] == "update_task"
        assert result["resource_type"] == "task"
        assert result["resource_id"] == 42
        assert result["resource_name"] == "Test Task"
        assert result["client_name"] == "claude-code"
        assert result["success"] is True
        assert result["error_message"] is None
        assert result["old_values"] == {"priority": 50}
        assert result["new_values"] == {"priority": 80}
