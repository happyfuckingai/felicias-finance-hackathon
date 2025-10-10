# Google Cloud ADK Integration for Felicia Finance

This module provides Google Cloud Platform (GCP) integration for the Felicia Finance multi-agent orchestration system, enabling scalable agent deployment and workflow orchestration through Google Cloud Functions and related services. It includes a consolidated A2A (Agent-to-Agent) protocol implementation for secure inter-agent communication.

## Features

- **Cloud-Native Agent Deployment**: Deploy agents as Google Cloud Functions for automatic scaling and high availability
- **Multi-Agent Workflow Orchestration**: Define and execute complex financial workflows across distributed agents
- **A2A Protocol Integration**: Secure agent-to-agent communication with encrypted messaging and orchestration
- **Domain-Specific Agents**: Specialized banking and crypto agents with shared protocol components
- **Secure Agent Communication**: Enterprise-grade security through Google Cloud IAM and service accounts
- **Identity Management**: Secure agent identity and authentication via GCP identity services
- **Monitoring & Observability**: Built-in monitoring, logging, and tracing through Google Cloud Operations Suite
- **Graceful Degradation**: Offline mode support when GCP services are unavailable
- **Lazy Initialization**: On-demand service initialization for optimal resource usage

<<<<<<< Updated upstream
=======
## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  LiveKit Agent  │────│ ADK Integration │────│ GCP ADK Agents  │
│   (Orchestrator) │    │    Wrapper      │    │ (Cloud Functions)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                     ┌─────────────────┐
                     │ MCP Servers     │
                     │ Banking & Crypto│
                     └─────────────────┘
```

### A2A Protocol Structure

```
adk_agents/
├── 📁 a2a/                          # Konsoliderad A2A-struktur
│   ├── banking_a2a_integration/     # Bank-specifika agenter
│   │   └── banking_a2a_agent.py
│   ├── crypto_a2a_integration/      # Crypto-specifika agenter
│   │   └── crypto_a2a_agent.py
│   ├── core/                        # A2A-protokollkärna
│   │   ├── agent.py                 # A2AAgent, OrchestratorAgent
│   │   ├── auth.py                  # AuthenticationManager
│   │   ├── messaging.py             # Message, EncryptedMessage
│   │   ├── transport.py             # TransportLayer, TransportConfig
│   │   └── ...
│   └── shared/                      # Delade A2A komponenter
│       ├── protocol_interfaces.py
│       ├── error_handling.py
│       └── constants.py
├── 📁 adk/                          # Ren ADK integration
└── 📁 config/                       # Delad konfiguration
>>>>>>> Stashed changes
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

a2a_protocol:
  transport:
    protocol: "http2"
    host: "localhost"
    port: 8444
    ssl_enabled: false
  timeouts:
    connection_timeout: 30
    message_timeout: 60
    heartbeat_interval: 30

agents:
  banking_agent:
    name: "banking_agent"
    type: "a2a_agent"
    endpoint: "http://localhost:8444"
    capabilities:
      - "banking:accounts"
      - "banking:transactions"
      - "a2a:messaging"
  crypto_agent:
    name: "crypto_agent"
    type: "a2a_agent"
    endpoint: "http://localhost:8445"
    capabilities:
      - "crypto:trading"
      - "crypto:analysis"
      - "a2a:messaging"

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
from adk_agents.adk.adk_integration import ADKIntegration

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

### A2A Protocol Usage

```python
# Import A2A protocol components
from adk_agents.a2a.core import A2AAgent, OrchestratorAgent, TransportConfig
from adk_agents.a2a.banking_a2a_integration.banking_a2a_agent import BankingA2AAgent
from adk_agents.a2a.crypto_a2a_integration.crypto_a2a_agent import CryptoA2AAgent

# Create and initialize A2A agents
banking_agent = BankingA2AAgent("banking-agent-01")
crypto_agent = CryptoA2AAgent("crypto-agent-01")

await banking_agent.initialize()
await crypto_agent.initialize()

# Start agents
await banking_agent.start()
await crypto_agent.start()

# Send message between agents
await banking_agent.send_message(
    receiver_id="crypto-agent-01",
    message_type="balance_request",
    payload={"account_id": "12345"}
)

# Create orchestrator for workflow coordination
orchestrator = OrchestratorAgent("main-orchestrator")
await orchestrator.initialize()
await orchestrator.start()

# Create workflow
workflow_id = await orchestrator.create_workflow(
    "Financial Analysis",
    "Complete banking and crypto analysis"
)
```

### Agent Wrapper Integration

```python
from adk_agents.agents.adk_agent_wrapper import ADKAgentWrapper

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

### Domain-Specific A2A Agent Operations

```python
# Banking agent operations
from adk_agents.a2a.banking_a2a_integration.banking_a2a_agent import create_banking_agent

