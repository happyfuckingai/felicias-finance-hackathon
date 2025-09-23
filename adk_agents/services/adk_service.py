"""
Google Cloud ADK Service for Felicia Finance
Handles Google Cloud ADK integration and agent orchestration
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

import yaml
from google.auth import default
from google.cloud import aiplatform, functions_v2
from google.cloud.functions_v2 import FunctionServiceClient
from google.api_core.exceptions import GoogleAPICallError

from config import ADKConfig


class ADKService:
    """Google Cloud ADK Service for agent orchestration"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = ADKConfig(config_path)
        self.logger = logging.getLogger(__name__)

        # Initialize Google Cloud clients - deferred initialization
        self._credentials = None
        self._project_id = None
        self._aiplatform_client = None
        self._functions_client = None

        # Initialize on first use
        self._initialized = False
        self._initialization_failed = False

    async def initialize(self) -> bool:
        """Initialize Google Cloud ADK connections"""
        if self._initialization_failed:
            self.logger.warning("ADK Service initialization previously failed, skipping")
            return False

        try:
            # Get credentials and project ID with timeout
            self.logger.info("Attempting Google Cloud authentication...")
            self._credentials, self._project_id = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, default),
                timeout=10.0  # 10 second timeout
            )
            self.logger.info(f"Authenticated with project: {self._project_id}")

            # Initialize AI Platform client
            aiplatform.init(
                project=self.config.gcp.project_id,
                location=self.config.gcp.region,
                credentials=self._credentials
            )
            self._aiplatform_client = aiplatform

            # Initialize Cloud Functions client
            self._functions_client = FunctionServiceClient(
                credentials=self._credentials
            )

            self._initialized = True
            self.logger.info("ADK Service initialized successfully")
            return True

        except asyncio.TimeoutError:
            self.logger.warning("Google Cloud authentication timed out - running in offline mode")
            self._initialization_failed = True
            return False
        except Exception as e:
            self.logger.warning(f"Google Cloud authentication failed: {e} - running in offline mode")
            self._initialization_failed = True
            return False

    async def deploy_adk_agent(self, agent_config: Dict[str, Any]) -> Optional[str]:
        """Deploy an ADK agent as a Cloud Function"""
        if not self._initialized:
            await self.initialize()

        try:
            agent_name = agent_config.get("name", "felicia_agent")
            function_name = f"projects/{self._project_id}/locations/{self.config.gcp.region}/functions/{agent_name}"

            # Create function configuration
            function = functions_v2.Function()
            function.name = function_name
            function.description = agent_config.get("description", "Felicia Finance ADK Agent")

            # Set runtime and entry point
            function.runtime = "python310"
            function.entry_point = "handle_request"

            # Set source code (inline for simplicity - in production use GCS)
            source = functions_v2.Source()
            source.inline_source = self._generate_agent_code(agent_config)
            function.source = source

            # Set trigger (HTTP for now)
            function.https_trigger = functions_v2.HttpsTrigger()
            function.https_trigger.security_level = functions_v2.HttpsTrigger.SecurityLevel.SECURITY_LEVEL_SECURE_ALWAYS

            # Create the function
            operation = self._functions_client.create_function(
                request=functions_v2.CreateFunctionRequest(
                    location=f"projects/{self._project_id}/locations/{self.config.gcp.region}",
                    function=function,
                    function_id=agent_name
                )
            )

            # Wait for completion
            result = operation.result()
            self.logger.info(f"Deployed ADK agent: {result.name}")
            return result.https_trigger.url

        except GoogleAPICallError as e:
            self.logger.error(f"Failed to deploy ADK agent: {e}")
            return None

    async def invoke_agent(self, agent_name: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Invoke an ADK agent function"""
        if not self._initialized:
            await self.initialize()

        try:
            function_name = f"projects/{self._project_id}/locations/{self.config.gcp.region}/functions/{agent_name}"

            # Call the function
            response = self._functions_client.call_function(
                request=functions_v2.CallFunctionRequest(
                    name=function_name,
                    data=json.dumps(payload).encode("utf-8")
                )
            )

            result = json.loads(response.result)
            return result

        except Exception as e:
            self.logger.error(f"Failed to invoke agent {agent_name}: {e}")
            return None

    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all deployed ADK agents"""
        if not self._initialized:
            await self.initialize()

        try:
            functions = []
            request = functions_v2.ListFunctionsRequest(
                parent=f"projects/{self._project_id}/locations/{self.config.gcp.region}"
            )

            for function in self._functions_client.list_functions(request=request):
                functions.append({
                    "name": function.name,
                    "status": function.state.name,
                    "url": getattr(function.https_trigger, 'url', None) if hasattr(function, 'https_trigger') else None
                })

            return functions

        except Exception as e:
            self.logger.error(f"Failed to list agents: {e}")
            return []

    async def delete_agent(self, agent_name: str) -> bool:
        """Delete an ADK agent function"""
        if not self._initialized:
            await self.initialize()

        try:
            function_name = f"projects/{self._project_id}/locations/{self.config.gcp.region}/functions/{agent_name}"

            operation = self._functions_client.delete_function(
                request=functions_v2.DeleteFunctionRequest(name=function_name)
            )

            operation.result()  # Wait for completion
            self.logger.info(f"Deleted ADK agent: {agent_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete agent {agent_name}: {e}")
            return False

    def _generate_agent_code(self, agent_config: Dict[str, Any]) -> str:
        """Generate Python code for the ADK agent function"""
        agent_name = agent_config.get("name", "agent")
        capabilities = agent_config.get("capabilities", [])

        code = f'''"""
Auto-generated ADK Agent: {agent_name}
Generated by ADK Service
"""

import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_request(request) -> Dict[str, Any]:
    """Handle ADK agent request"""
    try:
        # Parse request data
        if hasattr(request, 'get_json'):
            data = request.get_json() or {{}}
        else:
            data = json.loads(request.data.decode('utf-8')) if request.data else {{}}

        action = data.get('action', 'status')
        logger.info(f"Processing action: {{action}} for agent: {agent_name}")

        # Route to appropriate handler based on capabilities
        capabilities = {capabilities}

        if action == 'status':
            return {{
                'agent': '{agent_name}',
                'status': 'active',
                'capabilities': capabilities,
                'timestamp': '2025-01-01T00:00:00Z'  # Would use real timestamp
            }}

        elif action == 'execute' and 'trading' in capabilities:
            return handle_trading_action(data)

        elif action == 'execute' and 'account_management' in capabilities:
            return handle_banking_action(data)

        else:
            return {{
                'error': f'Unsupported action: {{action}}',
                'supported_actions': ['status', 'execute'],
                'capabilities': capabilities
            }}

    except Exception as e:
        logger.error(f"Error processing request: {{e}}")
        return {{
            'error': str(e),
            'agent': '{agent_name}'
        }}


def handle_trading_action(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle trading-related actions"""
    # Placeholder for trading logic - would integrate with crypto MCP server
    return {{
        'action': 'trading',
        'result': 'Trading action processed',
        'data': data
    }}


def handle_banking_action(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle banking-related actions"""
    # Placeholder for banking logic - would integrate with bank MCP server
    return {{
        'action': 'banking',
        'result': 'Banking action processed',
        'data': data
    }}
'''

        return code