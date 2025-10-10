"""
Value-at-Risk (VaR) Calculator Module

This module provides comprehensive VaR calculations for portfolio risk management.
Supports historical, parametric, and Monte Carlo VaR methodologies.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class VaRCalculator:
    """
    Comprehensive Value-at-Risk calculator supporting multiple methodologies.

    VaR represents the maximum potential loss over a specific time period
    with a given confidence level.
    """

    def __init__(self, confidence_level: float = 0.95, time_horizon: int = 1):
        """
        Initialize VaR calculator.

        Args:
            confidence_level: Confidence level for VaR (e.g., 0.95 for 95%)
            time_horizon: Time horizon in days for VaR calculation
        """
        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        if time_horizon <= 0:
            raise ValueError("Time horizon must be positive")

        self.confidence_level = confidence_level
        self.time_horizon = time_horizon
        self.alpha = 1 - confidence_level  # Significance level

    def calculate_historical_var(self,
                                returns: Union[pd.Series, np.ndarray],
                                portfolio_value: float,
                                lookback_periods: Optional[int] = None) -> float:
        """
        Calculate Historical VaR using empirical distribution.

        Args:
            returns: Historical return series
            portfolio_value: Current portfolio value
            lookback_periods: Number of periods to use for calculation

        Returns:
            Historical VaR value
        """
        if isinstance(returns, pd.Series):
            returns = returns.values

        if lookback_periods is None:
            lookback_periods = len(returns)

        # Use most recent returns
        historical_returns = returns[-lookback_periods:]

        # Calculate VaR as the negative percentile of historical returns
        var_return = np.percentile(historical_returns, self.alpha * 100)

        # Scale by time horizon (square root of time rule)
        var_return_scaled = var_return * np.sqrt(self.time_horizon)

        # Convert to portfolio value
        var_value = -var_return_scaled * portfolio_value

        logger.info(".2f")
        return var_value

    def calculate_parametric_var(self,
                                returns: Union[pd.Series, np.ndarray],
                                portfolio_value: float,
                                lookback_periods: Optional[int] = None) -> float:
        """
        Calculate Parametric VaR assuming normal distribution.

        Args:
            returns: Historical return series
            portfolio_value: Current portfolio value
            lookback_periods: Number of periods to use for calculation

        Returns:
            Parametric VaR value
        """
        if isinstance(returns, pd.Series):
            returns = returns.values

        if lookback_periods is None:
            lookback_periods = len(returns)

        historical_returns = returns[-lookback_periods:]

        # Calculate mean and standard deviation
        mean_return = np.mean(historical_returns)
        std_return = np.std(historical_returns, ddof=1)  # Sample standard deviation

        # Calculate VaR using normal distribution
        z_score = stats.norm.ppf(self.alpha)
        var_return = mean_return + z_score * std_return

        # Scale by time horizon
        var_return_scaled = var_return * np.sqrt(self.time_horizon)

        # Convert to portfolio value
        var_value = -var_return_scaled * portfolio_value

        logger.info(".2f")
        return var_value

    def calculate_monte_carlo_var(self,
                                 returns: Union[pd.Series, np.ndarray],
                                 portfolio_value: float,
                                 simulations: int = 10000,
                                 lookback_periods: Optional[int] = None) -> float:
        """
        Calculate Monte Carlo VaR through simulation.

        Args:
            returns: Historical return series
            portfolio_value: Current portfolio value
            simulations: Number of Monte Carlo simulations
            lookback_periods: Number of periods to use for calculation

        Returns:
            Monte Carlo VaR value
        """
        if isinstance(returns, pd.Series):
            returns = returns.values

        if lookback_periods is None:
            lookback_periods = len(returns)

        historical_returns = returns[-lookback_periods:]

        # Generate random scenarios
        simulated_returns = np.random.choice(
            historical_returns,
            size=(simulations, self.time_horizon),
            replace=True
        )

        # Calculate portfolio values for each scenario
        simulated_portfolio_values = portfolio_value * np.exp(
            np.cumsum(simulated_returns, axis=1)
        )

        # Get final portfolio values after time horizon
        final_values = simulated_portfolio_values[:, -1]

        # Calculate VaR as loss (current value - percentile of final values)
        var_value = portfolio_value - np.percentile(final_values, self.alpha * 100)

        logger.info(".2f")
        return var_value

    def calculate_expected_shortfall(self,
                                    returns: Union[pd.Series, np.ndarray],
                                    portfolio_value: float,
                                    method: str = 'historical',
                                    lookback_periods: Optional[int] = None) -> float:
        """
        Calculate Expected Shortfall (ES) - average loss beyond VaR.

        Args:
            returns: Historical return series
            portfolio_value: Current portfolio value
            method: Method to use ('historical', 'parametric', 'monte_carlo')
            lookback_periods: Number of periods to use for calculation

        Returns:
            Expected Shortfall value
        """
        if isinstance(returns, pd.Series):
            returns = returns.values

        if lookback_periods is None:
            lookback_periods = len(returns)

        historical_returns = returns[-lookback_periods:]

        if method == 'historical':
            # Find returns worse than VaR
            var_return = np.percentile(historical_returns, self.alpha * 100)
            tail_returns = historical_returns[historical_returns <= var_return]
            es_return = np.mean(tail_returns)

        elif method == 'parametric':
            # For normal distribution, ES = μ + σ * φ(α) / α
            mean_return = np.mean(historical_returns)
            std_return = np.std(historical_returns, ddof=1)
            pdf_alpha = stats.norm.pdf(stats.norm.ppf(self.alpha))
            es_return = mean_return + std_return * (pdf_alpha / self.alpha)

        elif method == 'monte_carlo':
            # Use Monte Carlo simulation
            simulated_returns = np.random.choice(
                historical_returns,
                size=(10000, self.time_horizon),
                replace=True
            )
            simulated_portfolio_values = portfolio_value * np.exp(
                np.cumsum(simulated_returns, axis=1)
            )
            final_values = simulated_portfolio_values[:, -1]
            losses = portfolio_value - final_values
            var_loss = np.percentile(losses, self.alpha * 100)
            tail_losses = losses[losses >= var_loss]
            es_return = np.mean(tail_losses) / portfolio_value

        else:
            raise ValueError(f"Unknown method: {method}")

        # Scale by time horizon and convert to portfolio value
        es_return_scaled = es_return * np.sqrt(self.time_horizon)
        es_value = -es_return_scaled * portfolio_value

        logger.info(".2f")
        return es_value

    def calculate_var_contribution(self,
                                  asset_returns: pd.DataFrame,
                                  weights: np.ndarray,
                                  portfolio_value: float,
                                  method: str = 'parametric') -> np.ndarray:
        """
        Calculate individual asset contributions to portfolio VaR.

        Args:
            asset_returns: DataFrame with asset returns
            weights: Portfolio weights
            portfolio_value: Current portfolio value
            method: VaR calculation method

        Returns:
            Array of VaR contributions per asset
        """
        if method == 'parametric':
            # Calculate marginal VaR contribution
            covariance = asset_returns.cov().values
            portfolio_var = np.dot(weights.T, np.dot(covariance, weights))

            # Marginal contribution to risk
            marginal_var = np.dot(covariance, weights) / np.sqrt(portfolio_var)

            # VaR contribution
            portfolio_var_value = np.sqrt(portfolio_var) * stats.norm.ppf(self.alpha)
            var_contributions = weights * marginal_var * portfolio_var_value * portfolio_value

        elif method == 'historical':
            # Use historical simulation
            portfolio_returns = asset_returns.dot(weights)
            var_return = np.percentile(portfolio_returns.values, self.alpha * 100)

            # Calculate contributions using Euler allocation
            asset_vars = np.array([np.var(asset_returns.iloc[:, i]) for i in range(len(weights))])
            correlations = asset_returns.corr().values

            var_contributions = np.zeros(len(weights))
            for i in range(len(weights)):
                beta_i = correlations[i].dot(weights) * np.sqrt(asset_vars[i] / portfolio_returns.var())
                var_contributions[i] = weights[i] * beta_i * var_return * portfolio_value

        else:
            raise ValueError(f"Method {method} not supported for VaR contribution")

        return var_contributions


def calculate_portfolio_var(returns: pd.DataFrame,
                           weights: np.ndarray,
                           confidence_level: float = 0.95,
                           method: str = 'parametric') -> float:
    """
    Convenience function to calculate portfolio VaR.

    Args:
        returns: Asset returns DataFrame
        weights: Portfolio weights
        confidence_level: Confidence level for VaR
        method: Calculation method

    Returns:
        Portfolio VaR value
    """
    calculator = VaRCalculator(confidence_level)

    if method == 'parametric':
        # Calculate parametric portfolio VaR
        covariance = returns.cov().values
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(covariance, weights)))
        z_score = stats.norm.ppf(1 - confidence_level)
        portfolio_var_return = z_score * portfolio_volatility

        # Assume portfolio value of 1 for relative VaR
        return portfolio_var_return

    elif method == 'historical':
        portfolio_returns = returns.dot(weights)
        return calculator.calculate_historical_var(portfolio_returns, 1.0)

    else:
        raise ValueError(f"Unknown method: {method}")