banking_agent = await create_banking_agent("banking-01")

# Authenticate user for session
auth_response = await banking_agent.send_message(
    receiver_id="banking-01",
    message_type="authenticate_request",
    payload={
        "username": "user123",
        "password": "password123"
    }
)

# Get account balance
balance_response = await banking_agent.send_message(
    receiver_id="banking-01",
    message_type="balance_request",
    payload={
        "account_id": "main",
        "session_id": "session_user123"
    }
)

# Crypto agent operations
from adk_agents.a2a.crypto_a2a_integration.crypto_a2a_agent import create_crypto_agent

crypto_agent = await create_crypto_agent("crypto-01")

# Get market analysis
market_response = await crypto_agent.send_message(
    receiver_id="crypto-01",
    message_type="market_analysis_request",
    payload={
        "token_id": "bitcoin",
        "analysis_type": "price"
    }
)
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

## A2A Protocol

The A2A (Agent-to-Agent) protocol provides secure, encrypted communication between agents:

### Core Components

- **A2AAgent**: Base agent class with secure messaging capabilities
- **OrchestratorAgent**: Coordinates complex multi-agent workflows
- **TransportLayer**: HTTP/2 and WebSocket transport with encryption
- **Message/EncryptedMessage**: Secure message formats with authentication
- **AuthenticationManager**: Agent identity and session management

### A2A Message Types

- `balance_request/response`: Banking balance inquiries
- `transaction_request/response`: Transaction processing
- `market_analysis_request/response`: Crypto market analysis
- `trading_signal_request/response`: Trading signal generation
- `compliance_check_request/response`: Regulatory compliance
- `crypto_integration_request/response`: Cross-system integration

### Workflows

Define complex financial workflows using the orchestrator:

```python
from adk_agents.a2a.core import OrchestratorAgent

# Create orchestrator
orchestrator = OrchestratorAgent("financial-orchestrator")

# Create workflow
workflow_id = await orchestrator.create_workflow(
    "comprehensive_analysis",
    "Complete banking and crypto analysis workflow"
)

# Add banking compliance task
banking_task = orchestrator.add_task_to_workflow(
    workflow_id,
    "banking_compliance_check",
    "Check banking transactions for compliance",
    required_capabilities=["banking:compliance"]
)

# Add crypto analysis task
crypto_task = orchestrator.add_task_to_workflow(
    workflow_id,
    "crypto_portfolio_analysis",
    "Analyze crypto portfolio risk and market conditions",
    required_capabilities=["crypto:analysis"]
)

# Add integrated assessment
integrated_task = orchestrator.add_task_to_workflow(
    workflow_id,
    "integrated_risk_assessment",
    "Combine banking and crypto risk assessments",
    required_capabilities=["a2a:coordination"],
    dependencies=[banking_task, crypto_task]
)

# Execute workflow
await orchestrator.start_workflow(workflow_id)

# Monitor progress
status = orchestrator.get_workflow_status(workflow_id)
print(f"Workflow completion: {status['completion_percentage']}%")
```

## Security

- **Authentication**: Uses Google Cloud service accounts and IAM
- **Authorization**: Role-based access control for agent operations
- **A2A Encryption**: End-to-end encryption for agent-to-agent communication
- **Session Management**: Secure session handling with automatic expiration
- **Audit Logging**: All operations are logged for compliance

### A2A Security Features

- **Message Encryption**: All A2A messages are encrypted using industry-standard protocols
- **Agent Identity**: Cryptographic agent identities with verification
- **Secure Transport**: HTTP/2 with SSL/TLS or WebSocket with WSS
- **Authentication Tokens**: JWT-based session tokens with expiration
- **Access Control**: Capability-based permissions for agent operations

## A2A Protocol Components

### Core Protocol (`adk_agents/a2a/core/`)

- **A2AAgent**: Base class for all A2A-enabled agents
- **OrchestratorAgent**: Workflow coordination and task management
- **TransportLayer**: Network communication (HTTP/2, WebSocket)
- **AuthenticationManager**: Identity and session management
- **Message/EncryptedMessage**: Message formats and encryption
- **DiscoveryService**: Agent discovery and service registry

### Domain Agents (`adk_agents/a2a/*/`)

- **BankingA2AAgent**: Banking operations via Bank of Anthos MCP
- **CryptoA2AAgent**: Crypto trading via crypto MCP server
- **Shared Components**: Common interfaces, error handling, constants

### Agent Capabilities

**Banking Agent**:
- `banking:accounts` - Account management
- `banking:balances` - Balance inquiries
- `banking:transactions` - Transaction processing
- `banking:compliance` - Compliance checking

