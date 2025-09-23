"""
Main ADK Integration Class
Provides high-level interface for Google Cloud ADK integration
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from agents.adk_agent_wrapper import ADKAgentWrapper
from services.adk_service import ADKService
from config import ADKConfig


class ADKIntegration:
    """
    Main Google Cloud ADK Integration class for Felicia Finance

    This class provides a high-level interface to integrate Google Cloud ADK
    capabilities with the existing Felicia Finance multi-agent system.
    """

    def __init__(self, config_path: Optional[str] = None, agent_instance=None):
        """
        Initialize ADK Integration

        Args:
            config_path: Path to ADK configuration YAML file
            agent_instance: Existing LiveKit agent instance to wrap
        """
        self.config_path = config_path or str(Path(__file__).parent.parent / "config" / "adk_config.yaml")
        self.config = ADKConfig(self.config_path)
        self.agent_instance = agent_instance

        # Core services - initialize lazily
        self.adk_service = None
        self.agent_wrapper = None

        # Status tracking
        self._initialized = False
        self._initialization_attempted = False

        # Initialize logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=getattr(logging, self.config.logging.level),
            format=self.config.logging.format
        )

        self.logger.info("ADK Integration created (lazy initialization)")

    async def initialize(self) -> bool:
        """
        Initialize the ADK integration with lazy loading

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialization_attempted:
            return self._initialized

        self._initialization_attempted = True

        try:
            self.logger.info("Starting ADK integration initialization...")

            # Initialize ADK service lazily
            if self.adk_service is None:
                from services.adk_service import ADKService
                self.adk_service = ADKService(self.config_path)

            if not await self.adk_service.initialize():
                self.logger.warning("ADK service initialization failed - running in offline mode")
                # Continue without ADK service - graceful degradation

            # Initialize agent wrapper if agent provided
            if self.agent_instance and self.agent_wrapper is None:
                from agents.adk_agent_wrapper import ADKAgentWrapper
                self.agent_wrapper = ADKAgentWrapper(self.agent_instance, self.config_path)

                if not await self.agent_wrapper.initialize_adk():
                    self.logger.warning("ADK agent wrapper initialization failed - agent delegation disabled")
                    self.agent_wrapper = None

            self._initialized = True
            self.logger.info("ADK integration initialized successfully (with possible offline components)")
            return True

        except Exception as e:
            self.logger.warning(f"ADK integration initialization failed: {e} - running in offline mode")
            self._initialized = False
            return False

    async def execute_financial_workflow(self, workflow_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a financial workflow using ADK agents

        Args:
            workflow_name: Name of the workflow to execute
            data: Input data for the workflow

        Returns:
            Dict containing workflow execution results
        """
        if not self.agent_wrapper:
            return {"error": "No agent wrapper available"}

        return await self.agent_wrapper.execute_workflow(workflow_name, data)

    async def analyze_financial_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a financial query using the integrated ADK system

        Args:
            query: User's financial query

        Returns:
            Dict containing analysis results
        """
        if not self.agent_wrapper:
            return {"error": "No agent wrapper available"}

        return await self.agent_wrapper.get_financial_analysis(query)

    async def handle_banking_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle banking-specific requests (direct communication style)

        Args:
            request: Banking request data

        Returns:
            Dict containing banking operation results
        """
        return await self._handle_direct_agent_request("banking_agent", request)

    async def handle_crypto_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle crypto-specific requests (orchestrated multi-agent communication)

        Args:
            request: Crypto request data

        Returns:
            Dict containing crypto operation results
        """
        return await self._handle_orchestrated_agent_request("crypto_investment_bank", request)

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get the status of the entire ADK-integrated system

        Returns:
            Dict containing system status information
        """
        status = {
            "adk_integration": "active",
            "gcp_project": self.config.gcp.project_id,
            "region": self.config.gcp.region,
            "agents": {},
            "workflows": [w.name for w in self.config.workflows] if self.config.workflows else []
        }

        # Get agent statuses
        if self.agent_wrapper:
            agent_status = await self.agent_wrapper.get_system_status()
            status["agents"] = agent_status.get("agents", {})

        return status

    async def deploy_agent(self, agent_name: str, agent_config: Dict[str, Any]) -> Optional[str]:
        """
        Deploy a new agent to Google Cloud ADK

        Args:
            agent_name: Name of the agent
            agent_config: Agent configuration

        Returns:
            URL of deployed agent or None if failed
        """
        return await self.adk_service.deploy_adk_agent(agent_config)

    async def list_deployed_agents(self) -> List[Dict[str, Any]]:
        """
        List all deployed ADK agents

        Returns:
            List of deployed agent information
        """
        return await self.adk_service.list_agents()

    async def invoke_agent(self, agent_name: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Directly invoke an ADK-deployed agent

        Args:
            agent_name: Name of the agent to invoke
            payload: Data to send to the agent

        Returns:
            Agent response or None if failed
        """
        return await self.adk_service.invoke_agent(agent_name, payload)

    def register_workflow(self, workflow_config: Dict[str, Any]):
        """
        Register a new workflow

        Args:
            workflow_config: Workflow configuration
        """
        if self.agent_wrapper:
            steps = workflow_config.get("steps", [])
            self.agent_wrapper.register_custom_workflow(workflow_config["name"], steps)

    async def cleanup(self):
        """Clean up ADK resources"""
        # This would handle cleanup of deployed agents, etc.
        self.logger.info("ADK integration cleanup completed")

    # Convenience methods for common operations

    async def get_portfolio_analysis(self, user_id: str) -> Dict[str, Any]:
        """Get portfolio analysis across banking and crypto"""
        data = {"user_id": user_id}
        return await self.execute_financial_workflow("financial_analysis", data)

    async def execute_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a crypto trade"""
        return await self.handle_crypto_request({"query": "execute_trade", "data": trade_data})

    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get banking account balance"""
        return await self.handle_banking_request({"query": f"balance_{account_id}"})

    async def transfer_funds(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transfer funds between accounts"""
        return await self.handle_banking_request({"query": "transfer", "data": transfer_data})

    async def _handle_direct_agent_request(self, agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle direct communication with single-purpose agents (like banking)

        Args:
            agent_name: Name of the agent
            request: Request data

        Returns:
            Dict containing response
        """
        agent_config = self.config.get_agent_config(agent_name)
        if not agent_config:
            return {"error": f"Agent {agent_name} not configured"}

        # Direct communication - simple point-to-point
        if self.agent_wrapper:
            if agent_name == "banking_agent":
                return await self.agent_wrapper._invoke_direct_agent(
                    agent_name,
                    request.get("query", "status"),
                    request
                )

        return {"error": f"Direct communication not available for {agent_name}"}

    async def _handle_orchestrated_agent_request(self, agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle orchestrated communication with multi-agent teams (like crypto investment bank)

        Args:
            agent_name: Name of the multi-agent team
            request: Request data containing mission/strategy

        Returns:
            Dict containing orchestrated response with status updates
        """
        agent_config = self.config.get_agent_config(agent_name)
        if not agent_config:
            return {"error": f"Multi-agent team {agent_name} not configured"}

        # Orchestrated communication - complex multi-agent coordination
        mission = request.get("mission", request.get("query", ""))
        strategy_data = request.get("strategy", {})

        # Start orchestrated workflow
        workflow_data = {
            "mission": mission,
            "strategy": strategy_data,
            "team_members": [member.name for member in agent_config.team_members],
            "timestamp": "2025-01-01T00:00:00Z",  # Would use real timestamp
            "coordinator": "felicia_orchestrator"
        }

        # Create investment strategy workflow
        workflow_result = await self.execute_financial_workflow("investment_strategy_workflow", workflow_data)

        # For crypto requests, we expect ongoing status updates
        # In a real implementation, this would listen to an event bus
        return {
            "status": "orchestrated",
            "mission": mission,
            "team_activated": agent_config.name,
            "team_members": len(agent_config.team_members),
            "workflow_started": workflow_result.get("success", False),
            "estimated_completion": "TBD",  # Would be calculated based on complexity
            "progress_updates": [
                "Product Manager: Analyzing mission requirements...",
                "Architect: Designing investment strategy...",
                "Coordinator: Orchestrating team activities..."
            ]
        }

    async def get_investment_strategy(self, strategy_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request investment strategy from the crypto investment bank team

        Args:
            strategy_request: Investment strategy requirements

        Returns:
            Dict containing orchestrated strategy development
        """
        return await self._handle_orchestrated_agent_request("crypto_investment_bank", {
            "mission": "develop_investment_strategy",
            "strategy": strategy_request
        })

    async def execute_investment_trade(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute investment trade through the crypto investment bank team

        Args:
            trade_request: Trade execution parameters

        Returns:
            Dict containing orchestrated trade execution
        """
        return await self._handle_orchestrated_agent_request("crypto_investment_bank", {
            "mission": "execute_investment_trade",
            "strategy": trade_request
        })