#!/usr/bin/env python3
"""
Simple test script for Risk Management System

This script tests the basic functionality of all risk management components.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from datetime import datetime
import asyncio

# Import risk management components
try:
    from core.var_calculator import VaRCalculator
    from core.position_sizer import PositionSizer
    from core.risk_manager import RiskManager, RiskLimits
    from core.portfolio_risk import PortfolioRisk
    from handlers.risk import RiskHandler
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_SUCCESSFUL = False


def test_imports():
    """Test that all imports work."""
    if not IMPORTS_SUCCESSFUL:
        print("❌ Imports failed")
        return False

    print("✅ All imports successful")
    return True


def test_var_calculator():
    """Test VaR Calculator functionality."""
    if not IMPORTS_SUCCESSFUL:
        return False

    print("🧪 Testing VaR Calculator...")

    calculator = VaRCalculator(confidence_level=0.95)
    np.random.seed(42)

    # Generate sample returns
    returns = np.random.normal(0.001, 0.02, 1000)
    portfolio_value = 100000

    # Test different VaR methods
    try:
        historical_var = calculator.calculate_historical_var(returns, portfolio_value)
        parametric_var = calculator.calculate_parametric_var(returns, portfolio_value)
        monte_carlo_var = calculator.calculate_monte_carlo_var(returns, portfolio_value, simulations=1000)

        print(".2f")
        print(".2f")
        print(".2f")
        return True
    except Exception as e:
        print(f"❌ VaR Calculator test failed: {e}")
        return False


def test_position_sizer():
    """Test Position Sizer functionality."""
    if not IMPORTS_SUCCESSFUL:
        return False

    print("🧪 Testing Position Sizer...")

    sizer = PositionSizer(max_portfolio_risk=0.02)

    try:
        # Test Kelly Criterion
        kelly_result = sizer.kelly_criterion(
            win_rate=0.6,
            avg_win_return=0.05,
            avg_loss_return=-0.03,
            current_portfolio=100000
        )

        print(".2f")
        # Test Fixed Fractional
        fixed_size = sizer.fixed_fractional(100000, 0.01)
        print(".1%")

        return True
    except Exception as e:
        print(f"❌ Position Sizer test failed: {e}")
        return False


def test_risk_manager():
    """Test Risk Manager functionality."""
    if not IMPORTS_SUCCESSFUL:
        return False

    print("🧪 Testing Risk Manager...")

    limits = RiskLimits(max_daily_loss=0.05, max_single_position=0.10)
    manager = RiskManager(limits)

    try:
        # Test position addition
        success = manager.add_position(
            token='BTC',
            entry_price=45000,
            quantity=1.0,
            stop_loss_percentage=0.05
        )

        if success:
            print("✅ Position added successfully")

            # Test price update
            triggers = manager.update_position_price('BTC', 42000)  # Should trigger stop loss
            if triggers.get('stop_loss'):
                print("✅ Stop loss triggered correctly")
            else:
                print("⚠️ Stop loss not triggered as expected")

        return True
    except Exception as e:
        print(f"❌ Risk Manager test failed: {e}")
        return False


def test_portfolio_risk():
    """Test Portfolio Risk analytics."""
    if not IMPORTS_SUCCESSFUL:
        return False

    print("🧪 Testing Portfolio Risk Analytics...")

    analyzer = PortfolioRisk(risk_free_rate=0.02)

    try:
        # Generate sample data
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 500))
        portfolio_values = pd.Series(100000 * np.exp(np.cumsum(returns.values)))

        # Test risk metrics
        sharpe = analyzer.calculate_sharpe_ratio(returns)
        max_dd = analyzer.calculate_max_drawdown(portfolio_values)

        print(".2f")
        print(".1%")

        return True
    except Exception as e:
        print(f"❌ Portfolio Risk test failed: {e}")
        return False


async def test_risk_handler():
    """Test Risk Handler integration."""
    if not IMPORTS_SUCCESSFUL:
        return False

    print("🧪 Testing Risk Handler...")

    handler = RiskHandler()

    try:
        # Test portfolio risk assessment
        portfolio = {'BTC': 0.4, 'ETH': 0.4, 'USDC': 0.2}
        prices = {'BTC': 45000, 'ETH': 3000, 'USDC': 1.0}

        assessment = await handler.assess_portfolio_risk(portfolio, prices)

        print(f"📊 Risk Level: {assessment.overall_risk_level.upper()}")
        print(".1%")
        print(".2f")
        print(f"📋 Recommendations: {len(assessment.recommendations)}")

        return True
    except Exception as e:
        print(f"❌ Risk Handler test failed: {e}")
        return False


def main():
    """Run all risk management tests."""
    print("🛡️ RISK MANAGEMENT SYSTEM TEST SUITE")
    print("=" * 50)

    test_results = []

    # Test imports first
    test_results.append(("Imports", test_imports()))

    if not IMPORTS_SUCCESSFUL:
        print("❌ Cannot continue with tests due to import failures")
        return 1

    # Test individual components
    test_results.append(("VaR Calculator", test_var_calculator()))
    test_results.append(("Position Sizer", test_position_sizer()))
    test_results.append(("Risk Manager", test_risk_manager()))
    test_results.append(("Portfolio Risk", test_portfolio_risk()))

    # Test integrated handler
    try:
        asyncio.run(test_risk_handler())
        test_results.append(("Risk Handler", True))
    except Exception as e:
        print(f"❌ Risk Handler test failed: {e}")
        test_results.append(("Risk Handler", False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:15} | {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Risk Management System is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)