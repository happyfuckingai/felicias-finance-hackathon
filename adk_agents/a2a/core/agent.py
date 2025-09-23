"""
A2A Agent Implementation

Provides the core A2AAgent class that combines all A2A protocol components
for secure agent-to-agent communication.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime

from .identity import IdentityManager, AgentIdentity
from .auth import AuthenticationManager, AuthToken
from .messaging import MessagingService, Message
from .discovery import DiscoveryService, AgentRecord, ServiceQuery
from .transport import TransportLayer, TransportConfig

logger = logging.getLogger(__name__)


class A2AAgent:
    """Core A2A agent that provides secure agent-to-agent communication."""

    def __init__(self, agent_id: str, capabilities: List[str] = None,
                 transport_config: TransportConfig = None,
                 identity_storage: str = "./identities"):
        """
        Initialize an A2A agent.

        Args:
            agent_id: Unique identifier for this agent
            capabilities: List of capabilities this agent provides
            transport_config: Transport layer configuration
            identity_storage: Path to store agent identities
        """

        self.agent_id = agent_id
        self.capabilities = capabilities or ["a2a:messaging"]

        # Initialize core components
        self.identity_manager = IdentityManager(identity_storage)
        self.auth_manager = AuthenticationManager(self.identity_manager)
        self.messaging = MessagingService(self.identity_manager, self.auth_manager)
        self.discovery = DiscoveryService()

        # Initialize transport
        self.transport_config = transport_config or TransportConfig()
        self.transport = TransportLayer(self.transport_config)

        # Agent state
        self.identity: Optional[AgentIdentity] = None
        self.auth_token: Optional[AuthToken] = None
        self.running = False
        self.message_handlers: Dict[str, Callable] = {}

        # Register default message handlers
        self._register_default_handlers()

    async def initialize(self) -> bool:
        """Initialize the agent with identity and authentication."""

        try:
            # Load or create identity
            self.identity = self.identity_manager.get_identity(self.agent_id)
            if not self.identity:
                logger.info(f"Creating new identity for agent: {self.agent_id}")
                self.identity = self.identity_manager.create_identity(
                    capabilities=self.capabilities,
                    metadata={"agent_type": "a2a_agent", "version": "1.0.0"}
                )

            # Create authentication token
            self.auth_token = self.auth_manager.authenticate_agent(
                agent_id=self.agent_id,
                auth_method="jwt",
                permissions=["a2a:messaging", "a2a:discovery"]
            )

            if not self.auth_token:
                logger.error(f"Failed to authenticate agent: {self.agent_id}")
                return False

            # Register with discovery service
            agent_record = AgentRecord(
                agent_id=self.agent_id,
                agent_did=self.identity.did,
                capabilities=self.capabilities,
                endpoints=[f"http://{self.transport_config.host}:{self.transport_config.port}/a2a"],
                metadata={"status": "initializing"}
            )

            self.discovery.register_agent(agent_record)

            logger.info(f"Agent {self.agent_id} initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_id}: {e}")
            return False

    async def start(self) -> bool:
        """Start the agent and all its services."""

        if not self.identity or not self.auth_token:
            logger.error("Agent not initialized. Call initialize() first.")
            return False

        try:
            # Start transport layer
            await self.transport.start()

            # Start discovery service
            self.discovery.start()

            # Start server for incoming messages
            await self.transport.start_server()

            # Update status
            self.discovery.update_agent_status(self.agent_id, "active")

            self.running = True
            logger.info(f"Agent {self.agent_id} started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            return False

    async def stop(self):
        """Stop the agent and clean up resources."""

        self.running = False

        # Update status
        self.discovery.update_agent_status(self.agent_id, "inactive")

        # Stop services
        await self.transport.stop()
        self.discovery.stop()

        logger.info(f"Agent {self.agent_id} stopped")

    async def send_message(self, receiver_id: str, message_type: str,
                          payload: Dict[str, Any], correlation_id: str = None) -> Optional[str]:
        """Send a message to another agent."""

        if not self.running or not self.auth_token:
            logger.error("Agent not running or not authenticated")
            return None

        # Discover receiver
        query = ServiceQuery(agent_id=receiver_id)
        agents = self.discovery.discover_agents(query)

        if not agents:
            logger.error(f"Agent {receiver_id} not found in discovery service")
            return None

        receiver = agents[0]

        # Create message
        message = Message(
            message_id="",
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id,
            timestamp=datetime.utcnow()
        )

        # Send via transport
        target_url = f"{receiver.endpoints[0]}/message"

        try:
            response = await self.transport.send_message(message, target_url, self.auth_token)
            logger.info(f"Message sent to {receiver_id}: {message.message_id}")
            return message.message_id

        except Exception as e:
            logger.error(f"Failed to send message to {receiver_id}: {e}")
            return None

    async def send_encrypted_message(self, receiver_id: str, message_type: str,
                                    payload: Dict[str, Any]) -> Optional[str]:
        """Send an encrypted message to another agent."""

        if not self.running or not self.auth_token:
            logger.error("Agent not running or not authenticated")
            return None

        # Create session key if needed
        session_key = self.messaging.get_session_key(self.agent_id, receiver_id)
        if not session_key:
            session_key = self.messaging.create_session(self.agent_id, receiver_id)

        # Create message
        message = Message(
            message_id="",
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.utcnow()
        )

        # Encrypt and send
        encrypted_message = self.messaging.encryptor.encrypt_message(
            message, session_key, self.identity
        )

        # Discover receiver
        query = ServiceQuery(agent_id=receiver_id)
        agents = self.discovery.discover_agents(query)

        if not agents:
            logger.error(f"Agent {receiver_id} not found")
            return None

        receiver = agents[0]
        target_url = f"{receiver.endpoints[0]}/encrypted"

        try:
            response = await self.transport.send_encrypted_message(
                encrypted_message, target_url, self.auth_token
            )
            logger.info(f"Encrypted message sent to {receiver_id}")
            return encrypted_message.to_dict().get("message_id")

        except Exception as e:
            logger.error(f"Failed to send encrypted message: {e}")
            return None

    async def receive_messages(self) -> List[Message]:
        """Receive pending messages for this agent."""

        if not self.running or not self.auth_token:
            return []

        return self.messaging.receive_message(self.agent_id, self.auth_token)

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for incoming messages."""

        self.message_handlers[message_type] = handler

        # Register with messaging service
        self.messaging.router.register_handler(message_type, self.agent_id)

    def unregister_message_handler(self, message_type: str):
        """Unregister a message handler."""

        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            self.messaging.router.unregister_handler(message_type, self.agent_id)

    async def discover_agents(self, capabilities: List[str] = None,
                             max_results: int = 50) -> List[AgentRecord]:
        """Discover agents with specific capabilities."""

        query = ServiceQuery(
            capabilities=capabilities,
            max_results=max_results
        )

        return self.discovery.discover_agents(query)

    def get_agent_info(self, agent_id: str) -> Optional[AgentRecord]:
        """Get information about a specific agent."""

        return self.discovery.get_agent_record(agent_id)

    def update_capabilities(self, capabilities: List[str]):
        """Update agent capabilities."""

        self.capabilities = capabilities

        # Update identity
        if self.identity:
            self.identity.capabilities = capabilities

        # Update discovery record
        record = self.discovery.get_agent_record(self.agent_id)
        if record:
            record.capabilities = capabilities
            self.discovery.register_agent(record)

    def heartbeat(self):
        """Send heartbeat to discovery service."""

        self.discovery.heartbeat(self.agent_id)

    async def wait_for_message(self, message_type: str = None,
                              timeout: float = 30.0) -> Optional[Message]:
        """Wait for a specific type of message."""

        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            messages = await self.receive_messages()

            for message in messages:
                if message_type is None or message.message_type == message_type:
                    return message

            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

        return None

    def _register_default_handlers(self):
        """Register default message handlers."""

        async def handle_ping(message: Message, auth_token: AuthToken):
            """Handle ping messages."""
            response = message.create_response({"status": "pong"})
            # In a real implementation, send response back
            logger.debug(f"Received ping from {message.sender_id}")

        async def handle_discovery_request(message: Message, auth_token: AuthToken):
            """Handle discovery requests."""
            query_data = message.payload.get("query", {})
            query = ServiceQuery(**query_data)
            agents = self.discovery.discover_agents(query)

            response_payload = {
                "agents": [agent.to_dict() for agent in agents]
            }

            response = message.create_response(response_payload)
            # Send response back
            logger.debug(f"Discovery request from {message.sender_id}")

        # Register handlers
        self.register_message_handler("ping", handle_ping)
        self.register_message_handler("discovery_request", handle_discovery_request)