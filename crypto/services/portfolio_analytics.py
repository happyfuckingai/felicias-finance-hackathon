"""
Portfolio Analytics Service för Google Cloud Web3
Specialiserad service för portfolio performance tracking och risk metrics med BigQuery integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
from dataclasses import dataclass
from enum import Enum

from ..core.errors.error_handling import handle_errors, CryptoError, ValidationError
from ..core.risk.portfolio_risk import PortfolioRisk, RiskMetrics, PortfolioStats
from .bigquery_service import BigQueryService, get_bigquery_service
from .google_cloud_web3_provider import GoogleCloudWeb3Provider
from ..config.bigquery_queries import BigQueryQueries

logger = logging.getLogger(__name__)

class PortfolioMetricType(Enum):
    """Typer av portfolio metrics."""
    PERFORMANCE = "performance"
    RISK = "risk"
    ALLOCATION = "allocation"
    BENCHMARKING = "benchmarking"
    PREDICTIVE = "predictive"

class RebalancingAction(Enum):
    """Rebalanseringsåtgärder."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REDUCE = "reduce"

@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot struktur."""
    wallet_address: str
    timestamp: datetime
    total_value_usd: float
    chain_allocations: Dict[str, float]
    token_allocations: Dict[str, float]
    risk_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]

@dataclass
class RebalancingRecommendation:
    """Rebalanseringsrekommendation."""
    token_symbol: str
    current_weight: float
    target_weight: float
    action: RebalancingAction
    amount_usd: float
    reason: str
    priority: int  # 1-10, where 10 is highest priority

class PortfolioAnalyticsService:
    """
    Specialiserad portfolio analytics service för Google Cloud Web3.

    Features:
    - Real-tids portfolio performance från BigQuery materialized views
    - Risk-adjusted returns calculation (Sharpe, Sortino, Calmar ratios)
    - Multi-chain portfolio analysis och cross-chain optimization
    - Historical performance data från BigQuery
    - Integration med BigQuery materialized views för optimal prestanda
    - Automated portfolio rebalancing alerts och recommendations
    - Performance benchmarking mot market indices (BTC, ETH, Market)
    """

    def __init__(self, project_id: str, bigquery_service: Optional[BigQueryService] = None,
                 web3_provider: Optional[GoogleCloudWeb3Provider] = None):
        """
        Initiera Portfolio Analytics Service.

        Args:
            project_id: Google Cloud project ID
            bigquery_service: BigQuery service instans (optional)
            web3_provider: Google Cloud Web3 provider instans (optional)
        """
        self.project_id = project_id
        self.bigquery_service = bigquery_service or get_bigquery_service(project_id)
        self.web3_provider = web3_provider

        # Portfolio risk analyzer
        self.risk_analyzer = PortfolioRisk(risk_free_rate=0.02, periods_per_year=365)

        # Cache för analytics
        self.analytics_cache = {}
        self.cache_ttl = 300  # 5 minuter

        # Rebalancing thresholds
        self.rebalancing_thresholds = {
            'max_position_weight': 0.25,  # 25% max per position
            'min_position_weight': 0.01,   # 1% min per position
            'rebalancing_tolerance': 0.05, # 5% tolerance
            'risk_adjusted_target': True   # Use risk-adjusted targets
        }

        logger.info("Portfolio Analytics Service initierad")

    async def initialize(self) -> bool:
        """Initiera service dependencies."""
        try:
            # Initiera BigQuery service
            await self.bigquery_service.initialize()

            # Initiera Web3 provider om tillgänglig
            if self.web3_provider:
                # Placeholder för Web3 provider initialization
                pass

            logger.info("Portfolio Analytics Service dependencies initierade")
            return True

        except Exception as e:
            logger.error(f"Misslyckades att initiera Portfolio Analytics Service: {e}")
            raise CryptoError(f"Portfolio Analytics Service initialization failed: {str(e)}", "PORTFOLIO_ANALYTICS_INIT_ERROR")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @handle_errors(service_name="portfolio_analytics")
    async def get_portfolio_snapshot(self, wallet_address: str,
                                   include_live_data: bool = True) -> Dict[str, Any]:
        """
        Hämta comprehensive portfolio snapshot.

        Args:
            wallet_address: Wallet address
            include_live_data: Om live data ska inkluderas

        Returns:
            Portfolio snapshot data
        """
        # Kontrollera cache
        cache_key = f"snapshot_{wallet_address}_{include_live_data}"
        if cache_key in self.analytics_cache:
            cache_entry = self.analytics_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cache_entry['data']

        try:
            # Hämta från BigQuery först
            bigquery_data = await self._get_portfolio_data_from_bigquery(wallet_address)

            # Förbättra med live data om requested
            if include_live_data and self.web3_provider:
                live_data = await self._get_live_portfolio_data(wallet_address)
                bigquery_data = self._merge_bigquery_and_live_data(bigquery_data, live_data)

            # Beräkna avancerade metrics
            enhanced_data = await self._enhance_portfolio_data_with_analytics(bigquery_data)

            # Generera rebalancing recommendations
            rebalancing_recommendations = await self._generate_rebalancing_recommendations(
                wallet_address, enhanced_data
            )

            # Beräkna risk-adjusted metrics
            risk_analysis = await self._perform_risk_analysis(wallet_address, enhanced_data)

            snapshot_data = {
                'wallet_address': wallet_address,
                'timestamp': datetime.now().isoformat(),
                'portfolio_data': enhanced_data,
                'rebalancing_recommendations': rebalancing_recommendations,
                'risk_analysis': risk_analysis,
                'data_sources': {
                    'bigquery': True,
                    'live_web3': include_live_data and self.web3_provider is not None,
                    'enhanced_analytics': True
                },
                'cache_info': {
                    'cached': False,
                    'cache_key': cache_key
                }
            }

            # Cache resultatet
            self.analytics_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': snapshot_data
            }

            return snapshot_data

        except Exception as e:
            logger.error(f"Portfolio snapshot misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Portfolio snapshot failed: {str(e)}", "PORTFOLIO_SNAPSHOT_ERROR")

    @handle_errors(service_name="portfolio_analytics")
    async def get_performance_analytics(self, wallet_address: str,
                                      days: int = 30) -> Dict[str, Any]:
        """
        Hämta detaljerad performance analytics.

        Args:
            wallet_address: Wallet address
            days: Antal dagar att analysera

        Returns:
            Performance analytics data
        """
        try:
            # Hämta portfolio performance från BigQuery
            query = BigQueryQueries.get_portfolio_performance_query(
                wallet_address=wallet_address,
                days=days,
                project_id=self.project_id,
                dataset="blockchain_analytics"
            )

            result = await self.bigquery_service.execute_query(query)

            if not result['success'] or not result['rows']:
                return {
                    'success': False,
                    'error': 'No performance data found',
                    'wallet_address': wallet_address
                }

            performance_data = result['rows'][0]

            # Beräkna avancerade performance metrics
            advanced_metrics = await self._calculate_advanced_performance_metrics(
                wallet_address, days
            )

            # Generera performance insights
            insights = await self._generate_performance_insights(performance_data, advanced_metrics)

            return {
                'success': True,
                'wallet_address': wallet_address,
                'performance_data': performance_data,
                'advanced_metrics': advanced_metrics,
                'insights': insights,
                'analysis_period_days': days,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Performance analytics misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Performance analytics failed: {str(e)}", "PERFORMANCE_ANALYTICS_ERROR")

    @handle_errors(service_name="portfolio_analytics")
    async def get_risk_dashboard(self, wallet_address: str) -> Dict[str, Any]:
        """
        Hämta comprehensive risk dashboard.

        Args:
            wallet_address: Wallet address

        Returns:
            Risk dashboard data
        """
        try:
            # Hämta risk metrics från BigQuery
            query = BigQueryQueries.get_risk_metrics_query(
                wallet_address=wallet_address,
                project_id=self.project_id,
                dataset="blockchain_analytics"
            )

            result = await self.bigquery_service.execute_query(query)

            if not result['success'] or not result['rows']:
                return {
                    'success': False,
                    'error': 'No risk metrics found',
                    'wallet_address': wallet_address
                }

            risk_data = result['rows'][0]

            # Beräkna real-tids risk metrics
            live_risk_metrics = await self._calculate_real_time_risk_metrics(wallet_address)

            # Generera risk alerts
            risk_alerts = await self._generate_risk_alerts(wallet_address, risk_data, live_risk_metrics)

            # Skapa risk assessment
            risk_assessment = await self._create_risk_assessment(
                wallet_address, risk_data, live_risk_metrics, risk_alerts
            )

            return {
                'success': True,
                'wallet_address': wallet_address,
                'risk_data': risk_data,
                'live_risk_metrics': live_risk_metrics,
                'risk_alerts': risk_alerts,
                'risk_assessment': risk_assessment,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Risk dashboard misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Risk dashboard failed: {str(e)}", "RISK_DASHBOARD_ERROR")

    @handle_errors(service_name="portfolio_analytics")
    async def get_rebalancing_analysis(self, wallet_address: str) -> Dict[str, Any]:
        """
        Hämta rebalancing analysis och recommendations.

        Args:
            wallet_address: Wallet address

        Returns:
            Rebalancing analysis data
        """
        try:
            # Hämta current portfolio allocation
            balances_data = await self.bigquery_service.get_cross_chain_balances(wallet_address)

            if not balances_data['success']:
                return {
                    'success': False,
                    'error': 'No balance data found for rebalancing analysis',
                    'wallet_address': wallet_address
                }

            # Hämta risk metrics för optimal allocation
            risk_data = await self.get_risk_dashboard(wallet_address)

            # Beräkna optimal allocation
            optimal_allocation = await self._calculate_optimal_allocation(
                wallet_address, balances_data, risk_data
            )

            # Generera rebalancing recommendations
            recommendations = await self._generate_rebalancing_recommendations_from_analysis(
                wallet_address, balances_data, optimal_allocation
            )

            # Beräkna rebalancing cost och impact
            rebalancing_analysis = await self._analyze_rebalancing_impact(
                wallet_address, recommendations
            )

            return {
                'success': True,
                'wallet_address': wallet_address,
                'current_allocation': balances_data,
                'optimal_allocation': optimal_allocation,
                'recommendations': recommendations,
                'rebalancing_analysis': rebalancing_analysis,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Rebalancing analysis misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Rebalancing analysis failed: {str(e)}", "REBALANCING_ANALYSIS_ERROR")

    async def _get_portfolio_data_from_bigquery(self, wallet_address: str) -> Dict[str, Any]:
        """Hämta portfolio data från BigQuery."""
        try:
            # Hämta från multiple BigQuery views parallellt
            tasks = [
                self.bigquery_service.execute_query(
                    BigQueryQueries.get_cross_chain_balance_query(
                        wallet_address, self.project_id, "blockchain_analytics"
                    )
                ),
                self.bigquery_service.execute_query(
                    BigQueryQueries.get_daily_portfolio_values_query(
                        wallet_address, 30, self.project_id, "blockchain_analytics"
                    )
                ),
                self.bigquery_service.execute_query(
                    BigQueryQueries.get_risk_metrics_query(
                        wallet_address, self.project_id, "blockchain_analytics"
                    )
                )
            ]

            balances_result, portfolio_history_result, risk_result = await asyncio.gather(*tasks)

            return {
                'balances': balances_result.get('rows', []),
                'portfolio_history': portfolio_history_result.get('rows', []),
                'risk_metrics': risk_result.get('rows', [{}])[0] if risk_result.get('rows') else {},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"BigQuery portfolio data fetch misslyckades: {e}")
            return {}

    async def _get_live_portfolio_data(self, wallet_address: str) -> Dict[str, Any]:
        """Hämta live portfolio data från Google Cloud Web3."""
        try:
            if not self.web3_provider:
                return {}

            # Hämta live balances
            live_balances = await self.web3_provider.get_cross_chain_balances(wallet_address)

            # Hämta live transactions
            live_transactions = await self.web3_provider.get_transaction_history(
                wallet_address, limit=50
            )

            return {
                'live_balances': live_balances,
                'live_transactions': live_transactions,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"Live portfolio data fetch misslyckades: {e}")
            return {}

    def _merge_bigquery_and_live_data(self, bigquery_data: Dict[str, Any],
                                    live_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge BigQuery data med live data."""
        try:
            # Merge balances - live data har prioritet för senaste värden
            if 'live_balances' in live_data:
                merged_balances = self._merge_balance_data(
                    bigquery_data.get('balances', []),
                    live_data['live_balances']
                )
                bigquery_data['balances'] = merged_balances

            # Add live transaction data
            if 'live_transactions' in live_data:
                bigquery_data['live_transactions'] = live_data['live_transactions']

            return bigquery_data

        except Exception as e:
            logger.warning(f"Data merge misslyckades: {e}")
            return bigquery_data

    async def _enhance_portfolio_data_with_analytics(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Förbättra portfolio data med avancerad analytics."""
        try:
            wallet_address = portfolio_data.get('wallet_address', 'unknown')

            # Beräkna advanced performance metrics
            performance_metrics = await self._calculate_comprehensive_performance_metrics(
                wallet_address, portfolio_data
            )

            # Beräkna allocation analytics
            allocation_analytics = await self._calculate_allocation_analytics(
                portfolio_data.get('balances', [])
            )

            # Generera market benchmarking
            benchmarking_data = await self._generate_benchmarking_data(
                wallet_address, portfolio_data
            )

            enhanced_data = portfolio_data.copy()
            enhanced_data.update({
                'performance_metrics': performance_metrics,
                'allocation_analytics': allocation_analytics,
                'benchmarking_data': benchmarking_data,
                'enhanced_at': datetime.now().isoformat()
            })

            return enhanced_data

        except Exception as e:
            logger.warning(f"Portfolio data enhancement misslyckades: {e}")
            return portfolio_data

    async def _calculate_advanced_performance_metrics(self, wallet_address: str,
                                                    days: int) -> Dict[str, Any]:
        """Beräkna avancerade performance metrics."""
        try:
            # Hämta historical data för calculations
            query = BigQueryQueries.get_daily_portfolio_values_query(
                wallet_address, days, self.project_id, "blockchain_analytics"
            )

            result = await self.bigquery_service.execute_query(query)

            if not result['success'] or not result['rows']:
                return {}

            # Konvertera till pandas for advanced calculations
            import pandas as pd
            df = pd.DataFrame(result['rows'])

            if 'daily_return' in df.columns:
                returns = df['daily_return'].dropna()
                values = df['end_of_day_value'].dropna()

                # Use existing PortfolioRisk analyzer for comprehensive metrics
                risk_metrics = self.risk_analyzer.get_comprehensive_risk_metrics(
                    returns, values, confidence_level=0.95
                )

                portfolio_stats = self.risk_analyzer.get_portfolio_statistics(returns)

                return {
                    'risk_metrics': risk_metrics.__dict__,
                    'portfolio_stats': portfolio_stats.__dict__,
                    'rolling_metrics': await self._calculate_rolling_metrics(returns),
                    'drawdown_analysis': await self._analyze_drawdown_periods(values),
                    'return_distribution': await self._analyze_return_distribution(returns)
                }
            else:
                return {}

        except Exception as e:
            logger.warning(f"Advanced performance metrics calculation misslyckades: {e}")
            return {}

    async def _calculate_allocation_analytics(self, balances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Beräkna allocation analytics."""
        try:
            if not balances:
                return {}

            total_value = sum(balance.get('value_usd', 0) for balance in balances)

            # Chain allocation analysis
            chain_allocation = {}
            for balance in balances:
                chain = balance.get('chain', 'unknown')
                value = balance.get('value_usd', 0)
                if chain not in chain_allocation:
                    chain_allocation[chain] = 0
                chain_allocation[chain] += value

            # Token concentration analysis
            token_weights = [
                balance.get('value_usd', 0) / total_value
                for balance in balances
                if total_value > 0
            ]

            # Herfindahl-Hirschman Index för concentration
            hhi = sum(w ** 2 for w in token_weights) if token_weights else 0

            return {
                'total_value_usd': total_value,
                'chain_allocation': chain_allocation,
                'chain_diversity': len(chain_allocation),
                'token_concentration': {
                    'hhi': hhi,
                    'top_3_positions': sum(sorted(token_weights, reverse=True)[:3]),
                    'max_position': max(token_weights) if token_weights else 0
                },
                'diversification_score': self._calculate_diversification_score(chain_allocation, token_weights)
            }

        except Exception as e:
            logger.warning(f"Allocation analytics calculation misslyckades: {e}")
            return {}

    async def _generate_benchmarking_data(self, wallet_address: str,
                                        portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generera benchmarking data."""
        try:
            query = BigQueryQueries.get_performance_benchmarking_query(
                wallet_address, self.project_id, "blockchain_analytics"
            )

            result = await self.bigquery_service.execute_query(query)

            if not result['success'] or not result['rows']:
                return {}

            benchmarking_data = result['rows']

            # Beräkna relative performance metrics
            relative_performance = await self._calculate_relative_performance(benchmarking_data)

            return {
                'benchmarking_data': benchmarking_data,
                'relative_performance': relative_performance,
                'outperformance_periods': await self._analyze_outperformance_periods(benchmarking_data),
                'benchmarking_score': await self._calculate_benchmarking_score(benchmarking_data)
            }

        except Exception as e:
            logger.warning(f"Benchmarking data generation misslyckades: {e}")
            return {}

    async def _generate_rebalancing_recommendations(self, wallet_address: str,
                                                  portfolio_data: Dict[str, Any]) -> List[RebalancingRecommendation]:
        """Generera rebalancing recommendations."""
        try:
            recommendations = []

            allocation_analytics = portfolio_data.get('allocation_analytics', {})
            if not allocation_analytics:
                return recommendations

            total_value = allocation_analytics.get('total_value_usd', 0)
            token_weights = {}

            # Calculate current weights from balances
            balances = portfolio_data.get('balances', [])
            for balance in balances:
                symbol = balance.get('token_symbol', 'UNKNOWN')
                value = balance.get('value_usd', 0)
                if total_value > 0:
                    token_weights[symbol] = value / total_value

            # Generate recommendations based on risk thresholds
            for symbol, current_weight in token_weights.items():
                if current_weight > self.rebalancing_thresholds['max_position_weight']:
                    recommendations.append(RebalancingRecommendation(
                        token_symbol=symbol,
                        current_weight=current_weight,
                        target_weight=self.rebalancing_thresholds['max_position_weight'],
                        action=RebalancingAction.REDUCE,
                        amount_usd=(current_weight - self.rebalancing_thresholds['max_position_weight']) * total_value,
                        reason=f"Position weight {current_weight:.1%} exceeds maximum threshold {self.rebalancing_thresholds['max_position_weight']:.1%}",
                        priority=8
                    ))
                elif current_weight < self.rebalancing_thresholds['min_position_weight']:
                    recommendations.append(RebalancingRecommendation(
                        token_symbol=symbol,
                        current_weight=current_weight,
                        target_weight=self.rebalancing_thresholds['min_position_weight'],
                        action=RebalancingAction.BUY,
                        amount_usd=(self.rebalancing_thresholds['min_position_weight'] - current_weight) * total_value,
                        reason=f"Position weight {current_weight:.1%} below minimum threshold {self.rebalancing_thresholds['min_position_weight']:.1%}",
                        priority=5
                    ))

            # Sort by priority
            recommendations.sort(key=lambda x: x.priority, reverse=True)

            return [rec.__dict__ for rec in recommendations]

        except Exception as e:
            logger.warning(f"Rebalancing recommendations generation misslyckades: {e}")
            return []

    async def _perform_risk_analysis(self, wallet_address: str,
                                   portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk analysis."""
        try:
            # Use BigQuery data for risk calculations
            risk_data = portfolio_data.get('risk_metrics', {})

            # Calculate additional risk metrics
            additional_metrics = await self._calculate_additional_risk_metrics(
                wallet_address, portfolio_data
            )

            # Generate risk alerts
            risk_alerts = await self._generate_risk_alerts_from_data(
                risk_data, additional_metrics
            )

            # Create risk score
            risk_score = self._calculate_comprehensive_risk_score(
                risk_data, additional_metrics, risk_alerts
            )

            return {
                'risk_data': risk_data,
                'additional_metrics': additional_metrics,
                'risk_alerts': risk_alerts,
                'overall_risk_score': risk_score,
                'risk_level': self._get_risk_level_from_score(risk_score),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"Risk analysis misslyckades: {e}")
            return {}

    def _calculate_diversification_score(self, chain_allocation: Dict[str, float],
                                       token_weights: List[float]) -> float:
        """Beräkna diversifierings score."""
        try:
            # Chain diversification (50% weight)
            chain_count = len(chain_allocation)
            chain_diversity = min(chain_count / 5.0, 1.0)  # Max 5 chains = 1.0

            # Token concentration (50% weight)
            hhi = sum(w ** 2 for w in token_weights) if token_weights else 0
            # Lower HHI = better diversification
            concentration_penalty = min(hhi * 2, 1.0)  # HHI of 0.5+ = penalty of 1.0

            return (chain_diversity * 0.5) + ((1.0 - concentration_penalty) * 0.5)

        except Exception:
            return 0.5

    async def _calculate_rolling_metrics(self, returns) -> Dict[str, Any]:
        """Beräkna rolling metrics."""
        try:
            import pandas as pd
            returns_series = pd.Series(returns)

            # Rolling Sharpe ratio
            rolling_sharpe = returns_series.rolling(window=30).apply(
                lambda x: self.risk_analyzer.calculate_sharpe_ratio(x, annualize=False) * 30**0.5
            )

            # Rolling volatility
            rolling_volatility = returns_series.rolling(window=30).std() * 30**0.5

            return {
                'rolling_sharpe': rolling_sharpe.dropna().tolist(),
                'rolling_volatility': rolling_volatility.dropna().tolist(),
                'current_sharpe': rolling_sharpe.dropna().iloc[-1] if len(rolling_sharpe.dropna()) > 0 else 0,
                'current_volatility': rolling_volatility.dropna().iloc[-1] if len(rolling_volatility.dropna()) > 0 else 0
            }

        except Exception as e:
            logger.warning(f"Rolling metrics calculation misslyckades: {e}")
            return {}

    async def _analyze_drawdown_periods(self, values) -> Dict[str, Any]:
        """Analysera drawdown periods."""
        try:
            import pandas as pd
            values_series = pd.Series(values)

            # Calculate drawdowns
            peak = values_series.expanding().max()
            drawdown = (values_series - peak) / peak

            # Find drawdown periods
            drawdown_periods = []
            current_drawdown = None

            for i, dd in enumerate(drawdown):
                if dd < 0:  # In drawdown
                    if current_drawdown is None:
                        current_drawdown = {'start': i, 'start_date': values_series.index[i], 'peak': peak.iloc[i]}
                    current_drawdown['end'] = i
                    current_drawdown['end_date'] = values_series.index[i]
                    current_drawdown['max_drawdown'] = dd
                else:  # Recovery
                    if current_drawdown is not None:
                        drawdown_periods.append(current_drawdown)
                        current_drawdown = None

            return {
                'max_drawdown': drawdown.min(),
                'drawdown_periods': drawdown_periods,
                'avg_drawdown_length': sum(p['end'] - p['start'] for p in drawdown_periods) / len(drawdown_periods) if drawdown_periods else 0
            }

        except Exception as e:
            logger.warning(f"Drawdown analysis misslyckades: {e}")
            return {}

    async def _analyze_return_distribution(self, returns) -> Dict[str, Any]:
        """Analysera return distribution."""
        try:
            import pandas as pd
            from scipy import stats

            returns_series = pd.Series(returns)

            # Calculate distribution statistics
            skew = stats.skew(returns_series.dropna())
            kurtosis = stats.kurtosis(returns_series.dropna())

            # Calculate percentiles
            percentiles = returns_series.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).to_dict()

            return {
                'skewness': skew,
                'kurtosis': kurtosis,
                'percentiles': percentiles,
                'distribution_type': 'normal' if abs(skew) < 0.5 and abs(kurtosis) < 1 else 'non_normal'
            }

        except Exception as e:
            logger.warning(f"Return distribution analysis misslyckades: {e}")
            return {}

    async def _calculate_relative_performance(self, benchmarking_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Beräkna relative performance mot benchmarks."""
        try:
            if not benchmarking_data:
                return {}

            # Calculate cumulative relative performance
            relative_performance = {
                'vs_btc': sum(d.get('relative_vs_btc_1d', 0) for d in benchmarking_data if d.get('relative_vs_btc_1d') is not None),
                'vs_eth': sum(d.get('relative_vs_eth_1d', 0) for d in benchmarking_data if d.get('relative_vs_eth_1d') is not None),
                'vs_market': sum(d.get('relative_vs_market_1d', 0) for d in benchmarking_data if d.get('relative_vs_market_1d') is not None)
            }

            return relative_performance

        except Exception as e:
            logger.warning(f"Relative performance calculation misslyckades: {e}")
            return {}

    async def _analyze_outperformance_periods(self, benchmarking_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysera outperformance periods."""
        try:
            if not benchmarking_data:
                return {}

            # Count outperformance periods
            outperformance = {
                'btc_outperformance_days': sum(1 for d in benchmarking_data if d.get('btc_performance_category') == 'OUTPERFORMING_BTC'),
                'eth_outperformance_days': sum(1 for d in benchmarking_data if d.get('eth_performance_category') == 'OUTPERFORMING_ETH'),
                'total_days': len(benchmarking_data)
            }

            return outperformance

        except Exception as e:
            logger.warning(f"Outperformance analysis misslyckades: {e}")
            return {}

    async def _calculate_benchmarking_score(self, benchmarking_data: List[Dict[str, Any]]) -> float:
        """Beräkna benchmarking score."""
        try:
            if not benchmarking_data:
                return 0.5

            # Simple benchmarking score based on relative performance
            avg_relative_performance = sum(
                d.get('relative_vs_btc_30d', 0) for d in benchmarking_data
                if d.get('relative_vs_btc_30d') is not None
            ) / len(benchmarking_data)

            # Convert to 0-1 scale
            return max(0, min(1, (avg_relative_performance + 1) / 2))

        except Exception as e:
            logger.warning(f"Benchmarking score calculation misslyckades: {e}")
            return 0.5

    async def _calculate_real_time_risk_metrics(self, wallet_address: str) -> Dict[str, Any]:
        """Beräkna real-time risk metrics."""
        try:
            # Get latest portfolio data
            balances_data = await self.bigquery_service.get_cross_chain_balances(wallet_address)

            if not balances_data['success'] or not balances_data['balances']:
                return {}

            balances = balances_data['balances']

            # Calculate simple real-time metrics
            total_value = sum(balance.get('value_usd', 0) for balance in balances)

            if total_value == 0:
                return {}

            # Portfolio volatility (simplified)
            values = [balance.get('value_usd', 0) for balance in balances]
            volatility = sum(abs(v - total_value/len(values)) for v in values) / (total_value/len(values)) if values else 0

            # Concentration risk
            max_position = max(values) / total_value if total_value > 0 else 0

            return {
                'real_time_volatility': volatility,
                'max_position_concentration': max_position,
                'diversification_ratio': len(balances) / 5.0,  # Normalized to 5 assets
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"Real-time risk metrics calculation misslyckades: {e}")
            return {}

    async def _generate_risk_alerts_from_data(self, risk_data: Dict[str, Any],
                                            additional_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generera risk alerts från data."""
        alerts = []

        try:
            # Check against thresholds
            var_95 = risk_data.get('value_at_risk_95', 0)
            if var_95 > 0.10:  # 10% VaR threshold
                alerts.append({
                    'type': 'var_breach',
                    'severity': 'high',
                    'message': f'VaR 95% is {var_95:.1%}, exceeds 10% threshold',
                    'action': 'Consider reducing position sizes'
                })

            volatility = additional_metrics.get('real_time_volatility', 0)
            if volatility > 0.50:  # 50% volatility threshold
                alerts.append({
                    'type': 'volatility_breach',
                    'severity': 'medium',
                    'message': f'Portfolio volatility is {volatility:.1%}, exceeds 50% threshold',
                    'action': 'Monitor closely and consider hedging'
                })

            max_concentration = additional_metrics.get('max_position_concentration', 0)
            if max_concentration > 0.25:  # 25% concentration threshold
                alerts.append({
                    'type': 'concentration_breach',
                    'severity': 'high',
                    'message': f'Max position concentration is {max_concentration:.1%}, exceeds 25% threshold',
                    'action': 'Rebalance to reduce concentration risk'
                })

        except Exception as e:
            logger.warning(f"Risk alerts generation misslyckades: {e}")

        return alerts

    def _calculate_comprehensive_risk_score(self, risk_data: Dict[str, Any],
                                         additional_metrics: Dict[str, Any],
                                         risk_alerts: List[Dict[str, Any]]) -> float:
        """Beräkna comprehensive risk score."""
        try:
            score = 0.5  # Base score

            # Factor in VaR
            var_95 = risk_data.get('value_at_risk_95', 0)
            if var_95 > 0.10:
                score += 0.3
            elif var_95 < 0.05:
                score -= 0.1

            # Factor in volatility
            volatility = additional_metrics.get('real_time_volatility', 0)
            if volatility > 0.50:
                score += 0.2
            elif volatility < 0.20:
                score -= 0.1

            # Factor in concentration
            concentration = additional_metrics.get('max_position_concentration', 0)
            if concentration > 0.25:
                score += 0.2

            # Factor in alerts
            high_severity_alerts = sum(1 for alert in risk_alerts if alert.get('severity') == 'high')
            if high_severity_alerts > 0:
                score += min(high_severity_alerts * 0.1, 0.3)

            return max(0, min(1, score))  # Clamp to 0-1

        except Exception as e:
            logger.warning(f"Comprehensive risk score calculation misslyckades: {e}")
            return 0.5

    def _get_risk_level_from_score(self, risk_score: float) -> str:
        """Bestäm risk level från risk score."""
        if risk_score < 0.3:
            return 'LOW'
        elif risk_score < 0.6:
            return 'MEDIUM'
        elif risk_score < 0.8:
            return 'HIGH'
        else:
            return 'CRITICAL'

    async def clear_cache(self) -> None:
        """Rensa analytics cache."""
        self.analytics_cache.clear()
        logger.info("Portfolio Analytics cache rensad")

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check."""
        try:
            # Kontrollera BigQuery service
            bigquery_health = await self.bigquery_service.get_service_status()

            # Kontrollera cache status
            cache_size = len(self.analytics_cache)
            cache_health = 'healthy' if cache_size < 100 else 'warning'

            return {
                'service': 'portfolio_analytics',
                'status': 'healthy' if bigquery_health['status'] == 'healthy' else 'degraded',
                'bigquery_service': bigquery_health,
                'cache_size': cache_size,
                'cache_health': cache_health,
                'supported_metrics': [e.value for e in PortfolioMetricType],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'portfolio_analytics',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }