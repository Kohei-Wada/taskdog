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

# Build wheels for all packages and install into virtual environment
# Using wheels instead of uv sync to include taskdog-ui in the image
RUN set -e && \
    uv build --package taskdog-core --wheel --out-dir /tmp/wheels && \
    uv build --package taskdog-client --wheel --out-dir /tmp/wheels && \
    uv build --package taskdog-server --wheel --out-dir /tmp/wheels && \
    uv build --package taskdog-ui --wheel --out-dir /tmp/wheels && \
    uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python /tmp/wheels/*.whl && \
    rm -rf /tmp/wheels

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

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
# SQLAlchemy requires sqlite:/// prefix for database URL
ENV TASKDOG_STORAGE_DATABASE_URL=sqlite:////data/tasks.db
# Terminal settings for proper CLI/TUI output rendering (Rich/Textual)
ENV TERM=xterm-256color
ENV COLORTERM=truecolor

# Start taskdog-server
# Note: --workers 1 is required for WebSocket real-time sync
ENTRYPOINT ["/app/.venv/bin/taskdog-server", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
