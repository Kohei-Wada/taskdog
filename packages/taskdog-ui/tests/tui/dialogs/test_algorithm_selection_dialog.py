"""Tests for AlgorithmSelectionDialog."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from taskdog.tui.dialogs.algorithm_selection_dialog import AlgorithmSelectionDialog


def create_algorithm_metadata() -> list[tuple[str, str, str]]:
    """Create sample algorithm metadata for testing."""
    return [
        ("greedy", "Greedy", "Simple greedy scheduling"),
        ("balanced", "Balanced", "Balanced workload distribution"),
        ("genetic", "Genetic", "Genetic algorithm optimization"),
    ]


class TestAlgorithmSelectionDialogInit:
    """Test cases for AlgorithmSelectionDialog initialization."""

    def test_stores_algorithm_metadata(self) -> None:
        """Test that algorithm metadata is stored correctly."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)

        assert dialog.algorithms == metadata
        assert len(dialog.algorithms) == 3

    def test_stores_empty_metadata(self) -> None:
        """Test that empty metadata is stored correctly."""
        dialog = AlgorithmSelectionDialog([])

        assert dialog.algorithms == []

    def test_stores_selected_task_count(self) -> None:
        """Test that selected_task_count is stored correctly."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata, selected_task_count=5)

        assert dialog.selected_task_count == 5

    def test_default_selected_task_count_is_zero(self) -> None:
        """Test that default selected_task_count is zero."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)

        assert dialog.selected_task_count == 0


class TestAlgorithmSelectionDialogGetDefaultStartDate:
    """Test cases for _get_default_start_date method."""

    @patch("taskdog.tui.dialogs.algorithm_selection_dialog.datetime")
    def test_returns_today_on_weekday(self, mock_datetime: MagicMock) -> None:
        """Test that today is returned when current day is a weekday."""
        # Monday = 0
        mock_now = datetime(2025, 1, 6, 10, 0)  # Monday
        mock_datetime.now.return_value = mock_now

        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)

        result = dialog._get_default_start_date()

        assert result == "2025-01-06"

    @patch("taskdog.tui.dialogs.algorithm_selection_dialog.datetime")
    def test_returns_today_on_friday(self, mock_datetime: MagicMock) -> None:
        """Test that today is returned on Friday."""
        mock_now = datetime(2025, 1, 10, 10, 0)  # Friday
        mock_datetime.now.return_value = mock_now

        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)

        result = dialog._get_default_start_date()

        assert result == "2025-01-10"

    @patch("taskdog.tui.dialogs.algorithm_selection_dialog.datetime")
    def test_returns_next_monday_on_saturday(self, mock_datetime: MagicMock) -> None:
        """Test that next Monday is returned on Saturday."""
        mock_now = datetime(2025, 1, 11, 10, 0)  # Saturday
        mock_datetime.now.return_value = mock_now

        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)

        result = dialog._get_default_start_date()

        # Next Monday is January 13
        assert result == "2025-01-13"

    @patch("taskdog.tui.dialogs.algorithm_selection_dialog.datetime")
    def test_returns_next_monday_on_sunday(self, mock_datetime: MagicMock) -> None:
        """Test that next Monday is returned on Sunday."""
        mock_now = datetime(2025, 1, 12, 10, 0)  # Sunday
        mock_datetime.now.return_value = mock_now

        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)

        result = dialog._get_default_start_date()

        # Next Monday is January 13
        assert result == "2025-01-13"


class TestAlgorithmSelectionDialogActions:
    """Test cases for action methods."""

    def test_action_focus_next_calls_focus_next(self) -> None:
        """Test that action_focus_next calls focus_next."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog.focus_next = MagicMock()

        dialog.action_focus_next()

        dialog.focus_next.assert_called_once()

    def test_action_focus_previous_calls_focus_previous(self) -> None:
        """Test that action_focus_previous calls focus_previous."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog.focus_previous = MagicMock()

        dialog.action_focus_previous()

        dialog.focus_previous.assert_called_once()


