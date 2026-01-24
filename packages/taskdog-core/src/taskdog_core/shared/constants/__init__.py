"""Shared constants package."""

from datetime import datetime

from taskdog_core.domain.constants import (
    MAX_TAG_LENGTH,
    MAX_TAGS_PER_TASK,
    MAX_TASK_NAME_LENGTH,
    MIN_PRIORITY_EXCLUSIVE,
)
from taskdog_core.shared.constants.config_defaults import (
    DEFAULT_END_HOUR,
    DEFAULT_START_HOUR,
    MAX_ESTIMATED_DURATION_HOURS,
)
from taskdog_core.shared.constants.file_management import (
    CONFIG_FILE_NAME,
    NOTE_FILE_EXTENSION,
    NOTES_DIR_NAME,
)
from taskdog_core.shared.constants.formats import DATETIME_FORMAT
from taskdog_core.shared.constants.status_verbs import StatusVerbs
from taskdog_core.shared.constants.time import (
    DAYS_PER_WEEK,
    MAX_HOURS_PER_DAY_LIMIT,
    MIN_HOURS_PER_DAY_EXCLUSIVE,
)

# === Date and Time: Weekday Detection ===
# Re-exported from old shared/constants.py for backward compatibility
WEEKDAY_THRESHOLD = 5  # Friday is last weekday (Mon=0, Tue=1, ..., Fri=4)
SATURDAY = 5  # Saturday weekday number
SUNDAY = 6  # Sunday weekday number

# === Scheduling: Default Schedule Period ===
DEFAULT_SCHEDULE_DAYS = 13  # Calendar days for ~2 weeks (10 weekdays)

# === Sorting: Sentinel Values ===
SORT_SENTINEL_FUTURE = datetime(9999, 12, 31, 23, 59, 59)
SORT_SENTINEL_PAST = datetime(1, 1, 1, 0, 0, 0)

# === Workload: Daily Hour Thresholds ===
WORKLOAD_COMFORTABLE_HOURS = 6.0  # Green zone: comfortable daily load
WORKLOAD_MODERATE_HOURS = 8.0  # Yellow zone: moderate daily load

__all__ = [
    "CONFIG_FILE_NAME",
    "DATETIME_FORMAT",
    "DAYS_PER_WEEK",
    "DEFAULT_END_HOUR",
    "DEFAULT_SCHEDULE_DAYS",
    "DEFAULT_START_HOUR",
    "MAX_ESTIMATED_DURATION_HOURS",
    "MAX_HOURS_PER_DAY_LIMIT",
    "MAX_TAGS_PER_TASK",
    "MAX_TAG_LENGTH",
    "MAX_TASK_NAME_LENGTH",
    "MIN_HOURS_PER_DAY_EXCLUSIVE",
    "MIN_PRIORITY_EXCLUSIVE",
    "NOTES_DIR_NAME",
    "NOTE_FILE_EXTENSION",
    "SATURDAY",
    "SORT_SENTINEL_FUTURE",
    "SORT_SENTINEL_PAST",
    "SUNDAY",
    "WEEKDAY_THRESHOLD",
    "WORKLOAD_COMFORTABLE_HOURS",
    "WORKLOAD_MODERATE_HOURS",
    "StatusVerbs",
]
