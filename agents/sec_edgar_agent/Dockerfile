# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy requirements file
COPY sec_edgar_mcp/requirements.txt .

# Install Python dependencies
RUN uv pip install --system -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV SEC_EDGAR_USER_AGENT="SEC EDGAR MCP Cloud Run server@gcp.example.com"

# Expose port
EXPOSE 8080

# Run the server with HTTP transport
CMD ["python", "-m", "sec_edgar_mcp.server", "--transport", "http", "--host", "0.0.0.0", "--port", "8080"]