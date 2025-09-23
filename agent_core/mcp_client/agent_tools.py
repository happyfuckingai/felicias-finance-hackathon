import asyncio
import logging
import json
import inspect
import typing
import subprocess
import sys
import os
from typing import Any, List, Dict, Callable, Optional, Awaitable, Sequence, Tuple, Type, Union, cast
from uuid import uuid4

# Import from the MCP module
from .util import MCPUtil, FunctionTool
from .server import MCPServer, MCPServerSse, MCPServerStdio, _MCPServerWithClientSession
from livekit.agents import ChatContext, AgentSession, JobContext, FunctionTool as Tool
from mcp import CallToolRequest
from contextlib import AbstractAsyncContextManager
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
import mcp.types
from mcp.types import CallToolResult, JSONRPCMessage
from mcp.client.stdio import stdio_client

logger = logging.getLogger("mcp-agent-tools")

class CryptoMCPServer(_MCPServerWithClientSession):
    """MCP server implementation for the crypto trading system."""

    def __init__(self, cache_tools_list: bool = True, name: str = "Crypto MCP Server"):
        """Create a new Crypto MCP server instance.

        Args:
            cache_tools_list: Whether to cache the tools list for better performance
            name: A readable name for the server
        """
        super().__init__(cache_tools_list)
        self._name = name
        self.process = None
        self.connected = False

    @property
    def name(self) -> str:
        """A readable name for the server."""
        return self._name

    async def connect(self):
        """Connect to the crypto MCP server by starting it as a subprocess."""
        if self.connected:
            return

        try:
            # Get the path to the crypto MCP server
            crypto_server_path = os.path.join(os.path.dirname(__file__), '..', 'crypto_mcp_server', 'crypto_mcp_server.py')

            # Ensure the path exists
            if not os.path.exists(crypto_server_path):
                raise FileNotFoundError(f"Crypto MCP server not found at: {crypto_server_path}")

            # Start the crypto MCP server as a subprocess
            self.process = await asyncio.create_subprocess_exec(
                sys.executable,
                crypto_server_path,
                '--stdio',  # Use stdio transport for local communication
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(crypto_server_path)
            )

            # Create stdio transport
            transport = await self.exit_stack.enter_async_context(
                stdio_client(self.process.stdout, self.process.stdin)
            )

            read, write = transport
            session = await self.exit_stack.enter_async_context(mcp.types.ClientSession(read, write))
            await session.initialize()
            self.session = session
            self.connected = True

            self.logger.info(f"Connected to Crypto MCP server: {self.name}")

        except Exception as e:
            self.logger.error(f"Error connecting to Crypto MCP server: {e}")
            await self.cleanup()
            raise

    async def cleanup(self):
        """Cleanup the crypto MCP server."""
        async with self._cleanup_lock:
            try:
                if self.process:
                    # Terminate the subprocess
                    self.process.terminate()
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        self.process.kill()
                        await self.process.wait()

                await super().cleanup()
                self.connected = False
                self.logger.info(f"Cleaned up Crypto MCP server: {self.name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up Crypto MCP server: {e}")

