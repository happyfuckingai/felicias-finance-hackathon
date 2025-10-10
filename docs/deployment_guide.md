# Felicia's Finance - Deployment Guide

## Overview
Felicia's Finance is a comprehensive hybrid banking and DeFi platform featuring AI-powered voice agents, real-time visualizations, and multi-agent orchestration.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   LiveKit Agent  │    │   MCP Servers   │
│   (React)       │◄──►│   (Felicia)      │◄──►│   (Banking &    │
│   Port: 3000    │    │   Port: 8080     │    │    Crypto)      │
└─────────────────┘    └─────────────────┘    │   Ports: 8001,   │
                                              │   8000          │
┌─────────────────┐    ┌─────────────────┐    └─────────────────┘
│   A2A Protocol  │    │   ADK Agents     │
│   (Agent-to-    │◄──►│   (Banking,      │
│    Agent Comm)  │    │    Crypto Teams) │
└─────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows (WSL recommended)
- **Python**: 3.8+
- **Node.js**: 18+
- **Docker**: Optional (for MCP servers)
- **Google Cloud Account**: For ADK integration (optional)

### Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for frontend)
cd agent-starter-react
npm install
```

## Component Setup

### 1. Frontend (React + LiveKit)

```bash
# Navigate to frontend directory
cd agent-starter-react

# Install dependencies
npm install

# Start development server
npm run dev
# Server runs on http://localhost:3000
```

**Environment Variables:**
Create `.env.local`:
```bash
NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
NEXT_PUBLIC_LIVEKIT_API_KEY=your-api-key
NEXT_PUBLIC_LIVEKIT_API_SECRET=your-api-secret
```

### 2. LiveKit Agent (Felicia)

```bash
# From project root
python3 agent/agent.py
# Agent connects to LiveKit server
```

**Environment Variables:**
Create `.env`:
```bash
# LiveKit Configuration
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud

# OpenAI (for voice)
OPENAI_API_KEY=your-openai-key

# Mem0 (memory persistence)
MEM0_API_KEY=your-mem0-key

# Google GenAI (optional)
GOOGLE_API_KEY=your-google-key
```

### 3. MCP Servers (Banking & Crypto)

#### Banking MCP Server
```bash
cd bankofanthos_mcp_server
./start_sse.sh
# Server runs on http://localhost:8001/sse
```

#### Crypto MCP Server
```bash
cd crypto_mcp_server
python3 crypto_mcp_server.py --sse
# Server runs on http://localhost:8000/sse
```

### 4. A2A Protocol (Agent Communication)

```bash
# Start A2A communication layer
python3 a2a_client/client.py
# Handles agent-to-agent messaging
```

### 5. ADK Integration (Optional)

```bash
# Google Cloud ADK setup (optional)
# Requires GCP project and credentials
cd adk_integration
python3 setup_adk_environment.sh
```

## Health Monitoring

### Health Check System
```bash
# Run health monitor
python3 health_monitor.py
```

**Health Endpoints:**
- Frontend: `http://localhost:3000`
- Banking MCP: `http://localhost:8001/health`
- Crypto MCP: `http://localhost:8000/health`

## Production Deployment

### 1. Docker Deployment

#### Frontend Container
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

