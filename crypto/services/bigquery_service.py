"""
BigQuery Service för Google Cloud Web3 Blockchain Analytics
BigQuery client wrapper för blockchain data med integration till GoogleCloudWeb3Provider
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
import json

from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter
from google.api_core import exceptions as google_exceptions

from ..core.errors.error_handling import handle_errors, CryptoError, APIError
from ..core.analytics.analytics import MarketAnalyzer
from ..config.bigquery_config import get_bigquery_config, get_dataset_config, get_table_schema
from ..config.bigquery_queries import BigQueryQueries
from .google_cloud_web3_provider import GoogleCloudWeb3Provider

logger = logging.getLogger(__name__)

class BigQueryService:
    """
    BigQuery client wrapper för blockchain analytics och Google Cloud Web3 data.

    Features:
    - Portfolio analytics från BigQuery materialized views
    - Real-tids risk metrics beräkning
    - Cross-chain balance aggregation
    - Transaction analytics och pattern detection
    - Integration med GoogleCloudWeb3Provider för live data
    """

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """
        Initiera BigQuery service.

        Args:
            project_id: Google Cloud project ID
            credentials_path: Path till service account credentials
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.client: Optional[bigquery.Client] = None
        self.market_analyzer = MarketAnalyzer()
        self.web3_provider: Optional[GoogleCloudWeb3Provider] = None

        # Cache för queries
        self._query_cache = {}
        self._cache_ttl = 300  # 5 minuter

        # Setup BigQuery config
        self.config = get_bigquery_config()

    async def initialize(self) -> bool:
        """Initiera BigQuery client och dependencies."""
        try:
            # Initiera BigQuery client
            if self.credentials_path:
                self.client = bigquery.Client.from_service_account_json(
                    self.credentials_path,
                    project=self.project_id
                )
            else:
                self.client = bigquery.Client(project=self.project_id)

            # Initiera Market Analyzer
            await self.market_analyzer.__aenter__()

            # Initiera Google Cloud Web3 Provider (placeholder - skulle använda riktiga credentials)
            # self.web3_provider = GoogleCloudWeb3Provider(project_id, "api_key", "base_url")

            logger.info("BigQuery service initierad framgångsrikt")
            return True

        except Exception as e:
            logger.error(f"Misslyckades att initiera BigQuery service: {e}")
            raise CryptoError(f"BigQuery service initialization failed: {str(e)}", "BIGQUERY_INIT_ERROR")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()
        if hasattr(self.market_analyzer, '__aexit__'):
            await self.market_analyzer.__aexit__(exc_type, exc_val, exc_tb)

    @handle_errors(service_name="bigquery")
    async def execute_query(self, query: str, parameters: Optional[List[ScalarQueryParameter]] = None,
                          use_cache: bool = True) -> Dict[str, Any]:
        """
        Utför BigQuery query med caching och error handling.

        Args:
            query: SQL query att utföra
            parameters: Query parameters
            use_cache: Om cache ska användas

        Returns:
            Query resultat som dictionary
        """
        # Kontrollera cache
        cache_key = f"{hash(query)}_{str(parameters)}"
        if use_cache and cache_key in self._query_cache:
            cache_entry = self._query_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self._cache_ttl):
                logger.debug("Returnerar cachad query")
                return cache_entry['data']

        try:
            # Konfigurera query
            job_config = QueryJobConfig()
            if parameters:
                job_config.query_parameters = parameters

            # Sätt timeout och resource limits
            job_config.maximum_bytes_billed = self.config.MAX_BYTES_BILLED
            job_config.use_legacy_sql = self.config.USE_LEGACY_SQL

            # Utför query
            query_job = self.client.query(query, job_config=job_config)

            # Vänta på resultat
            result = query_job.result()

            # Konvertera till dictionary
            rows = []
            for row in result:
                rows.append(dict(row))

            response = {
                'success': True,
                'rows': rows,
                'total_rows': len(rows),
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'bytes_processed': query_job.total_bytes_processed,
                'execution_time': str(query_job.ended - query_job.started)
            }

            # Cache resultat
            if use_cache:
                self._query_cache[cache_key] = {
                    'timestamp': datetime.now(),
                    'data': response
                }

                # Begränsa cache storlek
                if len(self._query_cache) > 100:
                    oldest_key = min(self._query_cache.keys(),
                                   key=lambda k: self._query_cache[k]['timestamp'])
                    del self._query_cache[oldest_key]

            return response

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"BigQuery API error: {e}")
            raise APIError(f"BigQuery query failed: {str(e)}", "BIGQUERY_API_ERROR")
        except Exception as e:
            logger.error(f"BigQuery query error: {e}")
            raise CryptoError(f"BigQuery query error: {str(e)}", "BIGQUERY_QUERY_ERROR")

    @handle_errors(service_name="bigquery")
    async def get_portfolio_performance(self, wallet_address: str, days: int = 30) -> Dict[str, Any]:
        """
        Hämta portfolio performance för wallet från BigQuery.

        Args:
            wallet_address: Wallet address
            days: Antal dagar att analysera

        Returns:
            Portfolio performance data
        """
        try:
            # Skapa query
            query = BigQueryQueries.get_portfolio_performance_query(
                wallet_address=wallet_address,
                days=days,
                project_id=self.project_id,
                dataset="blockchain_analytics"
            )

            # Utför query
            result = await self.execute_query(query)
            if not result['success'] or not result['rows']:
                return {
                    'success': False,
                    'error': 'No portfolio data found',
                    'wallet_address': wallet_address
                }

            performance_data = result['rows'][0]

            # Förbättra med live data från Google Cloud Web3
            live_data = await self._enhance_with_live_data(wallet_address, performance_data)

            return {
                'success': True,
                'wallet_address': wallet_address,
                'performance': performance_data,
                'live_data': live_data,
                'analysis_period_days': days,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Portfolio performance query failed for {wallet_address}: {e}")
            raise CryptoError(f"Portfolio performance query failed: {str(e)}", "PORTFOLIO_PERFORMANCE_ERROR")

    @handle_errors(service_name="bigquery")
    async def get_cross_chain_balances(self, wallet_address: str) -> Dict[str, Any]:
        """
        Hämta cross-chain balances för wallet.

        Args:
            wallet_address: Wallet address

        Returns:
            Cross-chain balance data
        """
        try:
            # Hämta från BigQuery materialized view
            query = BigQueryQueries.get_cross_chain_balance_query(
                wallet_address=wallet_address,
                project_id=self.project_id,
                dataset="blockchain_analytics"
            )

            result = await self.execute_query(query)

            if not result['success']:
                return {
                    'success': False,
                    'error': 'No balance data found',
                    'wallet_address': wallet_address
                }

            balances = result['rows']

            # Förbättra med live data från Google Cloud Web3
            live_balances = await self._get_live_balances(wallet_address)

            return {
                'success': True,
                'wallet_address': wallet_address,
                'balances': balances,
                'live_balances': live_balances,
                'total_positions': len(balances),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Cross-chain balance query failed for {wallet_address}: {e}")
            raise CryptoError(f"Cross-chain balance query failed: {str(e)}", "CROSS_CHAIN_BALANCE_ERROR")

    @handle_errors(service_name="bigquery")
    async def get_risk_metrics(self, wallet_address: str) -> Dict[str, Any]:
        """
        Hämta risk metrics för wallet.

        Args:
            wallet_address: Wallet address

        Returns:
            Risk metrics data
        """
        try:
            # Hämta från BigQuery
            query = BigQueryQueries.get_risk_metrics_query(
                wallet_address=wallet_address,
                project_id=self.project_id,
                dataset="blockchain_analytics"
            )

            result = await self.execute_query(query)
            if not result['success'] or not result['rows']:
                return {
                    'success': False,
                    'error': 'No risk metrics found',
                    'wallet_address': wallet_address
                }

            risk_data = result['rows'][0]

            # Beräkna real-tids risk metrics
            live_risk_metrics = await self._calculate_live_risk_metrics(wallet_address)

            return {
                'success': True,
                'wallet_address': wallet_address,
                'risk_metrics': risk_data,
                'live_risk_metrics': live_risk_metrics,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Risk metrics query failed for {wallet_address}: {e}")
            raise CryptoError(f"Risk metrics query failed: {str(e)}", "RISK_METRICS_ERROR")

    @handle_errors(service_name="bigquery")
    async def get_transaction_analytics(self, wallet_address: str, chain: str = None,
                                      days: int = 7) -> Dict[str, Any]:
        """
        Hämta transaction analytics för wallet.

        Args:
            wallet_address: Wallet address
            chain: Specifik chain (None för alla)
            days: Antal dagar att analysera

        Returns:
            Transaction analytics data
        """
        try:
            # Hämta från BigQuery
            query = BigQueryQueries.get_transaction_history_query(
                wallet_address=wallet_address,
                chain=chain,
                days=days,
                project_id=self.project_id,
                dataset="blockchain_analytics"
            )

            result = await self.execute_query(query)

            if not result['success']:
                return {
                    'success': False,
                    'error': 'No transaction data found',
                    'wallet_address': wallet_address
                }

            transactions = result['rows']

            # Analysera transaction patterns
            pattern_analysis = await self._analyze_transaction_patterns(transactions)

            return {
                'success': True,
                'wallet_address': wallet_address,
                'transactions': transactions,
                'total_transactions': len(transactions),
                'pattern_analysis': pattern_analysis,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Transaction analytics query failed for {wallet_address}: {e}")
            raise CryptoError(f"Transaction analytics query failed: {str(e)}", "TRANSACTION_ANALYTICS_ERROR")

    async def _enhance_with_live_data(self, wallet_address: str,
                                    performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Förbättra performance data med live data från Google Cloud Web3."""
        try:
            if not self.web3_provider:
                return {}

            # Hämta live balances
            live_balances = await self.web3_provider.get_cross_chain_balances(wallet_address)

            # Hämta live transactions
            live_transactions = await self.web3_provider.get_transaction_history(
                wallet_address, limit=10
            )

            return {
                'live_balances': live_balances,
                'live_transactions': live_transactions,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"Failed to enhance with live data: {e}")
            return {}

    async def _get_live_balances(self, wallet_address: str) -> Dict[str, Any]:
        """Hämta live balances från Google Cloud Web3."""
        try:
            if not self.web3_provider:
                return {}

            return await self.web3_provider.get_cross_chain_balances(wallet_address)

        except Exception as e:
            logger.warning(f"Failed to get live balances: {e}")
            return {}

    async def _calculate_live_risk_metrics(self, wallet_address: str) -> Dict[str, Any]:
        """Beräkna live risk metrics."""
        try:
            # Hämta senaste portfolio data
            portfolio_data = await self.get_cross_chain_balances(wallet_address)
            if not portfolio_data['success']:
                return {}

            balances = portfolio_data['balances']
            total_value = sum(balance.get('value_usd', 0) for balance in balances)

            # Beräkna enkla risk metrics
            if not balances:
                return {}

            # Volatilitet (simplified)
            values = [balance.get('value_usd', 0) for balance in balances]
            volatility = self._calculate_volatility(values)

            # Value at Risk (simplified)
            var_95 = total_value * 0.05  # 5% VaR assumption

            # Diversification score
            chain_diversity = len(set(balance.get('chain') for balance in balances))
            diversification_score = min(chain_diversity / 5.0, 1.0)  # Max 5 chains

            return {
                'portfolio_value': total_value,
                'volatility': volatility,
                'var_95': var_95,
                'diversification_score': diversification_score,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"Failed to calculate live risk metrics: {e}")
            return {}

    def _calculate_volatility(self, values: List[float]) -> float:
        """Beräkna volatilitet från värden."""
        if len(values) < 2:
            return 0.0

        try:
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            return variance ** 0.5 / mean if mean > 0 else 0.0
        except (ZeroDivisionError, ValueError):
            return 0.0

    async def _analyze_transaction_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysera transaction patterns."""
        try:
            if not transactions:
                return {}

            # Beräkna grundläggande statistik
            values = [float(tx.get('value_eth', 0)) for tx in transactions]
            timestamps = [tx.get('timestamp') for tx in transactions]

            # Frequency analysis
            if len(timestamps) > 1:
                time_diffs = []
                for i in range(1, len(timestamps)):
                    try:
                        diff = (timestamps[i] - timestamps[i-1]).total_seconds()
                        if diff > 0:
                            time_diffs.append(diff)
                    except:
                        continue

                avg_time_between = sum(time_diffs) / len(time_diffs) if time_diffs else 0
            else:
                avg_time_between = 0

            return {
                'total_transactions': len(transactions),
                'avg_transaction_value': sum(values) / len(values) if values else 0,
                'max_transaction_value': max(values) if values else 0,
                'min_transaction_value': min(values) if values else 0,
                'avg_time_between_transactions': avg_time_between,
                'unique_addresses': len(set(tx.get('to_address', '') for tx in transactions)),
                'success_rate': len([tx for tx in transactions if tx.get('status') == 'success']) / len(transactions)
            }

        except Exception as e:
            logger.warning(f"Transaction pattern analysis failed: {e}")
            return {}

    @handle_errors(service_name="bigquery")
    async def get_wallet_overview(self, wallet_address: str) -> Dict[str, Any]:
        """
        Hämta comprehensive wallet overview.

        Args:
            wallet_address: Wallet address

        Returns:
            Complete wallet overview
        """
        try:
            # Kör alla queries parallellt
            tasks = [
                self.get_portfolio_performance(wallet_address, 30),
                self.get_cross_chain_balances(wallet_address),
                self.get_risk_metrics(wallet_address),
                self.get_transaction_analytics(wallet_address, days=7)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Samla resultat
            overview = {
                'success': True,
                'wallet_address': wallet_address,
                'timestamp': datetime.now().isoformat()
            }

            # Hantera varje resultat
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Query {i} failed: {result}")
                    continue

                if result['success']:
                    if i == 0:  # Portfolio performance
                        overview['performance'] = result.get('performance', {})
                        overview['live_data'] = result.get('live_data', {})
                    elif i == 1:  # Balances
                        overview['balances'] = result.get('balances', [])
                        overview['live_balances'] = result.get('live_balances', {})
                    elif i == 2:  # Risk metrics
                        overview['risk_metrics'] = result.get('risk_metrics', {})
                        overview['live_risk_metrics'] = result.get('live_risk_metrics', {})
                    elif i == 3:  # Transaction analytics
                        overview['transaction_analytics'] = result.get('pattern_analysis', {})
                        overview['recent_transactions'] = result.get('transactions', [])

            # Beräkna overall health score
            overview['health_score'] = self._calculate_health_score(overview)

            return overview

        except Exception as e:
            logger.error(f"Wallet overview query failed for {wallet_address}: {e}")
            raise CryptoError(f"Wallet overview query failed: {str(e)}", "WALLET_OVERVIEW_ERROR")

    def _calculate_health_score(self, overview: Dict[str, Any]) -> float:
        """Beräkna overall health score för wallet."""
        try:
            score = 50.0  # Base score

            # Performance factor
            performance = overview.get('performance', {})
            if performance:
                total_return = performance.get('total_return_percent', 0)
                if total_return > 10:
                    score += 20
                elif total_return > 0:
                    score += 10
                elif total_return < -20:
                    score -= 30
                elif total_return < 0:
                    score -= 15

            # Risk factor
            risk_metrics = overview.get('risk_metrics', {})
            if risk_metrics:
                var_95 = risk_metrics.get('var_95', 0)
                if var_95 < 0.05:
                    score += 15
                elif var_95 < 0.10:
                    score += 5
                elif var_95 > 0.20:
                    score -= 25

            # Activity factor
            balances = overview.get('balances', [])
            transactions = overview.get('recent_transactions', [])

            if len(balances) > 5:
                score += 10
            if len(transactions) > 10:
                score += 5

            return max(0, min(100, score))  # Clamp between 0-100

        except Exception as e:
            logger.warning(f"Health score calculation failed: {e}")
            return 50.0

    async def clear_cache(self) -> None:
        """Rensa query cache."""
        self._query_cache.clear()
        logger.info("BigQuery service cache rensad")

    async def get_service_status(self) -> Dict[str, Any]:
        """Hämta service status."""
        return {
            'service': 'bigquery_service',
            'project_id': self.project_id,
            'client_connected': self.client is not None,
            'market_analyzer_ready': hasattr(self.market_analyzer, 'session') and self.market_analyzer.session is not None,
            'web3_provider_ready': self.web3_provider is not None,
            'cache_size': len(self._query_cache),
            'timestamp': datetime.now().isoformat()
        }

# Global service instance
_bigquery_service: Optional[BigQueryService] = None

def get_bigquery_service(project_id: str, credentials_path: Optional[str] = None) -> BigQueryService:
    """Hämta global BigQuery service instans."""
    global _bigquery_service
    if _bigquery_service is None:
        _bigquery_service = BigQueryService(project_id, credentials_path)
    return _bigquery_service

async def get_wallet_overview(wallet_address: str, project_id: str,
                            credentials_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function för att hämta wallet overview.

    Args:
        wallet_address: Wallet address
        project_id: Google Cloud project ID
        credentials_path: Path till credentials

    Returns:
        Wallet overview data
    """
    service = get_bigquery_service(project_id, credentials_path)
    async with service:
        return await service.get_wallet_overview(wallet_address)