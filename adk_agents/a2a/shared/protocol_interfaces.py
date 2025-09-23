"""
A2A Protocol Interfaces

This module defines the core interfaces and abstract base classes
for A2A agents to ensure consistency across different domains.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """Standard A2A message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    AUTH = "auth"


class A2AAgentInterface(ABC):
    """Base interface for all A2A agents."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent and its connections."""
        pass

    @abstractmethod
    async def start(self) -> bool:
        """Start the agent's message handling."""
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """Stop the agent and clean up resources."""
        pass

    @abstractmethod
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a message handler for a specific message type."""
        pass

    @abstractmethod
    async def send_message(self, target_agent: str, message: Dict[str, Any]) -> bool:
        """Send a message to another agent."""
        pass

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Get the agent's unique identifier."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """Get the agent's capabilities."""
        pass


class MessageHandler(ABC):
    """Abstract base class for message handlers."""

    @abstractmethod
    async def handle_message(self, message: Dict[str, Any], sender: str) -> Dict[str, Any]:
        """Handle an incoming message and return a response."""
        pass


class TransportInterface(ABC):
    """Interface for transport layer implementations."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the transport layer."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the transport layer."""
        pass

    @abstractmethod
    async def send_data(self, data: bytes, target: str) -> bool:
        """Send data to a specific target."""
        pass

    @abstractmethod
    async def receive_data(self) -> tuple[bytes, str]:
        """Receive data from any source."""
        pass


class A2AMessage:
    """Standard A2A message format."""

    def __init__(self, message_type: MessageType, payload: Dict[str, Any],
                 sender: str, target: Optional[str] = None,
                 message_id: Optional[str] = None, correlation_id: Optional[str] = None):
        self.message_type = message_type
        self.payload = payload
        self.sender = sender
        self.target = target
        self.message_id = message_id or self._generate_id()
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow()

    def _generate_id(self) -> str:
        """Generate a unique message ID."""
        return f"msg_{int(datetime.utcnow().timestamp())}_{hash(self.sender) % 10000}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "message_type": self.message_type.value,
            "payload": self.payload,
            "sender": self.sender,
            "target": self.target,
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary format."""
        message_type = MessageType(data["message_type"])
        message = cls(
            message_type=message_type,
            payload=data["payload"],
            sender=data["sender"],
            target=data.get("target"),
            message_id=data.get("message_id"),
            correlation_id=data.get("correlation_id")
        )
        message.timestamp = datetime.fromisoformat(data["timestamp"])
        return message


class SessionManagerInterface(ABC):
    """Interface for session management."""

    @abstractmethod
    async def create_session(self, agent_id: str, session_data: Dict[str, Any]) -> str:
        """Create a new session for an agent."""
        pass

    @abstractmethod
    async def validate_session(self, session_id: str) -> bool:
        """Validate if a session is active and valid."""
        pass

    @abstractmethod
    async def expire_session(self, session_id: str) -> bool:
        """Expire a session."""
        pass

    @abstractmethod
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        pass