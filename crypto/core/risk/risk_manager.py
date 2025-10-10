"""
Risk Manager Module

This module provides comprehensive risk management functionality including:
- Stop-loss and take-profit orders
- Trailing stops
- Daily loss limits
- Position risk monitoring
- Emergency stop mechanisms
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a trading position with risk management parameters."""
    token: str
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: bool = False
    trailing_percentage: float = 0.05
    highest_price: Optional[float] = None
    max_drawdown: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class RiskLimits:
    """Risk limits configuration."""
    max_daily_loss: float = 0.05  # 5% max daily loss
    max_single_position: float = 0.10  # 10% max single position
    max_portfolio_var: float = 0.15  # 15% max portfolio VaR
    max_correlation: float = 0.8  # Max correlation between positions
    max_concentration: float = 0.25  # Max concentration in single asset


class RiskManager:
    """
    Comprehensive risk management system for trading positions.
    """

    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        """
        Initialize risk manager.

        Args:
            risk_limits: Risk limits configuration
        """
        self.risk_limits = risk_limits or RiskLimits()
        self.positions: Dict[str, Position] = {}
        self.daily_pnl_history: List[float] = []
        self.alerts: List[Dict] = []
        self.emergency_stop_triggered = False

        # Callbacks for external actions
        self.on_stop_loss_triggered: Optional[Callable] = None
        self.on_take_profit_triggered: Optional[Callable] = None
        self.on_emergency_stop: Optional[Callable] = None

    def add_position(self,
                    token: str,
                    entry_price: float,
                    quantity: float,
                    stop_loss_percentage: Optional[float] = None,
                    take_profit_percentage: Optional[float] = None,
                    trailing_stop: bool = False,
                    trailing_percentage: float = 0.05) -> bool:
        """
        Add a new position to risk management.

        Args:
            token: Asset token
            entry_price: Entry price
            quantity: Position quantity
            stop_loss_percentage: Stop loss as percentage from entry
            take_profit_percentage: Take profit as percentage from entry
            trailing_stop: Enable trailing stop
            trailing_percentage: Trailing stop percentage

        Returns:
            True if position added successfully, False if risk limits exceeded
        """
        if token in self.positions:
            logger.warning(f"Position for {token} already exists")
            return False

        # Check position size limits
        portfolio_value = self.get_portfolio_value()
        position_value = entry_price * quantity

        if portfolio_value > 0:
            position_percentage = position_value / portfolio_value
            if position_percentage > self.risk_limits.max_single_position:
                self._add_alert("Position size exceeds limit", "warning", {
                    'token': token,
                    'position_percentage': position_percentage,
                    'limit': self.risk_limits.max_single_position
                })
                return False

        # Create position
        position = Position(
            token=token,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(),
            trailing_stop=trailing_stop,
            trailing_percentage=trailing_percentage,
            highest_price=entry_price if trailing_stop else None
        )

        # Set stop loss
        if stop_loss_percentage:
            position.stop_loss = entry_price * (1 - stop_loss_percentage)

        # Set take profit
        if take_profit_percentage:
            position.take_profit = entry_price * (1 + take_profit_percentage)

        self.positions[token] = position

        logger.info(f"Added position for {token}: {quantity} @ {entry_price}")
        return True

    def update_position_price(self, token: str, current_price: float) -> Dict[str, bool]:
        """
        Update position with current price and check risk triggers.

        Args:
            token: Asset token
            current_price: Current market price

        Returns:
            Dictionary indicating which triggers were activated
        """
        if token not in self.positions:
            return {}

        position = self.positions[token]

        # Calculate unrealized P&L
        position_value = current_price * position.quantity
        entry_value = position.entry_price * position.quantity
        position.unrealized_pnl = position_value - entry_value

        # Calculate drawdown
        if position.highest_price is None or current_price > position.highest_price:
            position.highest_price = current_price
            position.max_drawdown = 0.0
        else:
            drawdown = (position.highest_price - current_price) / position.highest_price
            position.max_drawdown = max(position.max_drawdown, drawdown)

        triggers = {
            'stop_loss': False,
            'take_profit': False,
            'trailing_stop': False
        }

        # Check stop loss
        if position.stop_loss and current_price <= position.stop_loss:
            triggers['stop_loss'] = True
            self._trigger_stop_loss(token, current_price)
            return triggers

        # Check take profit
        if position.take_profit and current_price >= position.take_profit:
            triggers['take_profit'] = True
            self._trigger_take_profit(token, current_price)
            return triggers

        # Update trailing stop
        if position.trailing_stop and position.highest_price:
            new_stop = position.highest_price * (1 - position.trailing_percentage)
            if new_stop > position.stop_loss:
                position.stop_loss = new_stop
                triggers['trailing_stop'] = True

        return triggers

    def remove_position(self, token: str, exit_price: Optional[float] = None) -> bool:
        """
        Remove position from risk management.

        Args:
            token: Asset token
            exit_price: Exit price (optional)

        Returns:
            True if position removed successfully
        """
        if token not in self.positions:
            return False

        position = self.positions[token]

        # Calculate realized P&L if exit price provided
        if exit_price:
            realized_pnl = (exit_price - position.entry_price) * position.quantity
            self.daily_pnl_history.append(realized_pnl)

            logger.info(f"Closed position for {token}: Realized P&L = {realized_pnl}")

        del self.positions[token]
        return True

    def check_daily_risk_limits(self) -> bool:
        """
        Check if daily risk limits have been exceeded.

        Returns:
            True if limits exceeded, False otherwise
        """
        if not self.daily_pnl_history:
            return False

        daily_pnl = sum(self.daily_pnl_history)
        portfolio_value = self.get_portfolio_value()

        if portfolio_value <= 0:
            return False

        daily_loss_percentage = -daily_pnl / portfolio_value

        if daily_loss_percentage > self.risk_limits.max_daily_loss:
            self._add_alert("Daily loss limit exceeded", "critical", {
                'daily_loss': daily_loss_percentage,
                'limit': self.risk_limits.max_daily_loss
            })

            self._trigger_emergency_stop("Daily loss limit exceeded")
            return True

        return False

    def check_portfolio_concentration(self) -> bool:
        """
        Check portfolio concentration risk.

        Returns:
            True if concentration limits exceeded
        """
        portfolio_value = self.get_portfolio_value()
        if portfolio_value <= 0:
            return False

        max_concentration = 0.0
        max_token = None

        for token, position in self.positions.items():
            position_value = position.entry_price * position.quantity
            concentration = position_value / portfolio_value

            if concentration > max_concentration:
                max_concentration = concentration
                max_token = token

        if max_concentration > self.risk_limits.max_concentration:
            self._add_alert("Portfolio concentration exceeded", "warning", {
                'token': max_token,
                'concentration': max_concentration,
                'limit': self.risk_limits.max_concentration
            })
            return True

        return False

    def get_portfolio_value(self) -> float:
        """
        Calculate current portfolio value based on entry prices.

        Returns:
            Total portfolio value
        """
        return sum(position.entry_price * position.quantity
                  for position in self.positions.values())

    def get_portfolio_risk_metrics(self) -> Dict[str, float]:
        """
        Calculate portfolio risk metrics.

        Returns:
            Dictionary of risk metrics
        """
        if not self.positions:
            return {}

        portfolio_value = self.get_portfolio_value()
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        max_drawdown = max((pos.max_drawdown for pos in self.positions.values()), default=0.0)

        # Calculate portfolio concentration
        concentrations = []
        for position in self.positions.values():
            position_value = position.entry_price * position.quantity
            concentrations.append(position_value / portfolio_value)

        herfindahl_index = sum(c**2 for c in concentrations)  # Concentration measure

        return {
            'portfolio_value': portfolio_value,
            'unrealized_pnl': total_unrealized_pnl,
            'pnl_percentage': total_unrealized_pnl / portfolio_value if portfolio_value > 0 else 0,
            'max_drawdown': max_drawdown,
            'concentration_index': herfindahl_index,
            'num_positions': len(self.positions)
        }

    def emergency_stop(self, reason: str = "Manual emergency stop"):
        """
        Trigger emergency stop for all positions.

        Args:
            reason: Reason for emergency stop
        """
        logger.critical(f"Emergency stop triggered: {reason}")

        self.emergency_stop_triggered = True
        self._add_alert("Emergency stop triggered", "critical", {'reason': reason})

        # Close all positions
        tokens_to_close = list(self.positions.keys())
        for token in tokens_to_close:
            self.remove_position(token)

        if self.on_emergency_stop:
            self.on_emergency_stop(reason)

    def reset_daily_pnl(self):
        """Reset daily P&L history."""
        self.daily_pnl_history.clear()

    def get_alerts(self, clear: bool = False) -> List[Dict]:
        """
        Get current alerts.

        Args:
            clear: Whether to clear alerts after retrieval

        Returns:
            List of alerts
        """
        alerts = self.alerts.copy()
        if clear:
            self.alerts.clear()
        return alerts

    def _trigger_stop_loss(self, token: str, current_price: float):
        """Handle stop loss trigger."""
        logger.warning(f"Stop loss triggered for {token} @ {current_price}")

        position = self.positions[token]
        loss = (current_price - position.entry_price) * position.quantity

        self._add_alert("Stop loss triggered", "warning", {
            'token': token,
            'entry_price': position.entry_price,
            'exit_price': current_price,
            'loss': loss
        })

        self.remove_position(token, current_price)

        if self.on_stop_loss_triggered:
            self.on_stop_loss_triggered(token, current_price, loss)

    def _trigger_take_profit(self, token: str, current_price: float):
        """Handle take profit trigger."""
        logger.info(f"Take profit triggered for {token} @ {current_price}")

        position = self.positions[token]
        profit = (current_price - position.entry_price) * position.quantity

        self._add_alert("Take profit triggered", "info", {
            'token': token,
            'entry_price': position.entry_price,
            'exit_price': current_price,
            'profit': profit
        })

        self.remove_position(token, current_price)

        if self.on_take_profit_triggered:
            self.on_take_profit_triggered(token, current_price, profit)

    def _trigger_emergency_stop(self, reason: str):
        """Handle emergency stop trigger."""
        self.emergency_stop(reason)

    def _add_alert(self, message: str, severity: str, details: Dict):
        """Add alert to alert queue."""
        alert = {
            'timestamp': datetime.now(),
            'message': message,
            'severity': severity,
            'details': details
        }
        self.alerts.append(alert)

        # Log alert
        log_level = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'critical': logging.CRITICAL
        }.get(severity, logging.INFO)

        logger.log(log_level, f"Risk Alert: {message} - {details}")


