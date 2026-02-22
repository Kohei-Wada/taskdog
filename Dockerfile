# Taskdog Server Dockerfile
# https://github.com/Kohei-Wada/taskdog
#
# Build:
#   docker build -t taskdog-server .
#
# Run:
#   docker run -d -p 8000:8000 -v taskdog-data:/data taskdog-server

# Stage 1: Builder - build wheels using uv
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Copy dependency metadata first (changes infrequently -> better layer caching)
COPY pyproject.toml uv.lock ./
COPY packages/taskdog-core/pyproject.toml packages/taskdog-core/pyproject.toml
COPY packages/taskdog-client/pyproject.toml packages/taskdog-client/pyproject.toml
COPY packages/taskdog-server/pyproject.toml packages/taskdog-server/pyproject.toml
COPY packages/taskdog-ui/pyproject.toml packages/taskdog-ui/pyproject.toml

# Copy source code (changes frequently)
COPY packages/ ./packages/

# Build wheels for all packages
RUN uv build --package taskdog-core --wheel --out-dir /wheels && \
    uv build --package taskdog-client --wheel --out-dir /wheels && \
    uv build --package taskdog-server --wheel --out-dir /wheels && \
    uv build --package taskdog-ui --wheel --out-dir /wheels

# Stage 2: Runtime - minimal image with only what's needed
FROM python:3.13-slim-bookworm

WORKDIR /app

# Install wheels from builder stage
COPY --from=builder /wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels

# Copy demo scripts
COPY scripts/demo_data.py scripts/demo_data.json ./scripts/

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
ENTRYPOINT ["taskdog-server", "--host", "0.0.0.0", "--port", "8000"]
