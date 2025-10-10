"""
Position Sizer Module

This module provides various position sizing algorithms for risk-adjusted trading.
Includes Kelly Criterion, Fixed Fractional, and Risk Parity allocation methods.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from scipy.optimize import minimize
import logging

try:
    from pypfopt import EfficientFrontier, risk_models, expected_returns
except ImportError:
    logging.warning("pyportfolioopt not available. Some optimization features will be limited.")
    EfficientFrontier = None

logger = logging.getLogger(__name__)


class PositionSizer:
    """
    Comprehensive position sizing calculator with multiple risk-adjusted methods.
    """

    def __init__(self,
                 max_portfolio_risk: float = 0.02,
                 max_single_position: float = 0.10,
                 risk_free_rate: float = 0.02):
        """
        Initialize position sizer.

        Args:
            max_portfolio_risk: Maximum risk per trade as fraction of portfolio
            max_single_position: Maximum size of single position
            risk_free_rate: Risk-free rate for calculations
        """
        self.max_portfolio_risk = max_portfolio_risk
        self.max_single_position = max_single_position
        self.risk_free_rate = risk_free_rate

    def kelly_criterion(self,
                        win_rate: float,
                        avg_win_return: float,
                        avg_loss_return: float,
                        current_portfolio: float) -> Dict[str, float]:
        """
        Calculate Kelly Criterion optimal position size.

        Args:
            win_rate: Probability of winning trade (0-1)
            avg_win_return: Average return on winning trades
            avg_loss_return: Average return on losing trades (negative)
            current_portfolio: Current portfolio value

        Returns:
            Dictionary with position size and related metrics
        """
        if not 0 < win_rate < 1:
            raise ValueError("Win rate must be between 0 and 1")
        if avg_loss_return >= 0:
            raise ValueError("Average loss return must be negative")

        # Kelly formula: f = (p * b - q) / b
        # where b = |avg_win / avg_loss|, q = 1 - p
        win_return = abs(avg_win_return)
        loss_return = abs(avg_loss_return)
        b = win_return / loss_return
        kelly_fraction = (b * win_rate - (1 - win_rate)) / b

        # Conservative Kelly (half Kelly)
        conservative_kelly = kelly_fraction / 2

        # Apply maximum position limits
        position_size = min(conservative_kelly, self.max_single_position)

        # Calculate position value
        position_value = position_size * current_portfolio

        # Calculate expected risk
        expected_risk = position_size * (win_rate * avg_win_return +
                                       (1 - win_rate) * avg_loss_return)

        return {
            'kelly_fraction': kelly_fraction,
            'conservative_kelly': conservative_kelly,
            'position_size': position_size,
            'position_value': position_value,
            'expected_risk': expected_risk,
            'max_portfolio_risk': self.max_portfolio_risk
        }

    def fixed_fractional(self,
                        portfolio_value: float,
                        risk_per_trade: Optional[float] = None,
                        volatility: Optional[float] = None) -> float:
        """
        Calculate Fixed Fractional position size.

        Args:
            portfolio_value: Current portfolio value
            risk_per_trade: Risk per trade as fraction (uses max_portfolio_risk if None)
            volatility: Asset volatility (optional)

        Returns:
            Position size as fraction of portfolio
        """
        risk_fraction = risk_per_trade or self.max_portfolio_risk

        if volatility is None:
            # Simple fixed fractional
            return risk_fraction

        # Volatility-adjusted fixed fractional
        # Risk = Position * Volatility, so Position = Risk / Volatility
        position_size = risk_fraction / volatility

        # Apply maximum position limit
        return min(position_size, self.max_single_position)

    def fixed_ratio(self,
                   portfolio_value: float,
                   current_position_value: float,
                   delta: float = 0.02) -> float:
        """
        Calculate Fixed Ratio position size (anti-Martingale).

        Args:
            portfolio_value: Current portfolio value
            current_position_value: Current position value
            delta: Fixed ratio increment

        Returns:
            New position size
        """
        if current_position_value == 0:
            # First position
            return self.max_portfolio_risk

        # Fixed ratio formula
        new_position_size = current_position_value + delta * portfolio_value

        # Apply maximum limits
        return min(new_position_size / portfolio_value, self.max_single_position)

    def risk_parity_allocation(self,
                              asset_returns: pd.DataFrame,
                              target_volatility: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate Risk Parity allocation weights.

        Args:
            asset_returns: Historical asset returns
            target_volatility: Target portfolio volatility

        Returns:
            Dictionary of asset weights
        """
        if asset_returns.empty:
            raise ValueError("Asset returns cannot be empty")

        # Calculate covariance matrix
        cov_matrix = asset_returns.cov()

        # Calculate asset volatilities
        volatilities = np.sqrt(np.diag(cov_matrix))

        # Risk parity weights (inverse volatility)
        if target_volatility is None:
            weights = 1.0 / volatilities
            weights = weights / np.sum(weights)
        else:
            # Target volatility scaling
            current_vol = np.sqrt(np.sum(weights * (cov_matrix @ weights)))
            scale_factor = target_volatility / current_vol
            weights = weights * scale_factor
            weights = np.clip(weights, 0, self.max_single_position)

        # Convert to dictionary
        asset_weights = {}
        for i, asset in enumerate(asset_returns.columns):
            asset_weights[asset] = float(weights[i])

        return asset_weights

    def minimum_variance_allocation(self,
                                   asset_returns: pd.DataFrame,
                                   bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]:
        """
        Calculate Minimum Variance portfolio weights.

        Args:
            asset_returns: Historical asset returns
            bounds: Bounds for individual asset weights

        Returns:
            Dictionary of optimal weights
        """
        if asset_returns.empty:
            raise ValueError("Asset returns cannot be empty")

        cov_matrix = asset_returns.cov().values
        n_assets = len(asset_returns.columns)

        # Objective function: minimize portfolio variance
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]

        # Bounds for each asset
        weight_bounds = [bounds] * n_assets

        # Initial guess (equal weight)
        initial_weights = np.ones(n_assets) / n_assets

        # Optimization
        result = minimize(
            portfolio_variance,
            initial_weights,
            method='SLSQP',
            bounds=weight_bounds,
            constraints=constraints
        )

        if not result.success:
            logger.warning("Optimization failed, using equal weights")
            weights = initial_weights
        else:
            weights = result.x

        # Apply maximum position limit
        weights = np.clip(weights, 0, self.max_single_position)
        weights = weights / np.sum(weights)  # Re-normalize

        # Convert to dictionary
        asset_weights = {}
        for i, asset in enumerate(asset_returns.columns):
            asset_weights[asset] = float(weights[i])

        return asset_weights

    def max_sharpe_allocation(self,
                             asset_returns: pd.DataFrame,
                             bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]:
        """
        Calculate Maximum Sharpe Ratio portfolio weights.

        Args:
            asset_returns: Historical asset returns
            bounds: Bounds for individual asset weights

        Returns:
            Dictionary of optimal weights
        """
        if asset_returns.empty:
            raise ValueError("Asset returns cannot be empty")

        # Calculate expected returns and covariance
        mu = asset_returns.mean() * 252  # Annualized
        cov_matrix = asset_returns.cov() * 252  # Annualized

        n_assets = len(asset_returns.columns)

        # Objective function: maximize Sharpe ratio (minimize negative Sharpe)
        def neg_sharpe_ratio(weights):
            portfolio_return = np.dot(weights, mu)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
            return -sharpe

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]

        # Bounds for each asset
        weight_bounds = [bounds] * n_assets

        # Initial guess (equal weight)
        initial_weights = np.ones(n_assets) / n_assets

        # Optimization
        result = minimize(
            neg_sharpe_ratio,
            initial_weights,
            method='SLSQP',
            bounds=weight_bounds,
            constraints=constraints
        )

        if not result.success:
            logger.warning("Optimization failed, using equal weights")
            weights = initial_weights
        else:
            weights = result.x

        # Apply maximum position limit
        weights = np.clip(weights, 0, self.max_single_position)
        weights = weights / np.sum(weights)  # Re-normalize

        # Convert to dictionary
        asset_weights = {}
        for i, asset in enumerate(asset_returns.columns):
            asset_weights[asset] = float(weights[i])

        return asset_weights

    def equal_risk_contribution(self,
                               asset_returns: pd.DataFrame,
                               bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]:
        """
        Calculate Equal Risk Contribution (ERC) portfolio weights.

        Args:
            asset_returns: Historical asset returns
            bounds: Bounds for individual asset weights

        Returns:
            Dictionary of ERC weights
        """
        if asset_returns.empty:
            raise ValueError("Asset returns cannot be empty")

        cov_matrix = asset_returns.cov().values
        n_assets = len(asset_returns.columns)

        def risk_contribution(weights):
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            marginal_risk = np.dot(cov_matrix, weights) / portfolio_vol
            risk_contrib = weights * marginal_risk
            return risk_contrib

        def erc_objective(weights):
            contrib = risk_contribution(weights)
            return np.var(contrib)  # Minimize variance of risk contributions

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]

        # Bounds
        weight_bounds = [bounds] * n_assets

        # Initial guess
        initial_weights = np.ones(n_assets) / n_assets

        # Optimization
        result = minimize(
            erc_objective,
            initial_weights,
            method='SLSQP',
            bounds=weight_bounds,
            constraints=constraints
        )

        if not result.success:
            logger.warning("ERC optimization failed, using equal weights")
            weights = initial_weights
        else:
            weights = result.x

        # Apply maximum position limit
        weights = np.clip(weights, 0, self.max_single_position)
        weights = weights / np.sum(weights)

        # Convert to dictionary
        asset_weights = {}
        for i, asset in enumerate(asset_returns.columns):
            asset_weights[asset] = float(weights[i])

        return asset_weights

    def volatility_targeted_allocation(self,
                                      asset_returns: pd.DataFrame,
                                      target_volatility: float,
                                      bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]:
        """
        Calculate weights for target volatility portfolio.

        Args:
            asset_returns: Historical asset returns
            target_volatility: Target portfolio volatility
            bounds: Bounds for individual asset weights

        Returns:
            Dictionary of volatility-targeted weights
        """
        if asset_returns.empty:
            raise ValueError("Asset returns cannot be empty")

        cov_matrix = asset_returns.cov().values
        n_assets = len(asset_returns.columns)

        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        def volatility_constraint(weights):
            return portfolio_volatility(weights) - target_volatility

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
            {'type': 'eq', 'fun': volatility_constraint}     # Target volatility
        ]

        # Bounds
        weight_bounds = [bounds] * n_assets

        # Initial guess
        initial_weights = np.ones(n_assets) / n_assets

        # Optimization (minimize concentration for diversification)
        def concentration_objective(weights):
            return -np.sum(weights**2)  # Maximize diversification

        result = minimize(
            concentration_objective,
            initial_weights,
            method='SLSQP',
            bounds=weight_bounds,
            constraints=constraints
        )

        if not result.success:
            logger.warning("Volatility targeting failed, using minimum variance")
            return self.minimum_variance_allocation(asset_returns, bounds)

        weights = result.x

        # Apply maximum position limit
        weights = np.clip(weights, 0, self.max_single_position)
        weights = weights / np.sum(weights)

        # Convert to dictionary
        asset_weights = {}
        for i, asset in enumerate(asset_returns.columns):
            asset_weights[asset] = float(weights[i])

        return asset_weights


def optimize_portfolio_with_pyportfolioopt(asset_returns: pd.DataFrame,
                                          method: str = 'max_sharpe',
                                          bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]:
    """
    Optimize portfolio using pyportfolioopt library.

    Args:
        asset_returns: Historical asset returns
        method: Optimization method ('max_sharpe', 'min_volatility', 'max_quadratic_utility')
        bounds: Bounds for individual asset weights

    Returns:
        Dictionary of optimal weights
    """
    if EfficientFrontier is None:
        raise ImportError("pyportfolioopt is required for this function")

    # Calculate expected returns and covariance
    mu = expected_returns.mean_historical_return(asset_returns)
    S = risk_models.sample_cov(asset_returns)

    # Create Efficient Frontier
    ef = EfficientFrontier(mu, S, weight_bounds=bounds)

    # Optimize based on method
    if method == 'max_sharpe':
        ef.max_sharpe()
    elif method == 'min_volatility':
        ef.min_volatility()
    elif method == 'max_quadratic_utility':
        ef.max_quadratic_utility()
    else:
        raise ValueError(f"Unknown optimization method: {method}")

    # Get weights
    weights = ef.clean_weights()

    return weights