"""Default configuration values for taskdog."""

from datetime import time

# === Validation Limits ===
MAX_ESTIMATED_DURATION_HOURS = 999  # Maximum estimated duration in hours

# === Time Defaults ===
DEFAULT_START_TIME = time(9, 0)  # Business day start time (default: 09:00)
DEFAULT_END_TIME = time(18, 0)  # Business day end time (default: 18:00)

# === Backward Compatibility Aliases (deprecated) ===
# These integer aliases are deprecated. Use DEFAULT_START_TIME/DEFAULT_END_TIME instead.
DEFAULT_START_HOUR = DEFAULT_START_TIME.hour  # Deprecated: use DEFAULT_START_TIME
DEFAULT_END_HOUR = DEFAULT_END_TIME.hour  # Deprecated: use DEFAULT_END_TIME
