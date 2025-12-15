"""Tests for TaskdogApiClient facade."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from taskdog_client.taskdog_api_client import TaskdogApiClient


class TestTaskdogApiClientInit:
    """Test cases for TaskdogApiClient initialization."""

    @patch("taskdog_client.taskdog_api_client.BaseApiClient")
    @patch("taskdog_client.taskdog_api_client.TaskClient")
    @patch("taskdog_client.taskdog_api_client.LifecycleClient")
    @patch("taskdog_client.taskdog_api_client.RelationshipClient")
    @patch("taskdog_client.taskdog_api_client.QueryClient")
    @patch("taskdog_client.taskdog_api_client.AnalyticsClient")
    @patch("taskdog_client.taskdog_api_client.NotesClient")
    @patch("taskdog_client.taskdog_api_client.AuditClient")
    def test_init_creates_all_clients(
        self,
        mock_audit,
        mock_notes,
        mock_analytics,
        mock_query,
        mock_relationship,
        mock_lifecycle,
        mock_task,
        mock_base,
    ):
        """Test that initialization creates all specialized clients."""
        mock_base_instance = MagicMock()
        mock_base.return_value = mock_base_instance

        client = TaskdogApiClient(
            base_url="http://test:8000",
            timeout=60.0,
            api_key="test-key",
        )

        mock_base.assert_called_once_with("http://test:8000", 60.0, api_key="test-key")
        mock_task.assert_called_once_with(mock_base_instance)
        mock_lifecycle.assert_called_once_with(mock_base_instance)
        mock_relationship.assert_called_once_with(mock_base_instance)
        mock_analytics.assert_called_once_with(mock_base_instance)
        mock_notes.assert_called_once_with(mock_base_instance)
        mock_audit.assert_called_once_with(mock_base_instance)
        assert client.base_url == "http://test:8000"


class TestTaskdogApiClientProperties:
    """Test cases for TaskdogApiClient properties."""

    @pytest.fixture
    def client(self):
        """Create a TaskdogApiClient with mocked dependencies."""
        with patch("taskdog_client.taskdog_api_client.BaseApiClient") as mock_base:
            mock_base_instance = MagicMock()
            mock_base_instance.client = MagicMock()
            mock_base_instance.client_id = "test-client-id"
            mock_base_instance.api_key = "test-api-key"
            mock_base.return_value = mock_base_instance
            yield TaskdogApiClient()

    def test_client_property(self, client):
        """Test client property returns underlying httpx client."""
        assert client.client is not None

    def test_client_id_property(self, client):
        """Test client_id property returns base client's client_id."""
        assert client.client_id == "test-client-id"

    def test_api_key_property(self, client):
        """Test api_key property returns base client's api_key."""
        assert client.api_key == "test-api-key"

    def test_set_client_id(self, client):
        """Test set_client_id sets the client_id on base client."""
        client.set_client_id("new-client-id")
        assert client._base.client_id == "new-client-id"


