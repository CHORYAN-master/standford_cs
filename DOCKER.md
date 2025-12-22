# Docker Deployment Guide

## Quick Start

```bash
# Build and run
docker-compose up -d

# Access at http://localhost:8501
```

## Manual Build

```bash
# Build image
docker build -t mcp-ai-agent .

# Run container
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/app/logs \
  --name mcp-server \
  mcp-ai-agent
```

## Configuration

Edit `docker-compose.yml` environment variables or create `.env` file.

## Week 8 Preview

Full deployment guide coming next week!
