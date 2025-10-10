#!/usr/bin/env python3
"""
Health Monitoring System for Felicia's Finance
Provides health checks and monitoring for all system components
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """Health monitoring system for Felicia's Finance"""

    def __init__(self):
        self.components = {
            "agent": {"status": "unknown", "last_check": None, "details": {}},
            "mcp_banking": {"status": "unknown", "last_check": None, "details": {}},
            "mcp_crypto": {"status": "unknown", "last_check": None, "details": {}},
            "adk_agents": {"status": "unknown", "last_check": None, "details": {}},
            "frontend": {"status": "unknown", "last_check": None, "details": {}}
        }
        self.check_interval = 30  # seconds
        self.last_full_check = None

    async def check_agent_health(self) -> Dict[str, Any]:
        """Check agent health"""
        try:
            # Basic agent health check - file exists and can be imported
            agent_file = "agent_core/agent.py"
            if os.path.exists(agent_file):
                # Try importing agent module
                try:
                    spec = importlib.util.spec_from_file_location("agent_module", agent_file)
                    agent_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(agent_module)
                    return {
                        "status": "healthy",
                        "message": "Agent module loads successfully",
                        "details": {"file_exists": True, "importable": True}
                    }
                except Exception as e:
                    return {
                        "status": "degraded",
                        "message": f"Agent module has import issues: {e}",
                        "details": {"file_exists": True, "importable": False, "error": str(e)}
                    }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Agent file not found",
                    "details": {"file_exists": False}
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Agent health check failed: {e}",
                "details": {"error": str(e)}
            }

    async def check_mcp_server_health(self, service_name: str, port: int) -> Dict[str, Any]:
        """Check MCP server health"""
        try:
            import httpx
            timeout = httpx.Timeout(5.0)

            # Try to connect to MCP server
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"http://localhost:{port}/health")
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "message": f"{service_name} server responding",
                        "details": {"port": port, "response_time": response.elapsed.total_seconds()}
                    }
                else:
                    return {
                        "status": "degraded",
                        "message": f"{service_name} server returned status {response.status_code}",
                        "details": {"port": port, "status_code": response.status_code}
                    }
        except httpx.ConnectError:
            return {
                "status": "unhealthy",
                "message": f"{service_name} server not responding on port {port}",
                "details": {"port": port, "error": "connection refused"}
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"{service_name} health check failed: {e}",
                "details": {"port": port, "error": str(e)}
            }

    async def check_adk_integration_health(self) -> Dict[str, Any]:
        """Check ADK agents health"""
        try:
            # Try importing ADK integration
            sys.path.insert(0, 'adk_agents')
            try:
                from adk_agents.adk.adk_integration import ADKIntegration
                # Try creating instance (lazy initialization)
                adk = ADKIntegration()
                return {
                    "status": "healthy",
                    "message": "ADK integration loads (lazy initialization)",
                    "details": {"importable": True, "lazy_init": True}
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "message": f"ADK integration has issues: {e}",
                    "details": {"importable": False, "error": str(e)}
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"ADK health check failed: {e}",
                "details": {"error": str(e)}
            }

    async def check_frontend_health(self) -> Dict[str, Any]:
        """Check frontend health"""
        try:
            # Check if React app is running (basic port check)
            import httpx
            timeout = httpx.Timeout(2.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get("http://localhost:3000")
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "message": "Frontend responding on port 3000",
                        "details": {"port": 3000, "response_time": response.elapsed.total_seconds()}
                    }
                else:
                    return {
                        "status": "degraded",
                        "message": f"Frontend returned status {response.status_code}",
                        "details": {"port": 3000, "status_code": response.status_code}
                    }
        except httpx.ConnectError:
            return {
                "status": "unhealthy",
                "message": "Frontend not responding on port 3000",
                "details": {"port": 3000, "error": "connection refused"}
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Frontend health check failed: {e}",
                "details": {"port": 3000, "error": str(e)}
            }

    async def perform_full_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all components"""
        logger.info("Performing full health check...")

        # Update component statuses
        self.components["agent"]["status"] = "checking"
        self.components["agent"]["last_check"] = datetime.now().isoformat()

        # Check each component
        results = await asyncio.gather(
            self.check_agent_health(),
            self.check_mcp_server_health("banking", 8001),
            self.check_mcp_server_health("crypto", 8000),
            self.check_adk_integration_health(),
            self.check_frontend_health()
        )

        # Update component statuses
        component_names = ["agent", "mcp_banking", "mcp_crypto", "adk_agents", "frontend"]

        for name, result in zip(component_names, results):
            self.components[name]["status"] = result["status"]
            self.components[name]["details"] = result["details"]
            self.components[name]["last_check"] = datetime.now().isoformat()
            self.components[name]["message"] = result["message"]

        self.last_full_check = datetime.now()

        # Calculate overall health
        statuses = [comp["status"] for comp in self.components.values()]
        if all(status == "healthy" for status in statuses):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        health_report = {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": self.components,
            "summary": {
                "total_components": len(self.components),
                "healthy": sum(1 for comp in self.components.values() if comp["status"] == "healthy"),
                "degraded": sum(1 for comp in self.components.values() if comp["status"] == "degraded"),
                "unhealthy": sum(1 for comp in self.components.values() if comp["status"] == "unhealthy"),
                "unknown": sum(1 for comp in self.components.values() if comp["status"] == "unknown")
            }
        }

        logger.info(f"Health check complete: {overall_status}")
        return health_report

    async def get_health_report(self) -> Dict[str, Any]:
        """Get current health report"""
        # Perform fresh check if needed
        if self.last_full_check is None or (datetime.now() - self.last_full_check) > timedelta(seconds=self.check_interval):
            await self.perform_full_health_check()

        return {
            "overall_status": self._calculate_overall_status(),
            "timestamp": datetime.now().isoformat(),
            "components": self.components,
            "last_full_check": self.last_full_check.isoformat() if self.last_full_check else None
        }

    def _calculate_overall_status(self) -> str:
        """Calculate overall system status"""
        statuses = [comp["status"] for comp in self.components.values()]
        if all(status == "healthy" for status in statuses):
            return "healthy"
        elif any(status == "unhealthy" for status in statuses):
            return "unhealthy"
        elif any(status == "degraded" for status in statuses):
            return "degraded"
        else:
            return "unknown"


async def main():
    """Main function for health monitoring"""
    monitor = HealthMonitor()

    print("🚀 Starting Felicia's Finance Health Monitor")
    print("Press Ctrl+C to stop monitoring")

    try:
        while True:
            report = await monitor.perform_full_health_check()

            # Print summary
            print(f"\n📊 Health Check - {report['overall_status'].upper()}")
            print(f"Time: {report['timestamp']}")
            print("Components:")

            for name, comp in report['components'].items():
                status_icon = {
                    "healthy": "✅",
                    "degraded": "⚠️",
                    "unhealthy": "❌",
                    "unknown": "❓"
                }.get(comp["status"], "❓")

                print(f"  {status_icon} {name}: {comp['status']} - {comp.get('message', 'No message')}")

            print(f"\nSummary: {report['summary']['healthy']}/{report['summary']['total_components']} healthy")

            await asyncio.sleep(monitor.check_interval)

    except KeyboardInterrupt:
        print("\n🛑 Health monitoring stopped")


if __name__ == "__main__":
    # Add import for importlib if needed
    import importlib.util

    asyncio.run(main())