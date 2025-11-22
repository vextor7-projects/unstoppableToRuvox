# -----------------------------------------------------------------------------
# STAGE 1: Build - Install dependencies using Poetry
# -----------------------------------------------------------------------------
# Use the official Python 3.11 slim image for a smaller footprint
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true

# Install system dependencies required for build and runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libpq-dev \
        # Clean up
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy only the files needed for dependency installation
COPY poetry.lock pyproject.toml ./

# Install project dependencies
# --no-dev: Exclude development dependencies
# --no-root: Don't install the project package itself yet
RUN poetry install --no-dev --no-root --no-interaction --no-ansi

# -----------------------------------------------------------------------------
# STAGE 2: Runtime - Create the final production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

# Set the working directory
WORKDIR /app

# Set a non-root user for security
ENV APP_USER=appuser
RUN groupadd -r $APP_USER && useradd -r -g $APP_USER $APP_USER

# Install runtime-only system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        # Clean up
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY ./app ./app
COPY ./alembic.ini ./
COPY ./alembic ./alembic

# Set the PATH to use the virtual environment's binaries
ENV PATH="/app/.venv/bin:$PATH"

# Change ownership of the app directory to the non-root user
RUN chown -R $APP_USER:$APP_USER /app

# Switch to the non-root user
USER $APP_USER

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application
# We run alembic upgrade head first to apply migrations
# Then start uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