class TestTaskdogApiClientLifecycle:
    """Test cases for TaskdogApiClient lifecycle methods."""

    @pytest.fixture
    def client(self):
        """Create a TaskdogApiClient with mocked dependencies."""
        with patch("taskdog_client.taskdog_api_client.BaseApiClient") as mock_base:
            mock_base_instance = MagicMock()
            mock_base.return_value = mock_base_instance
            yield TaskdogApiClient()

    def test_close(self, client):
        """Test close delegates to base client."""
        client.close()
        client._base.close.assert_called_once()

    def test_context_manager(self):
        """Test context manager support."""
        with patch("taskdog_client.taskdog_api_client.BaseApiClient") as mock_base:
            mock_base_instance = MagicMock()
            mock_base.return_value = mock_base_instance

            with TaskdogApiClient() as client:
                assert client is not None

            mock_base_instance.close.assert_called_once()

    def test_check_health_success(self, client):
        """Test check_health returns True on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        client._base._safe_request.return_value = mock_response

        assert client.check_health() is True

    def test_check_health_failure(self, client):
        """Test check_health returns False on failure."""
        client._base._safe_request.side_effect = Exception("Connection error")

        assert client.check_health() is False


class TestTaskdogApiClientDelegation:
    """Test cases for TaskdogApiClient delegation methods."""

    @pytest.fixture
    def client(self):
        """Create a TaskdogApiClient with mocked dependencies."""
        with (
            patch("taskdog_client.taskdog_api_client.BaseApiClient"),
            patch("taskdog_client.taskdog_api_client.TaskClient") as mock_task,
            patch(
                "taskdog_client.taskdog_api_client.LifecycleClient"
            ) as mock_lifecycle,
            patch(
                "taskdog_client.taskdog_api_client.RelationshipClient"
            ) as mock_relationship,
            patch("taskdog_client.taskdog_api_client.QueryClient") as mock_query,
            patch(
                "taskdog_client.taskdog_api_client.AnalyticsClient"
            ) as mock_analytics,
            patch("taskdog_client.taskdog_api_client.NotesClient") as mock_notes,
            patch("taskdog_client.taskdog_api_client.AuditClient") as mock_audit,
        ):
            client = TaskdogApiClient()
            client._tasks = mock_task.return_value
            client._lifecycle = mock_lifecycle.return_value
            client._relationships = mock_relationship.return_value
            client._queries = mock_query.return_value
            client._analytics = mock_analytics.return_value
            client._notes = mock_notes.return_value
            client._audit = mock_audit.return_value
            yield client

    # Task CRUD methods
    def test_create_task(self, client):
        """Test create_task delegates to TaskClient."""
        deadline = datetime(2025, 12, 31, 18, 0, 0)
        client.create_task(
            name="Test Task",
            priority=5,
            deadline=deadline,
            estimated_duration=2.0,
            tags=["tag1"],
        )
        client._tasks.create_task.assert_called_once()

    def test_update_task(self, client):
        """Test update_task delegates to TaskClient."""
        client.update_task(task_id=1, name="Updated Task", priority=10)
        client._tasks.update_task.assert_called_once()

    def test_archive_task(self, client):
        """Test archive_task delegates to TaskClient."""
        client.archive_task(task_id=1)
        client._tasks.archive_task.assert_called_once_with(1)

    def test_restore_task(self, client):
        """Test restore_task delegates to TaskClient."""
        client.restore_task(task_id=1)
        client._tasks.restore_task.assert_called_once_with(1)

    def test_remove_task(self, client):
        """Test remove_task delegates to TaskClient."""
        client.remove_task(task_id=1)
        client._tasks.remove_task.assert_called_once_with(1)

    # Lifecycle methods
    def test_start_task(self, client):
        """Test start_task delegates to LifecycleClient."""
        client.start_task(task_id=1)
        client._lifecycle.start_task.assert_called_once_with(1)

    def test_complete_task(self, client):
        """Test complete_task delegates to LifecycleClient."""
        client.complete_task(task_id=1)
        client._lifecycle.complete_task.assert_called_once_with(1)

    def test_pause_task(self, client):
        """Test pause_task delegates to LifecycleClient."""
        client.pause_task(task_id=1)
        client._lifecycle.pause_task.assert_called_once_with(1)

    def test_cancel_task(self, client):
        """Test cancel_task delegates to LifecycleClient."""
        client.cancel_task(task_id=1)
        client._lifecycle.cancel_task.assert_called_once_with(1)

    def test_reopen_task(self, client):
        """Test reopen_task delegates to LifecycleClient."""
        client.reopen_task(task_id=1)
        client._lifecycle.reopen_task.assert_called_once_with(1)

    def test_fix_actual_times(self, client):
        """Test fix_actual_times delegates to LifecycleClient."""
        actual_start = datetime(2025, 1, 1, 9, 0, 0)
        client.fix_actual_times(task_id=1, actual_start=actual_start)
        client._lifecycle.fix_actual_times.assert_called_once()

    # Relationship methods
    def test_add_dependency(self, client):
        """Test add_dependency delegates to RelationshipClient."""
        client.add_dependency(task_id=1, depends_on_id=2)
        client._relationships.add_dependency.assert_called_once_with(1, 2)

    def test_remove_dependency(self, client):
        """Test remove_dependency delegates to RelationshipClient."""
        client.remove_dependency(task_id=1, depends_on_id=2)
        client._relationships.remove_dependency.assert_called_once_with(1, 2)

    def test_set_task_tags(self, client):
        """Test set_task_tags delegates to RelationshipClient."""
        client.set_task_tags(task_id=1, tags=["tag1", "tag2"])
        client._relationships.set_task_tags.assert_called_once_with(1, ["tag1", "tag2"])

    # Analytics methods
    def test_calculate_statistics(self, client):
        """Test calculate_statistics delegates to AnalyticsClient."""
        client.calculate_statistics(period="7d")
        client._analytics.calculate_statistics.assert_called_once_with("7d")

    def test_optimize_schedule(self, client):
        """Test optimize_schedule delegates to AnalyticsClient."""
        start = datetime(2025, 1, 1)
        client.optimize_schedule(
            algorithm="greedy",
            start_date=start,
            max_hours_per_day=8.0,
        )
        client._analytics.optimize_schedule.assert_called_once()

    def test_get_algorithm_metadata(self, client):
        """Test get_algorithm_metadata delegates to AnalyticsClient."""
        client.get_algorithm_metadata()
        client._analytics.get_algorithm_metadata.assert_called_once()

    # Query methods
    def test_list_tasks(self, client):
        """Test list_tasks delegates to QueryClient."""
        client.list_tasks(all=True, sort_by="priority")
        client._queries.list_tasks.assert_called_once()

    def test_list_today_tasks(self, client):
        """Test list_today_tasks delegates to QueryClient."""
        client.list_today_tasks()
        client._queries.list_today_tasks.assert_called_once()

    def test_list_week_tasks(self, client):
        """Test list_week_tasks delegates to QueryClient."""
        client.list_week_tasks()
        client._queries.list_week_tasks.assert_called_once()

    def test_get_task_by_id(self, client):
        """Test get_task_by_id delegates to QueryClient."""
        client.get_task_by_id(task_id=1)
        client._queries.get_task_by_id.assert_called_once_with(1)

    def test_get_task_detail(self, client):
        """Test get_task_detail delegates to QueryClient."""
        client.get_task_detail(task_id=1)
        client._queries.get_task_detail.assert_called_once_with(1)

    def test_get_gantt_data(self, client):
        """Test get_gantt_data delegates to QueryClient."""
        client.get_gantt_data()
        client._queries.get_gantt_data.assert_called_once()

    def test_get_tag_statistics(self, client):
        """Test get_tag_statistics delegates to QueryClient."""
        client.get_tag_statistics()
        client._queries.get_tag_statistics.assert_called_once()

    # Notes methods
    def test_get_task_notes(self, client):
        """Test get_task_notes delegates to NotesClient."""
        client.get_task_notes(task_id=1)
        client._notes.get_task_notes.assert_called_once_with(1)

    def test_update_task_notes(self, client):
        """Test update_task_notes delegates to NotesClient."""
        client.update_task_notes(task_id=1, content="Test content")
        client._notes.update_task_notes.assert_called_once_with(1, "Test content")

    def test_delete_task_notes(self, client):
        """Test delete_task_notes delegates to NotesClient."""
        client.delete_task_notes(task_id=1)
        client._notes.delete_task_notes.assert_called_once_with(1)

    def test_has_task_notes(self, client):
        """Test has_task_notes delegates to NotesClient."""
        client.has_task_notes(task_id=1)
        client._notes.has_task_notes.assert_called_once_with(1)

    # Audit methods
    def test_list_audit_logs(self, client):
        """Test list_audit_logs delegates to AuditClient."""
        client.list_audit_logs(limit=50)
        client._audit.list_audit_logs.assert_called_once()
