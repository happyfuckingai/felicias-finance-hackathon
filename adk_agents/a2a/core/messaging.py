"""
Messaging System for A2A Protocol

Handles message creation, encryption, decryption, and routing between agents.
Supports end-to-end encryption and message integrity verification.
"""

import json
import uuid
import time
import hashlib
from datetime import datetime
from typing import Dict, Optional, Any, List, Union
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from .identity import AgentIdentity
from .auth import AuthToken


@dataclass
class Message:
    """Represents a basic A2A message."""

    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str  # "request", "response", "notification", "event"
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None  # For request-response correlation
    ttl: Optional[int] = None  # Time to live in seconds
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        if self.metadata is None:
            self.metadata = {}
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp) if isinstance(self.timestamp, str) else datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    def is_expired(self) -> bool:
        """Check if message has expired based on TTL."""
        if not self.ttl:
            return False
        return (datetime.utcnow() - self.timestamp).total_seconds() > self.ttl

    def create_response(self, payload: Dict[str, Any] = None,
                       message_type: str = "response") -> 'Message':
        """Create a response message to this message."""
        return Message(
            message_id="",
            sender_id=self.receiver_id,
            receiver_id=self.sender_id,
            message_type=message_type,
            payload=payload or {},
            timestamp=datetime.utcnow(),
            correlation_id=self.message_id,
            metadata={"response_to": self.message_id}
        )


@dataclass
class EncryptedMessage:
    """Represents an encrypted A2A message."""

    encrypted_data: str  # Base64 encoded encrypted data
    iv: str  # Base64 encoded initialization vector
    auth_tag: str  # Base64 encoded authentication tag
    sender_id: str
    receiver_id: str
    timestamp: datetime
    algorithm: str = "AES-256-GCM"

    def to_dict(self) -> Dict[str, Any]:
        """Convert encrypted message to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EncryptedMessage':
        """Create encrypted message from dictionary."""
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class MessageEncryptor:
    """Handles encryption and decryption of messages."""

    def __init__(self, key_size: int = 32):  # 256-bit key
        self.key_size = key_size

    def generate_session_key(self, agent_a: str, agent_b: str,
                           shared_secret: str = None) -> bytes:
        """Generate a session key for two agents."""

        if shared_secret:
            key_material = f"{agent_a}:{agent_b}:{shared_secret}:{int(time.time())}"
        else:
            # Use a combination of agent IDs and timestamp as key material
            key_material = f"{agent_a}:{agent_b}:{int(time.time())}"

        # Derive key using HKDF-like construction
        key = hashlib.sha256(key_material.encode()).digest()
        return key[:self.key_size]

    def encrypt_message(self, message: Message, session_key: bytes,
                       sender_identity: AgentIdentity) -> EncryptedMessage:
        """Encrypt a message using AES-GCM."""

        import os
        import base64

        # Serialize message
        message_data = json.dumps(message.to_dict(), sort_keys=True).encode('utf-8')

        # Generate IV
        iv = os.urandom(12)  # 96-bit IV for GCM

        # Create cipher
        cipher = Cipher(algorithms.AES(session_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Encrypt the message
        ciphertext = encryptor.update(message_data) + encryptor.finalize()

        # Get authentication tag
        auth_tag = encryptor.tag

        return EncryptedMessage(
            encrypted_data=base64.b64encode(ciphertext).decode('utf-8'),
            iv=base64.b64encode(iv).decode('utf-8'),
            auth_tag=base64.b64encode(auth_tag).decode('utf-8'),
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            timestamp=datetime.utcnow()
        )

    def decrypt_message(self, encrypted_message: EncryptedMessage,
                       session_key: bytes) -> Optional[Message]:
        """Decrypt an encrypted message."""

        import base64

        try:
            # Decode encrypted data
            ciphertext = base64.b64decode(encrypted_message.encrypted_data)
            iv = base64.b64decode(encrypted_message.iv)
            auth_tag = base64.b64decode(encrypted_message.auth_tag)

            # Create cipher
            cipher = Cipher(algorithms.AES(session_key), modes.GCM(iv, auth_tag),
                          backend=default_backend())
            decryptor = cipher.decryptor()

            # Decrypt the message
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Deserialize message
            message_data = json.loads(plaintext.decode('utf-8'))
            return Message.from_dict(message_data)

        except Exception as e:
            print(f"Decryption failed: {e}")
            return None


class MessageSigner:
    """Handles message signing and verification."""

    def __init__(self, identity_manager):
        self.identity_manager = identity_manager

    def sign_message(self, message: Message, agent_id: str) -> str:
        """Sign a message with the agent's private key."""

        message_data = json.dumps(message.to_dict(), sort_keys=True).encode('utf-8')
        return self.identity_manager.sign_data(agent_id, message_data)

    def verify_message_signature(self, message: Message, signature: str,
                               agent_id: str) -> bool:
        """Verify a message signature."""

        message_data = json.dumps(message.to_dict(), sort_keys=True).encode('utf-8')
        return self.identity_manager.verify_signature(agent_id, message_data, signature)


