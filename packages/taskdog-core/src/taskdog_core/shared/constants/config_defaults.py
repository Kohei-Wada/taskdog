"""Default configuration values for taskdog."""

# === Optimization Defaults ===
DEFAULT_MAX_HOURS_PER_DAY = 6.0
DEFAULT_ALGORITHM = "greedy"

# === Task Defaults ===
DEFAULT_PRIORITY = 5

# === Validation Limits ===
MIN_PRIORITY_EXCLUSIVE = 0  # Priority must be > 0
MAX_ESTIMATED_DURATION_HOURS = 999  # Maximum estimated duration in hours

# === Time Defaults ===
DEFAULT_START_HOUR = 9  # Business day start hour
DEFAULT_END_HOUR = 18  # Business day end hour (used for deadlines)

# === API Server Defaults ===
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
