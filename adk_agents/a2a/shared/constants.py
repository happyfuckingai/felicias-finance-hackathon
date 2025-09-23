"""
A2A Protocol Constants

This module defines constants used across the A2A protocol implementation.
"""

from typing import Dict, Any

# Message Types
A2A_MESSAGE_TYPES = {
    "AUTH_REQUEST": "auth_request",
    "AUTH_RESPONSE": "auth_response",
    "BALANCE_REQUEST": "balance_request",
    "BALANCE_RESPONSE": "balance_response",
    "TRANSACTION_REQUEST": "transaction_request",
    "TRANSACTION_RESPONSE": "transaction_response",
    "COMPLIANCE_REQUEST": "compliance_request",
    "COMPLIANCE_RESPONSE": "compliance_response",
    "CRYPTO_REQUEST": "crypto_request",
    "CRYPTO_RESPONSE": "crypto_response",
    "MARKET_DATA_REQUEST": "market_data_request",
    "MARKET_DATA_RESPONSE": "market_data_response",
    "ERROR": "error",
    "HEARTBEAT": "heartbeat"
}

# Default Timeouts (in seconds)
DEFAULT_TIMEOUTS = {
    "CONNECTION_TIMEOUT": 30,
    "MESSAGE_TIMEOUT": 60,
    "HEARTBEAT_INTERVAL": 30,
    "SESSION_TIMEOUT": 3600,  # 1 hour
    "AUTH_TIMEOUT": 300,      # 5 minutes
}

# Agent Capabilities
BANKING_CAPABILITIES = [
    "banking:accounts",
    "banking:balances",
    "banking:transactions",
    "banking:history",
    "banking:contacts",
    "banking:transfers",
    "banking:compliance",
    "a2a:messaging"
]

CRYPTO_CAPABILITIES = [
    "crypto:trading",
    "crypto:analysis",
    "crypto:wallet",
    "crypto:signals",
    "crypto:tokens",
    "crypto:ai",
    "crypto:integration",
    "a2a:messaging"
]

# HTTP Status Codes
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503
}

# Protocol Versions
PROTOCOL_VERSIONS = {
    "SUPPORTED": ["1.0", "1.1"],
    "CURRENT": "1.1"
}

# Transport Protocols
TRANSPORT_PROTOCOLS = {
    "HTTP2": "http2",
    "WEBSOCKET": "websocket",
    "GRPC": "grpc"
}

# Error Codes
ERROR_CODES = {
    "CONNECTION_FAILED": "CONNECTION_FAILED",
    "AUTH_FAILED": "AUTH_FAILED",
    "INVALID_MESSAGE": "INVALID_MESSAGE",
    "TIMEOUT": "TIMEOUT",
    "VALIDATION_ERROR": "VALIDATION_ERROR",
    "PROTOCOL_ERROR": "PROTOCOL_ERROR",
    "SERVICE_UNAVAILABLE": "SERVICE_UNAVAILABLE"
}