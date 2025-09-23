"""
Shared A2A Protocol Components

This module contains shared components and interfaces for A2A agents
across different domains (banking, crypto, etc.).
"""

from .protocol_interfaces import A2AAgentInterface, MessageHandler, TransportInterface
from .error_handling import A2AError, ConnectionError, ProtocolError
from .constants import A2A_MESSAGE_TYPES, DEFAULT_TIMEOUTS

__all__ = [
    'A2AAgentInterface',
    'MessageHandler',
    'TransportInterface',
    'A2AError',
    'ConnectionError',
    'ProtocolError',
    'A2A_MESSAGE_TYPES',
    'DEFAULT_TIMEOUTS'
]