"""
ADK Configuration Loader
Loads and validates ADK configuration from YAML files
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import yaml
from pydantic import BaseModel, Field


class GCPConfig(BaseModel):
    """Google Cloud Platform configuration"""
    project_id: str = Field(..., description="GCP Project ID")
    region: str = Field(default="us-central1", description="GCP Region")
    service_account: Optional[str] = Field(default=None, description="Service Account Email")


class ADKConfigModel(BaseModel):
    """ADK Agent configuration"""
    agent_name: str = Field(..., description="Agent name")
    description: str = Field(default="", description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version")


class TeamMember(BaseModel):
    """Team member configuration for multi-agent teams"""
    name: str = Field(..., description="Team member name")
    role: str = Field(..., description="Team member role")


class AgentConfig(BaseModel):
    """Individual agent configuration"""
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type (mcp_server, adk_agent, multi_agent_team, etc.)")
    endpoint: Optional[str] = Field(default=None, description="Agent endpoint URL")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    communication_style: str = Field(default="direct", description="Communication style (direct, orchestrated)")
    team_members: List[TeamMember] = Field(default_factory=list, description="Team members for multi-agent systems")


class WorkflowStep(BaseModel):
    """Workflow step configuration"""
    agent: str = Field(..., description="Agent name to execute step")
    action: str = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class WorkflowConfig(BaseModel):
    """Workflow configuration"""
    name: str = Field(..., description="Workflow name")
    steps: List[WorkflowStep] = Field(default_factory=list, description="Workflow steps")


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")


class FeliciaADKConfig(BaseModel):
    """Complete Felicia ADK configuration"""
    gcp: GCPConfig = Field(..., description="GCP configuration")
    adk: ADKConfigModel = Field(..., description="ADK configuration")
    agents: Dict[str, AgentConfig] = Field(default_factory=dict, description="Agent configurations")
    workflows: List[WorkflowConfig] = Field(default_factory=list, description="Workflow configurations")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")


@dataclass
class ADKConfig:
    """ADK Configuration Manager"""

    config_path: Optional[str] = None
    _config: Optional[FeliciaADKConfig] = None

    def __post_init__(self):
        if self.config_path is None:
            # Default config path
            self.config_path = Path(__file__).parent / "adk_config.yaml"

        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(self.config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Convert agents dict to proper format
        if 'agents' in config_data:
            agents_dict = {}
            for agent_name, agent_data in config_data['agents'].items():
                agents_dict[agent_name] = AgentConfig(**agent_data)
            config_data['agents'] = agents_dict

        # Convert workflows list
        if 'workflows' in config_data:
            workflows_list = []
            for workflow_data in config_data['workflows']:
                steps = []
                for step_data in workflow_data.get('steps', []):
                    steps.append(WorkflowStep(**step_data))
                workflow_data['steps'] = steps
                workflows_list.append(WorkflowConfig(**workflow_data))
            config_data['workflows'] = workflows_list

        self._config = FeliciaADKConfig(**config_data)

    @property
    def gcp(self) -> GCPConfig:
        """Get GCP configuration"""
        return self._config.gcp

    @property
    def adk(self) -> ADKConfigModel:
        """Get ADK configuration"""
        return self._config.adk

    @property
    def agents(self) -> Dict[str, AgentConfig]:
        """Get agents configuration"""
        return self._config.agents

    @property
    def workflows(self) -> List[WorkflowConfig]:
        """Get workflows configuration"""
        return self._config.workflows

    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration"""
        return self._config.logging

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent"""
        return self.agents.get(agent_name)

    def get_workflow_config(self, workflow_name: str) -> Optional[WorkflowConfig]:
        """Get configuration for a specific workflow"""
        for workflow in self.workflows:
            if workflow.name == workflow_name:
                return workflow
        return None

    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to YAML file"""
        save_path = Path(config_path or self.config_path)

        # Convert back to dict format for YAML serialization
        config_dict = self._config.model_dump()

        # Convert agents back to dict
        if 'agents' in config_dict:
            agents_data = {}
            for agent_name, agent_config in config_dict['agents'].items():
                agents_data[agent_name] = agent_config
            config_dict['agents'] = agents_data

        # Convert workflows back to list of dicts
        if 'workflows' in config_dict:
            workflows_data = []
            for workflow in config_dict['workflows']:
                workflow_dict = workflow.copy()
                workflow_dict['steps'] = [step.model_dump() for step in workflow['steps']]
                workflows_data.append(workflow_dict)
            config_dict['workflows'] = workflows_data

        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)