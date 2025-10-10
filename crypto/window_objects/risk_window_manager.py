#!/usr/bin/env python3
"""
Risk Management Window Objects Manager

This module manages window objects for the AI Risk Agent, allowing the agent
to dynamically create and manage visual components in the frontend.

Window objects are used by the AI agent to:
- Create risk dashboards
- Show VaR calculations
- Display position sizing recommendations
- Present risk alerts
- Generate portfolio analytics

Integration with HappyOS frontend system.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class RiskWindowManager:
    """Manager for risk management window objects"""

    def __init__(self):
        self.active_windows = {}
        self.window_templates = self._load_window_templates()

    def _load_window_templates(self):
        """Load predefined window templates for common risk management views"""
        return {
            "portfolio_dashboard": {
                "type": "component",
                "componentName": "PortfolioRiskDashboard",
                "props": {
                    "portfolioData": {},
                    "refreshInterval": 30000,
                    "showVaR": True,
                    "showSharpe": True,
                    "showDrawdown": True
                },
                "position": {"x": 0, "y": 0, "w": 12, "h": 6},
                "title": "Portfolio Risk Dashboard"
            },

            "var_calculator": {
                "type": "component",
                "componentName": "VaRCalculator",
                "props": {
                    "tokenId": "BTC",
                    "confidenceLevel": 0.95,
                    "method": "historical"
                },
                "position": {"x": 0, "y": 6, "w": 6, "h": 6},
                "title": "VaR Calculator"
            },

            "position_sizer": {
                "type": "component",
                "componentName": "PositionSizer",
                "props": {
                    "tokenId": "BTC",
                    "capital": 10000,
                    "method": "kelly_criterion"
                },
                "position": {"x": 6, "y": 6, "w": 6, "h": 6},
                "title": "Position Size Optimizer"
            },

            "risk_alerts": {
                "type": "component",
                "componentName": "RiskAlertsPanel",
                "props": {
                    "portfolioData": {},
                    "refreshInterval": 15000,
                    "showAcknowledged": False
                },
                "position": {"x": 0, "y": 12, "w": 8, "h": 6},
                "title": "Risk Alerts Panel"
            },

            "risk_summary": {
                "type": "component",
                "componentName": "RiskSummaryCard",
                "props": {
                    "showOverallRisk": True,
                    "showTopRisks": True,
                    "compact": True
                },
                "position": {"x": 8, "y": 12, "w": 4, "h": 6},
                "title": "Risk Summary"
            }
        }

    async def create_portfolio_dashboard(self, portfolio_data: Dict[str, Any],
                                       position: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Create a portfolio risk dashboard window"""
        window_id = f"portfolio_dashboard_{uuid.uuid4().hex[:8]}"

        window_object = {
            "id": window_id,
            "type": "component",
            "componentName": "PortfolioRiskDashboard",
            "props": {
                "portfolioData": portfolio_data,
                "refreshInterval": 30000,
                "apiEndpoint": "/api/risk"
            },
            "position": position or {"x": 0, "y": 0, "w": 12, "h": 6},
            "title": f"Portfolio Risk - ${portfolio_data.get('total_value', 0):,.0f}",
            "timestamp": datetime.now().isoformat(),
            "autoRefresh": True,
            "category": "risk_management"
        }

        self.active_windows[window_id] = window_object
        logger.info(f"📊 Created portfolio dashboard window: {window_id}")

        return window_object

    async def create_var_calculator(self, token_id: str = "BTC",
                                   method: str = "historical",
                                   position: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Create a VaR calculator window"""
        window_id = f"var_calculator_{uuid.uuid4().hex[:8]}"

        window_object = {
            "id": window_id,
            "type": "component",
            "componentName": "VaRCalculator",
            "props": {
                "tokenId": token_id,
                "method": method,
                "confidenceLevel": 0.95,
                "apiEndpoint": "/api/risk"
            },
            "position": position or {"x": 0, "y": 6, "w": 6, "h": 6},
            "title": f"VaR Calculator - {token_id}",
            "timestamp": datetime.now().isoformat(),
            "category": "risk_analysis"
        }

        self.active_windows[window_id] = window_object
        logger.info(f"📉 Created VaR calculator window: {window_id}")

        return window_object

    async def create_position_sizer(self, token_id: str = "BTC",
                                   capital: float = 10000,
                                   position: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Create a position sizer window"""
        window_id = f"position_sizer_{uuid.uuid4().hex[:8]}"

        window_object = {
            "id": window_id,
            "type": "component",
            "componentName": "PositionSizer",
            "props": {
                "tokenId": token_id,
                "capital": capital,
                "method": "kelly_criterion",
                "apiEndpoint": "/api/risk"
            },
            "position": position or {"x": 6, "y": 6, "w": 6, "h": 6},
            "title": f"Position Sizer - {token_id}",
            "timestamp": datetime.now().isoformat(),
            "category": "position_management"
        }

        self.active_windows[window_id] = window_object
        logger.info(f"🎯 Created position sizer window: {window_id}")

        return window_object

    async def create_risk_alerts_panel(self, portfolio_data: Dict[str, Any],
                                      position: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Create a risk alerts panel window"""
        window_id = f"risk_alerts_{uuid.uuid4().hex[:8]}"

        window_object = {
            "id": window_id,
            "type": "component",
            "componentName": "RiskAlertsPanel",
            "props": {
                "portfolioData": portfolio_data,
                "refreshInterval": 15000,
                "apiEndpoint": "/api/risk"
            },
            "position": position or {"x": 0, "y": 12, "w": 8, "h": 6},
            "title": "Risk Alerts & Notifications",
            "timestamp": datetime.now().isoformat(),
            "autoRefresh": True,
            "category": "risk_monitoring"
        }

        self.active_windows[window_id] = window_object
        logger.info(f"🚨 Created risk alerts panel window: {window_id}")

        return window_object

    async def create_risk_dashboard_layout(self, portfolio_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a complete risk dashboard layout with multiple windows"""
        logger.info("🎨 Creating risk dashboard layout...")

        windows = []

        # Main portfolio dashboard
        dashboard = await self.create_portfolio_dashboard(portfolio_data)
        windows.append(dashboard)

        # VaR calculator for primary holding
        primary_holding = portfolio_data.get('holdings', [{}])[0].get('token_id', 'BTC')
        var_calc = await self.create_var_calculator(primary_holding)
        windows.append(var_calc)

        # Position sizer
        position_sizer = await self.create_position_sizer(primary_holding,
                                                         portfolio_data.get('total_value', 10000))
        windows.append(position_sizer)

        # Risk alerts panel
        alerts_panel = await self.create_risk_alerts_panel(portfolio_data)
        windows.append(alerts_panel)

        logger.info(f"✅ Created risk dashboard layout with {len(windows)} windows")
        return windows

    async def create_custom_risk_component(self, component_name: str,
                                         props: Dict[str, Any],
                                         position: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Create a custom risk management component window"""
        window_id = f"custom_risk_{uuid.uuid4().hex[:8]}"

        window_object = {
            "id": window_id,
            "type": "component",
            "componentName": component_name,
            "props": {
                "apiEndpoint": "/api/risk",
                **props
            },
            "position": position or {"x": 0, "y": 0, "w": 6, "h": 6},
            "title": f"Risk Component - {component_name}",
            "timestamp": datetime.now().isoformat(),
            "category": "custom_risk"
        }

        self.active_windows[window_id] = window_object
        logger.info(f"🔧 Created custom risk component window: {window_id}")

        return window_object

    async def update_window_props(self, window_id: str, new_props: Dict[str, Any]) -> bool:
        """Update properties of an existing window"""
        if window_id not in self.active_windows:
            logger.warning(f"Window {window_id} not found")
            return False

        # Merge new props with existing props
        self.active_windows[window_id]["props"] = {
            **self.active_windows[window_id]["props"],
            **new_props
        }

        self.active_windows[window_id]["timestamp"] = datetime.now().isoformat()
        logger.info(f"📝 Updated window properties: {window_id}")

        return True

    async def close_window(self, window_id: str) -> bool:
        """Close and remove a window"""
        if window_id in self.active_windows:
            del self.active_windows[window_id]
            logger.info(f"❌ Closed window: {window_id}")
            return True

        logger.warning(f"Window {window_id} not found")
        return False

    def get_active_windows(self) -> List[Dict[str, Any]]:
        """Get all active windows"""
        return list(self.active_windows.values())

    def get_windows_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get windows filtered by category"""
        return [w for w in self.active_windows.values() if w.get('category') == category]

    async def create_risk_alert_window(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a specialized risk alert window"""
        window_id = f"risk_alert_{uuid.uuid4().hex[:8]}"

        severity_colors = {
            "critical": "bg-red-100 border-red-300",
            "high": "bg-orange-100 border-orange-300",
            "medium": "bg-yellow-100 border-yellow-300",
            "low": "bg-blue-100 border-blue-300"
        }

        window_object = {
            "id": window_id,
            "type": "alert",
            "severity": alert_data.get('severity', 'medium'),
            "title": alert_data.get('title', 'Risk Alert'),
            "message": alert_data.get('message', ''),
            "recommendations": alert_data.get('recommendations', []),
            "timestamp": datetime.now().isoformat(),
            "position": {"x": 8, "y": 0, "w": 4, "h": 4},
            "style": severity_colors.get(alert_data.get('severity', 'medium'), 'bg-gray-100 border-gray-300'),
            "autoClose": alert_data.get('auto_close', False),
            "category": "risk_alert"
        }

        self.active_windows[window_id] = window_object
        logger.info(f"🚨 Created risk alert window: {window_id}")

        return window_object

    async def broadcast_risk_update(self, update_data: Dict[str, Any]):
        """Broadcast risk update to all relevant windows"""
        logger.info("📡 Broadcasting risk update to windows...")

        update_type = update_data.get('type', 'general')

        for window_id, window in self.active_windows.items():
            if self._should_receive_update(window, update_type):
                await self.update_window_props(window_id, {"lastUpdate": update_data})
                logger.debug(f"📡 Sent update to window: {window_id}")

    def _should_receive_update(self, window: Dict[str, Any], update_type: str) -> bool:
        """Determine if a window should receive a specific update"""
        window_type = window.get('componentName', '')

        # Risk dashboard should receive all risk updates
        if window_type == 'PortfolioRiskDashboard':
            return True

        # VaR calculator should receive market data updates
        if window_type == 'VaRCalculator' and update_type in ['market_data', 'price_update']:
            return True

        # Risk alerts panel should receive alert updates
        if window_type == 'RiskAlertsPanel' and update_type in ['alert', 'risk_change']:
            return True

        return False

# Global instance for easy access
risk_window_manager = RiskWindowManager()

# Utility functions for easy access
async def create_portfolio_dashboard(portfolio_data):
    """Convenience function to create portfolio dashboard"""
    return await risk_window_manager.create_portfolio_dashboard(portfolio_data)

async def create_var_calculator(token_id="BTC"):
    """Convenience function to create VaR calculator"""
    return await risk_window_manager.create_var_calculator(token_id)

async def create_risk_alerts_panel(portfolio_data):
    """Convenience function to create risk alerts panel"""
    return await risk_window_manager.create_risk_alerts_panel(portfolio_data)

async def create_full_risk_dashboard(portfolio_data):
    """Convenience function to create complete risk dashboard"""
    return await risk_window_manager.create_risk_dashboard_layout(portfolio_data)

if __name__ == "__main__":
    # Demo usage
    async def demo():
        # Sample portfolio data
        portfolio = {
            "holdings": [
                {"token_id": "BTC", "amount": 0.5, "current_price": 45000},
                {"token_id": "ETH", "amount": 8.0, "current_price": 3000}
            ],
            "total_value": 100000
        }

        # Create risk dashboard
        windows = await create_full_risk_dashboard(portfolio)
        print(f"Created {len(windows)} risk management windows")

        # Create a risk alert
        alert_data = {
            "severity": "high",
            "title": "High Volatility Detected",
            "message": "BTC volatility has increased by 25% in the last hour",
            "recommendations": ["Consider reducing position size", "Monitor closely"]
        }

        alert_window = await risk_window_manager.create_risk_alert_window(alert_data)
        print(f"Created risk alert window: {alert_window['id']}")

        # Get all active windows
        active = risk_window_manager.get_active_windows()
        print(f"Total active windows: {len(active)}")

    asyncio.run(demo())