#!/usr/bin/env python3
"""
Banking Agent for A2A Protocol Integration

This module provides a banking agent that integrates with the A2A protocol
and the existing Bank of Anthos MCP server for secure inter-agent communication
in the Felicia's Finance system.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from adk_agents.a2a.core import A2AAgent, TransportConfig

logger = logging.getLogger(__name__)


class BankOfAnthosHTTPClient:
    """
    HTTP client for communicating with Bank of Anthos MCP server.
    Replaces direct coupling with proper API-based communication.
    """

    def __init__(self, base_url: str = None):
        """Initialize HTTP client with MCP server endpoint."""
        self.base_url = base_url or os.getenv('BANKOFANTHOS_MCP_URL', 'http://localhost:8001')
        self.api_key = os.getenv('BANKOFANTHOS_MCP_API_KEY', 'dev-key')
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

    async def authenticate_user(self, username: str, password: str) -> tuple[bool, str]:
        """Authenticate user via MCP server API."""
        try:
            response = await self.client.post(
                "/authenticate_user",
                json={"username": username, "password": password}
            )

            if response.status_code == 200:
                result = response.json()
                if "✅" in result:  # Success indicator from MCP tool
                    # Extract token from response (simplified parsing)
                    token_start = result.find("Token: `") + 8
                    token_end = result.find("`", token_start)
                    token = result[token_start:token_end] if token_start > 7 else "mock_token"

                    return True, token
                else:
                    return False, result
            else:
                return False, f"Authentication failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, f"Authentication error: {str(e)}"

    async def get_account_balance(self, account_id: str, token: str) -> tuple[bool, str]:
        """Get account balance via MCP server API."""
        try:
            response = await self.client.post(
                "/get_account_balance",
                json={"account_id": account_id, "token": token}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Balance retrieval failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Balance retrieval error: {e}")
            return False, f"Balance retrieval error: {str(e)}"

    async def get_transaction_history(self, account_id: str, token: str) -> tuple[bool, str]:
        """Get transaction history via MCP server API."""
        try:
            response = await self.client.post(
                "/get_transaction_history",
                json={"account_id": account_id, "token": token}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"History retrieval failed: {response.status_code}"

        except Exception as e:
            logger.error(f"History retrieval error: {e}")
            return False, f"History retrieval error: {str(e)}"

    async def execute_fiat_transfer(self, transfer_data: dict, token: str) -> tuple[bool, str]:
        """Execute fiat transfer via MCP server API."""
        try:
            # Convert amount to USD if it's in cents
            if isinstance(transfer_data.get('amount'), (int, float)) and transfer_data['amount'] > 100:
                transfer_data['amount'] = transfer_data['amount'] / 100

            response = await self.client.post(
                "/execute_fiat_transfer",
                json={
                    "from_account": transfer_data.get('fromAccountNum'),
                    "to_account": transfer_data.get('toAccountNum'),
                    "amount_usd": transfer_data.get('amount'),
                    "token": token,
                    "uuid": transfer_data.get('uuid')
                }
            )

            if response.status_code == 200:
                result = response.json()
                return "✅" in result, result  # Check for success indicator
            else:
                return False, f"Transfer failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Transfer error: {e}")
            return False, f"Transfer error: {str(e)}"

    async def execute_deposit(self, deposit_data: dict, token: str) -> tuple[bool, str]:
        """Execute deposit via MCP server API."""
        try:
            response = await self.client.post(
                "/execute_deposit",
                json={
                    "from_external_account": deposit_data.get('fromAccountNum'),
                    "from_routing": deposit_data.get('fromRoutingNum'),
                    "to_account": deposit_data.get('toAccountNum'),
                    "amount_usd": deposit_data.get('amount'),
                    "token": token,
                    "uuid": deposit_data.get('uuid')
                }
            )

            if response.status_code == 200:
                result = response.json()
                return "✅" in result, result
            else:
                return False, f"Deposit failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Deposit error: {e}")
            return False, f"Deposit error: {str(e)}"

    async def get_contacts(self, token: str) -> tuple[bool, str]:
        """Get contacts via MCP server API."""
        try:
            response = await self.client.post(
                "/get_contacts",
                json={"token": token}
            )

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Contacts retrieval failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Contacts retrieval error: {e}")
            return False, f"Contacts retrieval error: {str(e)}"

    async def add_contact(self, label: str, account_num: str, routing_num: str,
                         is_external: bool, token: str) -> tuple[bool, str]:
        """Add contact via MCP server API."""
        try:
            response = await self.client.post(
                "/add_contact",
                json={
                    "label": label,
                    "account_num": account_num,
                    "routing_num": routing_num,
                    "is_external": is_external,
                    "token": token
                }
            )

            if response.status_code == 200:
                result = response.json()
                return "✅" in result, result
            else:
                return False, f"Add contact failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Add contact error: {e}")
            return False, f"Add contact error: {str(e)}"


# Global HTTP client instance
banking_http_client = None


class BankingA2AAgent(A2AAgent):
    """
    Banking agent that extends A2A agent with banking-specific capabilities.

    This agent can:
    - Handle banking operations (balances, transactions, contacts)
    - Communicate securely with other agents via A2A protocol
    - Participate in orchestrated workflows (e.g., compliance checks)
    - Provide banking data to crypto agents for integrated financial operations
    """

    def __init__(self, agent_id: str, transport_config: TransportConfig = None):
        """Initialize the banking A2A agent."""

        # Initialize with banking-specific capabilities
        capabilities = [
            "banking:accounts",         # Account management
            "banking:balances",         # Balance inquiries
            "banking:transactions",     # Transaction processing
            "banking:history",          # Transaction history
            "banking:contacts",         # Contact management
            "banking:transfers",        # Money transfers
            "banking:compliance",       # Compliance operations
            "a2a:messaging"             # Standard A2A messaging
        ]

        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            transport_config=transport_config
        )

        # Banking-specific state
        self.active_sessions: Dict[str, str] = {}  # session_id -> user_token
        self.pending_operations: Dict[str, Dict[str, Any]] = {}
        self.http_client: Optional[BankOfAnthosHTTPClient] = None

        logger.info(f"Banking A2A agent {agent_id} initialized")

    async def initialize(self) -> bool:
        """Initialize the banking agent with A2A setup."""

        success = await super().initialize()
        if not success:
            return False

        # Initialize HTTP client for MCP server communication
        self.http_client = BankOfAnthosHTTPClient()

        # Register banking-specific message handlers
        self._register_banking_handlers()

        return True

    def _register_banking_handlers(self):
        """Register handlers for banking-specific A2A messages."""

        async def handle_balance_request(message, auth_token):
            """Handle balance inquiry requests from other agents."""
            payload = message.payload
            account_id = payload.get("account_id")
            session_id = payload.get("session_id")

            if not account_id or not session_id:
                response = message.create_response({
                    "error": "Missing account_id or session_id"
                })
                return response

            # Validate session
            user_token = self.active_sessions.get(session_id)
            if not user_token:
                response = message.create_response({
                    "error": "Invalid or expired session"
                })
                return response

            # Get balance from banking system via HTTP API
            async with self.http_client as client:
                success, result = await client.get_account_balance(account_id, user_token)

            if success:
                balance_data = json.loads(result)
                response = message.create_response({
                    "status": "success",
                    "balance": balance_data
                })
            else:
                response = message.create_response({
                    "status": "error",
                    "error": result
                })

            return response

        async def handle_transaction_history_request(message, auth_token):
            """Handle transaction history requests from other agents."""
            payload = message.payload
            account_id = payload.get("account_id")
            session_id = payload.get("session_id")

            if not account_id or not session_id:
                response = message.create_response({
                    "error": "Missing account_id or session_id"
                })
                return response

            # Validate session
            user_token = self.active_sessions.get(session_id)
            if not user_token:
                response = message.create_response({
                    "error": "Invalid or expired session"
                })
                return response

            # Get transaction history via HTTP API
            async with self.http_client as client:
                success, result = await client.get_transaction_history(account_id, user_token)

            if success:
                history_data = json.loads(result)
                response = message.create_response({
                    "status": "success",
                    "transactions": history_data
                })
            else:
                response = message.create_response({
                    "status": "error",
                    "error": result
                })

            return response

        async def handle_transfer_request(message, auth_token):
            """Handle transfer requests from other agents."""
            payload = message.payload
            transfer_data = payload.get("transfer_data")
            session_id = payload.get("session_id")

            if not transfer_data or not session_id:
                response = message.create_response({
                    "error": "Missing transfer_data or session_id"
                })
                return response

            # Validate session
            user_token = self.active_sessions.get(session_id)
            if not user_token:
                response = message.create_response({
                    "error": "Invalid or expired session"
                })
                return response

            # Execute transfer via HTTP API
            async with self.http_client as client:
                success, result = await client.execute_fiat_transfer(transfer_data, user_token)

            if success:
                response = message.create_response({
                    "status": "success",
                    "message": result
                })
            else:
                response = message.create_response({
                    "status": "error",
                    "error": result
                })

            return response

        async def handle_authenticate_request(message, auth_token):
            """Handle user authentication requests for session creation."""
            payload = message.payload
            username = payload.get("username")
            password = payload.get("password")

            if not username or not password:
                response = message.create_response({
                    "error": "Missing username or password"
                })
                return response

            # Authenticate user via HTTP API
            async with self.http_client as client:
                success, result = await client.authenticate_user(username, password)

            if success:
                # Create session
                session_id = f"session_{username}_{int(datetime.utcnow().timestamp())}"
                self.active_sessions[session_id] = result  # result is the JWT token

                # Set session expiry (simplified - in production use proper session management)
                asyncio.create_task(self._expire_session(session_id, 3600))  # 1 hour

                response = message.create_response({
                    "status": "success",
                    "session_id": session_id,
                    "message": "Authentication successful"
                })
            else:
                response = message.create_response({
                    "status": "error",
                    "error": result
                })

            return response

        async def handle_compliance_check_request(message, auth_token):
            """Handle compliance check requests from orchestrator or crypto agents."""
            payload = message.payload
            account_id = payload.get("account_id")
            check_type = payload.get("check_type", "general")
            session_id = payload.get("session_id")

            if not account_id or not session_id:
                response = message.create_response({
                    "error": "Missing account_id or session_id"
                })
                return response

            # Validate session
            user_token = self.active_sessions.get(session_id)
            if not user_token:
                response = message.create_response({
                    "error": "Invalid or expired session"
                })
                return response

            # Perform compliance check
            compliance_result = await self._perform_compliance_check(
                account_id, check_type, user_token
            )

            response = message.create_response({
                "status": "success",
                "compliance_check": compliance_result
            })

            return response

        async def handle_crypto_integration_request(message, auth_token):
            """Handle requests from crypto agent for banking-crypto integration."""
            payload = message.payload
            operation = payload.get("operation")
            session_id = payload.get("session_id")

            if not operation or not session_id:
                response = message.create_response({
                    "error": "Missing operation or session_id"
                })
                return response

            # Validate session
            user_token = self.active_sessions.get(session_id)
            if not user_token:
                response = message.create_response({
                    "error": "Invalid or expired session"
                })
                return response

            # Handle different crypto integration operations
            if operation == "get_balance_for_trading":
                account_id = payload.get("account_id")
                if not account_id:
                    response = message.create_response({
                        "error": "Missing account_id for balance check"
                    })
                    return response

                async with self.http_client as client:
                    success, result = await client.get_account_balance(account_id, user_token)
                if success:
                    balance_data = json.loads(result)
                    response = message.create_response({
                        "status": "success",
                        "balance": balance_data,
                        "operation": operation
                    })
                else:
                    response = message.create_response({
                        "status": "error",
                        "error": result,
                        "operation": operation
                    })

            elif operation == "execute_deposit":
                deposit_data = payload.get("deposit_data")
                if not deposit_data:
                    response = message.create_response({
                        "error": "Missing deposit_data"
                    })
                    return response

                async with self.http_client as client:
                    success, result = await client.execute_deposit(deposit_data, user_token)
                response = message.create_response({
                    "status": "success" if success else "error",
                    "message": result,
                    "operation": operation
                })

            else:
                response = message.create_response({
                    "error": f"Unknown operation: {operation}"
                })

            return response

        # Register all handlers
        self.register_message_handler("balance_request", handle_balance_request)
        self.register_message_handler("transaction_history_request", handle_transaction_history_request)
        self.register_message_handler("transfer_request", handle_transfer_request)
        self.register_message_handler("authenticate_request", handle_authenticate_request)
        self.register_message_handler("compliance_check_request", handle_compliance_check_request)
        self.register_message_handler("crypto_integration_request", handle_crypto_integration_request)

    async def _perform_compliance_check(self, account_id: str, check_type: str, user_token: str) -> Dict[str, Any]:
        """Perform a compliance check on an account."""

        compliance_result = {
            "account_id": account_id,
            "check_type": check_type,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": []
        }

        try:
            # Get account balance via HTTP API
            async with self.http_client as client:
                success, result = await client.get_account_balance(account_id, user_token)
            if success:
                balance_data = json.loads(result)
                balance = balance_data.get("balance", 0)

                # Check for suspicious activity (simplified compliance check)
                compliance_result["checks"].append({
                    "check": "balance_threshold",
                    "status": "passed" if balance < 10000 else "flagged",
                    "details": f"Balance: ${balance}"
                })
            else:
                compliance_result["checks"].append({
                    "check": "balance_check",
                    "status": "error",
                    "details": result
                })

            # Get transaction history via HTTP API
            async with self.http_client as client:
                success, result = await client.get_transaction_history(account_id, user_token)
            if success:
                transactions = json.loads(result)

                # Check for unusual transaction patterns
                large_transactions = [t for t in transactions if t.get("amount", 0) > 5000]
                compliance_result["checks"].append({
                    "check": "large_transaction_check",
                    "status": "passed" if len(large_transactions) == 0 else "flagged",
                    "details": f"Found {len(large_transactions)} large transactions"
                })

                # Check for frequent transactions
                recent_transactions = [t for t in transactions
                                     if (datetime.utcnow() - datetime.fromisoformat(t.get("timestamp", ""))).days < 7]
                compliance_result["checks"].append({
                    "check": "transaction_frequency",
                    "status": "passed" if len(recent_transactions) < 10 else "flagged",
                    "details": f"{len(recent_transactions)} transactions in last 7 days"
                })

            else:
                compliance_result["checks"].append({
                    "check": "transaction_check",
                    "status": "error",
                    "details": result
                })

            # Overall compliance status
            failed_checks = [c for c in compliance_result["checks"] if c["status"] in ["flagged", "error"]]
            compliance_result["overall_status"] = "compliant" if not failed_checks else "requires_review"

        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            compliance_result["overall_status"] = "error"
            compliance_result["error"] = str(e)

        return compliance_result

    async def _expire_session(self, session_id: str, delay_seconds: int):
        """Expire a session after a delay."""

        await asyncio.sleep(delay_seconds)
        self.active_sessions.pop(session_id, None)
        logger.info(f"Session {session_id} expired")

    async def get_user_balance(self, session_id: str, account_id: str) -> Optional[Dict[str, Any]]:
        """Get user balance for internal operations."""

        user_token = self.active_sessions.get(session_id)
        if not user_token:
            return None

        async with self.http_client as client:
            success, result = await client.get_account_balance(account_id, user_token)
        if success:
            return json.loads(result)
        return None

    async def execute_secure_transfer(self, session_id: str, transfer_data: Dict[str, Any]) -> bool:
        """Execute a secure transfer for internal operations."""

        user_token = self.active_sessions.get(session_id)
        if not user_token:
            return False

        async with self.http_client as client:
            success, _ = await client.execute_fiat_transfer(transfer_data, user_token)
        return success

    def get_agent_status(self) -> Dict[str, Any]:
        """Get the current status of the banking agent."""

        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "active_sessions": len(self.active_sessions),
            "pending_operations": len(self.pending_operations),
            "connected": self.running,
            "last_heartbeat": datetime.utcnow().isoformat()
        }


# Convenience functions for creating and managing banking agents

async def create_banking_agent(agent_id: str = "banking-agent-01",
                              host: str = "localhost", port: int = 8444) -> BankingA2AAgent:
    """Create and initialize a banking A2A agent."""

    transport_config = TransportConfig(
        protocol="http2",
        host=host,
        port=port,
        ssl_enabled=False  # Disable SSL for local development
    )

    agent = BankingA2AAgent(agent_id, transport_config)

    success = await agent.initialize()
    if not success:
        raise RuntimeError(f"Failed to initialize banking agent {agent_id}")

    success = await agent.start()
    if not success:
        raise RuntimeError(f"Failed to start banking agent {agent_id}")

    return agent


async def get_banking_agent_status(agent: BankingA2AAgent) -> Dict[str, Any]:
    """Get comprehensive status of a banking agent."""

    base_status = agent.get_agent_status()

    # Add banking-specific status
    base_status.update({
        "banking_services": {
            "transaction_service": "available",  # Could check actual service health
            "balance_service": "available",
            "contacts_service": "available"
        },
        "active_banking_sessions": len(agent.active_sessions)
    })

    return base_status


if __name__ == "__main__":
    # Example usage
    async def main():
        logging.basicConfig(level=logging.INFO)

        # Create banking agent
        agent = await create_banking_agent()

        try:
            # Keep agent running
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            await agent.stop()
            logger.info("Banking agent shutdown complete")

    asyncio.run(main())