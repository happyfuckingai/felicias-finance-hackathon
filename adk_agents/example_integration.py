"""
Example integration of Google Cloud ADK with Felicia Finance
This demonstrates how to integrate the ADK wrapper with the existing LiveKit agent
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk.adk_integration import ADKIntegration
from agent_core.agent import FeliciaAgent  # Import your existing agent


async def main():
    """Main integration example"""

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting Felicia Finance ADK integration example...")

    try:
        # Initialize existing Felicia agent
        felicia_agent = FeliciaAgent()
        logger.info("✓ Existing Felicia agent initialized")

        # Initialize ADK integration with existing agent
        adk_integration = ADKIntegration(
            config_path=str(Path(__file__).parent / "config" / "adk_config.yaml"),
            agent_instance=felicia_agent
        )

        # Initialize ADK services
        logger.info("Initializing ADK integration...")
        if not await adk_integration.initialize():
            logger.error("Failed to initialize ADK integration")
            return

        logger.info("✓ ADK integration initialized successfully")

        # Demonstrate system status
        logger.info("Getting system status...")
        status = await adk_integration.get_system_status()
        logger.info(f"System status: {status}")

        # Example financial analysis
        logger.info("Running financial analysis...")
        analysis_result = await adk_integration.analyze_financial_query(
            "What is the current status of my banking and crypto portfolio?"
        )
        logger.info(f"Analysis result: {analysis_result}")

        # Example banking operation
        logger.info("Testing banking integration...")
        banking_result = await adk_integration.handle_banking_request({
            "query": "get_balance",
            "account_id": "main_account"
        })
        logger.info(f"Banking result: {banking_result}")

        # Example crypto operation
        logger.info("Testing crypto integration...")
        crypto_result = await adk_integration.handle_crypto_request({
            "query": "portfolio_analysis",
            "include_risk": True
        })
        logger.info(f"Crypto result: {crypto_result}")

        # Example workflow execution
        logger.info("Executing financial analysis workflow...")
        workflow_result = await adk_integration.execute_financial_workflow(
            "financial_analysis",
            {
                "user_id": "demo_user",
                "timestamp": "2025-01-01T00:00:00Z",
                "query": "Comprehensive portfolio review"
            }
        )
        logger.info(f"Workflow result: {workflow_result}")

        # List deployed agents
        logger.info("Listing deployed ADK agents...")
        agents = await adk_integration.list_deployed_agents()
        logger.info(f"Deployed agents: {len(agents)} found")

        for agent in agents:
            logger.info(f"  - {agent.get('name', 'unknown')}: {agent.get('status', 'unknown')}")

        logger.info("✓ ADK integration example completed successfully!")

    except Exception as e:
        logger.error(f"Integration example failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if 'adk_integration' in locals():
            await adk_integration.cleanup()


async def demo_adk_deployment():
    """Demonstrate ADK agent deployment (requires GCP authentication)"""

    logger = logging.getLogger(__name__)
    logger.info("Demonstrating ADK agent deployment...")

    try:
        adk_integration = ADKIntegration()

        if not await adk_integration.initialize():
            logger.error("Failed to initialize ADK for deployment demo")
            return

        # Deploy a demo agent
        demo_agent_config = {
            "name": "demo_financial_agent",
            "description": "Demo financial analysis agent",
            "capabilities": ["analysis", "reporting", "insights"]
        }

        logger.info("Deploying demo agent to Google Cloud Functions...")
        agent_url = await adk_integration.deploy_agent("demo_financial_agent", demo_agent_config)

        if agent_url:
            logger.info(f"✓ Demo agent deployed successfully: {agent_url}")

            # Test the deployed agent
            logger.info("Testing deployed agent...")
            test_result = await adk_integration.invoke_agent("demo_financial_agent", {
                "action": "status"
            })

            if test_result:
                logger.info(f"✓ Agent test successful: {test_result}")
            else:
                logger.error("✗ Agent test failed")

        else:
            logger.error("✗ Agent deployment failed")

    except Exception as e:
        logger.error(f"Deployment demo failed: {e}")


async def demo_custom_workflow():
    """Demonstrate custom workflow creation and execution"""

    logger = logging.getLogger(__name__)
    logger.info("Demonstrating custom workflow creation...")

    try:
        adk_integration = ADKIntegration()

        if not await adk_integration.initialize():
            logger.error("Failed to initialize ADK for workflow demo")
            return

        # Register a custom workflow
        custom_workflow = {
            "name": "risk_assessment_workflow",
            "steps": [
                {
                    "agent": "banking_agent",
                    "action": "assess_liquidity",
                    "parameters": {"account_id": "main"}
                },
                {
                    "agent": "crypto_agent",
                    "action": "assess_market_risk",
                    "parameters": {"portfolio_id": "user_portfolio"}
                },
                {
                    "agent": "felicia_orchestrator",
                    "action": "consolidate_risk_report",
                    "parameters": {"format": "comprehensive"}
                }
            ]
        }

        adk_integration.register_workflow(custom_workflow)
        logger.info("✓ Custom workflow registered")

        # Execute the custom workflow
        logger.info("Executing custom workflow...")
        result = await adk_integration.execute_financial_workflow(
            "risk_assessment_workflow",
            {
                "user_id": "demo_user",
                "assessment_date": "2025-01-01"
            }
        )

        logger.info(f"✓ Custom workflow executed: {result}")

    except Exception as e:
        logger.error(f"Custom workflow demo failed: {e}")


if __name__ == "__main__":
    # Run the main integration example
    asyncio.run(main())

    # Uncomment to run additional demos (require GCP authentication)
    # asyncio.run(demo_adk_deployment())
    # asyncio.run(demo_custom_workflow())