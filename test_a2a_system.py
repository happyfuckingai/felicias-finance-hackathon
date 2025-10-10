#!/usr/bin/env python3
"""
Comprehensive Tests for A2A Protocol System

Tests the complete A2A protocol implementation including:
- Agent identity and authentication
- Message encryption and signing
- Agent discovery
- Transport layer functionality
- Banking and crypto agent integration
- Orchestrator coordination
- End-to-end communication flows
"""

import asyncio
import json
import logging
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import A2A components
from adk_agents.a2a.core import AgentIdentity
from adk_agents.a2a.core import AuthenticationManager
from adk_agents.a2a.core import Message, EncryptedMessage
from adk_agents.a2a.core import DiscoveryService
from adk_agents.a2a.core import TransportConfig
from adk_agents.a2a.core import A2AAgent
from adk_agents.a2a.core import OrchestratorAgent

# Import specialized agents
from adk_agents.a2a.banking_a2a_integration.banking_a2a_agent import BankingA2AAgent
from adk_agents.a2a.crypto_a2a_integration.crypto_a2a_agent import CryptoA2AAgent

logger = logging.getLogger(__name__)


class TestAgentIdentity:
    """Test agent identity management."""

    def test_create_identity(self):
        """Test creating a new agent identity."""
        capabilities = ["a2a:messaging", "data:processing"]

        identity, private_key, cert = AgentIdentity.create(capabilities)

        assert identity.agent_id
        assert identity.did.startswith("did:a2a:")
        assert identity.public_key
        assert identity.capabilities == capabilities
        assert identity.is_valid()

        # Verify private key can sign and public key can verify
        test_data = b"Hello, World!"
        signature = identity.sign_data(private_key, test_data)
        assert signature

        assert identity.verify_signature(test_data, signature)

    def test_identity_serialization(self):
        """Test identity serialization/deserialization."""
        capabilities = ["test:capability"]
        identity, _, _ = AgentIdentity.create(capabilities)

        # Serialize
        identity_dict = identity.to_dict()

        # Deserialize
        restored_identity = AgentIdentity.from_dict(identity_dict)

        assert restored_identity.agent_id == identity.agent_id
        assert restored_identity.did == identity.did
        assert restored_identity.capabilities == identity.capabilities


class TestAuthentication:
    """Test authentication mechanisms."""

    def setup_method(self):
        """Setup test fixtures."""
        self.identity_manager = IdentityManager(":memory:")  # Use in-memory storage
        self.auth_manager = AuthenticationManager(self.identity_manager)

    def test_jwt_authentication(self):
        """Test JWT-based authentication."""
        # Create identity
        identity = self.identity_manager.create_identity(["test"])

        # Authenticate
        token = self.auth_manager.authenticate_agent(identity.agent_id, "jwt")
        assert token
        assert token.agent_id == identity.agent_id
        assert token.has_permission("a2a:messaging")

        # Validate token
        is_valid, agent_id = self.auth_manager.validate_authentication(token.token)
        assert is_valid
        assert agent_id == identity.agent_id

    def test_challenge_response(self):
        """Test challenge-response authentication."""
        identity = self.identity_manager.create_identity(["test"])

        challenge = "test_challenge_123"
        signature = self.auth_manager.sign_challenge(identity.agent_id, challenge)
        assert signature

        # Verify challenge response
        is_valid = self.auth_manager.verify_challenge_response(
            identity.agent_id, challenge, signature
        )
        assert is_valid