class MessageRouter:
    """Routes messages between agents."""

    def __init__(self):
        self.routes: Dict[str, List[str]] = {}  # message_type -> list of handler agent IDs
        self.pending_responses: Dict[str, Message] = {}  # correlation_id -> original message

    def register_handler(self, message_type: str, agent_id: str):
        """Register an agent to handle a specific message type."""

        if message_type not in self.routes:
            self.routes[message_type] = []
        if agent_id not in self.routes[message_type]:
            self.routes[message_type].append(agent_id)

    def unregister_handler(self, message_type: str, agent_id: str):
        """Unregister an agent from handling a message type."""

        if message_type in self.routes and agent_id in self.routes[message_type]:
            self.routes[message_type].remove(agent_id)
            if not self.routes[message_type]:
                del self.routes[message_type]

    def get_handlers(self, message_type: str) -> List[str]:
        """Get all agents that can handle a message type."""
        return self.routes.get(message_type, [])

    def store_pending_response(self, message: Message):
        """Store a message waiting for a response."""
        self.pending_responses[message.message_id] = message

    def get_pending_message(self, correlation_id: str) -> Optional[Message]:
        """Get the original message for a correlation ID."""
        return self.pending_responses.get(correlation_id)

    def clear_pending_response(self, message_id: str):
        """Clear a pending response after it's been handled."""
        self.pending_responses.pop(message_id, None)


