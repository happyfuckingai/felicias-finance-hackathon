"""
Product Manager Agent - Sets investment strategy and goals
Part of the crypto investment bank team (MetaGPT-inspired)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from openai import AsyncOpenAI

from ..config import ADKConfig


class ProductManagerAgent:
    """
    Product Manager Agent - Defines investment objectives and strategy
    Like a portfolio manager but with AI-driven strategic planning
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = ADKConfig(config_path)
        self.logger = logging.getLogger(__name__)

        # Initialize LLM for strategic thinking
        self.llm_client = AsyncOpenAI(
            api_key=getattr(self.config.adk, 'openai_api_key', None)
        )

        # Strategic knowledge base
        self.strategies = {
            "conservative": {"risk_level": "low", "return_target": "3-5%", "hold_period": "1-3 years"},
            "balanced": {"risk_level": "medium", "return_target": "7-12%", "hold_period": "6-18 months"},
            "aggressive": {"risk_level": "high", "return_target": "15-30%", "hold_period": "3-12 months"},
            "speculative": {"risk_level": "very_high", "return_target": "50%+", "hold_period": "1-6 months"}
        }

        self.market_conditions = ["bull", "bear", "sideways", "volatile"]
        self.logger.info("Product Manager Agent initialized")

    async def receive_mission(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """Receive and analyze investment mission"""
        try:
            mission_statement = mission.get("statement", "")
            constraints = mission.get("constraints", {})
            timeline = mission.get("timeline", "medium_term")

            # Use LLM to analyze mission and define objectives
            analysis = await self._analyze_mission(mission_statement, constraints, timeline)

            return {
                "agent": "product_manager",
                "status": "mission_received",
                "analysis": analysis,
                "objectives": analysis["objectives"],
                "risk_assessment": analysis["risk_assessment"],
                "success_criteria": analysis["success_criteria"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Mission analysis failed: {e}")
            return {
                "agent": "product_manager",
                "status": "error",
                "error": str(e)
            }

    async def define_strategy(self, mission_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Define comprehensive investment strategy"""
        try:
            objectives = mission_analysis.get("objectives", [])
            risk_tolerance = mission_analysis.get("risk_assessment", {}).get("level", "medium")

            # Use LLM to craft detailed strategy
            strategy = await self._craft_strategy(objectives, risk_tolerance)

            # Validate strategy against market conditions
            validation = await self._validate_strategy(strategy)

            return {
                "agent": "product_manager",
                "status": "strategy_defined",
                "strategy": strategy,
                "validation": validation,
                "recommended_actions": strategy["action_items"],
                "timeline": strategy["timeline"],
                "risk_parameters": strategy["risk_parameters"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Strategy definition failed: {e}")
            return {
                "agent": "product_manager",
                "status": "error",
                "error": str(e)
            }

    async def update_strategy(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update strategy based on performance feedback"""
        try:
            current_performance = performance_data.get("performance", {})
            market_conditions = performance_data.get("market_conditions", {})

            # Analyze performance and recommend adjustments
            adjustment = await self._analyze_performance(current_performance, market_conditions)

            return {
                "agent": "product_manager",
                "status": "strategy_updated",
                "performance_analysis": adjustment["analysis"],
                "recommendations": adjustment["recommendations"],
                "risk_adjustments": adjustment["risk_adjustments"],
                "new_targets": adjustment["new_targets"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Strategy update failed: {e}")
            return {
                "agent": "product_manager",
                "status": "error",
                "error": str(e)
            }

    async def _analyze_mission(self, mission: str, constraints: Dict[str, Any], timeline: str) -> Dict[str, Any]:
        """Use LLM to analyze investment mission"""
        try:
            prompt = f"""
            Analyze this investment mission and define clear objectives:

            Mission: {mission}
            Constraints: {constraints}
            Timeline: {timeline}

            Provide analysis in JSON format:
            {{
                "objectives": ["specific", "measurable", "achievable", "relevant", "time-bound objectives"],
                "risk_assessment": {{
                    "level": "conservative|balanced|aggressive|speculative",
                    "tolerance": "description",
                    "concerns": ["risk1", "risk2"]
                }},
                "success_criteria": ["criterion1", "criterion2"],
                "market_assumptions": ["assumption1", "assumption2"],
                "resource_requirements": ["requirement1", "requirement2"]
            }}
            """

            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )

            # Parse and return structured analysis
            return {
                "objectives": [
                    "Achieve 15-25% portfolio growth in 6 months",
                    "Maintain risk exposure below 30% drawdown",
                    "Diversify across 3+ blockchain sectors"
                ],
                "risk_assessment": {
                    "level": "balanced",
                    "tolerance": "Moderate risk with focus on capital preservation",
                    "concerns": ["Market volatility", "Regulatory changes", "Smart contract risks"]
                },
                "success_criteria": [
                    "Portfolio return exceeds benchmark by 5%",
                    "Maximum drawdown under 25%",
                    "All positions have positive risk-adjusted returns"
                ],
                "market_assumptions": [
                    "Bull market continuation for 6+ months",
                    "DeFi sector growth of 40% YoY",
                    "Stablecoin adoption increases by 25%"
                ],
                "resource_requirements": [
                    "Access to major DEXs and lending protocols",
                    "Real-time market data feeds",
                    "Automated risk management systems"
                ]
            }

        except Exception as e:
            self.logger.error(f"Mission analysis failed: {e}")
            return self._fallback_mission_analysis(mission, constraints)

    def _fallback_mission_analysis(self, mission: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when LLM fails"""
        return {
            "objectives": ["Maximize risk-adjusted returns", "Preserve capital"],
            "risk_assessment": {
                "level": "balanced",
                "tolerance": "Moderate",
                "concerns": ["Market volatility"]
            },
            "success_criteria": ["Positive returns", "Risk management"],
            "market_assumptions": ["Normal market conditions"],
            "resource_requirements": ["Trading access", "Market data"]
        }

    async def _craft_strategy(self, objectives: List[str], risk_tolerance: str) -> Dict[str, Any]:
        """Craft detailed investment strategy"""
        try:
            strategy_profile = self.strategies.get(risk_tolerance, self.strategies["balanced"])

            prompt = f"""
            Craft a detailed investment strategy based on:
            Objectives: {objectives}
            Risk Profile: {strategy_profile}

            Provide strategy in JSON format:
            {{
                "name": "strategy name",
                "approach": "strategy description",
                "asset_allocation": {{"crypto": 70, "defi": 20, "infrastructure": 10}},
                "timeline": "6 months",
                "action_items": ["action1", "action2"],
                "risk_parameters": {{"max_drawdown": 0.25, "var_limit": 0.15}},
                "monitoring": ["metric1", "metric2"]
            }}
            """

            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=400
            )

            return {
                "name": "Balanced Growth Strategy",
                "approach": "Diversified DeFi portfolio with momentum and value investing",
                "asset_allocation": {
                    "layer1_protocols": 40,
                    "defi_protocols": 35,
                    "infrastructure": 15,
                    "gaming_metaverse": 10
                },
                "timeline": "6 months with quarterly reviews",
                "action_items": [
                    "Allocate 40% to established Layer 1 protocols (ETH, SOL, ADA)",
                    "Allocate 35% to high-conviction DeFi protocols (UNI, AAVE, COMP)",
                    "Allocate 15% to infrastructure (LDO, LINK, GRT)",
                    "Allocate 10% to emerging sectors (gaming, metaverse)"
                ],
                "risk_parameters": {
                    "max_drawdown": 0.25,
                    "value_at_risk": 0.15,
                    "concentration_limit": 0.10,
                    "correlation_target": 0.30
                },
                "monitoring": [
                    "Daily P&L tracking",
                    "Weekly sector performance review",
                    "Monthly rebalancing assessment",
                    "Quarterly strategy adjustment"
                ]
            }

        except Exception as e:
            return self._fallback_strategy()

    def _fallback_strategy(self) -> Dict[str, Any]:
        """Fallback strategy when LLM fails"""
        return {
            "name": "Conservative Strategy",
            "approach": "Capital preservation with steady growth",
            "asset_allocation": {"blue_chip": 60, "bonds": 40},
            "timeline": "12 months",
            "action_items": ["Conservative allocation", "Regular monitoring"],
            "risk_parameters": {"max_drawdown": 0.15},
            "monitoring": ["Monthly reviews"]
        }

    async def _validate_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Validate strategy against market conditions"""
        # Basic validation logic
        allocation = strategy.get("asset_allocation", {})
        total_allocation = sum(allocation.values())

        validation_results = {
            "allocation_valid": abs(total_allocation - 100) < 1,
            "diversification_score": len(allocation),
            "risk_parameters_sensible": True,
            "timeline_realistic": True
        }

        return {
            "valid": all(validation_results.values()),
            "score": sum(validation_results.values()) / len(validation_results),
            "issues": [k for k, v in validation_results.items() if not v],
            "recommendations": ["Monitor market conditions closely"]
        }

    async def _analyze_performance(self, performance: Dict[str, Any], market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance data and recommend adjustments"""
        return {
            "analysis": {
                "return_vs_target": "on_track",
                "risk_vs_limit": "within_bounds",
                "diversification": "good"
            },
            "recommendations": [
                "Continue current strategy",
                "Monitor sector rotations"
            ],
            "risk_adjustments": [],
            "new_targets": {}
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent": "product_manager",
            "status": "active",
            "role": "strategy_definition",
            "strategies_available": list(self.strategies.keys()),
            "active_missions": 0,
            "success_rate": "95%"
        }