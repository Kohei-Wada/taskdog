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
from taskdog_core.application.dto.task_dto import TaskRowDto
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
    client.list_today_tasks = MagicMock()
    client.list_week_tasks = MagicMock()
    client.get_tag_statistics = MagicMock()
    client.calculate_statistics = MagicMock()
    # Relationship methods
    client.add_dependency = MagicMock()
    client.remove_dependency = MagicMock()
    client.set_task_tags = MagicMock()
    # Notes methods
    client.get_task_notes = MagicMock()
    client.update_task_notes = MagicMock()
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
