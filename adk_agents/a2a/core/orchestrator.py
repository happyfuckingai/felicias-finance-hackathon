"""
Orchestrator Agent for A2A Protocol

Provides coordination and orchestration capabilities for multi-agent systems,
managing workflows, task delegation, and agent collaboration.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .agent import A2AAgent
from .discovery import AgentRecord, ServiceQuery
from .messaging import Message
from .transport import TransportConfig

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a task in the workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    """Status of a workflow."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task in a workflow."""

    task_id: str
    task_type: str
    description: str
    assigned_agent: Optional[str] = None
    required_capabilities: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Task IDs this task depends on
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None

    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if this task is ready to run (all dependencies completed)."""
        return all(dep in completed_tasks for dep in self.dependencies)

    def mark_started(self):
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: Any = None):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def mark_failed(self, error_message: str):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message


@dataclass
class Workflow:
    """Represents a multi-agent workflow."""

    workflow_id: str
    name: str
    description: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)  # Shared context between tasks

    def add_task(self, task: Task):
        """Add a task to the workflow."""
        self.tasks[task.task_id] = task

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to run."""
        completed_task_ids = {
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED
        }

        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING and task.is_ready(completed_task_ids)
        ]

    def get_running_tasks(self) -> List[Task]:
        """Get currently running tasks."""
        return [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]

    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return all(task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                  for task in self.tasks.values())

    def get_completion_percentage(self) -> float:
        """Get workflow completion percentage."""
        if not self.tasks:
            return 100.0

        completed = sum(1 for task in self.tasks.values()
                       if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED])
        return (completed / len(self.tasks)) * 100.0


