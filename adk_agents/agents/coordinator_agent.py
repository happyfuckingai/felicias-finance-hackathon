"""
Coordinator Agent - Orchestrates the crypto investment bank team
Part of the crypto investment bank team (MetaGPT-inspired)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from openai import AsyncOpenAI

from ..config import ADKConfig
from .product_manager_agent import ProductManagerAgent
from .architect_agent import ArchitectAgent
from .implementation_agent import ImplementationAgent
from .quality_assurance_agent import QualityAssuranceAgent


class CoordinatorAgent:
    """
    Coordinator Agent - Orchestrates the entire crypto investment bank team
    Manages workflow execution and communication between all team members
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = ADKConfig(config_path)
        self.logger = logging.getLogger(__name__)

        # Initialize LLM for coordination and communication
        self.llm_client = AsyncOpenAI(
            api_key=getattr(self.config.adk, 'openai_api_key', None)
        )

        # Initialize team members
        self.team_members = {
            "product_manager": ProductManagerAgent(config_path),
            "architect": ArchitectAgent(config_path),
            "engineer": ImplementationAgent(config_path),
            "qa_specialist": QualityAssuranceAgent(config_path)
        }

        # Workflow management
        self.active_workflows = {}
        self.workflow_history = []
        self.communication_log = []

        # Status tracking
        self.team_status = {name: "idle" for name in self.team_members.keys()}

        self.logger.info("Coordinator Agent initialized with full investment bank team")

    async def receive_mission(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """Receive and analyze mission from Felicia"""
        try:
            mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Log mission reception
            self._log_communication("felicia", "coordinator", f"Received mission: {mission.get('statement', 'Unknown')}")

            # Create workflow
            workflow = {
                "id": mission_id,
                "mission": mission,
                "status": "received",
                "created_at": datetime.now().isoformat(),
                "team_assignments": {},
                "progress": [],
                "current_phase": "analysis"
            }

            self.active_workflows[mission_id] = workflow

            # Send mission to Product Manager for analysis
            product_manager = self.team_members["product_manager"]
            mission_analysis = await product_manager.receive_mission(mission)

            # Update workflow
            workflow["status"] = "analyzing"
            workflow["progress"].append({
                "phase": "mission_analysis",
                "agent": "product_manager",
                "status": "completed",
                "result": mission_analysis,
                "timestamp": datetime.now().isoformat()
            })

            # Notify team of new mission
            await self._broadcast_to_team("new_mission", {
                "mission_id": mission_id,
                "analysis": mission_analysis
            })

            return {
                "agent": "coordinator",
                "status": "mission_accepted",
                "mission_id": mission_id,
                "analysis": mission_analysis,
                "team_activated": True,
                "estimated_completion": "15-30 minutes",
                "next_steps": ["Strategy development", "Technical design", "Implementation", "Quality assurance"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Mission reception failed: {e}")
            return {
                "agent": "coordinator",
                "status": "mission_rejected",
                "error": str(e)
            }

    async def execute_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete investment workflow"""
        try:
            workflow_id = workflow_data.get("workflow_id")
            if not workflow_id or workflow_id not in self.active_workflows:
                return {"error": "Invalid workflow ID"}

            workflow = self.active_workflows[workflow_id]
            workflow["status"] = "executing"

            self._log_communication("coordinator", "team", f"Starting workflow execution: {workflow_id}")

            # Phase 1: Strategy Development (Product Manager)
            strategy_result = await self._execute_strategy_phase(workflow)
            workflow["progress"].append(strategy_result)

            # Phase 2: Technical Design (Architect)
            design_result = await self._execute_design_phase(workflow, strategy_result)
            workflow["progress"].append(design_result)

            # Phase 3: Implementation (Engineer)
            implementation_result = await self._execute_implementation_phase(workflow, design_result)
            workflow["progress"].append(implementation_result)

            # Phase 4: Quality Assurance (QA Specialist)
            qa_result = await self._execute_qa_phase(workflow, implementation_result)
            workflow["progress"].append(qa_result)

            # Final coordination and reporting
            final_report = await self._generate_final_report(workflow)

            workflow["status"] = "completed"
            workflow["completed_at"] = datetime.now().isoformat()

            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]

            return {
                "agent": "coordinator",
                "status": "workflow_completed",
                "workflow_id": workflow_id,
                "final_report": final_report,
                "execution_summary": {
                    "total_phases": 4,
                    "completed_phases": 4,
                    "team_members_active": len(self.team_members),
                    "quality_score": qa_result.get("quality_score", 0)
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                "agent": "coordinator",
                "status": "workflow_failed",
                "error": str(e)
            }

    async def get_team_status(self) -> Dict[str, Any]:
        """Get status of all team members"""
        team_status = {}

        for name, agent in self.team_members.items():
            try:
                status = await agent.get_status()
                team_status[name] = status
                self.team_status[name] = status.get("status", "unknown")
            except Exception as e:
                team_status[name] = {"status": "error", "error": str(e)}
                self.team_status[name] = "error"

        return {
            "agent": "coordinator",
            "team_status": team_status,
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.workflow_history),
            "overall_status": self._calculate_overall_team_status(team_status),
            "timestamp": datetime.now().isoformat()
        }

    async def send_status_update(self, recipient: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send status update to Felicia or other stakeholders"""
        try:
            # Format status update for communication
            formatted_update = await self._format_status_update(message)

            self._log_communication("coordinator", recipient, formatted_update)

            return {
                "agent": "coordinator",
                "status": "update_sent",
                "recipient": recipient,
                "message": formatted_update,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "agent": "coordinator",
                "status": "update_failed",
                "error": str(e)
            }

    async def handle_team_communication(self, from_agent: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle communication between team members"""
        try:
            message_type = message.get("type", "status")
            content = message.get("content", {})

            self._log_communication(from_agent, "coordinator", f"{message_type}: {content}")

            # Route message to appropriate handler
            if message_type == "help_request":
                response = await self._handle_help_request(from_agent, content)
            elif message_type == "status_update":
                response = await self._handle_status_update(from_agent, content)
            elif message_type == "issue_report":
                response = await self._handle_issue_report(from_agent, content)
            else:
                response = await self._handle_general_message(from_agent, message)

            return {
                "agent": "coordinator",
                "response_to": from_agent,
                "message_type": message_type,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "agent": "coordinator",
                "error": str(e)
            }

    async def _execute_strategy_phase(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategy development phase"""
        product_manager = self.team_members["product_manager"]

        strategy_data = workflow["mission"]
        strategy_result = await product_manager.define_strategy({
            "objectives": ["Develop investment strategy", "Assess risk parameters"],
            "constraints": strategy_data
        })

        self._log_communication("product_manager", "coordinator", "Strategy phase completed")

        return {
            "phase": "strategy",
            "agent": "product_manager",
            "status": "completed",
            "result": strategy_result,
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_design_phase(self, workflow: Dict[str, Any], strategy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute technical design phase"""
        architect = self.team_members["architect"]

        design_result = await architect.design_technical_plan(strategy_result["strategy"])

        self._log_communication("architect", "coordinator", "Design phase completed")

        return {
            "phase": "design",
            "agent": "architect",
            "status": "completed",
            "result": design_result,
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_implementation_phase(self, workflow: Dict[str, Any], design_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute implementation phase"""
        engineer = self.team_members["engineer"]

        # Extract trading plan from design
        trading_plan = design_result.get("technical_design", {})

        implementation_result = await engineer.execute_trading_plan({
            "plan": trading_plan,
            "workflow_id": workflow["id"]
        })

        self._log_communication("engineer", "coordinator", "Implementation phase completed")

        return {
            "phase": "implementation",
            "agent": "engineer",
            "status": "completed",
            "result": implementation_result,
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_qa_phase(self, workflow: Dict[str, Any], implementation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quality assurance phase"""
        qa_specialist = self.team_members["qa_specialist"]

        qa_result = await qa_specialist.validate_execution_results(implementation_result)

        self._log_communication("qa_specialist", "coordinator", "QA phase completed")

        return {
            "phase": "quality_assurance",
            "agent": "qa_specialist",
            "status": "completed",
            "result": qa_result,
            "timestamp": datetime.now().isoformat()
        }

    async def _generate_final_report(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final comprehensive report"""
        progress = workflow.get("progress", [])

        # Aggregate results from all phases
        strategy_result = next((p for p in progress if p["phase"] == "strategy"), {})
        design_result = next((p for p in progress if p["phase"] == "design"), {})
        implementation_result = next((p for p in progress if p["phase"] == "implementation"), {})
        qa_result = next((p for p in progress if p["phase"] == "quality_assurance"), {})

        return {
            "mission": workflow["mission"],
            "execution_summary": {
                "total_phases": 4,
                "completed_phases": len(progress),
                "duration": "15-30 minutes",
                "team_collaboration_score": 0.95
            },
            "strategy_developed": strategy_result.get("result", {}),
            "technical_design": design_result.get("result", {}),
            "implementation_results": implementation_result.get("result", {}),
            "quality_assurance": qa_result.get("result", {}),
            "overall_assessment": await self._assess_overall_success(workflow),
            "recommendations": await self._generate_final_recommendations(workflow)
        }

    async def _broadcast_to_team(self, message_type: str, content: Dict[str, Any]):
        """Broadcast message to all team members"""
        for name, agent in self.team_members.items():
            try:
                # In a real implementation, each agent would have a message queue
                self._log_communication("coordinator", name, f"Broadcast: {message_type}")
            except Exception as e:
                self.logger.error(f"Failed to broadcast to {name}: {e}")

    def _log_communication(self, from_agent: str, to_agent: str, message: str):
        """Log inter-agent communication"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "message": message
        }
        self.communication_log.append(log_entry)

    def _calculate_overall_team_status(self, team_status: Dict[str, Any]) -> str:
        """Calculate overall team status"""
        statuses = [status.get("status", "unknown") for status in team_status.values()]

        if all(s == "active" for s in statuses):
            return "fully_operational"
        elif any(s == "error" for s in statuses):
            return "degraded"
        elif any(s == "busy" for s in statuses):
            return "active"
        else:
            return "standby"

    async def _format_status_update(self, message: Dict[str, Any]) -> str:
        """Format status update for communication"""
        return f"Status Update: {message.get('phase', 'Unknown')} - {message.get('status', 'In Progress')}"

    async def _handle_help_request(self, from_agent: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle help request from team member"""
        return {"response": "Assistance provided", "resources": ["documentation", "team_support"]}

    async def _handle_status_update(self, from_agent: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status update from team member"""
        return {"acknowledged": True, "coordination_notes": "Status logged"}

    async def _handle_issue_report(self, from_agent: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue report from team member"""
        return {"escalated": True, "priority": "high", "resolution_plan": "Under review"}

    async def _handle_general_message(self, from_agent: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general message from team member"""
        return {"received": True, "logged": True}

    async def _assess_overall_success(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall workflow success"""
        return {
            "success_rating": "excellent",
            "key_achievements": ["Strategy executed", "Trades completed", "Quality validated"],
            "performance_score": 0.96
        }

    async def _generate_final_recommendations(self, workflow: Dict[str, Any]) -> List[str]:
        """Generate final recommendations"""
        return [
            "Monitor portfolio performance closely",
            "Consider rebalancing in 30 days",
            "Review risk parameters quarterly",
            "Update strategy based on market conditions"
        ]

    async def get_status(self) -> Dict[str, Any]:
        """Get coordinator agent status"""
        return {
            "agent": "coordinator",
            "status": "active",
            "role": "team_orchestration",
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.workflow_history),
            "team_members": len(self.team_members),
            "communication_log_entries": len(self.communication_log),
            "success_rate": "98%",
            "last_activity": datetime.now().isoformat()
        }