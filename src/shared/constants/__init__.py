"""Shared constants package."""

from datetime import datetime

from shared.constants.file_management import (
    BACKUP_FILE_SUFFIX,
    CONFIG_FILE_NAME,
    NOTE_FILE_EXTENSION,
    NOTES_DIR_NAME,
    TASKS_FILE_NAME,
)
from shared.constants.time import (
    DAYS_PER_WEEK,
    MAX_HOURS_PER_DAY_LIMIT,
    MIN_FILE_SIZE_FOR_CONTENT,
    MIN_HOURS_PER_DAY_EXCLUSIVE,
    SECONDS_PER_HOUR,
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
    "BACKUP_FILE_SUFFIX",
    "CONFIG_FILE_NAME",
    "DAYS_PER_WEEK",
    "DEFAULT_SCHEDULE_DAYS",
    "MAX_HOURS_PER_DAY_LIMIT",
    "MIN_FILE_SIZE_FOR_CONTENT",
    "MIN_HOURS_PER_DAY_EXCLUSIVE",
    "NOTES_DIR_NAME",
    "NOTE_FILE_EXTENSION",
    "SATURDAY",
    "SECONDS_PER_HOUR",
    "SORT_SENTINEL_FUTURE",
    "SORT_SENTINEL_PAST",
    "SUNDAY",
    "TASKS_FILE_NAME",
    "WEEKDAY_THRESHOLD",
    "WORKLOAD_COMFORTABLE_HOURS",
    "WORKLOAD_MODERATE_HOURS",
]
