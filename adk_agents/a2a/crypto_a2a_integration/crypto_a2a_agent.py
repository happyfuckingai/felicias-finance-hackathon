#!/usr/bin/env python3
"""
Crypto Agent for A2A Protocol Integration

This module provides a crypto agent that integrates with the A2A protocol
and the existing crypto MCP server for secure inter-agent communication
in the Felicia's Finance system.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from adk_agents.a2a.core import A2AAgent, TransportConfig
import httpx
import json
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CryptoMCPHTTPClient:
    """
    HTTP client for communicating with crypto MCP server.
    Replaces direct coupling with proper API-based communication.
    """

    def __init__(self, base_url: str = None):
        """Initialize HTTP client with MCP server endpoint."""
        self.base_url = base_url or os.getenv('CRYPTO_MCP_URL', 'http://localhost:8002')
        self.api_key = os.getenv('CRYPTO_MCP_API_KEY', 'dev-key')
        self.timeout = 30.0

        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            timeout=self.timeout
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def check_price(self, token_id: str) -> tuple[bool, str]:
        """Check token price via MCP server API."""
        try:
            response = await self.client.post(
                "/check_price",
                json={"token_id": token_id}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Price check failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Price check error: {e}")
            return False, f"Price check error: {str(e)}"

    async def analyze_token(self, token_id: str, days: int = 7) -> tuple[bool, str]:
        """Analyze token via MCP server API."""
        try:
            response = await self.client.post(
                "/analyze_token",
                json={"token_id": token_id, "days": days}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Token analysis failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Token analysis error: {e}")
            return False, f"Token analysis error: {str(e)}"

    async def generate_signal(self, token_id: str) -> tuple[bool, str]:
        """Generate trading signal via MCP server API."""
        try:
            response = await self.client.post(
                "/generate_signal",
                json={"token_id": token_id}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Signal generation failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return False, f"Signal generation error: {str(e)}"

    async def research_token(self, token_id: str) -> tuple[bool, str]:
        """Research token via MCP server API."""
        try:
            response = await self.client.post(
                "/research_token",
                json={"token_id": token_id}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Token research failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Token research error: {e}")
            return False, f"Token research error: {str(e)}"

    async def create_wallet(self) -> tuple[bool, str]:
        """Create wallet via MCP server API."""
        try:
            response = await self.client.post(
                "/create_wallet",
                json={}
            )

            if response.status_code == 200:
                result = response.json()
                return "✅" in result, result  # Check for success indicator
            else:
                return False, f"Wallet creation failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Wallet creation error: {e}")
            return False, f"Wallet creation error: {str(e)}"

    async def show_balance(self, private_key: str) -> tuple[bool, str]:
        """Show wallet balance via MCP server API."""
        try:
            response = await self.client.post(
                "/show_balance",
                json={"private_key": private_key}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Balance check failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return False, f"Balance check error: {str(e)}"

    async def send_transaction(self, private_key: str, to_address: str, amount_eth: float) -> tuple[bool, str]:
        """Send transaction via MCP server API."""
        try:
            response = await self.client.post(
                "/send_transaction",
                json={"private_key": private_key, "to_address": to_address, "amount_eth": amount_eth}
            )

            if response.status_code == 200:
                result = response.json()
                return "✅" in result, result
            else:
                return False, f"Transaction failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Transaction error: {e}")
            return False, f"Transaction error: {str(e)}"

    async def deploy_token(self, private_key: str, name: str, symbol: str, total_supply: int) -> tuple[bool, str]:
        """Deploy token via MCP server API."""
        try:
            response = await self.client.post(
                "/deploy_token",
                json={"private_key": private_key, "name": name, "symbol": symbol, "total_supply": total_supply}
            )

            if response.status_code == 200:
                result = response.json()
                return "✅" in result, result
            else:
                return False, f"Token deployment failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Token deployment error: {e}")
            return False, f"Token deployment error: {str(e)}"

    async def get_ai_trading_advice(self, token_id: str) -> tuple[bool, str]:
        """Get AI trading advice via MCP server API."""
        try:
            response = await self.client.post(
                "/get_ai_trading_advice",
                json={"token_id": token_id}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"AI trading advice failed: {response.status_code}"

        except Exception as e:
            logger.error(f"AI trading advice error: {e}")
            return False, f"AI trading advice error: {str(e)}"


# Global HTTP client instance
crypto_http_client = None


class CryptoA2AAgent(A2AAgent):
    """
    Crypto agent that extends A2A agent with cryptocurrency-specific capabilities.

    This agent can:
    - Handle crypto trading operations (analysis, signals, wallet management)
    - Communicate securely with other agents via A2A protocol
    - Participate in orchestrated workflows (e.g., integrated banking-crypto operations)
    - Provide market analysis and trading signals to banking agents
    - Execute cross-system financial operations (fiat to crypto conversions)
    """

    def __init__(self, agent_id: str, transport_config: TransportConfig = None):
        """Initialize the crypto A2A agent."""

        # Initialize with crypto-specific capabilities
        capabilities = [
            "crypto:trading",         # Trading operations
            "crypto:analysis",         # Market analysis
            "crypto:wallet",           # Wallet management
            "crypto:signals",          # Trading signals
            "crypto:tokens",           # Token operations
            "crypto:ai",               # AI-powered trading
            "crypto:integration",      # Banking-crypto integration
            "a2a:messaging"            # Standard A2A messaging
        ]

        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            transport_config=transport_config
        )

        # Crypto-specific state
        self.active_trading_sessions: Dict[str, Dict[str, Any]] = {}
        self.pending_trades: Dict[str, Dict[str, Any]] = {}
        self.market_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Crypto A2A agent {agent_id} initialized")

    async def initialize(self) -> bool:
        """Initialize the crypto agent with A2A setup."""

        success = await super().initialize()
        if not success:
            return False

        # Initialize HTTP client for MCP server communication
        global crypto_http_client
        crypto_http_client = CryptoMCPHTTPClient()

        # Register crypto-specific message handlers
        self._register_crypto_handlers()

        return True

    def _register_crypto_handlers(self):
        """Register handlers for crypto-specific A2A messages."""

        async def handle_market_analysis_request(message, auth_token):
            """Handle market analysis requests from other agents."""
            payload = message.payload
            token_id = payload.get("token_id")
            analysis_type = payload.get("analysis_type", "price")

            if not token_id:
                response = message.create_response({
                    "error": "Missing token_id"
                })
                return response

            try:
                async with crypto_http_client as client:
                    if analysis_type == "price":
                        success, result = await client.check_price(token_id)
                        result = result if success else {"success": False, "error": result}
                    elif analysis_type == "analysis":
                        days = payload.get("days", 7)
                        success, result = await client.analyze_token(token_id, days)
                        result = result if success else {"success": False, "error": result}
                    elif analysis_type == "signal":
                        success, result = await client.generate_signal(token_id)
                        result = result if success else {"success": False, "error": result}
                    elif analysis_type == "research":
                        success, result = await client.research_token(token_id)
                        result = result if success else {"success": False, "error": result}
                    else:
                        result = {"success": False, "error": f"Unknown analysis type: {analysis_type}"}

                response = message.create_response({
                    "status": "success" if result.get("success") else "error",
                    "analysis_type": analysis_type,
                    "token_id": token_id,
                    "result": result
                })

            except Exception as e:
                logger.error(f"Market analysis failed for {token_id}: {e}")
                response = message.create_response({
                    "status": "error",
                    "error": f"Analysis failed: {str(e)}",
                    "token_id": token_id,
                    "analysis_type": analysis_type
                })

            return response

        async def handle_trading_signal_request(message, auth_token):
            """Handle trading signal requests from other agents."""
            payload = message.payload
            token_id = payload.get("token_id")
            use_ai = payload.get("use_ai", False)

            if not token_id:
                response = message.create_response({
                    "error": "Missing token_id"
                })
                return response

            try:
                async with crypto_http_client as client:
                    if use_ai:
                        # Use XGBoost AI manager
                        success, result = await client.get_ai_trading_advice(token_id)
                        result = result if success else {"success": False, "error": result}
                    else:
                        # Use traditional signal generator
                        success, result = await client.generate_signal(token_id)
                        result = result if success else {"success": False, "error": result}

                response = message.create_response({
                    "status": "success" if result.get("success") else "error",
                    "token_id": token_id,
                    "use_ai": use_ai,
                    "signal": result
                })

            except Exception as e:
                logger.error(f"Trading signal generation failed for {token_id}: {e}")
                response = message.create_response({
                    "status": "error",
                    "error": f"Signal generation failed: {str(e)}",
                    "token_id": token_id
                })

            return response

        async def handle_wallet_operation_request(message, auth_token):
            """Handle wallet operation requests from other agents."""
            payload = message.payload
            operation = payload.get("operation")
            private_key = payload.get("private_key")

            if not operation or not private_key:
                response = message.create_response({
                    "error": "Missing operation or private_key"
                })
                return response

            try:
                async with crypto_http_client as client:
                    if operation == "create_wallet":
                        success, result = await client.create_wallet()
                        result = result if success else {"success": False, "error": result}
                    elif operation == "show_balance":
                        success, result = await client.show_balance(private_key)
                        result = result if success else {"success": False, "error": result}
                    elif operation == "send_transaction":
                        to_address = payload.get("to_address")
                        amount = payload.get("amount_eth")
                        if not to_address or amount is None:
                            result = {"success": False, "error": "Missing to_address or amount_eth"}
                        else:
                            success, result = await client.send_transaction(private_key, to_address, amount)
                            result = result if success else {"success": False, "error": result}
                    else:
                        result = {"success": False, "error": f"Unknown wallet operation: {operation}"}

                response = message.create_response({
                    "status": "success" if result.get("success") else "error",
                    "operation": operation,
                    "result": result
                })

            except Exception as e:
                logger.error(f"Wallet operation failed: {e}")
                response = message.create_response({
                    "status": "error",
                    "error": f"Wallet operation failed: {str(e)}",
                    "operation": operation
                })

            return response

        async def handle_token_operation_request(message, auth_token):
            """Handle token operation requests from other agents."""
            payload = message.payload
            operation = payload.get("operation")
            private_key = payload.get("private_key")

            if not operation or not private_key:
                response = message.create_response({
                    "error": "Missing operation or private_key"
                })
                return response

            try:
                async with crypto_http_client as client:
                    if operation == "deploy_token":
                        name = payload.get("name")
                        symbol = payload.get("symbol")
                        total_supply = payload.get("total_supply", 1000000)

                        if not name or not symbol:
                            result = {"success": False, "error": "Missing name or symbol"}
                        else:
                            success, result = await client.deploy_token(private_key, name, symbol, total_supply)
                            result = result if success else {"success": False, "error": result}
                    else:
                        result = {"success": False, "error": f"Unknown token operation: {operation}"}

                response = message.create_response({
                    "status": "success" if result.get("success") else "error",
                    "operation": operation,
                    "result": result
                })

            except Exception as e:
                logger.error(f"Token operation failed: {e}")
                response = message.create_response({
                    "status": "error",
                    "error": f"Token operation failed: {str(e)}",
                    "operation": operation
                })

            return response

        async def handle_banking_integration_request(message, auth_token):
            """Handle requests from banking agent for crypto-banking integration."""
            payload = message.payload
            operation = payload.get("operation")
            banking_session_id = payload.get("banking_session_id")

            if not operation:
                response = message.create_response({
                    "error": "Missing operation"
                })
                return response

            try:
                if operation == "convert_fiat_to_crypto":
                    # Handle fiat to crypto conversion
                    fiat_amount = payload.get("fiat_amount")
                    target_token = payload.get("target_token", "ethereum")

                    if not fiat_amount:
                        result = {"success": False, "error": "Missing fiat_amount"}
                    else:
                        # Simulate fiat to crypto conversion
                        # In real implementation, this would interact with exchanges
                        result = await self._simulate_fiat_to_crypto_conversion(
                            fiat_amount, target_token, banking_session_id
                        )

                elif operation == "get_crypto_portfolio_value":
                    # Get crypto portfolio value in fiat
                    wallet_address = payload.get("wallet_address")

                    if not wallet_address:
                        result = {"success": False, "error": "Missing wallet_address"}
                    else:
                        result = await self._get_crypto_portfolio_value(wallet_address)

                elif operation == "execute_cross_chain_transfer":
                    # Execute transfer between different blockchains
                    from_chain = payload.get("from_chain")
                    to_chain = payload.get("to_chain")
                    amount = payload.get("amount")
                    token = payload.get("token")

                    if not all([from_chain, to_chain, amount, token]):
                        result = {"success": False, "error": "Missing required parameters"}
                    else:
                        result = await self._execute_cross_chain_transfer(
                            from_chain, to_chain, amount, token
                        )

                else:
                    result = {"success": False, "error": f"Unknown integration operation: {operation}"}

                response = message.create_response({
                    "status": "success" if result.get("success") else "error",
                    "operation": operation,
                    "result": result
                })

            except Exception as e:
                logger.error(f"Banking integration operation failed: {e}")
                response = message.create_response({
                    "status": "error",
                    "error": f"Integration operation failed: {str(e)}",
                    "operation": operation
                })

            return response

        async def handle_risk_assessment_request(message, auth_token):
            """Handle risk assessment requests from orchestrator."""
            payload = message.payload
            portfolio = payload.get("portfolio", [])
            risk_tolerance = payload.get("risk_tolerance", "medium")

            try:
                risk_assessment = await self._assess_portfolio_risk(portfolio, risk_tolerance)

                response = message.create_response({
                    "status": "success",
                    "risk_assessment": risk_assessment
                })

            except Exception as e:
                logger.error(f"Risk assessment failed: {e}")
                response = message.create_response({
                    "status": "error",
                    "error": f"Risk assessment failed: {str(e)}"
                })

            return response

        async def handle_market_data_request(message, auth_token):
            """Handle market data requests from banking agents."""
            payload = message.payload
            token_ids = payload.get("token_ids", [])
            data_type = payload.get("data_type", "price")

            try:
                market_data = await self._get_market_data(token_ids, data_type)

                response = message.create_response({
                    "status": "success",
                    "market_data": market_data,
                    "data_type": data_type
                })

            except Exception as e:
                logger.error(f"Market data request failed: {e}")
                response = message.create_response({
                    "status": "error",
                    "error": f"Market data request failed: {str(e)}"
                })

            return response

        # Register all handlers
        self.register_message_handler("market_analysis_request", handle_market_analysis_request)
        self.register_message_handler("trading_signal_request", handle_trading_signal_request)
        self.register_message_handler("wallet_operation_request", handle_wallet_operation_request)
        self.register_message_handler("token_operation_request", handle_token_operation_request)
        self.register_message_handler("banking_integration_request", handle_banking_integration_request)
        self.register_message_handler("risk_assessment_request", handle_risk_assessment_request)
        self.register_message_handler("market_data_request", handle_market_data_request)

    async def _simulate_fiat_to_crypto_conversion(self, fiat_amount: float,
                                                 target_token: str,
                                                 banking_session_id: str) -> Dict[str, Any]:
        """Simulate fiat to crypto conversion (would integrate with real exchange)."""

        # Get current price of target token
        async with crypto_http_client as client:
            success, price_result = await client.check_price(target_token)

        if not success:
            return {"success": False, "error": "Could not get token price"}

        price_data = price_result
        if not price_data.get("success"):
            return {"success": False, "error": "Could not get token price"}

        token_price = price_data.get("price", 0)

        # Calculate how much crypto user gets
        # Simplified conversion (would need real exchange rates)
        crypto_amount = fiat_amount / token_price

        return {
            "success": True,
            "fiat_amount": fiat_amount,
            "crypto_amount": crypto_amount,
            "target_token": target_token,
            "exchange_rate": token_price,
            "transaction_id": f"conversion_{int(datetime.utcnow().timestamp())}",
            "note": "This is a simulation - real implementation would use exchange APIs"
        }

    async def _get_crypto_portfolio_value(self, wallet_address: str) -> Dict[str, Any]:
        """Get the fiat value of a crypto portfolio."""

        # This is a simplified implementation
        # Real implementation would query blockchain APIs or wallet services

        return {
            "success": True,
            "wallet_address": wallet_address,
            "total_value_usd": 0.0,  # Would calculate actual value
            "assets": [],
            "last_updated": datetime.utcnow().isoformat(),
            "note": "This is a simulation - real implementation would query blockchain"
        }

    async def _execute_cross_chain_transfer(self, from_chain: str, to_chain: str,
                                           amount: float, token: str) -> Dict[str, Any]:
        """Execute a cross-chain transfer."""

        # This is a highly simplified simulation
        # Real implementation would use bridges like Polygon Bridge, Arbitrum, etc.

        return {
            "success": True,
            "from_chain": from_chain,
            "to_chain": to_chain,
            "amount": amount,
            "token": token,
            "bridge_fee": amount * 0.001,  # 0.1% bridge fee
            "estimated_completion": "10-30 minutes",
            "transaction_hash": f"bridge_{int(datetime.utcnow().timestamp())}",
            "note": "This is a simulation - real implementation would use bridge protocols"
        }

    async def _assess_portfolio_risk(self, portfolio: List[Dict[str, Any]],
                                    risk_tolerance: str) -> Dict[str, Any]:
        """Assess risk of a crypto portfolio."""

        try:
            total_value = sum(asset.get("value_usd", 0) for asset in portfolio)

            # Calculate diversification
            unique_assets = len(set(asset.get("symbol", "") for asset in portfolio))

            # Assess volatility (simplified)
            volatile_assets = ["BTC", "ETH", "SOL", "DOT"]  # High volatility tokens
            volatility_score = sum(1 for asset in portfolio
                                 if asset.get("symbol", "").upper() in volatile_assets)

            # Risk assessment logic
            if risk_tolerance == "low":
                max_volatility_score = 1
                max_concentration = 0.6
            elif risk_tolerance == "medium":
                max_volatility_score = 3
                max_concentration = 0.8
            else:  # high
                max_volatility_score = 5
                max_concentration = 1.0

            # Check concentration risk
            concentration_risk = "low"
            if portfolio:
                max_asset_value = max(asset.get("value_usd", 0) for asset in portfolio)
                concentration_pct = max_asset_value / total_value if total_value > 0 else 0

                if concentration_pct > max_concentration:
                    concentration_risk = "high"
                elif concentration_pct > (max_concentration * 0.7):
                    concentration_risk = "medium"

            # Overall risk score
            risk_score = 0
            if volatility_score > max_volatility_score:
                risk_score += 2
            if concentration_risk == "high":
                risk_score += 2
            elif concentration_risk == "medium":
                risk_score += 1

            if unique_assets < 3:
                risk_score += 1  # Lack of diversification

            risk_level = "low" if risk_score <= 1 else "medium" if risk_score <= 3 else "high"

            return {
                "portfolio_value_usd": total_value,
                "unique_assets": unique_assets,
                "volatility_score": volatility_score,
                "concentration_risk": concentration_risk,
                "overall_risk_level": risk_level,
                "risk_score": risk_score,
                "recommendations": self._generate_risk_recommendations(risk_level, unique_assets)
            }

        except Exception as e:
            logger.error(f"Portfolio risk assessment failed: {e}")
            return {"error": str(e)}

    def _generate_risk_recommendations(self, risk_level: str, unique_assets: int) -> List[str]:
        """Generate risk management recommendations."""

        recommendations = []

        if risk_level == "high":
            recommendations.append("Consider reducing position sizes in volatile assets")
            recommendations.append("Implement stop-loss orders on all positions")

        if unique_assets < 5:
            recommendations.append("Increase diversification by adding more asset classes")

        if risk_level in ["medium", "high"]:
            recommendations.append("Regular portfolio rebalancing recommended")
            recommendations.append("Consider dollar-cost averaging for new investments")

        if not recommendations:
            recommendations.append("Portfolio risk profile looks good")

        return recommendations

    async def _get_market_data(self, token_ids: List[str], data_type: str) -> Dict[str, Any]:
        """Get market data for multiple tokens."""

        results = {}

        for token_id in token_ids:
            try:
                async with crypto_http_client as client:
                    if data_type == "price":
                        success, data = await client.check_price(token_id)
                        data = data if success else {"success": False, "error": data}
                    elif data_type == "analysis":
                        success, data = await client.analyze_token(token_id)
                        data = data if success else {"success": False, "error": data}
                    else:
                        data = {"success": False, "error": f"Unknown data type: {data_type}"}

                results[token_id] = data

            except Exception as e:
                results[token_id] = {"success": False, "error": str(e)}

        return {
            "data_type": data_type,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get the current status of the crypto agent."""

        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "active_trading_sessions": len(self.active_trading_sessions),
            "pending_trades": len(self.pending_trades),
            "market_cache_size": len(self.market_cache),
            "connected": self.running,
            "last_heartbeat": datetime.utcnow().isoformat()
        }


