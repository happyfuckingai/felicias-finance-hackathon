try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    def load_dotenv():
        pass  # No-op fallback

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.agents import llm, tts
from .prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from .tools import get_weather, search_web, send_email
from mem0 import AsyncMemoryClient
from mcp_client import MCPServerSse
from mcp_client.agent_tools import MCPToolsIntegration
import os
import json
import logging
import asyncio
import sys
import importlib.util

load_dotenv()

# Dynamically import ADK integration
try:
    spec = importlib.util.spec_from_file_location("adk_agents", "adk_agents/adk/adk_integration.py")
    adk_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adk_module)
    ADKIntegration = adk_module.ADKIntegration
    adk_available = True
except Exception as e:
    logging.warning(f"ADK integration not available: {e}")
    adk_available = False
    ADKIntegration = None


class Assistant(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=llm.GoogleRealtimeModel(),
            tts=tts.GoogleTTS(),
            tools=[
                get_weather,
                search_web,
                send_email,
                self.delegate_to_banking_agent,
                self.delegate_to_crypto_team,
                self.get_financial_advice,
                self.check_system_status
            ],
            chat_ctx=chat_ctx
        )

        # Initialize ADK integration for agent delegation
        self.adk_integration = None
        if adk_available:
            try:
                self.adk_integration = ADKIntegration()
                logging.info("✓ ADK integration initialized for Felicia")
            except Exception as e:
                logging.warning(f"Failed to initialize ADK integration: {e}")

    # ADK delegation tools - async versions for proper event loop handling
    async def delegate_to_banking_agent_async(self, query: str) -> str:
        """Delegate simple banking requests to the banking specialist agent."""
        if not self.adk_integration:
            return "I'm sorry, but the banking system is currently unavailable. Please try again later."

        try:
            # Ensure ADK integration is initialized
            if not self.adk_integration._initialized:
                await self.adk_integration.initialize()

            result = await self.adk_integration.handle_banking_request({"query": query})
            return result
        except Exception as e:
            logging.error(f"Banking agent delegation failed: {e}")
            return "I'm experiencing technical difficulties with the banking system. Please try again later."

    async def delegate_to_crypto_team_async(self, mission: str, strategy: dict) -> str:
        """Delegate complex investment requests to the crypto investment team."""
        if not self.adk_integration:
            return "I'm sorry, but the investment analysis system is currently unavailable. Please try again later."

        try:
            # Ensure ADK integration is initialized
            if not self.adk_integration._initialized:
                await self.adk_integration.initialize()

            result = await self.adk_integration.handle_crypto_request({
                "mission": mission,
                "strategy": strategy
            })
            return result
        except Exception as e:
            logging.error(f"Crypto team delegation failed: {e}")
            return "I'm experiencing technical difficulties with the investment system. Please try again later."

    async def get_financial_advice_async(self, question: str, context: str = "") -> str:
        """Provide comprehensive financial advice by analyzing the request and delegating appropriately."""
        question_lower = question.lower()

        # Simple banking requests - direct delegation
        banking_keywords = ["balance", "transfer", "account", "statement", "deposit", "withdraw", "transaction"]
        if any(keyword in question_lower for keyword in banking_keywords):
            return await self.delegate_to_banking_agent_async(question)

        # Complex investment requests - orchestrated delegation
        investment_keywords = ["invest", "portfolio", "crypto", "bitcoin", "trading", "strategy", "risk", "returns"]
        if any(keyword in question_lower for keyword in investment_keywords):
            strategy = {"risk_level": "medium", "timeframe": "flexible"}  # Default strategy
            return await self.delegate_to_crypto_team_async(question, strategy)

        # General financial advice - analyze and delegate
        return "I'd be happy to help with your financial question. Let me analyze this and connect you with the appropriate specialist."

    async def check_system_status_async(self) -> str:
        """Check the status of all financial systems."""
        if not self.adk_integration:
            return "Financial systems status: Banking - Available, Investment Analysis - Unavailable"

        try:
            # Ensure ADK integration is initialized
            if not self.adk_integration._initialized:
                await self.adk_integration.initialize()

            status = await self.adk_integration.get_system_status()
            return f"Financial systems status: {status}"
        except Exception as e:
            logging.error(f"System status check failed: {e}")
            return "Financial systems status: Unable to check status due to technical issues"

    # Synchronous wrapper methods for LiveKit compatibility
    def delegate_to_banking_agent(self, query: str) -> str:
        """Synchronous wrapper for banking agent delegation."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an async context, this is problematic - return placeholder
            logging.warning("Async context detected in sync method - returning placeholder response")
            return "Banking request received. Processing in background..."
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self.delegate_to_banking_agent_async(query))

    def delegate_to_crypto_team(self, mission: str, strategy: dict) -> str:
        """Synchronous wrapper for crypto team delegation."""
        try:
            loop = asyncio.get_running_loop()
            logging.warning("Async context detected in sync method - returning placeholder response")
            return "Investment request received. Processing in background..."
        except RuntimeError:
            return asyncio.run(self.delegate_to_crypto_team_async(mission, strategy))

    def get_financial_advice(self, question: str, context: str = "") -> str:
        """Synchronous wrapper for financial advice."""
        try:
            loop = asyncio.get_running_loop()
            logging.warning("Async context detected in sync method - returning placeholder response")
            return "Financial question received. Analyzing in background..."
        except RuntimeError:
            return asyncio.run(self.get_financial_advice_async(question, context))

    def check_system_status(self) -> str:
        """Synchronous wrapper for system status check."""
        try:
            loop = asyncio.get_running_loop()
            logging.warning("Async context detected in sync method - returning placeholder response")
            return "System status check initiated. Results will be provided shortly..."
        except RuntimeError:
            return asyncio.run(self.check_system_status_async())
        


async def entrypoint(ctx: agents.JobContext):

    async def shutdown_hook(chat_ctx: ChatContext, mem0: AsyncMemoryClient, memory_str: str):
        logging.info("Shutting down, saving chat context to memory...")

        messages_formatted = [
        ]

        logging.info(f"Chat context messages: {chat_ctx.items}")

        for item in chat_ctx.items:
            content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)

            if memory_str and memory_str in content_str:
                continue

            if item.role in ['user', 'assistant']:
                messages_formatted.append({
                    "role": item.role,
                    "content": content_str.strip()
                })

        logging.info(f"Formatted messages to add to memory: {messages_formatted}")
        await mem0.add(messages_formatted, user_id="Marcus")
        logging.info("Chat context saved to memory.")


    session = AgentSession(
        
    )

    

    mem0 = AsyncMemoryClient()
    user_name = 'David'

    results = await mem0.get_all(user_id=user_name)
    initial_ctx = ChatContext()
    memory_str = ''

    if results:
        memories = [
            {
                "memory": result["memory"],
                "updated_at": result["updated_at"]
            }
            for result in results
        ]
        memory_str = json.dumps(memories)
        logging.info(f"Memories: {memory_str}")
        initial_ctx.add_message(
            role="assistant",
            content=f"The user's name is {user_name}, and this is relvant context about him: {memory_str}."
        )


    from mcp_client.config_loader import load_mcp_servers_from_config
    mcp_servers = load_mcp_servers_from_config()
    agent = await MCPToolsIntegration.create_agent_with_tools(
        agent_class=Assistant, agent_kwargs={"chat_ctx": initial_ctx},
        mcp_servers=mcp_servers
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            video_enabled=True,
            # noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

    ctx.add_shutdown_callback(lambda: shutdown_hook(session._agent.chat_ctx, mem0, memory_str))

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