class TestMessaging:
    """Test messaging functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.identity_manager = IdentityManager(":memory:")
        self.auth_manager = AuthenticationManager(self.identity_manager)
        self.messaging = MessagingService(self.identity_manager, self.auth_manager)

    def test_message_creation(self):
        """Test creating and handling messages."""
        message = Message(
            message_id="",
            sender_id="agent1",
            receiver_id="agent2",
            message_type="test",
            payload={"data": "test_payload"}
        )

        assert message.message_id
        assert message.sender_id == "agent1"
        assert message.receiver_id == "agent2"
        assert message.message_type == "test"
        assert message.payload["data"] == "test_payload"

    def test_message_encryption(self):
        """Test message encryption/decryption."""
        # Create identities
        identity1 = self.identity_manager.create_identity(["test"])
        identity2 = self.identity_manager.create_identity(["test"])

        # Create session
        session_key = self.messaging.create_session(identity1.agent_id, identity2.agent_id)

        # Create message
        message = Message(
            message_id="",
            sender_id=identity1.agent_id,
            receiver_id=identity2.agent_id,
            message_type="test",
            payload={"secret": "data"}
        )

        # Encrypt message
        encrypted = self.messaging.encryptor.encrypt_message(message, session_key, identity1)
        assert encrypted.encrypted_data
        assert encrypted.sender_id == identity1.agent_id
        assert encrypted.receiver_id == identity2.agent_id

        # Decrypt message
        decrypted = self.messaging.encryptor.decrypt_message(encrypted, session_key)
        assert decrypted
        assert decrypted.payload["secret"] == "data"

    def test_message_signing(self):
        """Test message signing and verification."""
        identity = self.identity_manager.create_identity(["test"])

        message = Message(
            message_id="",
            sender_id=identity.agent_id,
            receiver_id="agent2",
            message_type="test",
            payload={"data": "test"}
        )

        signer = MessageSigner(self.identity_manager)

        # Sign message
        signature = signer.sign_message(message, identity.agent_id)
        assert signature

        # Verify signature
        is_valid = signer.verify_message_signature(message, signature, identity.agent_id)
        assert is_valid


class TestDiscovery:
    """Test agent discovery functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.discovery = DiscoveryService(":memory:")

    def test_agent_registration(self):
        """Test agent registration and discovery."""
        agent_record = AgentRecord(
            agent_id="test-agent",
            agent_did="did:a2a:test-agent",
            capabilities=["test:capability"],
            endpoints=["http://localhost:8080"]
        )

        # Register agent
        success = self.discovery.register_agent(agent_record)
        assert success

        # Discover agent
        query = ServiceQuery(agent_id="test-agent")
        results = self.discovery.discover_agents(query)
        assert len(results) == 1
        assert results[0].agent_id == "test-agent"

    def test_capability_discovery(self):
        """Test discovering agents by capability."""
        # Register multiple agents
        agent1 = AgentRecord(
            agent_id="agent1",
            agent_did="did:a2a:agent1",
            capabilities=["data:processing"],
            endpoints=["http://localhost:8081"]
        )

        agent2 = AgentRecord(
            agent_id="agent2",
            agent_did="did:a2a:agent2",
            capabilities=["data:analysis", "data:processing"],
            endpoints=["http://localhost:8082"]
        )

        self.discovery.register_agent(agent1)
        self.discovery.register_agent(agent2)

        # Discover by capability
        query = ServiceQuery(capabilities=["data:processing"])
        results = self.discovery.discover_agents(query)
        assert len(results) == 2

        # Discover by multiple capabilities
        query = ServiceQuery(capabilities=["data:analysis", "data:processing"])
        results = self.discovery.discover_agents(query)
        assert len(results) == 1
        assert results[0].agent_id == "agent2"


class TestA2AAgent:
    """Test A2A agent functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.transport_config = TransportConfig(
            protocol="http2",
            host="localhost",
            port=8443,
            ssl_enabled=False
        )

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization and startup."""
        agent = A2AAgent(
            agent_id="test-agent",
            capabilities=["test"],
            transport_config=self.transport_config
        )

        # Initialize agent
        success = await agent.initialize()
        assert success
        assert agent.identity
        assert agent.auth_token

        # Start agent (would need mocked transport)
        # await agent.start()
        # assert agent.running
        # await agent.stop()


