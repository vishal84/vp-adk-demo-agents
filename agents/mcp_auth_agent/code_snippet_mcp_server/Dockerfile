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

# Set PORT environment variable (Cloud Run will override this)
ENV PORT=8080

# Command to run the FastMCP application
CMD exec uv run python main.py
