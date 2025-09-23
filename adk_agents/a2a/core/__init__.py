"""
A2A Protocol Core Components

This module contains the core A2A protocol implementation including
agent management, messaging, authentication, and orchestration.
"""

__version__ = "1.0.0"
__author__ = "Felicia's Finance Development Team"

from .client import A2AClient
from .agent import A2AAgent
from .identity import AgentIdentity
from .auth import AuthenticationManager
from .messaging import Message, EncryptedMessage
from .discovery import DiscoveryService
from .transport import TransportLayer, TransportConfig
from .orchestrator import OrchestratorAgent

__all__ = [
    "A2AClient",
    "A2AAgent",
    "AgentIdentity",
    "AuthenticationManager",
    "Message",
    "EncryptedMessage",
    "DiscoveryService",
    "TransportLayer",
    "TransportConfig",
    "OrchestratorAgent",
]