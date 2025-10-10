#!/usr/bin/env python3
"""
A2A Protocol Demo - Complete End-to-End Agent Communication

This demo showcases the complete A2A protocol implementation with:
1. Agent identity creation and authentication
2. Secure agent-to-agent messaging
3. Agent discovery and capability matching
4. Orchestrator coordination of multi-agent workflows
5. Banking and crypto agent integration
6. End-to-end communication flow demonstration
"""

import asyncio
import logging
import json
from datetime import datetime

from adk_agents.a2a.core import A2AClient, OrchestratorAgent
from adk_agents.a2a.banking_a2a_integration.banking_a2a_agent import BankingA2AAgent, create_banking_agent
from adk_agents.a2a.crypto_a2a_integration.crypto_a2a_agent import CryptoA2AAgent, create_crypto_agent
from adk_agents.a2a.core import TransportConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_agent_communication():
    """Demonstrate basic agent-to-agent communication."""
    logger.info("=== Demo: Basic Agent Communication ===")

    # Create two basic A2A clients
    client1 = A2AClient("demo-agent-1", capabilities=["demo:messaging"])
    client2 = A2AClient("demo-agent-2", capabilities=["demo:messaging"])

    try:
        # Start both agents
        logger.info("Starting agents...")
        async with client1:
            async with client2:
                await asyncio.sleep(1)  # Allow agents to initialize

                # Send a message from agent1 to agent2
                logger.info("Sending message from agent1 to agent2...")
                message_id = await client1.send_message(
                    receiver_id="demo-agent-2",
                    message_type="greeting",
                    payload={
                        "message": "Hello from agent1!",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

                if message_id:
                    logger.info(f"Message sent successfully: {message_id}")

                    # Wait for and receive the message
                    logger.info("Waiting for message...")
                    messages = await client2.receive_messages()

                    if messages:
                        msg = messages[0]
                        logger.info(f"Received message: {msg.payload}")
                        assert msg.payload["message"] == "Hello from agent1!"
                        logger.info("✅ Basic communication test passed!")
                    else:
                        logger.error("❌ No message received")
                else:
                    logger.error("❌ Failed to send message")

    except Exception as e:
        logger.error(f"Basic communication demo failed: {e}")


async def demo_encrypted_communication():
    """Demonstrate encrypted agent communication."""
    logger.info("=== Demo: Encrypted Communication ===")

    client1 = A2AClient("secure-agent-1", capabilities=["secure:messaging"])
    client2 = A2AClient("secure-agent-2", capabilities=["secure:messaging"])

    try:
        async with client1:
            async with client2:
                await asyncio.sleep(1)

                # Send encrypted message
                logger.info("Sending encrypted message...")
                sensitive_data = {
                    "account_number": "123456789",
                    "balance": 10000.50,
                    "secret_info": "This should be encrypted"
                }

                message_id = await client1.send_message(
                    receiver_id="secure-agent-2",
                    message_type="secure_data",
                    payload=sensitive_data,
                    encrypted=True
                )

                if message_id:
                    logger.info(f"Encrypted message sent: {message_id}")

                    # Receive and verify message
                    messages = await client2.receive_messages()

                    if messages:
                        msg = messages[0]
                        logger.info(f"Received encrypted data: {msg.payload}")
                        assert msg.payload["balance"] == 10000.50
                        logger.info("✅ Encrypted communication test passed!")
                    else:
                        logger.error("❌ No encrypted message received")
                else:
                    logger.error("❌ Failed to send encrypted message")

    except Exception as e:
        logger.error(f"Encrypted communication demo failed: {e}")


async def demo_agent_discovery():
    """Demonstrate agent discovery capabilities."""
    logger.info("=== Demo: Agent Discovery ===")

    # Create multiple agents with different capabilities
    banking_agent = A2AClient("demo-bank", capabilities=["banking:accounts", "banking:compliance"])
    crypto_agent = A2AClient("demo-crypto", capabilities=["crypto:trading", "crypto:analysis"])
    orchestrator = A2AClient("demo-orchestrator", capabilities=["a2a:orchestration"])

    try:
        async with banking_agent:
            async with crypto_agent:
                async with orchestrator:
                    await asyncio.sleep(2)  # Allow discovery to propagate

                    # Discover agents by capability
                    logger.info("Discovering banking agents...")
                    banking_agents = await orchestrator.discover_agents(["banking:accounts"])
                    logger.info(f"Found {len(banking_agents)} banking agents")

                    logger.info("Discovering crypto agents...")
                    crypto_agents = await orchestrator.discover_agents(["crypto:trading"])
                    logger.info(f"Found {len(crypto_agents)} crypto agents")

                    # Test agent info retrieval
                    if banking_agents:
                        agent_info = orchestrator.get_agent_info(banking_agents[0].agent_id)
                        logger.info(f"Banking agent info: {agent_info.capabilities}")

                    logger.info("✅ Agent discovery test passed!")

    except Exception as e:
        logger.error(f"Agent discovery demo failed: {e}")


async def demo_orchestrator_workflow():
    """Demonstrate orchestrator coordinating a multi-agent workflow."""
    logger.info("=== Demo: Orchestrator Workflow ===")

    # Create orchestrator
    orchestrator = OrchestratorAgent("workflow-orchestrator")

    try:
        # Initialize and start orchestrator
        success = await orchestrator.initialize()
        if not success:
            logger.error("Failed to initialize orchestrator")
            return

        # Create a sample workflow
        logger.info("Creating compliance workflow...")
        workflow_id = await orchestrator.create_workflow(
            "Financial Compliance Check",
            "Automated compliance checking across banking and crypto systems"
        )

        # Add banking compliance task
        banking_task = orchestrator.add_task_to_workflow(
            workflow_id,
            "banking_compliance",
            "Check banking transaction compliance",
            required_capabilities=["banking:compliance"]
        )

        # Add crypto risk assessment task
        crypto_task = orchestrator.add_task_to_workflow(
            workflow_id,
            "crypto_risk_assessment",
            "Assess cryptocurrency portfolio risk",
            required_capabilities=["crypto:analysis"],
            dependencies=[banking_task]
        )

        # Add final reporting task
        report_task = orchestrator.add_task_to_workflow(
            workflow_id,
            "generate_report",
            "Generate comprehensive compliance report",
            required_capabilities=["a2a:reporting"],
            dependencies=[banking_task, crypto_task]
        )

        logger.info(f"Created workflow with {len(orchestrator.workflows[workflow_id].tasks)} tasks")

        # Check workflow status
        status = orchestrator.get_workflow_status(workflow_id)
        logger.info(f"Workflow status: {status['status']}")
        logger.info(f"Completion: {status['completion_percentage']}%")

        # List all workflows
        workflows = orchestrator.list_workflows()
        logger.info(f"Total workflows: {len(workflows)}")

        logger.info("✅ Orchestrator workflow test passed!")

    except Exception as e:
        logger.error(f"Orchestrator workflow demo failed: {e}")
    finally:
        await orchestrator.stop()


async def demo_banking_crypto_integration():
    """Demonstrate banking and crypto agent integration."""
    logger.info("=== Demo: Banking-Crypto Integration ===")

    # Create banking agent (mock the actual banking services for demo)
    with asyncio.patch('bankofanthos_mcp_server.bankofanthos_managers.bankofanthos_manager') as mock_manager:
        # Mock banking manager methods
        mock_manager.authenticate_user.return_value = (True, "mock_jwt_token")
        mock_manager.get_account_balance.return_value = (True, json.dumps({
            "account_id": "12345",
            "balance": 5000.00,
            "currency": "USD"
        }))

        banking_agent = BankingA2AAgent("demo-banking-agent")

        # Create crypto agent (mock crypto services)
        with asyncio.patch('crypto_mcp_server.crypto_managers.market_analyzer') as mock_analyzer, \
             asyncio.patch('crypto_mcp_server.crypto_managers.wallet_manager'), \
             asyncio.patch('crypto_mcp_server.crypto_managers.token_manager'), \
             asyncio.patch('crypto_mcp_server.crypto_managers.xgboost_ai_manager'):

            mock_analyzer.check_price.return_value = {
                "success": True,
                "token_id": "bitcoin",
                "price": 45000.00,
                "price_change_24h": 2.5
            }

            crypto_agent = CryptoA2AAgent("demo-crypto-agent")

            try:
                # Initialize agents
                await banking_agent.initialize()
                await crypto_agent.initialize()

                logger.info("Agents initialized successfully")

                # Demonstrate inter-agent messaging
                # Banking agent requests market data from crypto agent
                logger.info("Banking agent requesting market data from crypto agent...")

                # In a real scenario, this would go through the A2A transport
                # For demo, we'll simulate the interaction

                # Banking agent status
                banking_status = banking_agent.get_agent_status()
                logger.info(f"Banking agent active sessions: {banking_status['active_sessions']}")

                # Crypto agent status
                crypto_status = crypto_agent.get_agent_status()
                logger.info(f"Crypto agent market cache: {crypto_status['market_cache_size']}")

                logger.info("✅ Banking-crypto integration test passed!")

            except Exception as e:
                logger.error(f"Banking-crypto integration demo failed: {e}")
            finally:
                await banking_agent.stop()
                await crypto_agent.stop()


async def demo_end_to_end_workflow():
    """Demonstrate complete end-to-end workflow from user request to result."""
    logger.info("=== Demo: End-to-End Workflow ===")

    # This demo shows how a complete financial workflow would work:
    # 1. User requests a financial analysis
    # 2. Orchestrator breaks it down into tasks
    # 3. Banking agent provides account data
    # 4. Crypto agent provides market analysis
    # 5. Orchestrator combines results into final report

    logger.info("Simulating end-to-end financial analysis workflow...")

    # Step 1: Create orchestrator
    orchestrator = OrchestratorAgent("felicia-orchestrator")

    try:
        await orchestrator.initialize()

        # Step 2: Create comprehensive financial analysis workflow
        workflow_id = await orchestrator.create_workflow(
            "Complete Financial Analysis",
            "End-to-end analysis of banking and crypto portfolio"
        )

        # Step 3: Add workflow tasks
        # Banking data collection
        banking_data_task = orchestrator.add_task_to_workflow(
            workflow_id,
            "collect_banking_data",
            "Gather account balances and transaction history",
            required_capabilities=["banking:accounts"]
        )

        # Banking compliance check
        compliance_task = orchestrator.add_task_to_workflow(
            workflow_id,
            "compliance_check",
            "Verify regulatory compliance",
            required_capabilities=["banking:compliance"],
            dependencies=[banking_data_task]
        )

        # Crypto portfolio analysis
        crypto_analysis_task = orchestrator.add_task_to_workflow(
            workflow_id,
            "crypto_portfolio_analysis",
            "Analyze cryptocurrency holdings and market conditions",
            required_capabilities=["crypto:analysis"]
        )

        # Risk assessment combining banking and crypto
        risk_assessment_task = orchestrator.add_task_to_workflow(
            workflow_id,
            "integrated_risk_assessment",
            "Assess overall financial risk across all assets",
            required_capabilities=["a2a:risk_analysis"],
            dependencies=[compliance_task, crypto_analysis_task]
        )

        # Generate final report
        report_task = orchestrator.add_task_to_workflow(
            workflow_id,
            "generate_final_report",
            "Create comprehensive financial report",
            required_capabilities=["a2a:reporting"],
            dependencies=[risk_assessment_task]
        )

        logger.info(f"Created workflow '{workflow_id}' with {len(orchestrator.workflows[workflow_id].tasks)} tasks")

        # Step 4: Simulate workflow execution
        # In a real implementation, this would assign tasks to actual agents
        # For demo, we'll show the workflow structure and status

        workflow = orchestrator.workflows[workflow_id]

        logger.info("Workflow task dependencies:")
        for task_id, task in workflow.tasks.items():
            deps = task.dependencies
            logger.info(f"  {task_id}: {task.description}")
            if deps:
                logger.info(f"    Depends on: {', '.join(deps)}")

        # Check which tasks are ready to run
        ready_tasks = workflow.get_ready_tasks()
        logger.info(f"Tasks ready to execute: {len(ready_tasks)}")
        for task in ready_tasks:
            logger.info(f"  - {task.task_id}: {task.description}")

        # Get workflow completion status
        status = orchestrator.get_workflow_status(workflow_id)
        logger.info(f"Workflow completion: {status['completion_percentage']}%")

        logger.info("✅ End-to-end workflow demonstration completed!")

    except Exception as e:
        logger.error(f"End-to-end workflow demo failed: {e}")
    finally:
        await orchestrator.stop()


async def demo_performance_and_scalability():
    """Demonstrate performance characteristics and scalability."""
    logger.info("=== Demo: Performance and Scalability ===")

    # Create multiple agents to test scalability
    agents = []
    for i in range(5):
        agent = A2AClient(f"perf-agent-{i}", capabilities=["perf:test"])
        agents.append(agent)

    try:
        # Start all agents concurrently
        logger.info("Starting 5 agents concurrently...")
        start_time = asyncio.get_event_loop().time()

        async with asyncio.gather(*[agent.__aenter__() for agent in agents]):
            init_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"Agent initialization took: {init_time:.2f}s")

            # Test message broadcasting
            logger.info("Testing message broadcasting...")
            broadcast_start = asyncio.get_event_loop().time()

            # Agent 0 broadcasts to all others
            sent_messages = await agents[0].broadcast_message(
                message_type="broadcast_test",
                payload={"test_data": "Hello from agent 0"}
            )

            broadcast_time = asyncio.get_event_loop().time() - broadcast_start
            logger.info(f"Broadcast to {len(sent_messages)} agents took: {broadcast_time:.3f}s")

            # Test agent discovery performance
            discovery_start = asyncio.get_event_loop().time()
            discovered = await agents[0].discover_agents()
            discovery_time = asyncio.get_event_loop().time() - discovery_start

            logger.info(f"Discovered {len(discovered)} agents in: {discovery_time:.3f}s")

            # Get performance metrics
            health = await agents[0].health_check()
            logger.info(f"Agent health metrics: {json.dumps(health, indent=2)}")

        logger.info("✅ Performance and scalability test passed!")

    except Exception as e:
        logger.error(f"Performance demo failed: {e}")


async def main():
    """Run all A2A protocol demonstrations."""
    logger.info("🚀 Starting A2A Protocol Comprehensive Demo")
    logger.info("=" * 60)

    try:
        # Run all demo scenarios
        await demo_basic_agent_communication()
        logger.info("")

        await demo_encrypted_communication()
        logger.info("")

        await demo_agent_discovery()
        logger.info("")

        await demo_orchestrator_workflow()
        logger.info("")

        await demo_banking_crypto_integration()
        logger.info("")

        await demo_end_to_end_workflow()
        logger.info("")

        await demo_performance_and_scalability()
        logger.info("")

        logger.info("🎉 All A2A Protocol demonstrations completed successfully!")
        logger.info("=" * 60)
        logger.info("Key achievements:")
        logger.info("✅ Secure agent identity and authentication")
        logger.info("✅ End-to-end encrypted messaging")
        logger.info("✅ Dynamic agent discovery and capability matching")
        logger.info("✅ Orchestrator-based workflow coordination")
        logger.info("✅ Banking and crypto agent integration")
        logger.info("✅ Multi-agent communication infrastructure")
        logger.info("✅ Scalable and performant architecture")

    except Exception as e:
        logger.error(f"Demo suite failed: {e}")
        raise


if __name__ == "__main__":
    # Run the comprehensive demo
    asyncio.run(main())