class TestAlgorithmSelectionDialogSubmit:
    """Test cases for action_submit method."""

    def test_submit_clears_previous_error(self) -> None:
        """Test that submit clears previous validation error."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog._clear_validation_error = MagicMock()

        # Mock the query_one to return mocked widgets
        mock_select = MagicMock()
        mock_select.value = "greedy"
        mock_max_hours = MagicMock()
        mock_max_hours.value = "8"
        mock_max_hours.is_valid = True
        mock_start_date = MagicMock()
        mock_start_date.value = "2025-01-06"
        mock_start_date.is_valid = True
        mock_checkbox = MagicMock()
        mock_checkbox.value = False

        def mock_query_one(selector: str, widget_type: type) -> MagicMock:
            if "algorithm" in selector:
                return mock_select
            elif "max-hours" in selector:
                return mock_max_hours
            elif "start-date" in selector:
                return mock_start_date
            elif "force" in selector:
                return mock_checkbox
            return MagicMock()

        dialog.query_one = mock_query_one
        dialog.dismiss = MagicMock()

        dialog.action_submit()

        dialog._clear_validation_error.assert_called_once()

    def test_submit_shows_error_when_algorithm_blank(self) -> None:
        """Test that error is shown when algorithm is blank."""
        from textual.widgets import Select

        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog._clear_validation_error = MagicMock()
        dialog._show_validation_error = MagicMock()

        mock_select = MagicMock()
        mock_select.value = Select.BLANK

        def mock_query_one(selector: str, widget_type: type) -> MagicMock:
            if "algorithm" in selector:
                return mock_select
            return MagicMock()

        dialog.query_one = mock_query_one
        dialog.dismiss = MagicMock()

        dialog.action_submit()

        dialog._show_validation_error.assert_called_once()
        assert "algorithm" in dialog._show_validation_error.call_args[0][0].lower()
        dialog.dismiss.assert_not_called()

    def test_submit_shows_error_when_max_hours_empty(self) -> None:
        """Test that error is shown when max hours is empty."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog._clear_validation_error = MagicMock()
        dialog._show_validation_error = MagicMock()

        mock_select = MagicMock()
        mock_select.value = "greedy"
        mock_max_hours = MagicMock()
        mock_max_hours.value = ""  # Empty
        mock_max_hours.is_valid = True
        mock_start_date = MagicMock()
        mock_start_date.value = "2025-01-06"
        mock_checkbox = MagicMock()

        def mock_query_one(selector: str, widget_type: type) -> MagicMock:
            if "algorithm" in selector:
                return mock_select
            elif "max-hours" in selector:
                return mock_max_hours
            elif "start-date" in selector:
                return mock_start_date
            elif "force" in selector:
                return mock_checkbox
            return MagicMock()

        dialog.query_one = mock_query_one
        dialog.dismiss = MagicMock()

        dialog.action_submit()

        dialog._show_validation_error.assert_called_once()
        assert "max hours" in dialog._show_validation_error.call_args[0][0].lower()
        dialog.dismiss.assert_not_called()

    def test_submit_shows_error_when_start_date_empty(self) -> None:
        """Test that error is shown when start date is empty."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog._clear_validation_error = MagicMock()
        dialog._show_validation_error = MagicMock()

        mock_select = MagicMock()
        mock_select.value = "greedy"
        mock_max_hours = MagicMock()
        mock_max_hours.value = "6.0"  # Valid max hours
        mock_max_hours.is_valid = True
        mock_start_date = MagicMock()
        mock_start_date.value = "   "  # Empty after strip
        mock_checkbox = MagicMock()

        def mock_query_one(selector: str, widget_type: type) -> MagicMock:
            if "algorithm" in selector:
                return mock_select
            elif "max-hours" in selector:
                return mock_max_hours
            elif "start-date" in selector:
                return mock_start_date
            elif "force" in selector:
                return mock_checkbox
            return MagicMock()

        dialog.query_one = mock_query_one
        dialog.dismiss = MagicMock()

        dialog.action_submit()

        dialog._show_validation_error.assert_called_once()
        assert "start date" in dialog._show_validation_error.call_args[0][0].lower()
        dialog.dismiss.assert_not_called()

    def test_submit_focuses_max_hours_when_invalid(self) -> None:
        """Test that max hours input is focused when invalid."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog._clear_validation_error = MagicMock()

        mock_select = MagicMock()
        mock_select.value = "greedy"
        mock_max_hours = MagicMock()
        mock_max_hours.value = "invalid"
        mock_max_hours.is_valid = False
        mock_max_hours.focus = MagicMock()
        mock_start_date = MagicMock()
        mock_start_date.value = "2025-01-06"
        mock_checkbox = MagicMock()

        def mock_query_one(selector: str, widget_type: type) -> MagicMock:
            if "algorithm" in selector:
                return mock_select
            elif "max-hours" in selector:
                return mock_max_hours
            elif "start-date" in selector:
                return mock_start_date
            elif "force" in selector:
                return mock_checkbox
            return MagicMock()

        dialog.query_one = mock_query_one
        dialog.dismiss = MagicMock()

        dialog.action_submit()

        mock_max_hours.focus.assert_called_once()
        dialog.dismiss.assert_not_called()

    def test_submit_focuses_start_date_when_invalid(self) -> None:
        """Test that start date input is focused when invalid."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog._clear_validation_error = MagicMock()

        mock_select = MagicMock()
        mock_select.value = "greedy"
        mock_max_hours = MagicMock()
        mock_max_hours.value = "8"
        mock_max_hours.is_valid = True
        mock_start_date = MagicMock()
        mock_start_date.value = "invalid-date"
        mock_start_date.is_valid = False
        mock_start_date.focus = MagicMock()
        mock_checkbox = MagicMock()

        def mock_query_one(selector: str, widget_type: type) -> MagicMock:
            if "algorithm" in selector:
                return mock_select
            elif "max-hours" in selector:
                return mock_max_hours
            elif "start-date" in selector:
                return mock_start_date
            elif "force" in selector:
                return mock_checkbox
            return MagicMock()

        dialog.query_one = mock_query_one
        dialog.dismiss = MagicMock()

        dialog.action_submit()

        mock_start_date.focus.assert_called_once()
        dialog.dismiss.assert_not_called()

    def test_submit_dismisses_with_valid_data(self) -> None:
        """Test that dialog dismisses with valid data."""
        metadata = create_algorithm_metadata()
        dialog = AlgorithmSelectionDialog(metadata)
        dialog._clear_validation_error = MagicMock()

        mock_select = MagicMock()
        mock_select.value = "balanced"
        mock_max_hours = MagicMock()
        mock_max_hours.value = "6.5"
        mock_max_hours.is_valid = True
        mock_start_date = MagicMock()
        mock_start_date.value = "today"
        mock_start_date.is_valid = True
        mock_checkbox = MagicMock()
        mock_checkbox.value = True

        def mock_query_one(selector: str, widget_type: type) -> MagicMock:
            if "algorithm" in selector:
                return mock_select
            elif "max-hours" in selector:
                return mock_max_hours
            elif "start-date" in selector:
                return mock_start_date
            elif "force" in selector:
                return mock_checkbox
            return MagicMock()

        dialog.query_one = mock_query_one
        dialog.dismiss = MagicMock()

        dialog.action_submit()

        dialog.dismiss.assert_called_once()
        result = dialog.dismiss.call_args[0][0]
        assert result[0] == "balanced"  # algorithm
        assert result[1] == 6.5  # max_hours
        assert isinstance(result[2], datetime)  # start_date
        assert result[3] is True  # force_override
