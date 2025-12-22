# MCP AI Agent - Docker Image
# Security-hardened Python 3.11 environment

FROM python:3.11-slim

# Metadata
LABEL maintainer="MCP AI Agent Team"
LABEL description="Security-hardened MCP server with Streamlit UI"
LABEL version="2.0.0"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash mcpuser && \
    mkdir -p /app /data && \
    chown -R mcpuser:mcpuser /app /data

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY --chown=mcpuser:mcpuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=mcpuser:mcpuser . .

# Create .env from example if not exists
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Switch to non-root user
USER mcpuser

# Expose ports
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command (can be overridden)
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
