"""Application-wide constants and magic number definitions.

This module contains named constants to replace magic numbers throughout the codebase.
Using named constants improves readability, maintainability, and documentation.
"""

from datetime import datetime

# === Date and Time: Weekday Detection ===
WEEKDAY_THRESHOLD = 5  # Friday is last weekday (Mon=0, Tue=1, ..., Fri=4)
SATURDAY = 5  # Saturday weekday number
SUNDAY = 6  # Sunday weekday number

# === Scheduling: Default Schedule Period ===
DEFAULT_SCHEDULE_DAYS = 13  # Calendar days for ~2 weeks (10 weekdays)
# This gives approximately 2 weeks of weekdays when no deadline is set

# === Sorting: Sentinel Values ===
SORT_SENTINEL_FUTURE = datetime(9999, 12, 31, 23, 59, 59)
# Represents "infinity" for sorting - used when date is None to sort it last
SORT_SENTINEL_PAST = datetime(1, 1, 1, 0, 0, 0)
# Represents negative infinity - could be used for sorting items first

# === Workload: Daily Hour Thresholds ===
WORKLOAD_COMFORTABLE_HOURS = 6.0  # Green zone: comfortable daily load
WORKLOAD_MODERATE_HOURS = 8.0  # Yellow zone: moderate daily load
# Red zone: > 8.0 hours (overload warning)
