# MCP AI Agent - Production Docker Image
# Multi-stage build for optimized size and security

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Metadata
LABEL maintainer="MCP AI Agent Team" \
      description="Security-hardened MCP server with Streamlit UI" \
      version="2.0.0" \
      org.opencontainers.image.source="https://github.com/CHORYAN-master/standford_cs"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r mcpuser -g 1000 && \
    useradd -r -u 1000 -g mcpuser -m -s /bin/bash mcpuser && \
    mkdir -p /app /data /app/logs && \
    chown -R mcpuser:mcpuser /app /data

# Copy virtual environment from builder
COPY --from=builder --chown=mcpuser:mcpuser /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=mcpuser:mcpuser config.py .
COPY --chown=mcpuser:mcpuser security.py .
COPY --chown=mcpuser:mcpuser utils.py .
COPY --chown=mcpuser:mcpuser server.py .
COPY --chown=mcpuser:mcpuser app.py .
COPY --chown=mcpuser:mcpuser .env.example .

# Create .env from example if not provided
RUN if [ ! -f .env ]; then cp .env.example .env; fi && \
    chmod 644 .env

# Switch to non-root user
USER mcpuser

# Expose ports
# 8501: Streamlit UI
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=40s \
            --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Volume for persistent data
VOLUME ["/data", "/app/logs"]

# Default command: Streamlit UI
CMD ["streamlit", "run", "app.py", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501", \
     "--server.headless", "true", \
     "--server.runOnSave", "false", \
     "--browser.gatherUsageStats", "false"]