class MessageQueue:
    """In-memory message queue for agent communication."""

    def __init__(self, max_size: int = 1000):
        self.queue: List[Message] = []
        self.max_size = max_size
        self.lock = None  # Would use asyncio.Lock in async context

    def enqueue(self, message: Message) -> bool:
        """Add a message to the queue."""

        if len(self.queue) >= self.max_size:
            return False

        self.queue.append(message)
        return True

    def dequeue(self) -> Optional[Message]:
        """Remove and return the next message from the queue."""

        if not self.queue:
            return None

        return self.queue.pop(0)

    def peek(self) -> Optional[Message]:
        """Return the next message without removing it."""

        if not self.queue:
            return None

        return self.queue[0]

    def size(self) -> int:
        """Get the current queue size."""
        return len(self.queue)

    def clear_expired(self):
        """Remove expired messages from the queue."""

        current_time = datetime.utcnow()
        self.queue = [
            msg for msg in self.queue
            if not msg.is_expired()
        ]

    def get_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get all messages addressed to a specific agent."""

        messages = [msg for msg in self.queue if msg.receiver_id == agent_id]
        # Remove from queue
        self.queue = [msg for msg in self.queue if msg.receiver_id != agent_id]
        return messages


class MessagingService:
    """Central messaging service for A2A communication."""

    def __init__(self, identity_manager, auth_manager):
        self.identity_manager = identity_manager
        self.auth_manager = auth_manager
        self.encryptor = MessageEncryptor()
        self.signer = MessageSigner(identity_manager)
        self.router = MessageRouter()
        self.queue = MessageQueue()

        # Session keys for agent pairs
        self.session_keys: Dict[str, bytes] = {}

    def create_session(self, agent_a: str, agent_b: str) -> str:
        """Create an encrypted session between two agents."""

        session_key = self.encryptor.generate_session_key(agent_a, agent_b)
        session_id = f"{agent_a}:{agent_b}"

        self.session_keys[session_id] = session_key
        return session_id

    def get_session_key(self, agent_a: str, agent_b: str) -> Optional[bytes]:
        """Get the session key for two agents."""

        session_id = f"{agent_a}:{agent_b}"
        return self.session_keys.get(session_id)

    def send_message(self, message: Message, auth_token: AuthToken,
                    encrypt: bool = True) -> bool:
        """Send a message (with optional encryption)."""

        # Validate authentication
        is_valid, agent_id = self.auth_manager.validate_authentication(
            auth_token.token, ["a2a:messaging"]
        )
        if not is_valid or agent_id != message.sender_id:
            return False

        # Sign the message
        signature = self.signer.sign_message(message, message.sender_id)

        if encrypt:
            # Get or create session key
            session_key = self.get_session_key(message.sender_id, message.receiver_id)
            if not session_key:
                # Create session if it doesn't exist
                self.create_session(message.sender_id, message.receiver_id)
                session_key = self.get_session_key(message.sender_id, message.receiver_id)

            # Encrypt message
            sender_identity = self.identity_manager.get_identity(message.sender_id)
            encrypted_message = self.encryptor.encrypt_message(message, session_key, sender_identity)

            # Add signature to metadata
            encrypted_message.metadata = {"signature": signature}

            # Queue encrypted message (would normally send over network)
            return self._queue_encrypted_message(encrypted_message)
        else:
            # Queue plain message with signature
            message.metadata["signature"] = signature
            return self.queue.enqueue(message)

    def receive_message(self, agent_id: str, auth_token: AuthToken) -> List[Message]:
        """Receive messages for an agent."""

        # Validate authentication
        is_valid, authenticated_agent = self.auth_manager.validate_authentication(
            auth_token.token, ["a2a:messaging"]
        )
        if not is_valid or authenticated_agent != agent_id:
            return []

        # Get messages for this agent
        messages = self.queue.get_messages_for_agent(agent_id)

        # Verify signatures
        verified_messages = []
        for message in messages:
            signature = message.metadata.get("signature")
            if signature and self.signer.verify_message_signature(message, signature, message.sender_id):
                verified_messages.append(message)
            else:
                print(f"Invalid signature for message {message.message_id}")

        return verified_messages

    def send_encrypted_message(self, encrypted_message: EncryptedMessage,
                              auth_token: AuthToken) -> bool:
        """Send an already encrypted message."""

        # Validate authentication
        is_valid, agent_id = self.auth_manager.validate_authentication(
            auth_token.token, ["a2a:messaging"]
        )
        if not is_valid or agent_id != encrypted_message.sender_id:
            return False

        return self._queue_encrypted_message(encrypted_message)

    def receive_encrypted_message(self, agent_id: str, auth_token: AuthToken) -> List[Message]:
        """Receive and decrypt messages for an agent."""

        # This would normally receive from network
        # For now, return empty list as encrypted messages are handled differently
        return []

    def _queue_encrypted_message(self, encrypted_message: EncryptedMessage) -> bool:
        """Queue an encrypted message (placeholder for network transport)."""

        # In a real implementation, this would send over the network
        # For now, we'll simulate by storing in a separate encrypted queue

        # Create a placeholder message to indicate encrypted content
        placeholder = Message(
            message_id="",
            sender_id=encrypted_message.sender_id,
            receiver_id=encrypted_message.receiver_id,
            message_type="encrypted",
            payload={"encrypted_message": encrypted_message.to_dict()},
            timestamp=datetime.utcnow()
        )

        return self.queue.enqueue(placeholder)

    def route_message(self, message: Message) -> List[str]:
        """Route a message to appropriate handlers."""

        return self.router.get_handlers(message.message_type)