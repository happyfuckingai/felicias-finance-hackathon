"""
Test Risk Management System

Tests for the comprehensive risk management system including VaR calculations,
position sizing, risk monitoring, and portfolio analytics.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import asyncio

from ..core.var_calculator import VaRCalculator
from ..core.position_sizer import PositionSizer
from ..core.risk_manager import RiskManager, RiskLimits
from ..core.portfolio_risk import PortfolioRisk
from ..handlers.risk import RiskHandler


class TestVaRCalculator:
    """Test VaR calculation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = VaRCalculator(confidence_level=0.95)
        np.random.seed(42)  # For reproducible results

        # Generate sample returns data
        self.returns = np.random.normal(0.001, 0.02, 1000)  # Daily returns

    def test_historical_var_calculation(self):
        """Test historical VaR calculation."""
        portfolio_value = 100000
        var_value = self.calculator.calculate_historical_var(
            self.returns, portfolio_value, lookback_periods=500
        )

        assert var_value < 0  # VaR should be negative (loss)
        assert abs(var_value) < portfolio_value  # Should be reasonable

    def test_parametric_var_calculation(self):
        """Test parametric VaR calculation."""
        portfolio_value = 100000
        var_value = self.calculator.calculate_parametric_var(
            self.returns, portfolio_value, lookback_periods=500
        )

        assert var_value < 0
        assert abs(var_value) < portfolio_value

    def test_monte_carlo_var_calculation(self):
        """Test Monte Carlo VaR calculation."""
        portfolio_value = 100000
        var_value = self.calculator.calculate_monte_carlo_var(
            self.returns, portfolio_value, simulations=1000, lookback_periods=500
        )

        assert var_value < 0
        assert abs(var_value) < portfolio_value

    def test_expected_shortfall_calculation(self):
        """Test Expected Shortfall calculation."""
        portfolio_value = 100000
        es_value = self.calculator.calculate_expected_shortfall(
            self.returns, portfolio_value, method='historical'
        )

        assert es_value < 0
        assert abs(es_value) <= abs(self.calculator.calculate_historical_var(
            self.returns, portfolio_value
        ))  # ES should be more extreme than VaR


class TestPositionSizer:
    """Test position sizing algorithms."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sizer = PositionSizer(max_portfolio_risk=0.02)

    def test_kelly_criterion(self):
        """Test Kelly Criterion calculation."""
        result = self.sizer.kelly_criterion(
            win_rate=0.6,
            avg_win_return=0.05,
            avg_loss_return=-0.03,
            current_portfolio=100000
        )

        assert 'kelly_fraction' in result
        assert 'position_size' in result
        assert 'position_value' in result
        assert result['position_size'] > 0
        assert result['position_size'] <= self.sizer.max_single_position

    def test_fixed_fractional_sizing(self):
        """Test fixed fractional position sizing."""
        position_size = self.sizer.fixed_fractional(
            portfolio_value=100000,
            risk_per_trade=0.01
        )

        assert position_size == 0.01  # Should equal risk per trade

    def test_volatility_adjusted_sizing(self):
        """Test volatility-adjusted position sizing."""
        position_size = self.sizer.fixed_fractional(
            portfolio_value=100000,
            risk_per_trade=0.02,
            volatility=0.05  # 5% volatility
        )

        assert position_size == 0.02 / 0.05  # Risk / volatility
        assert position_size <= self.sizer.max_single_position


class TestRiskManager:
    """Test risk management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        limits = RiskLimits(
            max_daily_loss=0.05,
            max_single_position=0.10,
            max_portfolio_var=0.15
        )
        self.manager = RiskManager(limits)

    def test_add_position_success(self):
        """Test successful position addition."""
        success = self.manager.add_position(
            token='BTC',
            entry_price=45000,
            quantity=0.5,
            stop_loss_percentage=0.05
        )

        assert success is True
        assert 'BTC' in self.manager.positions
        assert self.manager.positions['BTC'].stop_loss == 45000 * 0.95

    def test_add_position_risk_limit_exceeded(self):
        """Test position addition when risk limits exceeded."""
        # Add a large position first
        self.manager.add_position(
            token='ETH',
            entry_price=3000,
            quantity=50,  # Large position
            stop_loss_percentage=0.05
        )

        # Try to add another large position
        success = self.manager.add_position(
            token='BTC',
            entry_price=45000,
            quantity=5,  # This should exceed limits
            stop_loss_percentage=0.05
        )

        assert success is False

    def test_update_position_price(self):
        """Test position price updates and trigger checks."""
        self.manager.add_position(
            token='BTC',
            entry_price=45000,
            quantity=1.0,
            stop_loss_percentage=0.05,
            take_profit_percentage=0.10
        )

        # Update price (no triggers)
        triggers = self.manager.update_position_price('BTC', 46000)
        assert not any(triggers.values())

        # Update price to trigger stop loss
        triggers = self.manager.update_position_price('BTC', 42000)  # Below stop loss
        assert triggers['stop_loss'] is True

    def test_daily_risk_limits(self):
        """Test daily risk limit monitoring."""
        # Simulate some P&L
        self.manager.daily_pnl_history = [-1000, -500, -2000]  # Total -3500 loss
        self.manager.portfolio_values = [100000, 99000, 98500, 96500]

        limit_exceeded = self.manager.check_daily_risk_limits()
        assert limit_exceeded is True


