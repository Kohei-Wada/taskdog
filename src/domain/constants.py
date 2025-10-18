"""Domain-wide constants.

DEPRECATED: DEFAULT_START_HOUR and DEFAULT_END_HOUR are deprecated.
Use config.time.default_start_hour and config.time.default_end_hour instead.
These constants will be removed in a future version.
"""

# Datetime format used throughout the application
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# DEPRECATED: Use config.time.default_start_hour instead
# This constant is kept for backward compatibility and will be removed in v2.0
DEFAULT_START_HOUR = 9  # Default hour for task start times (business day start)

# DEPRECATED: Use config.time.default_end_hour instead
# This constant is kept for backward compatibility and will be removed in v2.0
DEFAULT_END_HOUR = 18  # Default hour for task end times and deadlines (business day end)
