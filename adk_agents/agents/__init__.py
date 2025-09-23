"""
Felicia Finance Agent Implementations
Individual agents with LLM capabilities for the ADK integration
"""

from .banking_agent import BankingAgent
from .product_manager_agent import ProductManagerAgent
from .architect_agent import ArchitectAgent
from .implementation_agent import ImplementationAgent
from .quality_assurance_agent import QualityAssuranceAgent
from .coordinator_agent import CoordinatorAgent
from .adk_agent_wrapper import ADKAgentWrapper

__all__ = [
    'BankingAgent',
    'ProductManagerAgent',
    'ArchitectAgent',
    'ImplementationAgent',
    'QualityAssuranceAgent',
    'CoordinatorAgent',
    'ADKAgentWrapper'
]