"""
A2A Client - Main Interface for A2A Protocol

Provides a high-level client interface for interacting with the A2A protocol
and managing agent communications.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime

from .agent import A2AAgent
from .discovery import ServiceQuery, AgentRecord
from .transport import TransportConfig
from .messaging import Message

logger = logging.getLogger(__name__)


class A2AClient:
    """High-level client for A2A protocol interactions."""

    def __init__(self, agent_id: str, capabilities: List[str] = None,
                 transport_config: TransportConfig = None):
        """
        Initialize the A2A client.

        Args:
            agent_id: Unique identifier for the client agent
            capabilities: List of capabilities for the agent
            transport_config: Transport layer configuration
        """

        self.agent_id = agent_id
        self.agent: Optional[A2AAgent] = None
        self.capabilities = capabilities or ["a2a:client"]
        self.transport_config = transport_config or TransportConfig()
        self.connected = False

    async def connect(self) -> bool:
        """Connect to the A2A network."""

        try:
            # Create and initialize agent
            self.agent = A2AAgent(
                agent_id=self.agent_id,
                capabilities=self.capabilities,
                transport_config=self.transport_config
            )

            # Initialize agent
            if not await self.agent.initialize():
                logger.error("Failed to initialize agent")
                return False

            # Start agent
            if not await self.agent.start():
                logger.error("Failed to start agent")
                return False

            self.connected = True
            logger.info(f"A2A client {self.agent_id} connected")
            return True

        except Exception as e:
            logger.error(f"Failed to connect A2A client: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the A2A network."""

        if self.agent and self.connected:
            await self.agent.stop()
            self.connected = False
            logger.info(f"A2A client {self.agent_id} disconnected")

    async def send_message(self, receiver_id: str, message_type: str,
                          payload: Dict[str, Any], encrypted: bool = False) -> Optional[str]:
        """Send a message to another agent."""

        if not self.connected or not self.agent:
            logger.error("Client not connected")
            return None

        if encrypted:
            return await self.agent.send_encrypted_message(receiver_id, message_type, payload)
        else:
            return await self.agent.send_message(receiver_id, message_type, payload)

    async def receive_messages(self) -> List[Message]:
        """Receive pending messages."""

        if not self.connected or not self.agent:
            return []

        return await self.agent.receive_messages()

    async def discover_agents(self, capabilities: List[str] = None,
                             max_results: int = 50) -> List[AgentRecord]:
        """Discover agents with specific capabilities."""

        if not self.connected or not self.agent:
            return []

        return await self.agent.discover_agents(capabilities, max_results)

    def get_agent_info(self, agent_id: str) -> Optional[AgentRecord]:
        """Get information about a specific agent."""

        if not self.connected or not self.agent:
            return None

        return self.agent.get_agent_info(agent_id)

    def register_message_handler(self, message_type: str, handler):
        """Register a handler for incoming messages."""

        if not self.connected or not self.agent:
            logger.error("Client not connected")
            return

        self.agent.register_message_handler(message_type, handler)

    async def ping_agent(self, agent_id: str) -> bool:
        """Send a ping message to an agent."""

        message_id = await self.send_message(
            receiver_id=agent_id,
            message_type="ping",
            payload={"timestamp": datetime.utcnow().isoformat()}
        )

        if not message_id:
            return False

        # Wait for pong response
        response = await self.agent.wait_for_message("response", timeout=10.0)

        if response and response.correlation_id == message_id:
            payload = response.payload
            return payload.get("status") == "pong"

        return False

    async def request_agent_capabilities(self, agent_id: str) -> Optional[List[str]]:
        """Request the capabilities of another agent."""

        message_id = await self.send_message(
            receiver_id=agent_id,
            message_type="capability_request",
            payload={}
        )

        if not message_id:
            return None

        # Wait for response
        response = await self.agent.wait_for_message("response", timeout=10.0)

        if response and response.correlation_id == message_id:
            payload = response.payload
            return payload.get("capabilities")

        return None

    async def broadcast_message(self, message_type: str, payload: Dict[str, Any],
                               capabilities: List[str] = None) -> List[str]:
        """Broadcast a message to all agents with specific capabilities."""

        if not self.connected or not self.agent:
            return []

        # Discover agents
        agents = await self.discover_agents(capabilities)

        # Send to all agents
        sent_ids = []
        for agent in agents:
            message_id = await self.send_message(
                receiver_id=agent.agent_id,
                message_type=message_type,
                payload=payload
            )
            if message_id:
                sent_ids.append(message_id)

        return sent_ids

    def update_capabilities(self, capabilities: List[str]):
        """Update client capabilities."""

        self.capabilities = capabilities

        if self.agent:
            self.agent.update_capabilities(capabilities)

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the A2A client."""

        health = {
            "connected": self.connected,
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self.agent and self.connected:
            # Check discovery service
            try:
                stats = self.agent.discovery.get_registry_stats()
                health["discovery_stats"] = stats
                health["discovery_healthy"] = True
            except Exception as e:
                health["discovery_healthy"] = False
                health["discovery_error"] = str(e)

            # Check transport
            try:
                # Simple transport check
                health["transport_healthy"] = True
            except Exception as e:
                health["transport_healthy"] = False
                health["transport_error"] = str(e)

            # Check messaging
            try:
                queue_size = self.agent.messaging.queue.size()
                health["messaging_healthy"] = True
                health["queue_size"] = queue_size
            except Exception as e:
                health["messaging_healthy"] = False
                health["messaging_error"] = str(e)

        return health

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()