"""
Risk Handler Module

This module provides the main risk management interface for the trading system.
It integrates VaR calculations, position sizing, risk monitoring, and portfolio analytics.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from ..core.var_calculator import VaRCalculator
from ..core.position_sizer import PositionSizer
from ..core.risk_manager import RiskManager, RiskLimits
from ..core.portfolio_risk import PortfolioRisk, RiskMetrics, PortfolioStats
from ..core.error_handling import handle_errors, TradingError

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessment:
    """Container for comprehensive risk assessment results."""
    overall_risk_level: str  # 'low', 'medium', 'high', 'critical'
    var_95: float
    expected_shortfall: float
    sharpe_ratio: float
    max_drawdown: float
    concentration_risk: float
    correlation_risk: float
    position_limit_breached: bool
    daily_loss_limit_breached: bool
    recommendations: List[str]
    alerts: List[Dict[str, Any]]


@dataclass
class PositionRiskProfile:
    """Risk profile for individual positions."""
    token: str
    position_size: float
    stop_loss_distance: float
    take_profit_distance: float
    unrealized_pnl: float
    risk_contribution: float
    correlation_to_portfolio: float
    volatility: float


class RiskHandler:
    """
    Main risk management handler that coordinates all risk-related functionality.
    """

    def __init__(self,
                 risk_limits: Optional[RiskLimits] = None,
                 confidence_level: float = 0.95,
                 risk_free_rate: float = 0.02):
        """
        Initialize risk handler.

        Args:
            risk_limits: Risk limits configuration
            confidence_level: Confidence level for VaR calculations
            risk_free_rate: Risk-free rate for risk metrics
        """
        self.confidence_level = confidence_level
        self.risk_free_rate = risk_free_rate

        # Initialize core components
        self.var_calculator = VaRCalculator(confidence_level)
        self.position_sizer = PositionSizer()
        self.risk_manager = RiskManager(risk_limits or RiskLimits())
        self.portfolio_risk = PortfolioRisk(risk_free_rate)

        # Risk monitoring state
        self.portfolio_returns: List[float] = []
        self.portfolio_values: List[float] = []
        self.asset_returns: Dict[str, List[float]] = {}
        self.market_returns: List[float] = []

        # Callbacks
        self.on_risk_alert: Optional[Callable] = None
        self.on_emergency_stop: Optional[Callable] = None

        # Monitoring settings
        self.monitoring_active = False
        self.monitoring_interval = 60  # seconds

        logger.info("Risk Handler initialized")

    @handle_errors
    async def assess_portfolio_risk(self,
                                   portfolio: Dict[str, float],
                                   current_prices: Dict[str, float],
                                   historical_data: Optional[Dict[str, pd.DataFrame]] = None) -> RiskAssessment:
        """
        Perform comprehensive portfolio risk assessment.

        Args:
            portfolio: Current portfolio positions {token: quantity}
            current_prices: Current asset prices {token: price}
            historical_data: Historical price data for risk calculations

        Returns:
            Comprehensive risk assessment
        """
        if not portfolio:
            return RiskAssessment(
                overall_risk_level='low',
                var_95=0.0,
                expected_shortfall=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                concentration_risk=0.0,
                correlation_risk=0.0,
                position_limit_breached=False,
                daily_loss_limit_breached=False,
                recommendations=[],
                alerts=[]
            )

        # Calculate portfolio value
        portfolio_value = sum(quantity * current_prices.get(token, 0)
                            for token, quantity in portfolio.items())

        recommendations = []
        alerts = []

        # 1. VaR Calculation
        var_95 = 0.0
        expected_shortfall = 0.0

        if historical_data and len(self.portfolio_returns) > 30:
            try:
                portfolio_returns_series = pd.Series(self.portfolio_returns[-252:])  # Last year
                var_95 = self.var_calculator.calculate_historical_var(
                    portfolio_returns_series, portfolio_value
                )
                expected_shortfall = self.var_calculator.calculate_expected_shortfall(
                    portfolio_returns_series, portfolio_value
                )
            except Exception as e:
                logger.warning(f"VaR calculation failed: {e}")
                alerts.append({
                    'level': 'warning',
                    'message': 'VaR calculation failed',
                    'details': str(e)
                })

        # 2. Risk Metrics
        sharpe_ratio = 0.0
        max_drawdown = 0.0

        if len(self.portfolio_returns) > 30:
            try:
                portfolio_returns_series = pd.Series(self.portfolio_returns)
                portfolio_values_series = pd.Series(self.portfolio_values)

                sharpe_ratio = self.portfolio_risk.calculate_sharpe_ratio(portfolio_returns_series)
                max_drawdown = self.portfolio_risk.calculate_max_drawdown(portfolio_values_series)
            except Exception as e:
                logger.warning(f"Risk metrics calculation failed: {e}")

        # 3. Concentration Risk
        concentration_risk = self._calculate_concentration_risk(portfolio, current_prices, portfolio_value)

        # 4. Correlation Risk
        correlation_risk = 0.0
        if historical_data and len(historical_data) > 1:
            correlation_risk = self._calculate_correlation_risk(historical_data)

        # 5. Check Risk Limits
        position_limit_breached = self._check_position_limits(portfolio, current_prices, portfolio_value)
        daily_loss_limit_breached = self.risk_manager.check_daily_risk_limits()

        # 6. Generate Recommendations
        recommendations = self._generate_recommendations(
            var_95, sharpe_ratio, max_drawdown, concentration_risk,
            position_limit_breached, daily_loss_limit_breached
        )

        # 7. Determine Overall Risk Level
        overall_risk_level = self._determine_overall_risk_level(
            var_95, max_drawdown, concentration_risk, correlation_risk,
            position_limit_breached, daily_loss_limit_breached
        )

        # 8. Get current alerts from risk manager
        risk_alerts = self.risk_manager.get_alerts()
        alerts.extend(risk_alerts)

        return RiskAssessment(
            overall_risk_level=overall_risk_level,
            var_95=var_95,
            expected_shortfall=expected_shortfall,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            concentration_risk=concentration_risk,
            correlation_risk=correlation_risk,
            position_limit_breached=position_limit_breached,
            daily_loss_limit_breached=daily_loss_limit_breached,
            recommendations=recommendations,
            alerts=alerts
        )

    @handle_errors
    async def calculate_optimal_position_size(self,
                                            token: str,
                                            entry_price: float,
                                            portfolio_value: float,
                                            risk_tolerance: float = 0.02,
                                            method: str = 'kelly',
                                            **kwargs) -> Dict[str, Any]:
        """
        Calculate optimal position size using various methods.

        Args:
            token: Asset token
            entry_price: Expected entry price
            portfolio_value: Current portfolio value
            risk_tolerance: Maximum risk per trade
            method: Position sizing method ('kelly', 'fixed_fractional', 'risk_parity')
            **kwargs: Additional parameters for specific methods

        Returns:
            Position sizing results
        """
        if method == 'kelly':
            # Need win rate and return statistics
            win_rate = kwargs.get('win_rate', 0.55)
            avg_win_return = kwargs.get('avg_win_return', 0.10)
            avg_loss_return = kwargs.get('avg_loss_return', -0.05)

            result = self.position_sizer.kelly_criterion(
                win_rate, avg_win_return, avg_loss_return, portfolio_value
            )

        elif method == 'fixed_fractional':
            volatility = kwargs.get('volatility')
            result = {
                'position_size': self.position_sizer.fixed_fractional(
                    portfolio_value, risk_tolerance, volatility
                ),
                'position_value': self.position_sizer.fixed_fractional(
                    portfolio_value, risk_tolerance, volatility
                ) * portfolio_value,
                'max_portfolio_risk': risk_tolerance
            }

        elif method == 'risk_parity':
            # Would need full portfolio data for risk parity
            result = {
                'position_size': risk_tolerance,
                'position_value': risk_tolerance * portfolio_value,
                'method': 'risk_parity',
                'note': 'Requires full portfolio data'
            }

        else:
            raise ValueError(f"Unknown position sizing method: {method}")

        # Check against risk limits
        position_value = result.get('position_value', 0)
        position_percentage = position_value / portfolio_value if portfolio_value > 0 else 0

        if position_percentage > self.risk_manager.risk_limits.max_single_position:
            result['limit_warning'] = True
            result['recommended_size'] = self.risk_manager.risk_limits.max_single_position
            result['recommended_value'] = self.risk_manager.risk_limits.max_single_position * portfolio_value

        return result

    @handle_errors
    async def setup_risk_management(self,
                                   token: str,
                                   entry_price: float,
                                   quantity: float,
                                   stop_loss_percentage: float = 0.05,
                                   take_profit_percentage: float = 0.10,
                                   trailing_stop: bool = False) -> bool:
        """
        Set up risk management for a position.

        Args:
            token: Asset token
            entry_price: Entry price
            quantity: Position quantity
            stop_loss_percentage: Stop loss as percentage from entry
            take_profit_percentage: Take profit as percentage from entry
            trailing_stop: Enable trailing stop

        Returns:
            True if setup successful
        """
        return self.risk_manager.add_position(
            token=token,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss_percentage=stop_loss_percentage,
            take_profit_percentage=take_profit_percentage,
            trailing_stop=trailing_stop
        )

    @handle_errors
    async def update_position_prices(self,
                                    price_updates: Dict[str, float]) -> Dict[str, Dict[str, bool]]:
        """
        Update position prices and check risk triggers.

        Args:
            price_updates: {token: current_price}

        Returns:
            Dictionary of trigger activations per position
        """
        triggers_activated = {}

        for token, current_price in price_updates.items():
            triggers = self.risk_manager.update_position_price(token, current_price)
            if triggers:
                triggers_activated[token] = triggers

        # Check for emergency conditions
        if self.risk_manager.check_daily_risk_limits():
            await self._handle_emergency_stop("Daily loss limit exceeded")

        return triggers_activated

    @handle_errors
    async def get_portfolio_risk_profile(self,
                                        portfolio: Dict[str, float],
                                        historical_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        Get detailed risk profile for entire portfolio.

        Args:
            portfolio: Current portfolio positions
            historical_data: Historical price data

        Returns:
            Comprehensive portfolio risk profile
        """
        # Get basic risk metrics
        portfolio_value = sum(
            quantity * historical_data[token].iloc[-1] if historical_data and token in historical_data
            else quantity * 1.0  # Assume $1 if no data
            for token, quantity in portfolio.items()
        )

        # Calculate risk metrics if we have sufficient data
        risk_metrics = {}
        if len(self.portfolio_returns) > 30:
            portfolio_returns_series = pd.Series(self.portfolio_returns)
            portfolio_values_series = pd.Series(self.portfolio_values)

            comprehensive_metrics = self.portfolio_risk.get_comprehensive_risk_metrics(
                portfolio_returns_series,
                portfolio_values_series,
                self.market_returns if self.market_returns else None
            )
            risk_metrics = asdict(comprehensive_metrics)

        # Calculate position-specific risk profiles
        position_profiles = []
        if historical_data:
            for token, quantity in portfolio.items():
                if token in historical_data:
                    profile = self._calculate_position_risk_profile(
                        token, quantity, historical_data[token]
                    )
                    position_profiles.append(profile)

        return {
            'portfolio_value': portfolio_value,
            'num_positions': len(portfolio),
            'risk_metrics': risk_metrics,
            'position_profiles': [asdict(p) for p in position_profiles],
            'diversification_score': self._calculate_diversification_score(position_profiles),
            'last_updated': datetime.now().isoformat()
        }

    @handle_errors
    async def start_risk_monitoring(self):
        """Start continuous risk monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        logger.info("Risk monitoring started")

        # Start monitoring loop
        asyncio.create_task(self._risk_monitoring_loop())

    @handle_errors
    async def stop_risk_monitoring(self):
        """Stop risk monitoring."""
        self.monitoring_active = False
        logger.info("Risk monitoring stopped")

    async def _risk_monitoring_loop(self):
        """Main risk monitoring loop."""
        while self.monitoring_active:
            try:
                # Perform risk checks
                if self.risk_manager.check_daily_risk_limits():
                    await self._handle_risk_alert("Daily loss limit exceeded")

                if self.risk_manager.check_portfolio_concentration():
                    await self._handle_risk_alert("Portfolio concentration risk detected")

                # Get alerts from risk manager
                alerts = self.risk_manager.get_alerts(clear=True)
                for alert in alerts:
                    await self._handle_risk_alert(alert['message'], alert)

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    def _calculate_concentration_risk(self,
                                     portfolio: Dict[str, float],
                                     prices: Dict[str, float],
                                     portfolio_value: float) -> float:
        """Calculate portfolio concentration risk."""
        if portfolio_value == 0:
            return 0.0

        position_values = [
            quantity * prices.get(token, 0)
            for token, quantity in portfolio.items()
        ]

        # Herfindahl-Hirschman Index (HHI) for concentration
        total_value = sum(position_values)
        concentration_index = sum((value / total_value) ** 2 for value in position_values)

        # Normalize to 0-1 scale (higher values = more concentrated)
        return concentration_index

    def _calculate_correlation_risk(self, historical_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate average correlation risk."""
        if len(historical_data) < 2:
            return 0.0

        try:
            # Get returns for all assets
            returns_data = {}
            for token, df in historical_data.items():
                if 'close' in df.columns:
                    returns_data[token] = df['close'].pct_change().dropna()

            if not returns_data:
                return 0.0

            # Create returns DataFrame
            returns_df = pd.DataFrame(returns_data)

            # Calculate correlation matrix
            corr_matrix = returns_df.corr()

            # Calculate average absolute correlation (excluding diagonal)
            n = len(corr_matrix)
            avg_correlation = (
                corr_matrix.sum().sum() - n  # Subtract diagonal
            ) / (n * (n - 1))  # Divide by number of off-diagonal elements

            return abs(avg_correlation)

        except Exception as e:
            logger.warning(f"Correlation risk calculation failed: {e}")
            return 0.0

    def _check_position_limits(self,
                              portfolio: Dict[str, float],
                              prices: Dict[str, float],
                              portfolio_value: float) -> bool:
        """Check if any position exceeds size limits."""
        for token, quantity in portfolio.items():
            position_value = quantity * prices.get(token, 0)
            position_percentage = position_value / portfolio_value if portfolio_value > 0 else 0

            if position_percentage > self.risk_manager.risk_limits.max_single_position:
                return True
        return False

    def _calculate_position_risk_profile(self,
                                        token: str,
                                        quantity: float,
                                        historical_data: pd.DataFrame) -> PositionRiskProfile:
        """Calculate risk profile for individual position."""
        if 'close' not in historical_data.columns:
            return PositionRiskProfile(
                token=token,
                position_size=quantity,
                stop_loss_distance=0.0,
                take_profit_distance=0.0,
                unrealized_pnl=0.0,
                risk_contribution=0.0,
                correlation_to_portfolio=0.0,
                volatility=0.0
            )

        prices = historical_data['close']
        returns = prices.pct_change().dropna()

        # Calculate volatility
        volatility = returns.std() * np.sqrt(252)  # Annualized

        # Get position info from risk manager
        position_info = None
        if hasattr(self.risk_manager, 'positions') and token in self.risk_manager.positions:
            position = self.risk_manager.positions[token]
            position_info = {
                'stop_loss_distance': abs(position.entry_price - position.stop_loss) / position.entry_price if position.stop_loss else 0.0,
                'take_profit_distance': abs(position.take_profit - position.entry_price) / position.entry_price if position.take_profit else 0.0,
                'unrealized_pnl': position.unrealized_pnl
            }

        return PositionRiskProfile(
            token=token,
            position_size=quantity,
            stop_loss_distance=position_info['stop_loss_distance'] if position_info else 0.0,
            take_profit_distance=position_info['take_profit_distance'] if position_info else 0.0,
            unrealized_pnl=position_info['unrealized_pnl'] if position_info else 0.0,
            risk_contribution=volatility * quantity,  # Simplified
            correlation_to_portfolio=0.0,  # Would need portfolio correlation
            volatility=volatility
        )

    def _calculate_diversification_score(self, position_profiles: List[PositionRiskProfile]) -> float:
        """Calculate portfolio diversification score (0-1, higher is better)."""
        if not position_profiles:
            return 0.0

        # Simple diversification score based on number of positions and risk distribution
        n_positions = len(position_profiles)

        if n_positions == 1:
            return 0.1  # Poor diversification

        # Calculate risk concentration
        total_risk = sum(p.risk_contribution for p in position_profiles)
        if total_risk == 0:
            return 0.5

        risk_weights = [p.risk_contribution / total_risk for p in position_profiles]
        herfindahl_index = sum(w**2 for w in risk_weights)

        # Convert to diversification score (lower concentration = higher diversification)
        diversification_score = 1 - herfindahl_index

        # Adjust based on number of positions
        position_bonus = min(n_positions / 10, 0.3)  # Max bonus for 10+ positions

        return min(diversification_score + position_bonus, 1.0)

    def _generate_recommendations(self,
                                 var_95: float,
                                 sharpe_ratio: float,
                                 max_drawdown: float,
                                 concentration_risk: float,
                                 position_limit_breached: bool,
                                 daily_loss_limit_breached: bool) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []

        if var_95 > 0.15:  # 15% VaR
            recommendations.append("High VaR detected - consider reducing position sizes")

        if sharpe_ratio < 0.5:
            recommendations.append("Low Sharpe ratio - review investment strategy")

        if max_drawdown > 0.20:  # 20% drawdown
            recommendations.append("Significant drawdown - consider rebalancing or reducing risk")

        if concentration_risk > 0.25:
            recommendations.append("High concentration risk - diversify portfolio")

        if position_limit_breached:
            recommendations.append("Position size limits exceeded - reduce position sizes")

        if daily_loss_limit_breached:
            recommendations.append("Daily loss limit breached - halt trading")

        if not recommendations:
            recommendations.append("Risk levels acceptable - continue monitoring")

        return recommendations

    def _determine_overall_risk_level(self,
                                     var_95: float,
                                     max_drawdown: float,
                                     concentration_risk: float,
                                     correlation_risk: float,
                                     position_limit_breached: bool,
                                     daily_loss_limit_breached: bool) -> str:
        """Determine overall risk level."""
        risk_score = 0

        # VaR risk
        if var_95 > 0.10:
            risk_score += 2
        elif var_95 > 0.05:
            risk_score += 1

        # Drawdown risk
        if max_drawdown > 0.15:
            risk_score += 2
        elif max_drawdown > 0.10:
            risk_score += 1

        # Concentration risk
        if concentration_risk > 0.30:
            risk_score += 2
        elif concentration_risk > 0.20:
            risk_score += 1

        # Correlation risk
        if correlation_risk > 0.7:
            risk_score += 1

        # Limit breaches
        if position_limit_breached or daily_loss_limit_breached:
            risk_score += 3

        if risk_score >= 5:
            return 'critical'
        elif risk_score >= 3:
            return 'high'
        elif risk_score >= 1:
            return 'medium'
        else:
            return 'low'

    async def _handle_risk_alert(self, message: str, details: Optional[Dict] = None):
        """Handle risk alert notifications."""
        if self.on_risk_alert:
            await self.on_risk_alert(message, details)

    async def _handle_emergency_stop(self, reason: str):
        """Handle emergency stop situations."""
        logger.critical(f"Emergency stop triggered: {reason}")

        if self.on_emergency_stop:
            await self.on_emergency_stop(reason)

        # Stop monitoring
        await self.stop_risk_monitoring()


# Convenience functions
async def create_risk_handler(risk_limits: Optional[RiskLimits] = None) -> RiskHandler:
    """Create and initialize a risk handler with default settings."""
    handler = RiskHandler(risk_limits)
    return handler


async def quick_risk_assessment(portfolio: Dict[str, float],
                               prices: Dict[str, float]) -> str:
    """Quick risk assessment returning risk level only."""
    handler = RiskHandler()
    assessment = await handler.assess_portfolio_risk(portfolio, prices)
    return assessment.overall_risk_level