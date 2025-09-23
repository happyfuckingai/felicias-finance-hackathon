#!/usr/bin/env python3
"""
Example demonstrating how to use the Crypto MCP Server with LiveKit agents.

This example shows how to:
1. Create a Crypto MCP server instance
2. Register it with a LiveKit agent
3. Use the integrated risk management and trading tools
"""

import asyncio
import logging
from agent_tools import MCPToolsIntegration, CryptoMCPServer
from livekit.agents import Agent, Room
from livekit.agents.llm import ChatContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main example demonstrating crypto MCP integration."""

    logger.info("🚀 Starting Crypto MCP Agent Example")

    try:
        # Method 1: Use the convenience method to create and register crypto server
        logger.info("📡 Creating Crypto MCP server...")
        crypto_server = await MCPToolsIntegration.create_crypto_mcp_server()

        # Method 2: Alternatively, load from config
        # from config_loader import load_mcp_servers_from_config
        # servers = load_mcp_servers_from_config()
        # crypto_server = next((s for s in servers if isinstance(s, CryptoMCPServer)), None)

        if not crypto_server:
            logger.error("❌ Crypto MCP server not found")
            return

        # Connect to the crypto server
        logger.info("🔗 Connecting to crypto server...")
        await crypto_server.connect()

        # List available tools
        tools = await crypto_server.list_tools()
        logger.info(f"🛠️  Available tools: {len(tools)}")
        for tool in tools:
            logger.info(f"   ✅ {tool.name}: {tool.description}")

        # Create a simple agent for demonstration
        agent = Agent(
            name="Crypto Risk Agent",
            instructions="""
            You are an advanced crypto trading assistant with comprehensive risk management capabilities.
            You can analyze portfolios, calculate VaR, optimize position sizes, and generate risk recommendations.
            Always emphasize risk management in your trading advice.
            """
        )

        # Register crypto tools with the agent
        logger.info("🔧 Registering crypto tools with agent...")
        registered_tools = await MCPToolsIntegration.register_crypto_server_with_agent(
            agent, auto_connect=False
        )

        logger.info(f"✅ Successfully registered {len(registered_tools)} crypto tools")

        # Example of using the tools (this would normally be done through chat)
        logger.info("💡 Example usage:")
        logger.info("   - assess_portfolio_risk: Analyze portfolio risk with VaR models")
        logger.info("   - calculate_var: Calculate Value-at-Risk for specific tokens")
        logger.info("   - optimize_position_size: Get optimal position sizing recommendations")
        logger.info("   - analyze_portfolio_metrics: Get Sharpe/Sortino ratios and other metrics")
        logger.info("   - generate_risk_recommendations: Get AI-driven risk management advice")

        # Cleanup
        await crypto_server.cleanup()
        logger.info("🧹 Cleanup completed")

    except Exception as e:
        logger.error(f"❌ Error in crypto agent example: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())