class MCPToolsIntegration:
    """
    Helper class for integrating MCP tools with LiveKit agents.
    Provides utilities for registering dynamic tools from MCP servers.
    """

    @staticmethod
    async def prepare_dynamic_tools(mcp_servers: List[MCPServer],
                                   convert_schemas_to_strict: bool = True,
                                   auto_connect: bool = True) -> List[Callable]:
        """
        Fetches tools from multiple MCP servers and prepares them for use with LiveKit agents.

        Args:
            mcp_servers: List of MCPServer instances
            convert_schemas_to_strict: Whether to convert JSON schemas to strict format
            auto_connect: Whether to automatically connect to servers if they're not connected

        Returns:
            List of decorated tool functions ready to be added to a LiveKit agent
        """
        prepared_tools = []

        # Ensure all servers are connected if auto_connect is True
        if auto_connect:
            for server in mcp_servers:
                if not getattr(server, 'connected', False):
                    try:
                        logger.debug(f"Auto-connecting to MCP server: {server.name}")
                        await server.connect()
                    except Exception as e:
                        logger.error(f"Failed to connect to MCP server {server.name}: {e}")

        # Process each server
        for server in mcp_servers:
            logger.info(f"Fetching tools from MCP server: {server.name}")
            try:
                mcp_tools = await MCPUtil.get_function_tools(
                    server, convert_schemas_to_strict=convert_schemas_to_strict
                )
                logger.info(f"Received {len(mcp_tools)} tools from {server.name}")
            except Exception as e:
                logger.error(f"Failed to fetch tools from {server.name}: {e}")
                continue

            # Process each tool from this server
            for tool_instance in mcp_tools:
                try:
                    decorated_tool = MCPToolsIntegration._create_decorated_tool(tool_instance)
                    prepared_tools.append(decorated_tool)
                    logger.debug(f"Successfully prepared tool: {tool_instance.name}")
                except Exception as e:
                    logger.error(f"Failed to prepare tool '{tool_instance.name}': {e}")

        return prepared_tools

    @staticmethod
    def _create_decorated_tool(tool: FunctionTool) -> Callable:
        """
        Creates a decorated function for a single MCP tool that can be used with LiveKit agents.

        Args:
            tool: The FunctionTool instance to convert

        Returns:
            A decorated async function that can be added to a LiveKit agent's tools
        """
        # Get function_tool decorator from LiveKit
        # Import locally to avoid circular imports
        from livekit.agents.llm import function_tool

        # Create parameters list from JSON schema
        params = []
        annotations = {}
        schema_props = tool.params_json_schema.get("properties", {})
        schema_required = set(tool.params_json_schema.get("required", []))
        type_map = {
            "string": str, "integer": int, "number": float,
            "boolean": bool, "array": list, "object": dict,
        }

        # Build parameters from the schema properties
        for p_name, p_details in schema_props.items():
            json_type = p_details.get("type", "string")
            py_type = type_map.get(json_type, typing.Any)
            annotations[p_name] = py_type

            # Use inspect.Parameter.empty for required params, None otherwise
            default = inspect.Parameter.empty if p_name in schema_required else p_details.get("default", None)
            params.append(inspect.Parameter(
                name=p_name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                annotation=py_type,
                default=default
            ))

        # Define the actual function that will be called by the agent
        async def tool_impl(**kwargs):
            input_json = json.dumps(kwargs)
            logger.info(f"Invoking tool '{tool.name}' with args: {kwargs}")
            result_str = await tool.on_invoke_tool(None, input_json)
            logger.info(f"Tool '{tool.name}' result: {result_str}")
            return result_str

        # Set function metadata
        tool_impl.__signature__ = inspect.Signature(parameters=params)
        tool_impl.__name__ = tool.name
        tool_impl.__doc__ = tool.description
        tool_impl.__annotations__ = {'return': str, **annotations}

        # Apply the decorator and return
        return function_tool()(tool_impl)

    @staticmethod
    async def register_with_agent(agent, mcp_servers: List[MCPServer],
                                 convert_schemas_to_strict: bool = True,
                                 auto_connect: bool = True) -> List[Callable]:
        """
        Helper method to prepare and register MCP tools with a LiveKit agent.

        Args:
            agent: The LiveKit agent instance
            mcp_servers: List of MCPServer instances
            convert_schemas_to_strict: Whether to convert schemas to strict format
            auto_connect: Whether to auto-connect to servers

        Returns:
            List of tool functions that were registered
        """
        # Prepare the dynamic tools
        tools = await MCPToolsIntegration.prepare_dynamic_tools(
            mcp_servers,
            convert_schemas_to_strict=convert_schemas_to_strict,
            auto_connect=auto_connect
        )

        # Register with the agent
        if hasattr(agent, '_tools') and isinstance(agent._tools, list):
            agent._tools.extend(tools)
            logger.info(f"Registered {len(tools)} MCP tools with agent")

            # Log the names of registered tools
            if tools:
                tool_names = [getattr(t, '__name__', 'unknown') for t in tools]
                logger.info(f"Registered tool names: {tool_names}")
        else:
            logger.warning("Agent does not have a '_tools' attribute, tools were not registered")

        return tools

    @staticmethod
    async def create_agent_with_tools(agent_class, mcp_servers: List[MCPServer], agent_kwargs: Dict = None,
                                    convert_schemas_to_strict: bool = True) -> Any:
        """
        Factory method to create and initialize an agent with MCP tools already loaded.

        Args:
            agent_class: Agent class to instantiate
            mcp_servers: List of MCP servers to register with the agent
            agent_kwargs: Additional keyword arguments to pass to the agent constructor
            convert_schemas_to_strict: Whether to convert JSON schemas to strict format

        Returns:
            An initialized agent instance with MCP tools registered
        """
        # Connect to MCP servers
        for server in mcp_servers:
            if not getattr(server, 'connected', False):
                try:
                    logger.debug(f"Connecting to MCP server: {server.name}")
                    await server.connect()
                except Exception as e:
                    logger.error(f"Failed to connect to MCP server {server.name}: {e}")

        # Create agent instance
        agent_kwargs = agent_kwargs or {}
        agent = agent_class(**agent_kwargs)

        # Prepare tools
        tools = await MCPToolsIntegration.prepare_dynamic_tools(
            mcp_servers,
            convert_schemas_to_strict=convert_schemas_to_strict,
            auto_connect=False  # Already connected above
        )

        # Register tools with agent
        if tools and hasattr(agent, '_tools') and isinstance(agent._tools, list):
            agent._tools.extend(tools)
            logger.info(f"Registered {len(tools)} MCP tools with agent")

            # Log the names of registered tools
            tool_names = [getattr(t, '__name__', 'unknown') for t in tools]
            logger.info(f"Registered tool names: {tool_names}")
        else:
            if not tools:
                logger.warning("No tools were found to register with the agent")
            else:
                logger.warning("Agent does not have a '_tools' attribute, tools were not registered")

        return agent

    @staticmethod
    async def create_crypto_mcp_server(cache_tools_list: bool = True, name: str = "Crypto MCP Server") -> CryptoMCPServer:
        """
        Factory method to create and initialize a Crypto MCP server instance.

        Args:
            cache_tools_list: Whether to cache the tools list for better performance
            name: A readable name for the server

        Returns:
            An initialized CryptoMCPServer instance
        """
        server = CryptoMCPServer(cache_tools_list=cache_tools_list, name=name)
        return server

    @staticmethod
    async def register_crypto_server_with_agent(agent, cache_tools_list: bool = True,
                                                auto_connect: bool = True) -> List[Callable]:
        """
        Helper method to create and register the Crypto MCP server with a LiveKit agent.

        Args:
            agent: The LiveKit agent instance
            cache_tools_list: Whether to cache the crypto server tools list
            auto_connect: Whether to automatically connect to the crypto server

        Returns:
            List of tool functions that were registered
        """
        # Create and connect to crypto MCP server
        crypto_server = await MCPToolsIntegration.create_crypto_mcp_server(cache_tools_list=cache_tools_list)

        if auto_connect:
            await crypto_server.connect()

        # Register with agent using the generic method
        return await MCPToolsIntegration.register_with_agent(agent, [crypto_server],
                                                           convert_schemas_to_strict=True,
                                                           auto_connect=False)
