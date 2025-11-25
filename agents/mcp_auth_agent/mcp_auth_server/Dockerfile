# Use an official lightweight Python image.
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY pyproject.toml .

# Install any dependencies
RUN uv sync

# Copy the content of the local src directory to the working directory
COPY src/ .

# Command to run the application
# Gunicorn is a production-ready WSGI server. Cloud Run provides the $PORT environment variable.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
