#!/usr/bin/env python3
"""
AI Risk Management Agent for LiveKit

This agent provides conversational AI-driven risk management for crypto trading.
It integrates with the MCP server to access all risk management tools and
can dynamically create visual components in the frontend.

Features:
- Natural language risk analysis
- Portfolio risk monitoring
- VaR calculations and explanations
- Position sizing recommendations
- Risk alerts and notifications
- Dynamic frontend component creation
- Real-time risk updates

Usage:
    python crypto/ai_risk_agent.py
"""

import os
import sys
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add crypto module to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# LiveKit imports
from livekit import api
from livekit.agents import AgentSession, Agent, Room
from livekit.agents.llm import ChatContext

# MCP integration
from mcp_client.agent_tools import MCPToolsIntegration, CryptoMCPServer

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIRiskAgent:
    """AI-powered Risk Management Agent for LiveKit"""

    def __init__(self):
        self.livekit_url = os.getenv('LIVEKIT_URL')
        self.api_key = os.getenv('LIVEKIT_API_KEY')
        self.api_secret = os.getenv('LIVEKIT_API_SECRET')
        self.mcp_server = None
        self.agent = None

        # Validate LiveKit configuration
        if not all([self.livekit_url, self.api_key, self.api_secret]):
            raise ValueError("Missing LiveKit configuration. Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET")

    async def initialize_mcp_server(self):
        """Initialize and connect to the crypto MCP server"""
        logger.info("🔗 Initializing Crypto MCP Server...")

        try:
            self.mcp_server = await MCPToolsIntegration.create_crypto_mcp_server()
            await self.mcp_server.connect()
            logger.info("✅ Crypto MCP Server connected successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP server: {e}")
            raise

    async def create_agent(self):
        """Create the LiveKit agent with MCP tools"""
        logger.info("🤖 Creating AI Risk Management Agent...")

        # Initialize MCP server first
        await self.initialize_mcp_server()

        # Create agent with comprehensive risk management capabilities
        self.agent = Agent(
            name="AI Risk Manager",
            instructions=self.get_agent_instructions(),
            tools=[]
        )

        # Register crypto MCP tools with the agent
        logger.info("🛠️ Registering risk management tools...")
        registered_tools = await MCPToolsIntegration.register_crypto_server_with_agent(
            self.agent, auto_connect=False
        )

        logger.info(f"✅ Registered {len(registered_tools)} risk management tools")

        return self.agent

    def get_agent_instructions(self):
        """Get comprehensive agent instructions for risk management"""
        return """
        You are an advanced AI Risk Management Agent specializing in cryptocurrency trading risk assessment and portfolio optimization.

        ## Core Capabilities
        - Portfolio risk analysis with VaR calculations
        - Position sizing optimization using Kelly Criterion
        - Real-time risk monitoring and alerts
        - Market risk assessment and recommendations
        - Dynamic visual component creation for risk dashboards

        ## Risk Management Tools Available
        - assess_portfolio_risk: Comprehensive portfolio risk assessment
        - calculate_var: Value-at-Risk calculations (Historical, Parametric, Monte Carlo)
        - optimize_position_size: Kelly Criterion and Risk Parity position sizing
        - analyze_portfolio_metrics: Sharpe/Sortino ratios, drawdown analysis
        - generate_risk_recommendations: AI-driven risk management advice

        ## Communication Style
        - Explain complex risk concepts in simple, understandable terms
        - Always provide risk warnings when appropriate
        - Suggest visual components when showing data
        - Use emojis to make responses more engaging
        - Be proactive about risk management

        ## Visual Component Creation
        When users want to see risk data visually, create components like:
        - PortfolioRiskDashboard: Real-time risk monitoring
        - VaRCalculator: Interactive VaR calculations
        - RiskAlertsPanel: Risk alerts and notifications
        - PositionSizer: Position size optimization

        ## Risk Assessment Framework
        Always consider:
        - Portfolio diversification
        - Market volatility
        - Liquidity risk
        - Counterparty risk
        - Regulatory compliance

        ## Emergency Protocols
        If extreme risk conditions are detected:
        - Immediately alert the user
        - Suggest risk mitigation strategies
        - Recommend position adjustments
        - Create visual risk alerts

        Remember: Risk management is about protecting capital while optimizing returns.
        """

    async def create_frontend_component(self, component_type: str, props: dict = None):
        """Create a frontend component dynamically"""
        component_config = {
            "type": "component",
            "componentName": component_type,
            "props": props or {},
            "timestamp": "2025-09-19T01:22:00Z"
        }

        logger.info(f"🎨 Creating frontend component: {component_type}")
        return component_config

    async def handle_risk_query(self, query: str):
        """Handle natural language risk management queries"""
        logger.info(f"📊 Processing risk query: {query}")

        # This would integrate with the agent's natural language processing
        # For now, return a structured response that can be used by the agent

        return {
            "query": query,
            "analysis_type": "risk_assessment",
            "requires_visualization": True,
            "suggested_components": ["PortfolioRiskDashboard", "VaRCalculator"]
        }

    async def generate_risk_report(self, portfolio_data: dict):
        """Generate a comprehensive risk report"""
        logger.info("📈 Generating comprehensive risk report...")

        try:
            # Use MCP tools to gather risk data
            if self.mcp_server:
                # Get portfolio risk assessment
                risk_assessment = await self.mcp_server.call_tool(
                    "assess_portfolio_risk",
                    {"portfolio_json": portfolio_data}
                )

                # Calculate VaR for major holdings
                var_calculations = []
                for holding in portfolio_data.get('holdings', []):
                    var_result = await self.mcp_server.call_tool(
                        "calculate_var",
                        {
                            "token_id": holding.get('token_id', 'BTC'),
                            "portfolio_value": portfolio_data.get('total_value', 10000)
                        }
                    )
                    var_calculations.append(var_result)

                # Generate recommendations
                recommendations = await self.mcp_server.call_tool(
                    "generate_risk_recommendations",
                    {"portfolio_json": portfolio_data}
                )

                return {
                    "risk_assessment": risk_assessment,
                    "var_calculations": var_calculations,
                    "recommendations": recommendations,
                    "generated_at": "2025-09-19T01:22:00Z"
                }
            else:
                raise ValueError("MCP server not initialized")

        except Exception as e:
            logger.error(f"❌ Error generating risk report: {e}")
            return {"error": str(e)}

    async def start_room_session(self, room_name: str = "risk-management-room"):
        """Start a LiveKit room session"""
        logger.info(f"🏠 Starting LiveKit room: {room_name}")

        try:
            # Connect to LiveKit
            room = Room(self.livekit_url, self.api_key, self.api_secret)
            await room.connect()

            # Create agent session
            session = AgentSession(room, self.agent)

            logger.info("✅ LiveKit session started successfully")
            return session

        except Exception as e:
            logger.error(f"❌ Failed to start LiveKit session: {e}")
            raise

    async def run_interactive_demo(self):
        """Run an interactive demo of the AI risk agent"""
        logger.info("🎯 Starting AI Risk Agent Interactive Demo")

        try:
            # Create agent
            await self.create_agent()

            # Start room session
            session = await self.start_room_session()

            # Demo portfolio data
            demo_portfolio = {
                "holdings": [
                    {"token_id": "BTC", "amount": 0.5, "current_price": 45000},
                    {"token_id": "ETH", "amount": 8.0, "current_price": 3000},
                    {"token_id": "ADA", "amount": 10000, "current_price": 0.5}
                ],
                "total_value": 100000
            }

            # Generate demo risk report
            logger.info("📊 Generating demo risk report...")
            risk_report = await self.generate_risk_report(demo_portfolio)

            logger.info("✅ Demo risk report generated successfully")
            logger.info(f"📈 Risk Report Summary: {len(risk_report)} sections")

            # Create frontend components
            dashboard_component = await self.create_frontend_component(
                "PortfolioRiskDashboard",
                {"portfolioData": demo_portfolio}
            )

            var_component = await self.create_frontend_component(
                "VaRCalculator",
                {"tokenId": "BTC"}
            )

            logger.info("🎨 Frontend components created for visualization")

            return {
                "session": session,
                "risk_report": risk_report,
                "components": [dashboard_component, var_component]
            }

        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise

async def main():
    """Main entry point for the AI Risk Agent"""
    logger.info("🚀 Starting AI Risk Management Agent")

    try:
        # Create and initialize the agent
        risk_agent = AIRiskAgent()

        # Run interactive demo
        demo_result = await risk_agent.run_interactive_demo()

        logger.info("✅ AI Risk Agent started successfully!")
        logger.info("🎯 Agent is ready to handle risk management queries")
        logger.info("📊 Risk monitoring and analysis tools are active")
        logger.info("🎨 Visual components can be created dynamically")

        # Keep the agent running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Agent shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Agent failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())