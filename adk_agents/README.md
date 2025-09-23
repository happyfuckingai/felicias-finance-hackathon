# Google Cloud ADK Integration for Felicia Finance

This module provides Google Cloud Platform (GCP) integration for the Felicia Finance multi-agent orchestration system, enabling scalable agent deployment and workflow orchestration through Google Cloud Functions and related services.

## Features

- **Cloud-Native Agent Deployment**: Deploy agents as Google Cloud Functions for automatic scaling and high availability
- **Multi-Agent Workflow Orchestration**: Define and execute complex financial workflows across distributed agents
- **Secure Agent Communication**: Enterprise-grade security through Google Cloud IAM and service accounts
- **Identity Management**: Secure agent identity and authentication via GCP identity services
- **Monitoring & Observability**: Built-in monitoring, logging, and tracing through Google Cloud Operations Suite
- **Graceful Degradation**: Offline mode support when GCP services are unavailable
- **Lazy Initialization**: On-demand service initialization for optimal resource usage

```

## Installation

1. **Set up virtual environment**:
```bash
cd adk_integration
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure Google Cloud**:
```bash
chmod +x setup_adk_environment.sh
./setup_adk_environment.sh
```

3. **Set up configuration**:
Edit `config/adk_config.yaml` with your GCP project details.

## Configuration

The ADK integration is configured through `config/adk_config.yaml`:

```yaml
gcp:
  project_id: "your-gcp-project"
  region: "us-central1"
  service_account: "felicia-adk-sa@your-project.iam.gserviceaccount.com"

adk:
  agent_name: "felicia_orchestrator"
  description: "Multi-agent orchestrator for Felicia Finance"

agents:
  banking_agent:
    name: "banking_agent"
    type: "mcp_server"
    endpoint: "http://localhost:8081"
    capabilities:
      - "account_management"
      - "transaction_processing"

workflows:
  - name: "financial_analysis"
    steps:
      - agent: "banking_agent"
        action: "get_balance"
      - agent: "crypto_agent"
        action: "analyze_portfolio"
```

## Usage

### Basic Integration

```python
from adk_integration.adk import ADKIntegration

# Initialize ADK integration with lazy loading
adk = ADKIntegration()

# Initialize (supports offline mode if GCP unavailable)
await adk.initialize()

# Analyze financial query
result = await adk.analyze_financial_query("What's my portfolio performance?")
print(result)

# Get portfolio analysis
portfolio = await adk.get_portfolio_analysis("user123")
print(portfolio)
```

### Agent Wrapper Integration

```python
from adk_integration.agents.adk_agent_wrapper import ADKAgentWrapper

# Wrap existing LiveKit agent
wrapped_agent = ADKAgentWrapper(your_existing_agent)
await wrapped_agent.initialize_adk()

# Execute workflow
result = await wrapped_agent.execute_workflow("financial_analysis", {
    "user_id": "user123",
    "query": "portfolio analysis"
})

# Get financial analysis
analysis = await wrapped_agent.get_financial_analysis("How is my investment performing?")
```

### Direct Banking/Crypto Operations

```python
# Handle banking requests
balance = await adk.handle_banking_request({"query": "get_balance", "account_id": "main"})

# Handle crypto requests
trade_result = await adk.handle_crypto_request({
    "mission": "execute_trade",
    "strategy": {"risk_level": "medium", "amount": 1000}
})

# Get system status
status = await adk.get_system_status()
```

### Direct ADK Service Usage

```python
from adk_integration.services.adk_service import ADKService

# Direct ADK service usage
adk_service = ADKService()
await adk_service.initialize()

# Deploy agent to Google Cloud Functions
agent_config = {
    "name": "custom_agent",
    "description": "Custom financial agent",
    "capabilities": ["analysis", "reporting"]
}
url = await adk_service.deploy_adk_agent(agent_config)

# Invoke deployed agent
result = await adk_service.invoke_agent("custom_agent", {
    "action": "analyze",
    "data": {"portfolio_id": "123"}
})
```

## Workflows

Define complex financial workflows that orchestrate multiple agents:

```python
# Register custom workflow
await adk.register_workflow({
    "name": "comprehensive_analysis",
    "steps": [
        {
            "agent": "banking_agent",
            "action": "get_balance",
            "parameters": {"account_id": "main"}
        },
        {
            "agent": "crypto_agent",
            "action": "analyze_portfolio",
            "parameters": {"include_risk": True}
        },
        {
            "agent": "felicia_orchestrator",
            "action": "generate_insights",
            "parameters": {"consolidate": True}
        }
    ]
})

# Execute workflow
result = await adk.execute_financial_workflow("comprehensive_analysis", {
    "user_id": "user123"
})
```

## Security

- **Authentication**: Uses Google Cloud service accounts and IAM
- **Authorization**: Role-based access control for agent operations
- **Encryption**: All inter-agent communication is encrypted
- **Audit Logging**: All operations are logged for compliance

## Monitoring

Monitor your ADK integration through Google Cloud Console:

- **Cloud Functions**: Monitor agent performance and scaling
- **Cloud Logging**: View detailed operation logs
- **Cloud Monitoring**: Set up alerts and dashboards
- **Cloud Trace**: Distributed tracing for complex workflows

## Testing

Run the test suite:

```bash
cd adk_integration
source venv/bin/activate
python -m pytest tests/
```

Or run basic functionality test:

```bash
python tests/test_adk_integration.py
```

## Deployment

### Development
```bash
# Local development with MCP servers
docker-compose up crypto_mcp_server bankofanthos_mcp_server
python -c "from adk_integration.adk import ADKIntegration; adk = ADKIntegration(); await adk.initialize()"
```

### Production
```bash
# Deploy to Google Cloud
gcloud builds submit --tag gcr.io/YOUR-PROJECT/felicia-adk
gcloud run deploy felicia-adk --image gcr.io/YOUR-PROJECT/felicia-adk --platform managed
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Ensure `gcloud auth login` has been run
   - Verify service account has proper permissions
   - Check project ID in configuration

2. **Deployment Failures**:
   - Verify Cloud Functions API is enabled
   - Check quota limits
   - Review function logs in Cloud Console

3. **Workflow Timeouts**:
   - Increase timeout settings in configuration
   - Optimize agent response times
   - Use async processing for long-running tasks

### Logs

View logs in Google Cloud Console:
```bash
gcloud logging read "resource.type=cloud_function" --limit=10
```

## API Reference

See the docstrings in the source code for detailed API documentation.

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure type hints are included
5. Run tests before submitting PR

## License

Copyright 2025 Felicia Finance. All rights reserved.
