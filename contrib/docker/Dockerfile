# Taskdog Server Dockerfile
# https://github.com/Kohei-Wada/taskdog
#
# Build:
#   docker build -f contrib/docker/Dockerfile -t taskdog-server .
#
# Run:
#   docker run -d -p 8000:8000 -v taskdog-data:/data taskdog-server

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy workspace configuration and packages
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/

# Install taskdog-server and taskdog-ui packages (includes taskdog-core as dependency)
# --no-editable ensures package data (tcss styles) are properly installed
RUN uv sync --locked --no-dev --no-editable --package taskdog-server --package taskdog-ui

# Create non-root user and data directory
RUN useradd -m -u 1000 taskdog \
    && mkdir -p /data \
    && chown -R taskdog:taskdog /data /app

USER taskdog

# Expose API port
EXPOSE 8000

# Data persistence volume
VOLUME /data

# Health check using Python (no curl needed)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Environment variables
# Add venv to PATH so taskdog CLI is directly accessible
ENV PATH="/app/.venv/bin:$PATH"
# SQLAlchemy requires sqlite:/// prefix for database URL
ENV TASKDOG_STORAGE_DATABASE_URL=sqlite:////data/tasks.db

# Start taskdog-server
# Note: --workers 1 is required for WebSocket real-time sync
ENTRYPOINT ["uv", "run", "taskdog-server", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
