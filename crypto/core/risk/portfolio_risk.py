"""
Portfolio Risk Analytics Module

This module provides comprehensive portfolio risk analysis including:
- Sharpe and Sortino ratios
- Maximum drawdown calculations
- Correlation analysis
- Beta calculations
- Risk-adjusted return metrics
- Portfolio optimization analytics
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Container for portfolio risk metrics."""
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    beta: float
    alpha: float
    calmar_ratio: float
    information_ratio: float
    value_at_risk: float
    expected_shortfall: float


@dataclass
class PortfolioStats:
    """Container for portfolio statistics."""
    total_return: float
    annualized_return: float
    annualized_volatility: float
    best_month: float
    worst_month: float
    positive_months: int
    total_months: int
    win_rate: float


class PortfolioRisk:
    """
    Comprehensive portfolio risk analytics and performance measurement.
    """

    def __init__(self, risk_free_rate: float = 0.02, periods_per_year: int = 365):
        """
        Initialize portfolio risk analyzer.

        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
            periods_per_year: Number of periods per year for annualization
        """
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year

    def calculate_sharpe_ratio(self,
                              returns: Union[pd.Series, np.ndarray],
                              annualize: bool = True) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted return).

        Args:
            returns: Portfolio returns series
            annualize: Whether to annualize the ratio

        Returns:
            Sharpe ratio
        """
        if isinstance(returns, pd.Series):
            returns = returns.values

        if len(returns) == 0:
            return 0.0

        excess_returns = returns - self.risk_free_rate / self.periods_per_year
        mean_excess_return = np.mean(excess_returns)
        volatility = np.std(excess_returns, ddof=1)

        if volatility == 0:
            return float('inf') if mean_excess_return > 0 else float('-inf')

        sharpe = mean_excess_return / volatility

        if annualize:
            sharpe *= np.sqrt(self.periods_per_year)

        return sharpe

    def calculate_sortino_ratio(self,
                               returns: Union[pd.Series, np.ndarray],
                               annualize: bool = True) -> float:
        """
        Calculate Sortino ratio (downside risk-adjusted return).

        Args:
            returns: Portfolio returns series
            annualize: Whether to annualize the ratio

        Returns:
            Sortino ratio
        """
        if isinstance(returns, pd.Series):
            returns = returns.values

        if len(returns) == 0:
            return 0.0

        excess_returns = returns - self.risk_free_rate / self.periods_per_year
        mean_excess_return = np.mean(excess_returns)

        # Calculate downside deviation (only negative returns)
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return float('inf') if mean_excess_return > 0 else 0.0

        downside_deviation = np.std(downside_returns, ddof=1)

        if downside_deviation == 0:
            return float('inf') if mean_excess_return > 0 else float('-inf')

        sortino = mean_excess_return / downside_deviation

        if annualize:
            sortino *= np.sqrt(self.periods_per_year)

        return sortino

    def calculate_max_drawdown(self,
                              portfolio_values: Union[pd.Series, np.ndarray]) -> float:
        """
        Calculate maximum drawdown.

        Args:
            portfolio_values: Portfolio values over time

        Returns:
            Maximum drawdown as decimal (e.g., 0.15 for 15%)
        """
        if isinstance(portfolio_values, pd.Series):
            portfolio_values = portfolio_values.values

        if len(portfolio_values) == 0:
            return 0.0

        # Calculate cumulative maximum values
        peak = np.maximum.accumulate(portfolio_values)

        # Calculate drawdowns
        drawdowns = (portfolio_values - peak) / peak

        # Find maximum drawdown
        max_drawdown = np.min(drawdowns)

        return abs(max_drawdown)  # Return positive value

    def calculate_calmar_ratio(self,
                              returns: Union[pd.Series, np.ndarray],
                              portfolio_values: Union[pd.Series, np.ndarray],
                              annualize: bool = True) -> float:
        """
        Calculate Calmar ratio (return vs. maximum drawdown).

        Args:
            returns: Portfolio returns series
            portfolio_values: Portfolio values over time
            annualize: Whether to annualize the ratio

        Returns:
            Calmar ratio
        """
        if isinstance(returns, pd.Series):
            returns = returns.values
        if isinstance(portfolio_values, pd.Series):
            portfolio_values = portfolio_values.values

        if len(returns) == 0 or len(portfolio_values) == 0:
            return 0.0

        annualized_return = np.mean(returns) * self.periods_per_year
        max_drawdown = self.calculate_max_drawdown(portfolio_values)

        if max_drawdown == 0:
            return float('inf') if annualized_return > 0 else float('-inf')

        return annualized_return / max_drawdown

    def calculate_beta(self,
                      portfolio_returns: Union[pd.Series, np.ndarray],
                      market_returns: Union[pd.Series, np.ndarray]) -> float:
        """
        Calculate portfolio beta relative to market.

        Args:
            portfolio_returns: Portfolio returns
            market_returns: Market/benchmark returns

        Returns:
            Portfolio beta
        """
        if isinstance(portfolio_returns, pd.Series):
            portfolio_returns = portfolio_returns.values
        if isinstance(market_returns, pd.Series):
            market_returns = market_returns.values

        if len(portfolio_returns) != len(market_returns):
            min_len = min(len(portfolio_returns), len(market_returns))
            portfolio_returns = portfolio_returns[-min_len:]
            market_returns = market_returns[-min_len:]

        if len(portfolio_returns) < 2:
            return 1.0  # Default to market beta if insufficient data

        # Calculate covariance and market variance
        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns, ddof=1)

        if market_variance == 0:
            return 1.0

        return covariance / market_variance

    def calculate_alpha(self,
                       portfolio_returns: Union[pd.Series, np.ndarray],
                       market_returns: Union[pd.Series, np.ndarray]) -> float:
        """
        Calculate Jensen's alpha.

        Args:
            portfolio_returns: Portfolio returns
            market_returns: Market/benchmark returns

        Returns:
            Portfolio alpha (annualized)
        """
        if isinstance(portfolio_returns, pd.Series):
            portfolio_returns = portfolio_returns.values
        if isinstance(market_returns, pd.Series):
            market_returns = market_returns.values

        if len(portfolio_returns) != len(market_returns):
            min_len = min(len(portfolio_returns), len(market_returns))
            portfolio_returns = portfolio_returns[-min_len:]
            market_returns = market_returns[-min_len:]

        if len(portfolio_returns) < 2:
            return 0.0

        beta = self.calculate_beta(portfolio_returns, market_returns)

        portfolio_excess_return = np.mean(portfolio_returns) - self.risk_free_rate / self.periods_per_year
        market_excess_return = np.mean(market_returns) - self.risk_free_rate / self.periods_per_year

        alpha = portfolio_excess_return - beta * market_excess_return
        return alpha * self.periods_per_year  # Annualize

    def calculate_information_ratio(self,
                                   portfolio_returns: Union[pd.Series, np.ndarray],
                                   benchmark_returns: Union[pd.Series, np.ndarray]) -> float:
        """
        Calculate Information ratio (active return vs. tracking error).

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            Information ratio (annualized)
        """
        if isinstance(portfolio_returns, pd.Series):
            portfolio_returns = portfolio_returns.values
        if isinstance(benchmark_returns, pd.Series):
            benchmark_returns = benchmark_returns.values

        if len(portfolio_returns) != len(benchmark_returns):
            min_len = min(len(portfolio_returns), len(benchmark_returns))
            portfolio_returns = portfolio_returns[-min_len:]
            benchmark_returns = benchmark_returns[-min_len:]

        if len(portfolio_returns) < 2:
            return 0.0

        # Calculate active returns (portfolio - benchmark)
        active_returns = portfolio_returns - benchmark_returns

        mean_active_return = np.mean(active_returns)
        tracking_error = np.std(active_returns, ddof=1)

        if tracking_error == 0:
            return float('inf') if mean_active_return > 0 else float('-inf')

        information_ratio = mean_active_return / tracking_error
        return information_ratio * np.sqrt(self.periods_per_year)  # Annualize

    def calculate_correlation_matrix(self,
                                    asset_returns: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix for assets.

        Args:
            asset_returns: DataFrame with asset returns

        Returns:
            Correlation matrix
        """
        return asset_returns.corr()

    def calculate_covariance_matrix(self,
                                   asset_returns: pd.DataFrame,
                                   annualize: bool = True) -> pd.DataFrame:
        """
        Calculate covariance matrix for assets.

        Args:
            asset_returns: DataFrame with asset returns
            annualize: Whether to annualize covariance

        Returns:
            Covariance matrix
        """
        cov_matrix = asset_returns.cov()
        if annualize:
            cov_matrix *= self.periods_per_year
        return cov_matrix

    def calculate_portfolio_volatility(self,
                                      weights: np.ndarray,
                                      cov_matrix: pd.DataFrame) -> float:
        """
        Calculate portfolio volatility given weights and covariance matrix.

        Args:
            weights: Portfolio weights
            cov_matrix: Covariance matrix

        Returns:
            Portfolio volatility (annualized)
        """
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix.values, weights))
        return np.sqrt(portfolio_variance)

    def calculate_risk_contributions(self,
                                    weights: np.ndarray,
                                    cov_matrix: pd.DataFrame) -> np.ndarray:
        """
        Calculate individual asset risk contributions to portfolio.

        Args:
            weights: Portfolio weights
            cov_matrix: Covariance matrix

        Returns:
            Risk contributions per asset
        """
        portfolio_vol = self.calculate_portfolio_volatility(weights, cov_matrix)

        # Marginal risk contribution
        marginal_risk = np.dot(cov_matrix.values, weights) / portfolio_vol

        # Total risk contribution
        risk_contributions = weights * marginal_risk

        return risk_contributions

    def calculate_efficient_frontier(self,
                                    asset_returns: pd.DataFrame,
                                    target_returns: Optional[np.ndarray] = None,
                                    num_portfolios: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate efficient frontier portfolios.

        Args:
            asset_returns: DataFrame with asset returns
            target_returns: Specific target returns to optimize for
            num_portfolios: Number of portfolios to generate

        Returns:
            Tuple of (returns, volatilities, weights)
        """
        n_assets = len(asset_returns.columns)
        mu = asset_returns.mean() * self.periods_per_year
        cov_matrix = asset_returns.cov() * self.periods_per_year

        if target_returns is None:
            # Generate range of target returns
            min_return = mu.min()
            max_return = mu.max()
            target_returns = np.linspace(min_return, max_return, num_portfolios)

        portfolio_returns = []
        portfolio_vols = []
        portfolio_weights = []

        for target_return in target_returns:
            # Minimize volatility for given return
            def objective(weights):
                return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
                {'type': 'eq', 'fun': lambda x: np.dot(x, mu) - target_return}  # Target return
            ]

            bounds = [(0, 1) for _ in range(n_assets)]  # Long-only

            from scipy.optimize import minimize
            result = minimize(objective, np.ones(n_assets)/n_assets,
                            method='SLSQP', bounds=bounds, constraints=constraints)

            if result.success:
                weights = result.x
                ret = np.dot(weights, mu)
                vol = objective(weights)

                portfolio_returns.append(ret)
                portfolio_vols.append(vol)
                portfolio_weights.append(weights)

        return (np.array(portfolio_returns),
                np.array(portfolio_vols),
                np.array(portfolio_weights))

    def get_comprehensive_risk_metrics(self,
                                      portfolio_returns: Union[pd.Series, np.ndarray],
                                      portfolio_values: Union[pd.Series, np.ndarray],
                                      market_returns: Optional[Union[pd.Series, np.ndarray]] = None,
                                      confidence_level: float = 0.95) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for portfolio.

        Args:
            portfolio_returns: Portfolio returns series
            portfolio_values: Portfolio values over time
            market_returns: Market/benchmark returns (optional)
            confidence_level: Confidence level for VaR calculations

        Returns:
            RiskMetrics object with all calculated metrics
        """
        if isinstance(portfolio_returns, pd.Series):
            portfolio_returns = portfolio_returns.values
        if isinstance(portfolio_values, pd.Series):
            portfolio_values = portfolio_values.values

        # Basic metrics
        sharpe = self.calculate_sharpe_ratio(portfolio_returns)
        sortino = self.calculate_sortino_ratio(portfolio_returns)
        max_dd = self.calculate_max_drawdown(portfolio_values)
        volatility = np.std(portfolio_returns, ddof=1) * np.sqrt(self.periods_per_year)

        # Beta and alpha (if market returns provided)
        if market_returns is not None:
            if isinstance(market_returns, pd.Series):
                market_returns = market_returns.values

            beta = self.calculate_beta(portfolio_returns, market_returns)
            alpha = self.calculate_alpha(portfolio_returns, market_returns)
        else:
            beta = 1.0
            alpha = 0.0

        # Calmar ratio
        calmar = self.calculate_calmar_ratio(portfolio_returns, portfolio_values)

        # Information ratio (using market as benchmark if provided)
        if market_returns is not None:
            info_ratio = self.calculate_information_ratio(portfolio_returns, market_returns)
        else:
            info_ratio = 0.0

        # VaR and ES (simplified calculation)
        from scipy import stats
        var_95 = -np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        tail_returns = portfolio_returns[portfolio_returns <= var_95]
        expected_shortfall = -np.mean(tail_returns) if len(tail_returns) > 0 else var_95

        return RiskMetrics(
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            volatility=volatility,
            beta=beta,
            alpha=alpha,
            calmar_ratio=calmar,
            information_ratio=info_ratio,
            value_at_risk=var_95,
            expected_shortfall=expected_shortfall
        )

    def get_portfolio_statistics(self,
                                portfolio_returns: Union[pd.Series, np.ndarray]) -> PortfolioStats:
        """
        Calculate comprehensive portfolio statistics.

        Args:
            portfolio_returns: Portfolio returns series

        Returns:
            PortfolioStats object
        """
        if isinstance(portfolio_returns, pd.Series):
            portfolio_returns = portfolio_returns.values

        if len(portfolio_returns) == 0:
            return PortfolioStats(0, 0, 0, 0, 0, 0, 0, 0)

        # Monthly returns (assuming daily data)
        monthly_returns = []
        for i in range(0, len(portfolio_returns), 30):  # Rough monthly grouping
            month_return = np.prod(1 + portfolio_returns[i:i+30]) - 1
            monthly_returns.append(month_return)

        monthly_returns = np.array(monthly_returns)

        total_return = np.prod(1 + portfolio_returns) - 1
        annualized_return = (1 + total_return) ** (self.periods_per_year / len(portfolio_returns)) - 1
        annualized_volatility = np.std(portfolio_returns, ddof=1) * np.sqrt(self.periods_per_year)

        best_month = np.max(monthly_returns) if len(monthly_returns) > 0 else 0
        worst_month = np.min(monthly_returns) if len(monthly_returns) > 0 else 0

        positive_months = np.sum(monthly_returns > 0)
        total_months = len(monthly_returns)
        win_rate = positive_months / total_months if total_months > 0 else 0

        return PortfolioStats(
            total_return=total_return,
            annualized_return=annualized_return,
            annualized_volatility=annualized_volatility,
            best_month=best_month,
            worst_month=worst_month,
            positive_months=positive_months,
            total_months=total_months,
            win_rate=win_rate
        )


def calculate_rolling_risk_metrics(returns: pd.Series,
                                  window: int = 252,
                                  risk_free_rate: float = 0.02) -> pd.DataFrame:
    """
    Calculate rolling risk metrics.

    Args:
        returns: Returns series
        window: Rolling window size
        risk_free_rate: Risk-free rate

    Returns:
        DataFrame with rolling risk metrics
    """
    analyzer = PortfolioRisk(risk_free_rate=risk_free_rate)

    rolling_metrics = pd.DataFrame(index=returns.index)

    # Rolling Sharpe ratio
    excess_returns = returns - risk_free_rate / 365
    rolling_metrics['rolling_sharpe'] = (
        excess_returns.rolling(window=window).mean() /
        excess_returns.rolling(window=window).std()
    ) * np.sqrt(365)

    # Rolling volatility
    rolling_metrics['rolling_volatility'] = (
        returns.rolling(window=window).std() * np.sqrt(365)
    )

    # Rolling maximum drawdown
    rolling_max = returns.rolling(window=window).max()
    rolling_min = returns.rolling(window=window).min()
    rolling_metrics['rolling_max_drawdown'] = (
        (rolling_max - rolling_min) / rolling_max
    ).abs()

    return rolling_metrics