**Crypto Agent**:
- `crypto:trading` - Trading operations
- `crypto:analysis` - Market analysis
- `crypto:wallet` - Wallet management
- `crypto:ai` - AI-powered trading advice

## Monitoring

Monitor your ADK integration through Google Cloud Console:

- **Cloud Functions**: Monitor agent performance and scaling
- **Cloud Logging**: View detailed operation logs
- **Cloud Monitoring**: Set up alerts and dashboards
- **Cloud Trace**: Distributed tracing for complex workflows

## Testing

### A2A Protocol Tests

Run A2A-specific tests:

```bash
cd adk_agents

# Test A2A protocol core functionality
python -c "
import asyncio
from a2a.core import A2AAgent, TransportConfig

async def test_a2a():
    # Create test agent
    config = TransportConfig(protocol='http2', host='localhost', port=8444, ssl_enabled=False)
    agent = A2AAgent('test-agent', ['test:capability'], config)
    
    success = await agent.initialize()
    print(f'A2A Agent initialized: {success}')
    
    # Test message creation
    from a2a.core import Message
    message = Message(
        message_id='test-123',
        sender_id='test-agent',
        receiver_id='target-agent',
        message_type='test_request',
        payload={'data': 'test'}
    )
    print(f'Message created: {message.message_id}')
    
asyncio.run(test_a2a())
"

# Test banking agent
python -c "
import asyncio
from a2a.banking_a2a_integration.banking_a2a_agent import create_banking_agent

async def test_banking():
    agent = await create_banking_agent('test-banking', 'localhost', 8444)
    print('Banking agent created successfully!')

asyncio.run(test_banking())
"
```

### Full Test Suite

Run the complete test suite:

```bash
cd adk_agents
source venv/bin/activate
python -m pytest tests/
```

Or run basic functionality test:

```bash
python tests/test_adk_integration.py
```

### Integration Tests

Test the complete A2A workflow:

```bash
python integration_test.py
```

## Deployment

### Development
```bash
# Local development with A2A agents and MCP servers
cd adk_agents

# Start A2A agents
python -c "
import asyncio
from a2a.banking_a2a_integration.banking_a2a_agent import create_banking_agent
from a2a.crypto_a2a_integration.crypto_a2a_agent import create_crypto_agent

async def main():
    banking_agent = await create_banking_agent('banking-01', 'localhost', 8444)
    crypto_agent = await create_crypto_agent('crypto-01', 'localhost', 8445)
    print('A2A agents started successfully!')

asyncio.run(main())
"

# In separate terminals, start MCP servers
docker-compose up crypto_mcp_server bankofanthos_mcp_server
```

### Production
```bash
# Deploy ADK integration to Google Cloud
gcloud builds submit --tag gcr.io/YOUR-PROJECT/felicia-adk
gcloud run deploy felicia-adk --image gcr.io/YOUR-PROJECT/felicia-adk --platform managed

# Deploy A2A agents as Cloud Functions
gcloud functions deploy felicia-banking-agent \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --source adk_agents/a2a/banking_a2a_integration/ \
  --entry-point create_banking_agent

gcloud functions deploy felicia-crypto-agent \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --source adk_agents/a2a/crypto_a2a_integration/ \
  --entry-point create_crypto_agent
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

## A2A Protocol Benefits

The consolidated A2A protocol structure provides several key advantages:

- **🔧 Maintainability**: All A2A components are now organized under `adk_agents/a2a/`
- **📦 Modularity**: Clear separation between core protocol, domain agents, and shared components
- **🔒 Security**: End-to-end encrypted communication between agents
- **⚡ Scalability**: Easy to add new agent types and capabilities
- **🎯 Domain Focus**: Specialized agents for banking and crypto operations
- **🔄 Integration**: Seamless integration with existing MCP servers

### Migration from External A2A Protocol

The system has been migrated from the external `a2a_protocol/` module to the consolidated structure under `adk_agents/a2a/core/`. All imports have been updated:

- `from a2a_protocol import A2AAgent` → `from adk_agents.a2a.core import A2AAgent`
- `from a2a_protocol.transport import TransportConfig` → `from adk_agents.a2a.core import TransportConfig`
- `from a2a_protocol.orchestrator import OrchestratorAgent` → `from adk_agents.a2a.core import OrchestratorAgent`

## Contributing

1. Follow the existing code structure under `adk_agents/a2a/`
2. Add tests for new A2A features in `tests/`
3. Update documentation for any new capabilities
4. Ensure type hints are included
5. Run tests before submitting PR
6. Follow A2A protocol conventions for new agents

## License

Copyright 2025 Felicia Finance. All rights reserved.
