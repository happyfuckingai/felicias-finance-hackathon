"""
Agent Discovery Service for A2A Protocol

Provides service registry and agent discovery mechanisms to locate and connect
with other agents in the A2A network.
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Set
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentRecord:
    """Record of an agent in the discovery service."""

    agent_id: str
    agent_did: str
    capabilities: List[str]
    endpoints: List[str]  # List of endpoint URLs
    metadata: Dict[str, Any]
    registered_at: datetime
    last_seen: datetime
    status: str = "active"  # "active", "inactive", "suspended"
    ttl: int = 300  # Time to live in seconds

    def __post_init__(self):
        if not isinstance(self.registered_at, datetime):
            self.registered_at = datetime.fromisoformat(self.registered_at) if isinstance(self.registered_at, str) else datetime.utcnow()
        if not isinstance(self.last_seen, datetime):
            self.last_seen = datetime.fromisoformat(self.last_seen) if isinstance(self.last_seen, str) else datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['registered_at'] = self.registered_at.isoformat()
        data['last_seen'] = self.last_seen.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentRecord':
        """Create from dictionary."""
        return cls(**data)

    def is_expired(self) -> bool:
        """Check if the record has expired."""
        return (datetime.utcnow() - self.last_seen).total_seconds() > self.ttl

    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities

    def update_last_seen(self):
        """Update the last seen timestamp."""
        self.last_seen = datetime.utcnow()


@dataclass
class ServiceQuery:
    """Query for discovering agents."""

    capabilities: Optional[List[str]] = None
    agent_id: Optional[str] = None
    status: Optional[str] = "active"
    max_results: int = 50
    include_metadata: bool = False


class DiscoveryService:
    """Central service registry for A2A agent discovery."""

    def __init__(self, registry_file: str = "agent_registry.json"):
        self.registry_file = registry_file
        self.agents: Dict[str, AgentRecord] = {}
        self.capability_index: Dict[str, Set[str]] = {}  # capability -> set of agent_ids
        self.running = False
        self.cleanup_task: Optional[asyncio.Task] = None

        # Load existing registry
        self._load_registry()

    def start(self):
        """Start the discovery service."""
        self.running = True
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_agents())
        logger.info("Discovery service started")

    def stop(self):
        """Stop the discovery service."""
        self.running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
        self._save_registry()
        logger.info("Discovery service stopped")

    def register_agent(self, agent_record: AgentRecord) -> bool:
        """Register an agent with the discovery service."""

        agent_id = agent_record.agent_id

        # Update existing or add new
        if agent_id in self.agents:
            # Update existing record
            existing = self.agents[agent_id]
            existing.endpoints = agent_record.endpoints
            existing.capabilities = agent_record.capabilities
            existing.metadata = agent_record.metadata
            existing.last_seen = datetime.utcnow()
            existing.status = agent_record.status
            existing.ttl = agent_record.ttl
        else:
            # Add new record
            agent_record.registered_at = datetime.utcnow()
            self.agents[agent_id] = agent_record

        # Update capability index
        self._update_capability_index(agent_id, agent_record.capabilities)

        # Save to disk
        self._save_registry()

        logger.info(f"Registered agent: {agent_id}")
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the discovery service."""

        if agent_id not in self.agents:
            return False

        # Remove from capability index
        capabilities = self.agents[agent_id].capabilities
        for capability in capabilities:
            if capability in self.capability_index:
                self.capability_index[capability].discard(agent_id)
                if not self.capability_index[capability]:
                    del self.capability_index[capability]

        # Remove agent
        del self.agents[agent_id]

        # Save to disk
        self._save_registry()

        logger.info(f"Unregistered agent: {agent_id}")
        return True

    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update an agent's status."""

        if agent_id not in self.agents:
            return False

        self.agents[agent_id].status = status
        self.agents[agent_id].last_seen = datetime.utcnow()

        self._save_registry()
        return True

    def heartbeat(self, agent_id: str) -> bool:
        """Update agent's last seen timestamp."""

        if agent_id not in self.agents:
            return False

        self.agents[agent_id].update_last_seen()
        return True

    def discover_agents(self, query: ServiceQuery) -> List[AgentRecord]:
        """Discover agents matching the query criteria."""

        candidates = list(self.agents.values())

        # Filter by agent_id
        if query.agent_id:
            candidates = [agent for agent in candidates if agent.agent_id == query.agent_id]

        # Filter by status
        if query.status:
            candidates = [agent for agent in candidates if agent.status == query.status]

        # Filter by capabilities
        if query.capabilities:
            filtered = []
            for agent in candidates:
                if all(agent.has_capability(cap) for cap in query.capabilities):
                    filtered.append(agent)
            candidates = filtered

        # Remove expired agents
        candidates = [agent for agent in candidates if not agent.is_expired()]

        # Limit results
        candidates = candidates[:query.max_results]

        # Remove metadata if not requested
        if not query.include_metadata:
            for agent in candidates:
                agent.metadata = {}

        return candidates

    def get_agent_record(self, agent_id: str) -> Optional[AgentRecord]:
        """Get a specific agent's record."""

        agent = self.agents.get(agent_id)
        if agent and not agent.is_expired():
            return agent
        return None

    def get_agents_by_capability(self, capability: str) -> List[AgentRecord]:
        """Get all agents with a specific capability."""

        agent_ids = self.capability_index.get(capability, set())
        agents = []

        for agent_id in agent_ids:
            agent = self.agents.get(agent_id)
            if agent and not agent.is_expired() and agent.status == "active":
                agents.append(agent)

        return agents

    def get_all_capabilities(self) -> List[str]:
        """Get all available capabilities in the registry."""

        return list(self.capability_index.keys())

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent registry."""

        total_agents = len(self.agents)
        active_agents = len([a for a in self.agents.values() if a.status == "active" and not a.is_expired()])
        capabilities = len(self.capability_index)

        # Count agents by status
        status_counts = {}
        for agent in self.agents.values():
            if not agent.is_expired():
                status_counts[agent.status] = status_counts.get(agent.status, 0) + 1

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_capabilities": capabilities,
            "status_counts": status_counts
        }

    def _update_capability_index(self, agent_id: str, capabilities: List[str]):
        """Update the capability index for an agent."""

        # Remove old capabilities
        for cap_set in self.capability_index.values():
            cap_set.discard(agent_id)

        # Add new capabilities
        for capability in capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = set()
            self.capability_index[capability].add(agent_id)

        # Clean up empty capability sets
        empty_caps = [cap for cap, agents in self.capability_index.items() if not agents]
        for cap in empty_caps:
            del self.capability_index[cap]

    async def _cleanup_expired_agents(self):
        """Periodically clean up expired agent records."""

        while self.running:
            try:
                await asyncio.sleep(60)  # Clean up every minute

                expired_agents = []
                for agent_id, agent in self.agents.items():
                    if agent.is_expired():
                        expired_agents.append(agent_id)

                for agent_id in expired_agents:
                    logger.info(f"Removing expired agent: {agent_id}")
                    self.unregister_agent(agent_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def _load_registry(self):
        """Load agent registry from disk."""

        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)

            for agent_data in data.get('agents', []):
                try:
                    agent = AgentRecord.from_dict(agent_data)
                    if not agent.is_expired():
                        self.agents[agent.agent_id] = agent
                        self._update_capability_index(agent.agent_id, agent.capabilities)
                except Exception as e:
                    logger.error(f"Error loading agent record: {e}")

            logger.info(f"Loaded {len(self.agents)} agents from registry")

        except FileNotFoundError:
            logger.info("No existing registry file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading registry: {e}")

    def _save_registry(self):
        """Save agent registry to disk."""

        try:
            data = {
                'agents': [agent.to_dict() for agent in self.agents.values()],
                'last_updated': datetime.utcnow().isoformat()
            }

            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving registry: {e}")


class PeerDiscoveryService:
    """Peer-to-peer agent discovery for decentralized networks."""

    def __init__(self, local_agent_id: str, known_peers: List[str] = None):
        self.local_agent_id = local_agent_id
        self.known_peers = set(known_peers or [])
        self.discovered_agents: Dict[str, AgentRecord] = {}
        self.broadcast_addresses: List[str] = []
        self.running = False
        self.discovery_task: Optional[asyncio.Task] = None

    def add_broadcast_address(self, address: str):
        """Add a broadcast address for peer discovery."""
        if address not in self.broadcast_addresses:
            self.broadcast_addresses.append(address)

    def add_known_peer(self, peer_address: str):
        """Add a known peer for bootstrapping."""
        self.known_peers.add(peer_address)

    async def start_discovery(self):
        """Start peer discovery process."""
        self.running = True
        self.discovery_task = asyncio.create_task(self._discovery_loop())
        logger.info("Peer discovery started")

    async def stop_discovery(self):
        """Stop peer discovery process."""
        self.running = False
        if self.discovery_task:
            self.discovery_task.cancel()

    async def broadcast_presence(self):
        """Broadcast local agent presence to network."""

        presence_message = {
            "type": "agent_presence",
            "agent_id": self.local_agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # In a real implementation, this would use UDP broadcast
        # For now, we'll simulate by logging
        logger.debug(f"Broadcasting presence: {presence_message}")

    async def query_peers(self, query: ServiceQuery) -> List[AgentRecord]:
        """Query known peers for agents matching criteria."""

        results = []

        # Query known peers (simplified - would make actual network calls)
        for peer in self.known_peers:
            try:
                # In a real implementation:
                # agents = await self._query_peer(peer, query)
                # results.extend(agents)
                pass
            except Exception as e:
                logger.error(f"Error querying peer {peer}: {e}")

        return results

    async def _discovery_loop(self):
        """Main discovery loop."""

        while self.running:
            try:
                # Broadcast presence
                await self.broadcast_presence()

                # Query known peers for updates
                # (Implementation would go here)

                await asyncio.sleep(30)  # Discover every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
                await asyncio.sleep(5)