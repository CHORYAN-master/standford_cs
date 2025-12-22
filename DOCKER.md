# Docker Deployment Guide

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)
```bash
# Start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Access: http://localhost:8501
```

### Option 2: Docker Build & Run
```bash
# Build image
docker build -t mcp-ai-agent:2.0 .

# Run container
docker run -d \
  --name mcp-agent \
  -p 8501:8501 \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  mcp-ai-agent:2.0

# View logs
docker logs -f mcp-agent
```

---

## 🏗️ Architecture

### Multi-Stage Build
1. **Builder Stage**: Compile dependencies
2. **Runtime Stage**: Minimal production image

### Components
- **Streamlit UI**: Port 8501
- **MCP Server**: Embedded
- **Health Check**: `/health` endpoint
- **Logging**: `/app/logs/`
- **Data**: `/data/` volume

---

## 🔐 Security Features

### Container Security
- ✅ Non-root user (mcpuser:1000)
- ✅ Read-only .env file
- ✅ No new privileges
- ✅ Resource limits (2 CPU, 2GB RAM)
- ✅ Multi-stage build (minimal attack surface)

### Network Isolation
- Private network: `172.28.0.0/16`
- Only port 8501 exposed

---

## 📊 Health Monitoring

### Health Check Script
```bash
# Manual health check
docker exec mcp-agent python3 healthcheck.py

# View health status
docker inspect --format='{{.State.Health.Status}}' mcp-agent
```

### Health Check Verifies:
1. Environment variables
2. Required files
3. Python modules
4. Disk space
5. Log file access

### Status Codes
- `healthy`: All checks passed
- `unhealthy`: One or more checks failed
- `starting`: Initial startup period

---

## 🔧 Configuration

### Environment Variables

Create `.env` file or use `.env.docker`:

```bash
# Paths
BASE_DIR=/data
PROJECT_DIR=/app

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/mcp_server.log

# Security
MAX_FILE_SIZE_MB=10
MAX_CONTENT_SIZE_MB=5
RATE_LIMIT_CALLS_PER_MINUTE=100

# Timeouts
GIT_OPERATION_TIMEOUT=10
COMMAND_EXECUTION_TIMEOUT=30

# Port
STREAMLIT_PORT=8501
```

### Volume Mounts

1. **Data**: `./data:/data`
   - User files and data
   
2. **Logs**: `./logs:/app/logs`
   - Application logs
   
3. **Config**: `./.env:/app/.env:ro`
   - Environment configuration (read-only)

---

## 📋 Common Commands

### Container Management
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Shell access
docker-compose exec mcp-agent bash

# View health
docker-compose ps
```

### Debugging
```bash
# Check health
docker exec mcp-agent python3 healthcheck.py

# View environment
docker exec mcp-agent env

# Check files
docker exec mcp-agent ls -la /app

# Test security audit
docker exec mcp-agent python3 security_audit.py
```

### Cleanup
```bash
# Stop and remove
docker-compose down -v

# Remove image
docker rmi mcp-ai-agent:2.0

# Clean all
docker system prune -a
```

---

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Common issues:
# 1. Port 8501 already in use
# 2. Missing .env file
# 3. Permission issues
```

**Solutions:**
```bash
# Change port
STREAMLIT_PORT=8502 docker-compose up -d

# Create .env
cp .env.docker .env

# Fix permissions
sudo chown -R 1000:1000 data/ logs/
```

### Health Check Failing
```bash
# Run manual check
docker exec mcp-agent python3 healthcheck.py

# View output
docker inspect mcp-agent | jq '.[0].State.Health'
```

### Can't Access UI
```bash
# Check container status
docker ps

# Check port mapping
docker port mcp-agent

# Check firewall
sudo ufw status

# Test locally
curl http://localhost:8501
```

---

## 📈 Production Deployment

### 1. Build Production Image
```bash
docker build -t mcp-ai-agent:2.0-prod .
```

### 2. Push to Registry (Optional)
```bash
docker tag mcp-ai-agent:2.0-prod registry.example.com/mcp-agent:2.0
docker push registry.example.com/mcp-agent:2.0
```

### 3. Deploy with Compose
```bash
# Production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Monitor
```bash
# View stats
docker stats mcp-agent

# View health
watch -n 5 'docker inspect --format="{{.State.Health.Status}}" mcp-agent'
```

---

## 🔒 Security Best Practices

1. **Don't Commit Secrets**
   ```bash
   # Add to .gitignore
   .env
   .env.docker
   ```

2. **Use Read-Only Mounts**
   ```yaml
   volumes:
     - ./.env:/app/.env:ro  # Read-only
   ```

3. **Limit Resources**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 2G
   ```

4. **Regular Updates**
   ```bash
   # Rebuild with latest security patches
   docker-compose build --no-cache
   docker-compose up -d
   ```

---

## 📊 Monitoring Checklist

- [ ] Container running: `docker ps`
- [ ] Health status: `healthy`
- [ ] UI accessible: http://localhost:8501
- [ ] Logs clean: `docker-compose logs`
- [ ] Resource usage: `docker stats`
- [ ] Security audit: 90+ score

---

## 🎯 Next Steps

Week 8 will cover:
- [ ] CI/CD pipeline
- [ ] Kubernetes deployment
- [ ] Load balancing
- [ ] Monitoring dashboards
- [ ] Auto-scaling

---

**Version**: 2.0  
**Updated**: 2024-12-22  
**Status**: Production Ready
