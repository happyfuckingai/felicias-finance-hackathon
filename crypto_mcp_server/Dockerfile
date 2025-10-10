FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY crypto/config/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for MCP server
RUN pip install --no-cache-dir fastapi uvicorn sse-starlette mcp

# Copy application code
COPY crypto/ /app/crypto/
COPY crypto_mcp_server/ /app/crypto_mcp_server/
COPY adk_agents/ /app/adk_agents/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["python3", "crypto_mcp_server/crypto_mcp_server.py"]