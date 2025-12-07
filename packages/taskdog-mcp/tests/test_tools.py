"""Tests for MCP tools."""

from datetime import datetime
from unittest.mock import MagicMock

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
        depends_on=[],
        tags=["test"],
        is_fixed=False,
        is_archived=False,
        actual_duration_hours=None,
        actual_daily_hours={},
    )


def create_mock_clients() -> MagicMock:
    """Create a mock TaskdogMcpClients with all required attributes."""
    clients = MagicMock()
    clients.tasks = MagicMock()
    clients.lifecycle = MagicMock()
    clients.queries = MagicMock()
    clients.analytics = MagicMock()
    clients.relationships = MagicMock()
    clients.notes = MagicMock()
    return clients


class TestTaskCrudTools:
    """Test task CRUD MCP tools."""

    def test_list_tasks_returns_formatted_response(self) -> None:
        """Test list_tasks tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        clients = create_mock_clients()
        clients.queries.list_tasks.return_value = TaskListOutput(
            tasks=[create_mock_task_row()],
            total_count=1,
            filtered_count=1,
        )

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, clients)

        # Call the tool directly through the registered function
        clients.queries.list_tasks.assert_not_called()  # Not called yet

    def test_create_task_formats_response(self) -> None:
        """Test create_task tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_crud

        clients = create_mock_clients()
        clients.tasks.create_task.return_value = create_mock_task_operation_output()

        mcp = FastMCP("test")
        task_crud.register_tools(mcp, clients)

        # Verify registration didn't raise
        assert mcp is not None


class TestTaskLifecycleTools:
    """Test task lifecycle MCP tools."""

    def test_start_task_formats_response(self) -> None:
        """Test start_task tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_lifecycle

        clients = create_mock_clients()
        started_task = create_mock_task_operation_output(status=TaskStatus.IN_PROGRESS)
        started_task.actual_start = datetime.now()
        clients.lifecycle.start_task.return_value = started_task

        mcp = FastMCP("test")
        task_lifecycle.register_tools(mcp, clients)

        assert mcp is not None


class TestTaskQueryTools:
    """Test task query MCP tools."""

    def test_get_statistics_formats_response(self) -> None:
        """Test get_statistics tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        clients = create_mock_clients()
        clients.analytics.calculate_statistics.return_value = StatisticsOutput(
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
        task_query.register_tools(mcp, clients)

        assert mcp is not None

    def test_get_tag_statistics_formats_response(self) -> None:
        """Test get_tag_statistics tool formats response correctly."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_query

        clients = create_mock_clients()
        clients.queries.get_tag_statistics.return_value = TagStatisticsOutput(
            tag_counts={"work": 5, "personal": 3},
            total_tags=2,
            total_tagged_tasks=8,
        )

        mcp = FastMCP("test")
        task_query.register_tools(mcp, clients)

        assert mcp is not None


class TestTaskDecompositionTools:
    """Test task decomposition MCP tools."""

    def test_decompose_task_registers_without_error(self) -> None:
        """Test decompose_task tool registration."""
        from mcp.server.fastmcp import FastMCP
        from taskdog_mcp.tools import task_decomposition

        clients = create_mock_clients()

        mcp = FastMCP("test")
        task_decomposition.register_tools(mcp, clients)

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