#### Agent Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "agent/agent.py"]
```

### 2. Cloud Deployment Options

#### Option A: Google Cloud Run
```bash
# Deploy frontend
gcloud run deploy felicia-frontend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Deploy agent
gcloud run deploy felicia-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars LIVEKIT_URL=$LIVEKIT_URL
```

#### Option B: AWS ECS
```yaml
# ECS Task Definition
{
  "family": "felicia-finance",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "felicia-frontend:latest",
      "portMappings": [{"containerPort": 3000}]
    },
    {
      "name": "agent",
      "image": "felicia-agent:latest",
      "environment": [
        {"name": "LIVEKIT_URL", "value": "..."}
      ]
    }
  ]
}
```

### 3. Load Balancing
```nginx
# Example Nginx configuration
upstream felicia_frontend {
    server frontend1:3000;
    server frontend2:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://felicia_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Configuration

### Environment Variables Reference

| Variable | Component | Description | Example |
|----------|-----------|-------------|---------|
| `LIVEKIT_URL` | Agent | LiveKit WebSocket URL | `wss://felicia.livekit.cloud` |
| `LIVEKIT_API_KEY` | Agent | LiveKit API key | `API...` |
| `LIVEKIT_API_SECRET` | Agent | LiveKit API secret | `secret...` |
| `OPENAI_API_KEY` | Agent | OpenAI API key | `sk-...` |
| `MEM0_API_KEY` | Agent | Mem0 API key | `mem0-...` |
| `GOOGLE_API_KEY` | ADK | Google GenAI API key | `AIza...` |
| `BANKOFANTHOS_MCP_API_KEY` | MCP | Banking server API key | `bank-...` |
| `CRYPTO_MCP_API_KEY` | MCP | Crypto server API key | `crypto-...` |

### MCP Server Configuration

#### Roo Code Integration
```json
{
  "mcpServers": {
    "bankofanthos-server": {
      "url": "http://localhost:8001/sse",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    },
    "crypto-server": {
      "url": "http://localhost:8000/sse",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

## Monitoring & Maintenance

### Logging
- Agent logs: `logs/agent.log`
- MCP server logs: `logs/mcp_servers.log`
- Health monitor: `logs/health_monitor.log`

### Performance Monitoring
```bash
# Monitor system resources
python3 health_monitor.py --continuous

# Check agent performance
curl http://localhost:8080/health

# Monitor MCP servers
curl http://localhost:8001/health
curl http://localhost:8000/health
```

### Backup & Recovery
```bash
# Backup user data
python3 backup.py --users

# Backup agent memory
python3 backup.py --memory

# Restore from backup
python3 restore.py --from-backup 2025-01-01
```

## Troubleshooting

### Common Issues

#### Agent Won't Connect
```bash
# Check LiveKit credentials
echo $LIVEKIT_API_KEY

# Test LiveKit connection
python3 test_livekit.py

# Check agent logs
tail -f logs/agent.log
```

#### MCP Servers Not Responding
```bash
# Check server processes
ps aux | grep mcp

# Restart MCP servers
cd bankofanthos_mcp_server && ./start_sse.sh
cd crypto_mcp_server && python3 crypto_mcp_server.py --sse

# Check server logs
tail -f bankofanthos_mcp_server/logs/server.log
```

#### Frontend Loading Issues
```bash
# Check frontend logs
cd agent-starter-react && npm run dev 2>&1 | tee logs/frontend.log

# Clear cache
cd agent-starter-react && rm -rf .next && npm run build
```

### Debug Mode
```bash
# Run with debug logging
DEBUG=1 python3 agent/agent.py

# Test individual components
python3 test_a2a_system.py
python3 test_mcp_integration.py
```

## Security Considerations

### API Keys
- Store API keys in environment variables
- Never commit keys to version control
- Rotate keys regularly
- Use least privilege principles

### Network Security
- Use HTTPS in production
- Implement rate limiting
- Enable CORS appropriately
- Monitor for suspicious activity

### Data Protection
- Encrypt sensitive data at rest
- Use secure communication protocols
- Implement proper authentication
- Regular security audits

## Scaling

### Horizontal Scaling
```bash
# Multiple agent instances
docker-compose up --scale agent=3

# Load balancer configuration
# See nginx.conf.example
```

### Performance Optimization
```bash
# Database connection pooling
# Redis for session storage
# CDN for static assets
```

## Support

### Documentation
- API Documentation: `docs/api-reference.md`
- User Guide: `docs/user-guide.md`
- Architecture: `docs/architecture.md`

### Community
- GitHub Issues: Report bugs and request features
- Discord: Community support and discussions
- Documentation: Comprehensive guides and tutorials

---

**Deployment Checklist:**
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Services started in correct order
- [ ] Health checks passing
- [ ] Security measures implemented
- [ ] Monitoring configured
- [ ] Backup strategy in place