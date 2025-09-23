# A2A Protocol Client Library

A comprehensive Python implementation of the Agent-to-Agent (A2A) protocol for secure agent-to-agent communication in multi-agent systems. This library provides the foundation for building distributed, collaborative AI agent networks with enterprise-grade security and orchestration capabilities.

## Features

- **Cryptographic Identity Management**: RSA key pairs and X.509 certificate-based agent identities
- **Multi-Protocol Authentication**: JWT, OAuth2, and mutual TLS authentication support
- **End-to-End Encryption**: AES-256-GCM encrypted messaging with session key management
- **Decentralized Agent Discovery**: Service registry for dynamic agent discovery and capability matching
- **Flexible Transport Layer**: HTTP/2 and WebSocket transport protocols
- **Workflow Orchestration**: Advanced task coordination and delegation across multiple agents
- **Intelligent Message Routing**: Capability-based message routing and load balancing
- **Health Monitoring**: Comprehensive system health checks and metrics

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Agent Setup

```python
import asyncio
from a2a_client import A2AClient

async def main():
    # Create and connect an A2A client
    client = A2AClient("my-agent", capabilities=["data_processing", "analysis"])

    async with client:
        # Send a message to another agent
        message_id = await client.send_message(
            receiver_id="target-agent",
            message_type="data_request",
            payload={"query": "SELECT * FROM data"}
        )

        # Receive messages
        messages = await client.receive_messages()
        for msg in messages:
            print(f"Received: {msg.payload}")

asyncio.run(main())
```

### Orchestrator Agent

```python
from a2a_client import OrchestratorAgent

async def main():
    orchestrator = OrchestratorAgent("orchestrator-01")

    async with orchestrator:
        # Create a workflow
        workflow_id = await orchestrator.create_workflow(
            "Data Analysis Pipeline",
            "Process and analyze financial data"
        )

        # Add tasks to the workflow
        task1_id = orchestrator.add_task_to_workflow(
            workflow_id,
            "data_collection",
            "Collect financial data from APIs",
            required_capabilities=["api_access"]
        )

        task2_id = orchestrator.add_task_to_workflow(
            workflow_id,
            "data_analysis",
            "Analyze collected data",
            required_capabilities=["data_analysis"],
            dependencies=[task1_id]
        )

        # Start the workflow
        await orchestrator.start_workflow(workflow_id)

        # Monitor progress
        while True:
            status = orchestrator.get_workflow_status(workflow_id)
            print(f"Progress: {status['completion_percentage']}%")

            if status['status'] == 'completed':
                break

            await asyncio.sleep(1)

asyncio.run(main())
```

## Architecture

### Core Components

1. **Identity Management** (`identity.py`): Handles cryptographic identities, keys, and certificates
2. **Authentication** (`auth.py`): JWT, OAuth2, and mutual TLS authentication
3. **Messaging** (`messaging.py`): Message creation, encryption, and routing
4. **Discovery** (`discovery.py`): Agent discovery and service registry
5. **Transport** (`transport.py`): HTTP/2 and WebSocket transport layers
6. **Agent** (`agent.py`): Core A2A agent implementation
7. **Client** (`client.py`): High-level client interface
8. **Orchestrator** (`orchestrator.py`): Workflow coordination and task delegation

### Security Features

- **Cryptographic Keys**: RSA-2048 key pairs for identity
- **Certificate-based Authentication**: X.509 certificates for mutual TLS
- **End-to-End Encryption**: AES-256-GCM with session keys
- **Message Integrity**: HMAC signatures for message authentication
- **Secure Transport**: TLS 1.3 for all network communication

### Message Flow

```
Agent A → Discovery → Agent B Location → Transport → Encrypted Message → Agent B
    ↓              ↓                       ↓                   ↓
Identity   Service Registry         HTTP/2/WebSocket    AES-GCM Decryption
Verification                       Authentication       Message Processing
```

## Configuration

### Transport Configuration

```python
from a2a_client.transport import TransportConfig

config = TransportConfig(
    protocol="http2",
    host="localhost",
    port=8443,
    ssl_enabled=True,
    cert_file="path/to/cert.pem",
    key_file="path/to/key.pem"
)
```

### Agent Capabilities

Agents can declare capabilities for discovery and task assignment:

```python
capabilities = [
    "data_processing",
    "api_access",
    "analysis",
    "reporting",
    "orchestration"
]
```

## Integration with Existing Systems

The A2A client is designed to integrate seamlessly with existing agent systems:

### Banking Agent Integration

```python
# Integrate with existing banking MCP server
from a2a_client import A2AClient

banking_agent = A2AClient(
    "banking-agent",
    capabilities=["banking:accounts", "banking:transactions", "banking:compliance"]
)

# Register message handlers for banking operations
@banking_agent.register_message_handler("account_query")
async def handle_account_query(message):
    # Query banking data via MCP
    pass
```

### Crypto Agent Integration

```python
# Integrate with existing crypto trading system
crypto_agent = A2AClient(
    "crypto-agent",
    capabilities=["crypto:trading", "crypto:analysis", "crypto:risk"]
)

# Handle trading requests from orchestrator
@crypto_agent.register_message_handler("trading_signal")
async def handle_trading_signal(message):
    # Execute trading logic
    pass
```

## API Reference

### A2AClient

- `connect()`: Connect to A2A network
- `disconnect()`: Disconnect from network
- `send_message()`: Send message to agent
- `receive_messages()`: Get pending messages
- `discover_agents()`: Find agents by capabilities
- `ping_agent()`: Test connectivity to agent

### OrchestratorAgent

- `create_workflow()`: Create new workflow
- `add_task_to_workflow()`: Add task to workflow
- `start_workflow()`: Begin workflow execution
- `get_workflow_status()`: Get workflow progress
- `cancel_workflow()`: Stop workflow execution

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

## Security Considerations

- Store private keys securely (e.g., HSM, encrypted storage)
- Use certificate pinning for mutual TLS
- Regularly rotate session keys
- Validate agent identities before communication
- Implement rate limiting for message handling
- Use secure random number generation for all cryptographic operations

## Performance

- Concurrent message processing with asyncio
- Connection pooling for transport layer
- Efficient agent discovery with indexing
- Message queuing for high-throughput scenarios

## Monitoring

The A2A client provides health check endpoints and metrics:

```python
health = await client.health_check()
print(f"Connected: {health['connected']}")
print(f"Active agents: {health['discovery_stats']['active_agents']}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
