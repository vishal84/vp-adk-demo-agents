# Use an official lightweight Python image.
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory in the container
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy the content of the local src directory to the working directory
COPY src/ .

# Command to run the application
# Gunicorn is a production-ready WSGI server. Cloud Run provides the $PORT environment variable.
CMD exec uv run gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
