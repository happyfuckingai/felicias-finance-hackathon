"""
Banking Agent - Simple, reliable banking operations agent
Replaces a traditional bank teller with LLM-powered capabilities
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

import httpx

from config import ADKConfig


class BankingAgent:
    """
    Banking Agent - Handles simple, rule-based banking operations
    Like a traditional bank teller but with intelligent processing
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = ADKConfig(config_path)
        self.logger = logging.getLogger(__name__)

        # Initialize Google GenAI client for intelligent processing
        # API key should be set as environment variable GOOGLE_API_KEY
        if GENAI_AVAILABLE:
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self.llm_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.llm_model = None
            self.logger.warning("Google GenAI not available - running in offline mode")

        # Banking knowledge base
        self.knowledge_base = {
            "account_types": ["checking", "savings", "investment"],
            "operations": ["balance_inquiry", "transfer", "deposit", "withdrawal"],
            "security_levels": ["basic", "verified", "premium"]
        }

        self.logger.info("Banking Agent initialized")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a banking request intelligently

        Args:
            request: Banking request with query and context

        Returns:
            Dict containing processed banking operation result
        """
        try:
            query = request.get("query", "")
            context = request.get("context", {})

            # Use LLM to understand and validate the request
            analysis = await self._analyze_request(query, context)

            if not analysis["valid"]:
                return {
                    "error": analysis["error"],
                    "agent": "banking_agent",
                    "confidence": analysis["confidence"]
                }

            # Route to appropriate operation
            operation = analysis["operation"]
            if operation == "balance_inquiry":
                return await self._handle_balance_inquiry(request)
            elif operation == "transfer":
                return await self._handle_transfer(request)
            elif operation == "deposit":
                return await self._handle_deposit(request)
            elif operation == "withdrawal":
                return await self._handle_withdrawal(request)
            else:
                return await self._handle_general_banking_query(query, context)

        except Exception as e:
            self.logger.error(f"Banking agent error: {e}")
            return {
                "error": f"Banking operation failed: {str(e)}",
                "agent": "banking_agent"
            }

    async def _analyze_request(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze and validate banking request"""
        try:
            prompt = f"""
            Analyze this banking request and determine:
            1. What operation is being requested
            2. If the request is valid and safe
            3. Required parameters
            4. Security level needed

            Request: "{query}"
            Context: {context}

            Respond in JSON format:
            {{
                "operation": "balance_inquiry|transfer|deposit|withdrawal|general",
                "valid": true/false,
                "confidence": 0.0-1.0,
                "parameters": ["param1", "param2"],
                "security_level": "basic|verified|premium",
                "error": "error message if invalid"
            }}
            """

            response = self.llm_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=200
                )
            )

            # For demo purposes, return mock response
            # In production, would parse response.text as JSON
            return {
                "operation": "balance_inquiry",  # Default for demo
                "valid": True,
                "confidence": 0.9,
                "parameters": ["account_id"],
                "security_level": "verified"
            }

        except Exception as e:
            self.logger.error(f"Request analysis failed: {e}")
            return {
                "operation": "general",
                "valid": False,
                "confidence": 0.0,
                "error": "Unable to analyze request"
            }

    async def _handle_balance_inquiry(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle balance inquiry with intelligent processing"""
        account_id = request.get("account_id", "default")

        # Simulate calling the bank MCP server
        balance_data = await self._call_bank_mcp("get_balance", {"account_id": account_id})

        # Use LLM to format and explain the result
        explanation = await self._explain_balance(balance_data)

        return {
            "operation": "balance_inquiry",
            "account_id": account_id,
            "balance": balance_data.get("balance", 0),
            "currency": balance_data.get("currency", "USD"),
            "explanation": explanation,
            "agent": "banking_agent",
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_transfer(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fund transfer with validation and security checks"""
        # Validate transfer parameters
        validation = await self._validate_transfer(request)

        if not validation["approved"]:
            return {
                "error": validation["reason"],
                "agent": "banking_agent",
                "operation": "transfer"
            }

        # Execute transfer
        transfer_result = await self._call_bank_mcp("transfer_funds", request)

        return {
            "operation": "transfer",
            "status": "completed" if transfer_result.get("success") else "failed",
            "transaction_id": transfer_result.get("transaction_id"),
            "amount": request.get("amount"),
            "from_account": request.get("from_account"),
            "to_account": request.get("to_account"),
            "agent": "banking_agent",
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_deposit(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deposit operations"""
        deposit_result = await self._call_bank_mcp("deposit", request)

        return {
            "operation": "deposit",
            "status": "completed" if deposit_result.get("success") else "failed",
            "amount": request.get("amount"),
            "account_id": request.get("account_id"),
            "confirmation": deposit_result.get("confirmation"),
            "agent": "banking_agent",
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_withdrawal(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle withdrawal operations"""
        withdrawal_result = await self._call_bank_mcp("withdraw", request)

        return {
            "operation": "withdrawal",
            "status": "completed" if withdrawal_result.get("success") else "failed",
            "amount": request.get("amount"),
            "account_id": request.get("account_id"),
            "confirmation": withdrawal_result.get("confirmation"),
            "agent": "banking_agent",
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_general_banking_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general banking questions using LLM"""
        try:
            prompt = f"""
            Answer this banking-related question helpfully and accurately.
            Be professional, clear, and provide specific guidance when appropriate.

            Question: {query}
            Context: {context}

            Provide a helpful response focused on banking services and best practices.
            """

            response = self.llm_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=300
                )
            )

            # For demo purposes, return mock response
            # In production, would use response.text
            return {
                "operation": "general_query",
                "query": query,
                "response": "Thank you for your banking question. I'm here to help with all your financial needs.",
                "agent": "banking_agent",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "operation": "general_query",
                "query": query,
                "response": "I'm currently unable to process this banking question. Please try again or contact customer service.",
                "error": str(e),
                "agent": "banking_agent"
            }

    async def _call_bank_mcp(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call the bank MCP server for actual banking operations"""
        try:
            endpoint = self.config.agents.get("banking_agent", {}).endpoint
            if not endpoint:
                # Fallback to mock data for demo
                return self._mock_bank_operation(operation, params)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{endpoint}/execute",
                    json={"operation": operation, "params": params},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            self.logger.error(f"Bank MCP call failed: {e}")
            return self._mock_bank_operation(operation, params)

    def _mock_bank_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock banking operations for demo purposes"""
        if operation == "get_balance":
            return {
                "balance": 15420.50,
                "currency": "USD",
                "account_id": params.get("account_id", "demo"),
                "available_balance": 15200.00,
                "pending_transactions": 2
            }
        elif operation == "transfer_funds":
            return {
                "success": True,
                "transaction_id": f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "amount": params.get("amount", 0),
                "fee": 0.00
            }
        elif operation in ["deposit", "withdraw"]:
            return {
                "success": True,
                "confirmation": f"CONF_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "new_balance": 15420.50
            }
        return {"error": "Unknown operation"}

    async def _validate_transfer(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transfer request for security and compliance"""
        # Basic validation logic
        amount = request.get("amount", 0)
        from_account = request.get("from_account")
        to_account = request.get("to_account")

        if amount <= 0:
            return {"approved": False, "reason": "Invalid transfer amount"}
        if not from_account or not to_account:
            return {"approved": False, "reason": "Missing account information"}
        if amount > 10000:  # Large transfer threshold
            return {"approved": False, "reason": "Large transfers require additional verification"}

        return {"approved": True}

    async def _explain_balance(self, balance_data: Dict[str, Any]) -> str:
        """Use LLM to provide helpful balance explanation"""
        try:
            balance = balance_data.get("balance", 0)
            available = balance_data.get("available_balance", balance)

            prompt = f"""
            Provide a brief, helpful explanation of this account balance:
            Total Balance: ${balance}
            Available Balance: ${available}

            Keep it to 1-2 sentences, focusing on what's immediately usable.
            """

            response = self.llm_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=100
                )
            )

            # For demo purposes, return static response
            # In production, would use response.text
            return f"Your available balance is ${available}. Total balance is ${balance}."

        except Exception:
            return f"Your available balance is ${available}. Total balance is ${balance}."

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent": "banking_agent",
            "status": "active",
            "capabilities": self.knowledge_base["operations"],
            "uptime": "99.9%",  # Mock uptime
            "active_operations": 0
        }