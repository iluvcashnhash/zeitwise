# Stage 1: Base image with Python 3.10-slim
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the dependency files first to leverage Docker cache
COPY services/backend/pyproject.toml services/backend/poetry.lock* ./

# Stage 2: Install dependencies
FROM base as builder

# Copy only the dependency files first to leverage Docker cache
COPY services/backend/pyproject.toml services/backend/poetry.lock* ./

# Install build dependencies
RUN pip install --upgrade pip && \
    pip install build setuptools wheel

# Build and install the package in development mode
RUN python -m build --wheel --no-isolation

# Stage 3: Runtime image
FROM base as runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN addgroup --system appuser && \
    adduser --system --no-create-home --ingroup appuser appuser

# Copy the built wheel from builder
COPY --from=builder /app/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl

# Copy application code
COPY services/backend/ /app/

# Set ownership and permissions
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
