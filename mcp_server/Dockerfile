FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Set Python path to include parent directory
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create a non-root user to run the application
RUN useradd -m appuser
RUN mkdir -p /app/db && chown -R appuser:appuser /app/db
USER appuser

# Expose port for MCP server
EXPOSE 8000

# Start the MCP Teams server
CMD ["python", "mcp_server/server.py"]