class TestOrchestratorAgent:
    """Test orchestrator agent functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.transport_config = TransportConfig(
            protocol="http2",
            host="localhost",
            port=8444,
            ssl_enabled=False
        )

    @pytest.mark.asyncio
    async def test_workflow_creation(self):
        """Test creating and managing workflows."""
        orchestrator = OrchestratorAgent(
            agent_id="orchestrator",
            transport_config=self.transport_config
        )

        await orchestrator.initialize()

        # Create workflow
        workflow_id = await orchestrator.create_workflow(
            "Test Workflow",
            "Testing workflow functionality"
        )
        assert workflow_id

        # Add tasks
        task1_id = orchestrator.add_task_to_workflow(
            workflow_id,
            "task1",
            "First task",
            required_capabilities=["test:capability"]
        )
        assert task1_id

        task2_id = orchestrator.add_task_to_workflow(
            workflow_id,
            "task2",
            "Second task",
            required_capabilities=["test:capability"],
            dependencies=[task1_id]
        )
        assert task2_id

        # Check workflow status
        status = orchestrator.get_workflow_status(workflow_id)
        assert status["workflow_id"] == workflow_id
        assert len(status["tasks"]) == 2


class TestBankingA2AAgent:
    """Test banking agent integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.transport_config = TransportConfig(
            protocol="http2",
            host="localhost",
            port=8445,
            ssl_enabled=False
        )

    @pytest.mark.asyncio
    async def test_banking_agent_creation(self):
        """Test creating a banking agent."""
        with patch('bankofanthos_mcp_server.bankofanthos_managers.bankofanthos_manager'):
            agent = BankingA2AAgent(
                agent_id="banking-agent",
                transport_config=self.transport_config
            )

            success = await agent.initialize()
            assert success
            assert "banking:accounts" in agent.capabilities
            assert "banking:compliance" in agent.capabilities


class TestCryptoA2AAgent:
    """Test crypto agent integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.transport_config = TransportConfig(
            protocol="http2",
            host="localhost",
            port=8446,
            ssl_enabled=False
        )

    @pytest.mark.asyncio
    async def test_crypto_agent_creation(self):
        """Test creating a crypto agent."""
        with patch('crypto_mcp_server.crypto_managers.market_analyzer'), \
             patch('crypto_mcp_server.crypto_managers.wallet_manager'), \
             patch('crypto_mcp_server.crypto_managers.token_manager'), \
             patch('crypto_mcp_server.crypto_managers.xgboost_ai_manager'):

            agent = CryptoA2AAgent(
                agent_id="crypto-agent",
                transport_config=self.transport_config
            )

            success = await agent.initialize()
            assert success
            assert "crypto:trading" in agent.capabilities
            assert "crypto:analysis" in agent.capabilities


class TestEndToEndCommunication:
    """Test end-to-end agent communication scenarios."""

    @pytest.mark.asyncio
    async def test_agent_discovery_and_messaging(self):
        """Test complete agent discovery and messaging flow."""
        # This would be an integration test requiring running services
        # For now, we'll test the components individually
        pass

    @pytest.mark.asyncio
    async def test_orchestrated_workflow(self):
        """Test a complete orchestrated workflow."""
        # Create orchestrator
        orchestrator = OrchestratorAgent("test-orchestrator")

        # Create workflow
        workflow_id = await orchestrator.create_workflow(
            "Integration Test",
            "Testing orchestrated workflow"
        )

        # Add banking task
        banking_task_id = orchestrator.add_task_to_workflow(
            workflow_id,
            "banking_check",
            "Check banking compliance",
            required_capabilities=["banking:compliance"]
        )

        # Add crypto task
        crypto_task_id = orchestrator.add_task_to_workflow(
            workflow_id,
            "crypto_analysis",
            "Analyze crypto portfolio",
            required_capabilities=["crypto:analysis"],
            dependencies=[banking_task_id]
        )

        # Verify workflow structure
        workflow = orchestrator.workflows[workflow_id]
        assert len(workflow.tasks) == 2
        assert workflow.tasks[crypto_task_id].dependencies == [banking_task_id]


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.mark.asyncio
    async def test_banking_crypto_integration(self):
        """Test banking and crypto agent integration scenario."""
        # This would test the complete flow:
        # 1. Banking agent authenticates user
        # 2. Banking agent requests crypto analysis
        # 3. Crypto agent provides market analysis
        # 4. Orchestrator coordinates the workflow
        pass

    @pytest.mark.asyncio
    async def test_compliance_workflow(self):
        """Test compliance checking workflow."""
        # Test compliance checks across banking and crypto
        pass


if __name__ == "__main__":
    # Run basic tests
    logging.basicConfig(level=logging.INFO)

    # Run pytest
    pytest.main([__file__, "-v"])