class AdaptiveRiskManager(RiskManager):
    """
    Adaptive risk manager that adjusts limits based on market conditions.
    """

    def __init__(self, risk_limits: Optional[RiskLimits] = None, adaptation_factor: float = 0.1):
        """
        Initialize adaptive risk manager.

        Args:
            risk_limits: Base risk limits
            adaptation_factor: How much to adjust limits (0-1)
        """
        super().__init__(risk_limits)
        self.adaptation_factor = adaptation_factor
        self.market_volatility = 1.0  # Baseline volatility

    def adapt_to_market_conditions(self, market_volatility: float):
        """
        Adapt risk limits based on market volatility.

        Args:
            market_volatility: Current market volatility measure
        """
        self.market_volatility = market_volatility

        # Increase caution in high volatility
        if market_volatility > 1.5:
            adjustment = 1 - self.adaptation_factor
        # Relax limits in low volatility
        elif market_volatility < 0.7:
            adjustment = 1 + self.adaptation_factor
        else:
            adjustment = 1.0

        # Adjust limits
        self.risk_limits.max_daily_loss *= adjustment
        self.risk_limits.max_single_position *= adjustment
        self.risk_limits.max_portfolio_var *= adjustment

        logger.info(".2f")


def create_default_risk_manager() -> RiskManager:
    """
    Create a risk manager with default conservative settings.

    Returns:
        Configured RiskManager instance
    """
    limits = RiskLimits(
        max_daily_loss=0.03,  # 3% max daily loss
        max_single_position=0.05,  # 5% max single position
        max_portfolio_var=0.10,  # 10% max portfolio VaR
        max_correlation=0.7,
        max_concentration=0.15
    )

    return RiskManager(limits)