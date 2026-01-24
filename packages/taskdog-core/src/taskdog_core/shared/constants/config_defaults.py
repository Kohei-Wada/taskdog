"""Default configuration values for taskdog."""

from datetime import time

# === Validation Limits ===
MAX_ESTIMATED_DURATION_HOURS = 999  # Maximum estimated duration in hours

# === UI Input Completion Defaults ===
# Used when user enters date-only input (e.g., "2025-01-24" -> "2025-01-24 18:30:00")
DEFAULT_DEADLINE_TIME = time(18, 30)  # Default time for deadline input
DEFAULT_PLANNED_START_TIME = time(9, 30)  # Default time for planned_start input
DEFAULT_PLANNED_END_TIME = time(18, 30)  # Default time for planned_end input

# === Work Hours (for optimization) ===
# Defines the available working hours per day for schedule optimization
WORK_HOURS_START = time(9, 30)  # Work day start time
WORK_HOURS_END = time(18, 30)  # Work day end time
