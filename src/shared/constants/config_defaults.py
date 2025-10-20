"""Default configuration values for taskdog."""

# === Optimization Defaults ===
DEFAULT_MAX_HOURS_PER_DAY = 6.0
DEFAULT_ALGORITHM = "greedy"

# === Task Defaults ===
DEFAULT_PRIORITY = 5

# === Display Defaults ===
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# === Time Defaults ===
DEFAULT_START_HOUR = 9  # Business day start hour
DEFAULT_END_HOUR = 18  # Business day end hour (used for deadlines)
