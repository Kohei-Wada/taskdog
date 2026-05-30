"""Tests for TUIMessageBuilder."""

from taskdog.tui.messages import TUIMessageBuilder


class TestTUIMessageBuilderTaskUpdated:
    """Test cases for task_updated method."""

    def test_single_field_update(self) -> None:
        """Test update message with single field."""
        result = TUIMessageBuilder.task_updated(123, ["priority"])

        assert result == "Updated task 123: priority"

    def test_multiple_fields_update(self) -> None:
        """Test update message with multiple fields."""
        result = TUIMessageBuilder.task_updated(456, ["priority", "deadline", "name"])

        assert result == "Updated task 456: priority, deadline, name"

    def test_update_with_source(self) -> None:
        """Test update message with source client ID."""
        result = TUIMessageBuilder.task_updated(
            789, ["status"], source_client_id="user@example.com"
        )

        assert result == "Updated task 789: status by user@example.com"

    def test_empty_fields_list(self) -> None:
        """Test update message with empty fields list."""
        result = TUIMessageBuilder.task_updated(1, [])

        assert result == "Updated task 1: "


class TestTUIMessageBuilderWebsocketEvent:
    """Test cases for websocket_event method."""

    def test_minimal_event(self) -> None:
        """Test minimal event with only required fields."""
        result = TUIMessageBuilder.websocket_event("created", "Task Name")

        assert result == "Task created: Task Name"

    def test_event_with_task_id(self) -> None:
        """Test event with task ID."""
        result = TUIMessageBuilder.websocket_event("deleted", "Task Name", task_id=123)

        assert result == "Task deleted: Task Name (ID: 123)"

    def test_event_with_details(self) -> None:
        """Test event with details."""
        result = TUIMessageBuilder.websocket_event(
            "status changed", "Task Name", task_id=456, details="PENDING → IN_PROGRESS"
        )

        assert (
            result == "Task status changed: Task Name (ID: 456) (PENDING → IN_PROGRESS)"
        )

    def test_event_with_source(self) -> None:
        """Test event with source client ID."""
        result = TUIMessageBuilder.websocket_event(
            "updated", "Task Name", task_id=789, source_client_id="remote_client"
        )

        assert result == "Task updated: Task Name (ID: 789) by remote_client"

    def test_event_with_all_fields(self) -> None:
        """Test event with all fields."""
        result = TUIMessageBuilder.websocket_event(
            "updated",
            "Important Task",
            task_id=100,
            details="priority, deadline",
            source_client_id="user123",
        )

        assert (
            result
            == "Task updated: Important Task (ID: 100) (priority, deadline) by user123"
        )

    def test_event_empty_details_excluded(self) -> None:
        """Test that empty details are excluded."""
        result = TUIMessageBuilder.websocket_event(
            "created", "Task", task_id=1, details=""
        )

        assert result == "Task created: Task (ID: 1)"
        assert "()" not in result


class TestTUIMessageBuilderScheduleOptimized:
    """Test cases for schedule_optimized method."""

    def test_schedule_optimized_message(self) -> None:
        """Test schedule optimized message format."""
        result = TUIMessageBuilder.schedule_optimized("greedy", 10, 2)

        assert result == "Schedule optimized (greedy): 10 tasks scheduled, 2 failed"

    def test_schedule_optimized_no_failures(self) -> None:
        """Test schedule optimized with no failures."""
        result = TUIMessageBuilder.schedule_optimized("balanced", 5, 0)

        assert result == "Schedule optimized (balanced): 5 tasks scheduled, 0 failed"

    def test_schedule_optimized_all_failed(self) -> None:
        """Test schedule optimized when all tasks failed."""
        result = TUIMessageBuilder.schedule_optimized("genetic", 0, 3)

        assert result == "Schedule optimized (genetic): 0 tasks scheduled, 3 failed"
