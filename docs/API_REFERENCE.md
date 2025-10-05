# API Reference: Felicia's Finance Multi-Agent Platform

## Overview

This document provides comprehensive API documentation for the Felicia's Finance multi-agent orchestration platform. The API enables secure communication between agents, service discovery, and workflow orchestration.

## Base URL and Authentication

### Base URL
```
https://api.felicias-finance.example.com/v1
```

### Authentication
All API requests require authentication using JWT tokens obtained through the A2A protocol:

```http
Authorization: Bearer <jwt-token>
X-Agent-ID: <agent-identifier>
X-Signature: <rsa-sha256-signature>
```

## Core Agent API

### Agent Registration

#### Register Agent
```http
POST /agents/register
```

**Request Body:**
```json
{
  "agent_id": "banking-agent-001",
  "capabilities": [
    "banking:transactions",
    "banking:accounts",
    "banking:transfers"
  ],
  "metadata": {
    "version": "1.0.0",
    "description": "Banking operations agent",
    "contact": "admin@example.com"
  },
  "endpoints": {
    "health": "https://banking-agent.example.com/health",
    "services": "https://banking-agent.example.com/services"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "agent_id": "banking-agent-001",
  "registration_id": "reg-uuid-12345",
  "certificate": "-----BEGIN CERTIFICATE-----...",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

#### Update Agent
```http
PUT /agents/{agent_id}
```

#### Deregister Agent
```http
DELETE /agents/{agent_id}
```

### Agent Discovery

#### List Agents
```http
GET /agents
```

**Query Parameters:**
- `capability`: Filter by capability (e.g., `banking:transactions`)
- `status`: Filter by status (`active`, `inactive`, `maintenance`)
- `limit`: Maximum number of results (default: 50)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "banking-agent-001",
      "capabilities": ["banking:transactions", "banking:accounts"],
      "status": "active",
      "last_seen": "2024-01-15T10:30:00Z",
      "endpoints": {
        "health": "https://banking-agent.example.com/health",
        "services": "https://banking-agent.example.com/services"
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### Get Agent Details
```http
GET /agents/{agent_id}
```

**Response:**
```json
{
  "agent_id": "banking-agent-001",
  "capabilities": ["banking:transactions", "banking:accounts"],
  "status": "active",
  "metadata": {
    "version": "1.0.0",
    "description": "Banking operations agent",
    "uptime": "72h30m15s"
  },
  "services": [
    {
      "name": "banking:get_balance",
      "description": "Retrieve account balance",
      "parameters": {
        "account_id": {"type": "string", "required": true}
      },
      "returns": {
        "balance": {"type": "number"},
        "currency": {"type": "string"}
      }
    }
  ]
}
```

## Messaging API

### Send Message

#### Direct Message
```http
POST /messages/send
```

**Request Body:**
```json
{
  "recipient_id": "crypto-agent-001",
  "message_type": "request",
  "action": "crypto:get_price",
  "parameters": {
    "symbol": "BTC",
    "currency": "USD"
  },
  "metadata": {
    "priority": "high",
    "ttl": 3600,
    "correlation_id": "req-uuid-67890"
  }
}
```

**Response:**
```json
{
  "message_id": "msg-uuid-12345",
  "status": "sent",
  "timestamp": "2024-01-15T10:30:00Z",
  "estimated_delivery": "2024-01-15T10:30:01Z"
}
```

#### Broadcast Message
```http
POST /messages/broadcast
```

**Request Body:**
```json
{
  "capability_filter": "banking:*",
  "message_type": "notification",
  "action": "system:maintenance_alert",
  "parameters": {
    "maintenance_window": "2024-01-16T02:00:00Z",
    "duration": "2h",
    "affected_services": ["banking:transactions"]
  }
}
```

### Message History

#### Get Message History
```http
GET /messages/history
```

**Query Parameters:**
- `agent_id`: Filter by specific agent
- `message_type`: Filter by message type
- `start_time`: Start of time range (ISO 8601)
- `end_time`: End of time range (ISO 8601)
- `limit`: Maximum number of results
- `offset`: Pagination offset

**Response:**
```json
{
  "messages": [
    {
      "message_id": "msg-uuid-12345",
      "sender_id": "banking-agent-001",
      "recipient_id": "crypto-agent-001",
      "message_type": "request",
      "action": "crypto:get_price",
      "timestamp": "2024-01-15T10:30:00Z",
      "status": "delivered",
      "response_time": "150ms"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## Service Management API

### Service Registration

#### Register Service
```http
POST /services/register
```

**Request Body:**
```json
{
  "service_name": "banking:get_balance",
  "agent_id": "banking-agent-001",
  "description": "Retrieve account balance for a given account ID",
  "version": "1.0.0",
  "parameters": {
    "account_id": {
      "type": "string",
      "required": true,
      "description": "Unique account identifier"
    }
  },
  "returns": {
    "balance": {
      "type": "number",
      "description": "Current account balance"
    },
    "currency": {
      "type": "string",
      "description": "Currency code (ISO 4217)"
    }
  },
  "sla": {
    "response_time": "500ms",
    "availability": "99.9%"
  }
}
```

#### Update Service
```http
PUT /services/{service_name}
```

#### Deregister Service
```http
DELETE /services/{service_name}
```

### Service Discovery

#### List Services
```http
GET /services
```

**Query Parameters:**
- `capability`: Filter by capability pattern
- `agent_id`: Filter by providing agent
- `status`: Filter by service status

**Response:**
```json
{
  "services": [
    {
      "service_name": "banking:get_balance",
      "agent_id": "banking-agent-001",
      "description": "Retrieve account balance",
      "version": "1.0.0",
      "status": "active",
      "endpoint": "https://banking-agent.example.com/services/get_balance",
      "sla": {
        "response_time": "500ms",
        "availability": "99.9%"
      }
    }
  ]
}
```

#### Invoke Service
```http
POST /services/{service_name}/invoke
```

**Request Body:**
```json
{
  "parameters": {
    "account_id": "acc-12345"
  },
  "metadata": {
    "timeout": 5000,
    "retry_count": 3
  }
}
```

**Response:**
```json
{
  "result": {
    "balance": 1500.00,
    "currency": "USD"
  },
  "execution_time": "245ms",
  "agent_id": "banking-agent-001",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Workflow Orchestration API

### Workflow Management

#### Create Workflow
```http
POST /workflows
```

**Request Body:**
```json
{
  "workflow_name": "crypto_arbitrage",
  "description": "Automated cryptocurrency arbitrage workflow",
  "steps": [
    {
      "step_id": "get_prices",
      "service": "crypto:get_prices",
      "parameters": {
        "symbols": ["BTC", "ETH"],
        "exchanges": ["binance", "coinbase"]
      }
    },
    {
      "step_id": "analyze_arbitrage",
      "service": "crypto:analyze_arbitrage",
      "depends_on": ["get_prices"],
      "parameters": {
        "min_profit_threshold": 0.5
      }
    },
    {
      "step_id": "execute_trades",
      "service": "crypto:execute_trades",
      "depends_on": ["analyze_arbitrage"],
      "condition": "arbitrage_opportunities.length > 0"
    }
  ],
  "schedule": {
    "type": "interval",
    "interval": "5m"
  }
}
```

#### Execute Workflow
```http
POST /workflows/{workflow_id}/execute
```

#### Get Workflow Status
```http
GET /workflows/{workflow_id}/status
```

**Response:**
```json
{
  "workflow_id": "wf-uuid-12345",
  "status": "running",
  "started_at": "2024-01-15T10:30:00Z",
  "steps": [
    {
      "step_id": "get_prices",
      "status": "completed",
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:30:02Z",
      "result": {
        "BTC": {"binance": 45000, "coinbase": 45050},
        "ETH": {"binance": 3000, "coinbase": 3005}
      }
    },
    {
      "step_id": "analyze_arbitrage",
      "status": "running",
      "started_at": "2024-01-15T10:30:02Z"
    }
  ]
}
```

## Banking Agent API

### Account Operations

#### Get Account Balance
```http
GET /banking/accounts/{account_id}/balance
```

**Response:**
```json
{
  "account_id": "acc-12345",
  "balance": 1500.00,
  "available_balance": 1450.00,
  "currency": "USD",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### Get Transaction History
```http
GET /banking/accounts/{account_id}/transactions
```

**Query Parameters:**
- `start_date`: Start date for transaction history
- `end_date`: End date for transaction history
- `limit`: Maximum number of transactions
- `offset`: Pagination offset

**Response:**
```json
{
  "transactions": [
    {
      "transaction_id": "txn-12345",
      "type": "debit",
      "amount": 50.00,
      "currency": "USD",
      "description": "Coffee purchase",
      "timestamp": "2024-01-15T09:15:00Z",
      "balance_after": 1450.00
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Transfer Operations

#### Create Transfer
```http
POST /banking/transfers
```

**Request Body:**
```json
{
  "from_account": "acc-12345",
  "to_account": "acc-67890",
  "amount": 100.00,
  "currency": "USD",
  "description": "Payment for services",
  "reference": "ref-12345"
}
```

**Response:**
```json
{
  "transfer_id": "xfer-12345",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:32:00Z"
}
```

## Crypto Agent API

### Price Operations

#### Get Current Prices
```http
GET /crypto/prices
```

**Query Parameters:**
- `symbols`: Comma-separated list of symbols (e.g., `BTC,ETH`)
- `exchanges`: Comma-separated list of exchanges
- `currency`: Base currency for prices (default: USD)

**Response:**
```json
{
  "prices": {
    "BTC": {
      "binance": {
        "price": 45000.00,
        "timestamp": "2024-01-15T10:30:00Z",
        "volume_24h": 1234567.89
      },
      "coinbase": {
        "price": 45050.00,
        "timestamp": "2024-01-15T10:30:01Z",
        "volume_24h": 987654.32
      }
    }
  }
}
```

#### Get Price History
```http
GET /crypto/prices/history
```

### Trading Operations

#### Place Order
```http
POST /crypto/orders
```

**Request Body:**
```json
{
  "exchange": "binance",
  "symbol": "BTC/USD",
  "type": "market",
  "side": "buy",
  "amount": 0.1,
  "price": 45000.00
}
```

**Response:**
```json
{
  "order_id": "order-12345",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_execution": "2024-01-15T10:30:05Z"
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "The provided parameters are invalid",
    "details": {
      "field": "account_id",
      "reason": "Account ID must be a valid UUID"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req-uuid-12345"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_FAILED` | 401 | Invalid or expired authentication token |
| `AUTHORIZATION_DENIED` | 403 | Insufficient permissions for the requested operation |
| `AGENT_NOT_FOUND` | 404 | Specified agent does not exist |
| `SERVICE_UNAVAILABLE` | 503 | Requested service is temporarily unavailable |
| `INVALID_PARAMETERS` | 400 | Request parameters are invalid or missing |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests in a given time period |
| `INTERNAL_ERROR` | 500 | Internal server error occurred |

## Rate Limiting

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

### Rate Limit Tiers

| Tier | Requests per Hour | Burst Limit |
|------|------------------|-------------|
| Basic | 1,000 | 100 |
| Premium | 10,000 | 500 |
| Enterprise | 100,000 | 2,000 |

## SDK Examples

### Python SDK
```python
from felicias_finance import A2AClient

# Initialize client
client = A2AClient(
    base_url="https://api.felicias-finance.example.com/v1",
    agent_id="my-agent-001",
    private_key_path="./keys/agent.key",
    certificate_path="./certs/agent.crt"
)

# Register agent
await client.register_agent(
    capabilities=["custom:service"],
    metadata={"version": "1.0.0"}
)

# Send message
response = await client.send_message(
    recipient="banking-agent-001",
    action="banking:get_balance",
    parameters={"account_id": "acc-12345"}
)
```

### JavaScript SDK
```javascript
import { A2AClient } from '@felicias-finance/sdk';

const client = new A2AClient({
  baseUrl: 'https://api.felicias-finance.example.com/v1',
  agentId: 'my-agent-001',
  privateKey: fs.readFileSync('./keys/agent.key'),
  certificate: fs.readFileSync('./certs/agent.crt')
});

// Register agent
await client.registerAgent({
  capabilities: ['custom:service'],
  metadata: { version: '1.0.0' }
});

// Send message
const response = await client.sendMessage({
  recipient: 'banking-agent-001',
  action: 'banking:get_balance',
  parameters: { accountId: 'acc-12345' }
});
```

## Conclusion

This API reference provides comprehensive documentation for integrating with the Felicia's Finance multi-agent platform. The API design prioritizes security, scalability, and ease of use while providing powerful capabilities for building sophisticated agent-based systems.
