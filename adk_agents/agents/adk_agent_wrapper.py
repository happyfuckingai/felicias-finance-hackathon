"""
ADK Agent Wrapper for Felicia Finance
Wraps the existing LiveKit agent with Google Cloud ADK capabilities
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from config import ADKConfig
from services.adk_service import ADKService


class ADKAgentWrapper:
    """Wrapper to integrate existing LiveKit agent with Google Cloud ADK"""

    def __init__(self, agent_instance, config_path: Optional[str] = None):
        self.agent = agent_instance  # The existing LiveKit agent
        self.config = ADKConfig(config_path)
        self.adk_service = ADKService(config_path)
        self.logger = logging.getLogger(__name__)

        # ADK-specific state
        self.adk_agents = {}
        self.workflows = {}

        # Initialize logging
        logging.basicConfig(
            level=getattr(logging, self.config.logging.level),
            format=self.config.logging.format
        )

    async def initialize_adk(self) -> bool:
        """Initialize ADK integration"""
        try:
            # Initialize ADK service
            if not await self.adk_service.initialize():
                self.logger.error("Failed to initialize ADK service")
                return False

            # Deploy configured agents
            for agent_name, agent_config in self.config.agents.items():
                await self._deploy_adk_agent(agent_name, agent_config)

            # Register workflows
            for workflow_config in self.config.workflows:
                self.workflows[workflow_config.name] = workflow_config

            self.logger.info("ADK integration initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize ADK integration: {e}")
            return False

    async def _deploy_adk_agent(self, agent_name: str, agent_config: Any):
        """Deploy an agent to ADK"""
        agent_data = {
            "name": agent_config.name,
            "description": f"ADK wrapper for {agent_config.name}",
            "capabilities": agent_config.capabilities,
            "type": agent_config.type,
            "endpoint": agent_config.endpoint
        }

        # Deploy to Google Cloud Functions
        adk_url = await self.adk_service.deploy_adk_agent(agent_data)

        if adk_url:
            self.adk_agents[agent_name] = {
                "config": agent_config,
                "adk_url": adk_url,
                "status": "active"
            }
            self.logger.info(f"Deployed ADK agent: {agent_name} at {adk_url}")
        else:
            self.logger.error(f"Failed to deploy ADK agent: {agent_name}")

    async def execute_workflow(self, workflow_name: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow using ADK agents"""
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return {"error": f"Workflow not found: {workflow_name}"}

        results = {}
        current_data = initial_data.copy()

        try:
            for step in workflow.steps:
                step_result = await self._execute_workflow_step(step, current_data)
                results[step.action] = step_result

                # Update data for next step
                if isinstance(step_result, dict):
                    current_data.update(step_result)

            return {
                "success": True,
                "workflow": workflow_name,
                "results": results,
                "final_data": current_data
            }

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "workflow": workflow_name,
                "error": str(e),
                "partial_results": results
            }

    async def _execute_workflow_step(self, step: Any, data: Dict[str, Any]) -> Any:
        """Execute a single workflow step"""
        agent_name = step.agent
        action = step.action

        # Check if it's an ADK-deployed agent
        if agent_name in self.adk_agents:
            return await self._invoke_adk_agent(agent_name, action, data)
        else:
            # Fall back to direct agent invocation
            return await self._invoke_direct_agent(agent_name, action, data)

    async def _invoke_adk_agent(self, agent_name: str, action: str, data: Dict[str, Any]) -> Any:
        """Invoke an agent through ADK"""
        agent_info = self.adk_agents.get(agent_name)
        if not agent_info:
            raise ValueError(f"ADK agent not found: {agent_name}")

        payload = {
            "action": action,
            "data": data,
            "agent": agent_name
        }

        result = await self.adk_service.invoke_agent(agent_name, payload)
        return result

    async def _invoke_direct_agent(self, agent_name: str, action: str, data: Dict[str, Any]) -> Any:
        """Invoke an agent directly (for MCP servers)"""
        agent_config = self.config.get_agent_config(agent_name)
        if not agent_config or not agent_config.endpoint:
            raise ValueError(f"Agent configuration not found: {agent_name}")

        # For MCP servers, we would use HTTP client to call the endpoint
        # This is a placeholder - actual implementation would depend on MCP protocol
        import httpx

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{agent_config.endpoint}/execute",
                    json={
                        "action": action,
                        "data": data
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                self.logger.error(f"Direct agent invocation failed: {e}")
                raise

    async def get_financial_analysis(self, user_query: str) -> Dict[str, Any]:
        """Execute financial analysis workflow"""
        # Prepare initial data
        initial_data = {
            "query": user_query,
            "timestamp": "2025-01-01T00:00:00Z",  # Would use real timestamp
            "user_id": "felicia_user"
        }

        # Execute the financial analysis workflow
        result = await self.execute_workflow("financial_analysis", initial_data)

        # Add additional processing from the original agent
        if self.agent and hasattr(self.agent, 'process_financial_query'):
            enhanced_result = await self.agent.process_financial_query(user_query, result)
            return enhanced_result

        return result

    async def handle_banking_query(self, query: str) -> Dict[str, Any]:
        """Handle banking-specific queries"""
        return await self._invoke_adk_agent("banking_agent", "query", {"query": query})

    async def handle_crypto_query(self, query: str) -> Dict[str, Any]:
        """Handle crypto-specific queries"""
        return await self._invoke_adk_agent("crypto_agent", "query", {"query": query})

    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all agents and ADK integration"""
        status = {
            "adk_service": "active" if self.adk_service._initialized else "inactive",
            "agents": {},
            "workflows": list(self.workflows.keys())
        }

        # Check status of each deployed agent
        for agent_name, agent_info in self.adk_agents.items():
            agent_status = await self._check_agent_status(agent_name)
            status["agents"][agent_name] = {
                "status": agent_status,
                "adk_url": agent_info.get("adk_url"),
                "capabilities": agent_info["config"].capabilities
            }

        return status

    async def _check_agent_status(self, agent_name: str) -> str:
        """Check the status of an ADK agent"""
        try:
            result = await self.adk_service.invoke_agent(agent_name, {"action": "status"})
            return "active" if result and not result.get("error") else "error"
        except Exception:
            return "inactive"

    def register_custom_workflow(self, name: str, steps: List[Dict[str, Any]]):
        """Register a custom workflow"""
        workflow_steps = []
        for step_data in steps:
            workflow_steps.append(type('WorkflowStep', (), step_data)())

        workflow = type('WorkflowConfig', (), {
            "name": name,
            "steps": workflow_steps
        })()

        self.workflows[name] = workflow
        self.logger.info(f"Registered custom workflow: {name}")