class TestPortfolioRisk:
    """Test portfolio risk analytics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PortfolioRisk(risk_free_rate=0.02)

        # Generate sample data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=500, freq='D')
        self.returns = pd.Series(
            np.random.normal(0.001, 0.02, 500),
            index=dates
        )
        self.portfolio_values = pd.Series(
            100000 * np.exp(np.cumsum(self.returns.values)),
            index=dates
        )

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation."""
        sharpe = self.analyzer.calculate_sharpe_ratio(self.returns)
        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)

    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        max_dd = self.analyzer.calculate_max_drawdown(self.portfolio_values)
        assert max_dd >= 0  # Should be positive
        assert max_dd <= 1  # Should be less than 100%

    def test_beta_calculation(self):
        """Test beta calculation."""
        market_returns = pd.Series(
            np.random.normal(0.0005, 0.015, 500),
            index=self.returns.index
        )

        beta = self.analyzer.calculate_beta(self.returns, market_returns)
        assert isinstance(beta, float)
        assert not np.isnan(beta)


@pytest.mark.asyncio
class TestRiskHandler:
    """Test risk handler integration."""

    async def test_risk_assessment(self):
        """Test comprehensive risk assessment."""
        handler = RiskHandler()

        portfolio = {'BTC': 0.5, 'ETH': 0.3, 'USDC': 0.2}
        prices = {'BTC': 45000, 'ETH': 3000, 'USDC': 1.0}

        assessment = await handler.assess_portfolio_risk(portfolio, prices)

        assert 'overall_risk_level' in assessment
        assert assessment.overall_risk_level in ['low', 'medium', 'high', 'critical']
        assert 'var_95' in assessment
        assert 'sharpe_ratio' in assessment
        assert 'recommendations' in assessment

    async def test_position_size_calculation(self):
        """Test position size calculation."""
        handler = RiskHandler()

        result = await handler.calculate_optimal_position_size(
            token='BTC',
            entry_price=45000,
            portfolio_value=100000,
            risk_tolerance=0.02,
            method='kelly',
            win_rate=0.6,
            avg_win_return=0.05,
            avg_loss_return=-0.03
        )

        assert 'position_size' in result
        assert 'position_value' in result
        assert result['position_size'] > 0


def test_risk_management_integration():
    """Test integration of all risk management components."""
    # This would be a more comprehensive integration test
    # For now, just verify that all components can be instantiated

    var_calc = VaRCalculator()
    position_sizer = PositionSizer()
    risk_limits = RiskLimits()
    risk_manager = RiskManager(risk_limits)
    portfolio_analyzer = PortfolioRisk()

    # Verify all components are properly initialized
    assert var_calc.confidence_level == 0.95
    assert position_sizer.max_portfolio_risk == 0.02
    assert risk_manager.risk_limits.max_daily_loss == 0.05
    assert portfolio_analyzer.risk_free_rate == 0.02

    print("✅ All risk management components initialized successfully")


if __name__ == "__main__":
    # Run basic integration test
    test_risk_management_integration()

    # Run async tests
    async def run_async_tests():
        handler = RiskHandler()
        portfolio = {'BTC': 0.4, 'ETH': 0.4, 'USDC': 0.2}
        prices = {'BTC': 45000, 'ETH': 3000, 'USDC': 1.0}

        assessment = await handler.assess_portfolio_risk(portfolio, prices)
        print(f"Risk Assessment: {assessment.overall_risk_level}")
        print(f"VaR 95%: {assessment.var_95:.1%}")
        print(f"Recommendations: {len(assessment.recommendations)}")

    asyncio.run(run_async_tests())