class OrchestratorAgent(A2AAgent):
    """Agent that orchestrates multi-agent workflows and task delegation."""

    def __init__(self, agent_id: str, transport_config: TransportConfig = None):
        """Initialize the orchestrator agent."""

        super().__init__(
            agent_id=agent_id,
            capabilities=["a2a:orchestrator", "a2a:coordination", "a2a:workflow"],
            transport_config=transport_config
        )

        self.workflows: Dict[str, Workflow] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        self.agent_capabilities: Dict[str, List[str]] = {}  # Cache of agent capabilities

    async def initialize(self) -> bool:
        """Initialize the orchestrator agent."""

        success = await super().initialize()
        if not success:
            return False

        # Register orchestrator-specific message handlers
        self._register_orchestrator_handlers()

        return True

    def _register_orchestrator_handlers(self):
        """Register handlers for orchestrator-specific messages."""

        async def handle_task_assignment(message: Message, auth_token):
            """Handle task assignment responses."""
            payload = message.payload
            task_id = payload.get("task_id")
            status = payload.get("status")

            if task_id in self.task_assignments:
                workflow_id = None
                for wf in self.workflows.values():
                    if task_id in wf.tasks:
                        workflow_id = wf.workflow_id
                        break

                if workflow_id:
                    await self._handle_task_response(workflow_id, task_id, payload)

        async def handle_workflow_status_request(message: Message, auth_token):
            """Handle workflow status requests."""
            workflow_id = message.payload.get("workflow_id")

            if workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]
                status_response = {
                    "workflow_id": workflow_id,
                    "status": workflow.status.value,
                    "completion_percentage": workflow.get_completion_percentage(),
                    "tasks": {
                        task_id: {
                            "status": task.status.value,
                            "assigned_agent": task.assigned_agent,
                            "started_at": task.started_at.isoformat() if task.started_at else None,
                            "completed_at": task.completed_at.isoformat() if task.completed_at else None
                        }
                        for task_id, task in workflow.tasks.items()
                    }
                }

                response = message.create_response(status_response)
                # Send response back to requester

        async def handle_capability_update(message: Message, auth_token):
            """Handle capability updates from agents."""
            agent_id = message.sender_id
            capabilities = message.payload.get("capabilities", [])

            self.agent_capabilities[agent_id] = capabilities
            logger.info(f"Updated capabilities for agent {agent_id}: {capabilities}")

        self.register_message_handler("task_response", handle_task_assignment)
        self.register_message_handler("workflow_status_request", handle_workflow_status_request)
        self.register_message_handler("capability_update", handle_capability_update)

    async def create_workflow(self, name: str, description: str,
                             context: Dict[str, Any] = None) -> str:
        """Create a new workflow."""

        workflow_id = f"wf_{len(self.workflows) + 1}"
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            context=context or {}
        )

        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow: {workflow_id}")
        return workflow_id

    def add_task_to_workflow(self, workflow_id: str, task_type: str, description: str,
                           required_capabilities: List[str] = None,
                           parameters: Dict[str, Any] = None,
                           dependencies: List[str] = None) -> Optional[str]:
        """Add a task to a workflow."""

        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return None

        workflow = self.workflows[workflow_id]
        task_id = f"task_{workflow_id}_{len(workflow.tasks) + 1}"

        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            required_capabilities=required_capabilities or [],
            parameters=parameters or {},
            dependencies=dependencies or []
        )

        workflow.add_task(task)
        logger.info(f"Added task {task_id} to workflow {workflow_id}")
        return task_id

    async def start_workflow(self, workflow_id: str) -> bool:
        """Start executing a workflow."""

        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return False

        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()

        # Start workflow execution
        asyncio.create_task(self._execute_workflow(workflow_id))

        logger.info(f"Started workflow: {workflow_id}")
        return True

    async def _execute_workflow(self, workflow_id: str):
        """Execute a workflow by managing task assignments and dependencies."""

        workflow = self.workflows[workflow_id]

        try:
            while not workflow.is_completed():
                # Get ready tasks
                ready_tasks = workflow.get_ready_tasks()

                if not ready_tasks:
                    # Check if there are still running tasks
                    running_tasks = workflow.get_running_tasks()
                    if not running_tasks:
                        # No ready or running tasks, workflow might be stuck
                        logger.warning(f"Workflow {workflow_id} has no ready or running tasks")
                        break

                    # Wait for running tasks to complete
                    await asyncio.sleep(1)
                    continue

                # Assign and start ready tasks
                for task in ready_tasks:
                    await self._assign_and_start_task(workflow, task)

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.5)

            # Mark workflow as completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            logger.info(f"Workflow {workflow_id} completed")

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            logger.error(f"Workflow {workflow_id} failed: {e}")

    async def _assign_and_start_task(self, workflow: Workflow, task: Task):
        """Assign a task to an appropriate agent and start it."""

        # Find suitable agent
        suitable_agents = await self._find_suitable_agents(task.required_capabilities)

        if not suitable_agents:
            logger.error(f"No suitable agents found for task {task.task_id} with capabilities {task.required_capabilities}")
            task.mark_failed("No suitable agents available")
            return

        # Assign to first available agent (could implement load balancing)
        assigned_agent = suitable_agents[0].agent_id
        task.assigned_agent = assigned_agent
        self.task_assignments[task.task_id] = assigned_agent

        # Send task assignment
        assignment_payload = {
            "workflow_id": workflow.workflow_id,
            "task_id": task.task_id,
            "task_type": task.task_type,
            "description": task.description,
            "parameters": task.parameters,
            "context": workflow.context
        }

        message_id = await self.send_message(
            receiver_id=assigned_agent,
            message_type="task_assignment",
            payload=assignment_payload
        )

        if message_id:
            task.mark_started()
            logger.info(f"Assigned task {task.task_id} to agent {assigned_agent}")
        else:
            task.mark_failed("Failed to send task assignment")

    async def _handle_task_response(self, workflow_id: str, task_id: str, payload: Dict[str, Any]):
        """Handle a task response from an agent."""

        workflow = self.workflows[workflow_id]
        task = workflow.tasks[task_id]

        status = payload.get("status")
        result = payload.get("result")
        error = payload.get("error")

        if status == "completed":
            task.mark_completed(result)
            # Update workflow context with task result
            workflow.context[f"task_{task_id}_result"] = result
            logger.info(f"Task {task_id} completed successfully")
        elif status == "failed":
            task.mark_failed(error or "Task failed")
            logger.error(f"Task {task_id} failed: {error}")

        # Clean up assignment
        if task_id in self.task_assignments:
            del self.task_assignments[task_id]

    async def _find_suitable_agents(self, required_capabilities: List[str]) -> List[AgentRecord]:
        """Find agents that have the required capabilities."""

        # Discover agents with required capabilities
        agents = await self.discover_agents(required_capabilities)

        # Filter out this orchestrator agent
        agents = [agent for agent in agents if agent.agent_id != self.agent_id]

        return agents

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow."""

        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]

        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "completion_percentage": workflow.get_completion_percentage(),
            "task_count": len(workflow.tasks),
            "context": workflow.context
        }

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows."""

        return [
            self.get_workflow_status(wf_id)
            for wf_id in self.workflows.keys()
        ]

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""

        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows[workflow_id]

        if workflow.status != WorkflowStatus.RUNNING:
            return False

        # Cancel all running tasks
        for task in workflow.tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                # Notify assigned agent to cancel task
                if task.assigned_agent:
                    await self.send_message(
                        receiver_id=task.assigned_agent,
                        message_type="task_cancellation",
                        payload={"task_id": task.task_id}
                    )

        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.utcnow()

        logger.info(f"Cancelled workflow: {workflow_id}")
        return True

    async def update_agent_capabilities(self, agent_id: str, capabilities: List[str]):
        """Update cached capabilities for an agent."""

        self.agent_capabilities[agent_id] = capabilities

        # Broadcast capability update to other agents
        await self.send_message(
            receiver_id=agent_id,  # This might need to be broadcast
            message_type="capability_update",
            payload={"capabilities": capabilities}
        )