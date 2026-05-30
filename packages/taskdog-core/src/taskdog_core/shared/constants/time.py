"""Time and duration-related constants.

Note: The physical constant SECONDS_PER_HOUR has been moved to
domain.constants to comply with Clean Architecture principles.
"""

# Calendar
DAYS_PER_WEEK = 7

# Validation Limits
MAX_HOURS_PER_DAY_LIMIT = 24.0
MIN_HOURS_PER_DAY_EXCLUSIVE = 0  # Minimum hours per day (exclusive, must be > 0)
