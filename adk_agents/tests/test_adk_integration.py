"""
Tests for ADK Integration
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from adk.adk_integration import ADKIntegration
from config import ADKConfig


class TestADKIntegration:
    """Test cases for ADK Integration"""

    @pytest.fixture
    def mock_config(self):
        """Mock ADK configuration"""
        config = Mock()
        config.gcp.project_id = "test-project"
        config.gcp.region = "us-central1"
        config.logging.level = "INFO"
        config.workflows = []
        return config

    @pytest.fixture
    def mock_agent(self):
        """Mock LiveKit agent"""
        agent = Mock()
        agent.process_financial_query = AsyncMock(return_value={"result": "processed"})
        return agent

    @patch('adk_integration.services.adk_service.ADKService')
    @patch('adk_integration.agents.adk_agent_wrapper.ADKAgentWrapper')
    def test_initialization(self, mock_wrapper, mock_service, mock_config, mock_agent):
        """Test ADK integration initialization"""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.initialize = AsyncMock(return_value=True)
        mock_service.return_value = mock_service_instance

        mock_wrapper_instance = Mock()
        mock_wrapper_instance.initialize_adk = AsyncMock(return_value=True)
        mock_wrapper.return_value = mock_wrapper_instance

        # Create integration
        integration = ADKIntegration(config_path="test_config.yaml", agent_instance=mock_agent)

        # Test initialization
        result = asyncio.run(integration.initialize())
        assert result is True

        # Verify service initialization was called
        mock_service_instance.initialize.assert_called_once()
        mock_wrapper_instance.initialize_adk.assert_called_once()

    @patch('adk_integration.services.adk_service.ADKService')
    def test_financial_analysis(self, mock_service, mock_config, mock_agent):
        """Test financial analysis workflow"""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        mock_wrapper = Mock()
        mock_wrapper.get_financial_analysis = AsyncMock(return_value={
            "analysis": "complete",
            "insights": ["insight1", "insight2"]
        })

        with patch('adk_integration.agents.adk_agent_wrapper.ADKAgentWrapper', return_value=mock_wrapper):
            integration = ADKIntegration(agent_instance=mock_agent)

            # Test analysis
            result = asyncio.run(integration.analyze_financial_query("What is my portfolio worth?"))

            assert result["analysis"] == "complete"
            assert len(result["insights"]) == 2
            mock_wrapper.get_financial_analysis.assert_called_once_with("What is my portfolio worth?")

    @patch('adk_integration.services.adk_service.ADKService')
    def test_system_status(self, mock_service, mock_config, mock_agent):
        """Test system status retrieval"""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        mock_wrapper = Mock()
        mock_wrapper.get_system_status = AsyncMock(return_value={
            "adk_service": "active",
            "agents": {"banking_agent": {"status": "active"}},
            "workflows": ["financial_analysis"]
        })

        with patch('adk_integration.agents.adk_agent_wrapper.ADKAgentWrapper', return_value=mock_wrapper):
            integration = ADKIntegration(agent_instance=mock_agent)

            # Test status
            status = asyncio.run(integration.get_system_status())

            assert status["adk_integration"] == "active"
            assert "banking_agent" in status["agents"]
            mock_wrapper.get_system_status.assert_called_once()

    @patch('adk_integration.services.adk_service.ADKService')
    def test_agent_deployment(self, mock_service, mock_config):
        """Test agent deployment"""
        # Setup mock service
        mock_service_instance = Mock()
        mock_service_instance.deploy_adk_agent = AsyncMock(return_value="https://test-function-url")
        mock_service.return_value = mock_service_instance

        integration = ADKIntegration()

        # Test deployment
        agent_config = {
            "name": "test_agent",
            "description": "Test agent",
            "capabilities": ["test"]
        }

        result = asyncio.run(integration.deploy_agent("test_agent", agent_config))

        assert result == "https://test-function-url"
        mock_service_instance.deploy_adk_agent.assert_called_once_with(agent_config)

    @patch('adk_integration.services.adk_service.ADKService')
    def test_workflow_execution(self, mock_service, mock_config, mock_agent):
        """Test workflow execution"""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        mock_wrapper = Mock()
        mock_wrapper.execute_workflow = AsyncMock(return_value={
            "success": True,
            "results": {"step1": "result1"}
        })

        with patch('adk_integration.agents.adk_agent_wrapper.ADKAgentWrapper', return_value=mock_wrapper):
            integration = ADKIntegration(agent_instance=mock_agent)

            # Test workflow execution
            result = asyncio.run(integration.execute_financial_workflow("test_workflow", {"data": "test"}))

            assert result["success"] is True
            assert "step1" in result["results"]
            mock_wrapper.execute_workflow.assert_called_once_with("test_workflow", {"data": "test"})


if __name__ == "__main__":
    # Run basic functionality test
    async def test_basic_functionality():
        print("Testing basic ADK integration functionality...")

        try:
            # Test configuration loading
            config = ADKConfig()
            print(f"✓ Configuration loaded: {config.gcp.project_id}")

            # Test ADK service initialization (will fail without GCP credentials, but tests structure)
            adk_service = ADKService()
            print("✓ ADK service created")

            print("✓ Basic functionality test passed")

        except Exception as e:
            print(f"✗ Basic functionality test failed: {e}")

    asyncio.run(test_basic_functionality())