# Convenience functions for creating and managing crypto agents

async def create_crypto_agent(agent_id: str = "crypto-agent-01",
                             host: str = "localhost", port: int = 8445) -> CryptoA2AAgent:
    """Create and initialize a crypto A2A agent."""

    transport_config = TransportConfig(
        protocol="http2",
        host=host,
        port=port,
        ssl_enabled=False  # Disable SSL for local development
    )

    agent = CryptoA2AAgent(agent_id, transport_config)

    success = await agent.initialize()
    if not success:
        raise RuntimeError(f"Failed to initialize crypto agent {agent_id}")

    success = await agent.start()
    if not success:
        raise RuntimeError(f"Failed to start crypto agent {agent_id}")

    return agent


async def get_crypto_agent_status(agent: CryptoA2AAgent) -> Dict[str, Any]:
    """Get comprehensive status of a crypto agent."""

    base_status = agent.get_agent_status()

    # Add crypto-specific status
    base_status.update({
        "crypto_services": {
            "market_analyzer": "available",
            "wallet_manager": "available",
            "token_manager": "available",
            "ai_trading": "available"  # Would check actual availability
        },
        "active_trading_sessions": len(agent.active_trading_sessions)
    })

    return base_status


if __name__ == "__main__":
    # Example usage
    async def main():
        logging.basicConfig(level=logging.INFO)

        # Create crypto agent
        agent = await create_crypto_agent()

        try:
            # Keep agent running
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            await agent.stop()
            logger.info("Crypto agent shutdown complete")

    asyncio.run(main())