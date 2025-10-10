"""
Web3 BigQuery Integration Service
Unified integration mellan Google Cloud Web3 och BigQuery för blockchain analytics
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..core.errors.error_handling import handle_errors, CryptoError, ValidationError
from .google_cloud_web3_provider import GoogleCloudWeb3Provider
from .bigquery_service import BigQueryService, get_bigquery_service
from .portfolio_analytics import PortfolioAnalyticsService
from .blockchain_analytics import BlockchainAnalytics
from ..config.bigquery_config import get_bigquery_config

logger = logging.getLogger(__name__)

class Web3BigQueryIntegration:
    """
    Unified integration service för Google Cloud Web3 och BigQuery blockchain analytics.

    Features:
    - Real-tids data från Google Cloud Web3 Gateway
    - Historiska och aggregerade data från BigQuery materialized views
    - Portfolio performance tracking med risk metrics
    - Cross-chain balance aggregation och analytics
    - Automated portfolio rebalancing och optimization
    - Performance benchmarking mot market indices
    - Real-tids alerting och risk management
    """

    def __init__(self, project_id: str, web3_provider: Optional[GoogleCloudWeb3Provider] = None,
                 credentials_path: Optional[str] = None):
        """
        Initiera Web3 BigQuery Integration Service.

        Args:
            project_id: Google Cloud project ID
            web3_provider: Google Cloud Web3 provider instans
            credentials_path: Path till Google Cloud credentials
        """
        self.project_id = project_id
        self.credentials_path = credentials_path

        # Service components
        self.web3_provider = web3_provider
        self.bigquery_service: Optional[BigQueryService] = None
        self.portfolio_analytics: Optional[PortfolioAnalyticsService] = None
        self.blockchain_analytics: Optional[BlockchainAnalytics] = None

        # Integration cache
        self.integration_cache = {}
        self.cache_ttl = 300  # 5 minuter

        # Supported chains
        self.supported_chains = [
            'ethereum', 'polygon', 'arbitrum', 'optimism', 'base'
        ]

        # Integration status
        self.integration_status = {
            'web3_connected': False,
            'bigquery_connected': False,
            'portfolio_analytics_ready': False,
            'blockchain_analytics_ready': False
        }

        logger.info("Web3 BigQuery Integration Service initierad")

    async def initialize(self) -> bool:
        """Initiera alla service components."""
        try:
            logger.info("Initierar Web3 BigQuery Integration Service...")

            # Initiera BigQuery service
            self.bigquery_service = get_bigquery_service(self.project_id, self.credentials_path)
            await self.bigquery_service.initialize()
            self.integration_status['bigquery_connected'] = True

            # Initiera Web3 provider om inte provided
            if not self.web3_provider:
                # Placeholder för Web3 provider initialization
                # I produktion skulle detta använda riktiga credentials
                # self.web3_provider = GoogleCloudWeb3Provider(project_id, api_key, base_url)
                pass

            # Initiera Portfolio Analytics
            self.portfolio_analytics = PortfolioAnalyticsService(
                self.project_id, self.bigquery_service, self.web3_provider
            )
            await self.portfolio_analytics.initialize()
            self.integration_status['portfolio_analytics_ready'] = True

            # Initiera Blockchain Analytics
            if self.web3_provider:
                self.blockchain_analytics = BlockchainAnalytics(
                    self.web3_provider, "blockchain_analytics"
                )
                # blockchain_analytics har sin egen initialization
                self.integration_status['blockchain_analytics_ready'] = True

            # Markera Web3 som connected om tillgängligt
            self.integration_status['web3_connected'] = self.web3_provider is not None

            logger.info("Web3 BigQuery Integration Service initierad framgångsrikt")
            return True

        except Exception as e:
            logger.error(f"Misslyckades att initiera Web3 BigQuery Integration Service: {e}")
            raise CryptoError(f"Web3 BigQuery Integration initialization failed: {str(e)}", "INTEGRATION_INIT_ERROR")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @handle_errors(service_name="web3_bigquery_integration")
    async def get_comprehensive_wallet_analysis(self, wallet_address: str,
                                             include_live_data: bool = True,
                                             include_risk_analysis: bool = True) -> Dict[str, Any]:
        """
        Hämta comprehensive wallet analysis med all tillgänglig data.

        Args:
            wallet_address: Wallet address att analysera
            include_live_data: Om live data från Web3 ska inkluderas
            include_risk_analysis: Om risk analysis ska inkluderas

        Returns:
            Comprehensive wallet analysis
        """
        cache_key = f"comprehensive_{wallet_address}_{include_live_data}_{include_risk_analysis}"
        if cache_key in self.integration_cache:
            cache_entry = self.integration_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cache_entry['data']

        try:
            logger.info(f"Utför comprehensive wallet analysis för {wallet_address}")

            # Kör parallella queries för optimal prestanda
            tasks = []

            # Portfolio snapshot från Portfolio Analytics
            if self.portfolio_analytics:
                tasks.append(self.portfolio_analytics.get_portfolio_snapshot(wallet_address, include_live_data))

            # Blockchain analytics från Blockchain Analytics
            if self.blockchain_analytics:
                tasks.append(self.blockchain_analytics.get_portfolio_analytics(wallet_address))

            # BigQuery queries för historical data
            if self.bigquery_service:
                tasks.append(self.bigquery_service.get_wallet_overview(wallet_address))

            # Risk dashboard
            if include_risk_analysis and self.portfolio_analytics:
                tasks.append(self.portfolio_analytics.get_risk_dashboard(wallet_address))

            # Kör alla tasks parallellt
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Samla och merge resultaten
            comprehensive_analysis = await self._merge_analysis_results(
                wallet_address, results, include_live_data, include_risk_analysis
            )

            # Lägg till integration metadata
            comprehensive_analysis.update({
                'integration_info': {
                    'services_available': self.integration_status,
                    'data_sources': {
                        'web3_provider': self.web3_provider is not None,
                        'bigquery_service': self.bigquery_service is not None,
                        'portfolio_analytics': self.portfolio_analytics is not None,
                        'blockchain_analytics': self.blockchain_analytics is not None
                    },
                    'analysis_timestamp': datetime.now().isoformat(),
                    'supported_chains': self.supported_chains
                }
            })

            # Cache resultatet
            self.integration_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': comprehensive_analysis
            }

            logger.info(f"Comprehensive wallet analysis slutförd för {wallet_address}")
            return comprehensive_analysis

        except Exception as e:
            logger.error(f"Comprehensive wallet analysis misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Comprehensive wallet analysis failed: {str(e)}", "COMPREHENSIVE_ANALYSIS_ERROR")

    @handle_errors(service_name="web3_bigquery_integration")
    async def get_real_time_portfolio_monitoring(self, wallet_address: str,
                                               monitoring_interval: int = 60) -> Dict[str, Any]:
        """
        Hämta real-tids portfolio monitoring data.

        Args:
            wallet_address: Wallet address att monitorera
            monitoring_interval: Monitoring intervall i sekunder

        Returns:
            Real-tids monitoring data
        """
        try:
            # Hämta latest portfolio snapshot
            portfolio_data = await self.portfolio_analytics.get_portfolio_snapshot(
                wallet_address, include_live_data=True
            )

            # Hämta real-tids risk metrics
            risk_data = await self.portfolio_analytics.get_risk_dashboard(wallet_address)

            # Hämta latest transactions från Web3
            latest_transactions = {}
            if self.web3_provider:
                tx_history = await self.web3_provider.get_transaction_history(
                    wallet_address, limit=10
                )
                latest_transactions = tx_history.get('transactions', [])

            # Generera monitoring alerts
            alerts = await self._generate_monitoring_alerts(
                wallet_address, portfolio_data, risk_data, latest_transactions
            )

            # Skapa real-tids metrics
            real_time_metrics = {
                'portfolio_value': portfolio_data.get('portfolio_data', {}).get('total_value_usd', 0),
                'last_updated': datetime.now().isoformat(),
                'monitoring_interval': monitoring_interval,
                'data_freshness': 'real_time' if self.web3_provider else 'cached',
                'risk_status': risk_data.get('overall_risk_score', 0.5),
                'active_alerts_count': len(alerts)
            }

            return {
                'wallet_address': wallet_address,
                'real_time_metrics': real_time_metrics,
                'portfolio_snapshot': portfolio_data,
                'risk_analysis': risk_data,
                'latest_transactions': latest_transactions,
                'alerts': alerts,
                'monitoring_info': {
                    'interval': monitoring_interval,
                    'next_update': (datetime.now() + timedelta(seconds=monitoring_interval)).isoformat(),
                    'services_status': self.integration_status
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Real-tids portfolio monitoring misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Real-time portfolio monitoring failed: {str(e)}", "MONITORING_ERROR")

    @handle_errors(service_name="web3_bigquery_integration")
    async def get_portfolio_optimization_recommendations(self, wallet_address: str) -> Dict[str, Any]:
        """
        Hämta portfolio optimization recommendations.

        Args:
            wallet_address: Wallet address att optimera

        Returns:
            Portfolio optimization recommendations
        """
        try:
            # Hämta rebalancing analysis
            rebalancing_data = await self.portfolio_analytics.get_rebalancing_analysis(wallet_address)

            # Hämta risk-optimized allocation
            risk_optimized_allocation = await self._calculate_risk_optimized_allocation(wallet_address)

            # Generera optimization actions
            optimization_actions = await self._generate_optimization_actions(
                wallet_address, rebalancing_data, risk_optimized_allocation
            )

            # Beräkna expected impact
            expected_impact = await self._calculate_optimization_impact(
                wallet_address, optimization_actions
            )

            return {
                'wallet_address': wallet_address,
                'rebalancing_analysis': rebalancing_data,
                'risk_optimized_allocation': risk_optimized_allocation,
                'optimization_actions': optimization_actions,
                'expected_impact': expected_impact,
                'recommendations_summary': await self._generate_recommendations_summary(optimization_actions),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Portfolio optimization misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Portfolio optimization failed: {str(e)}", "OPTIMIZATION_ERROR")

    async def _merge_analysis_results(self, wallet_address: str, results: List[Any],
                                    include_live_data: bool, include_risk_analysis: bool) -> Dict[str, Any]:
        """Merge analysis results från olika services."""
        try:
            merged_data = {
                'wallet_address': wallet_address,
                'analysis_type': 'comprehensive',
                'live_data_included': include_live_data,
                'risk_analysis_included': include_risk_analysis
            }

            # Merge portfolio data
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Analysis {i} misslyckades: {result}")
                    continue

                if isinstance(result, dict):
                    if 'portfolio_data' in result:
                        merged_data['portfolio_data'] = result['portfolio_data']
                    if 'risk_analysis' in result:
                        merged_data['risk_analysis'] = result['risk_analysis']
                    if 'wallet_address' in result and result['wallet_address'] == wallet_address:
                        # Merge other relevant data
                        for key, value in result.items():
                            if key not in merged_data and key not in ['wallet_address', 'success']:
                                merged_data[key] = value

            # Calculate overall health score
            merged_data['overall_health_score'] = await self._calculate_overall_health_score(merged_data)

            return merged_data

        except Exception as e:
            logger.warning(f"Analysis results merge misslyckades: {e}")
            return {'wallet_address': wallet_address, 'error': str(e)}

    async def _generate_monitoring_alerts(self, wallet_address: str, portfolio_data: Dict[str, Any],
                                        risk_data: Dict[str, Any], transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generera monitoring alerts baserat på real-tids data."""
        alerts = []

        try:
            # Risk alerts
            risk_score = risk_data.get('overall_risk_score', 0.5)
            if risk_score > 0.8:
                alerts.append({
                    'type': 'risk',
                    'severity': 'critical',
                    'message': f'Critical risk level detected: {risk_score:.2f}',
                    'action': 'Immediate risk reduction required'
                })
            elif risk_score > 0.6:
                alerts.append({
                    'type': 'risk',
                    'severity': 'warning',
                    'message': f'High risk level detected: {risk_score:.2f}',
                    'action': 'Monitor closely and consider rebalancing'
                })

            # Performance alerts
            portfolio_value = portfolio_data.get('portfolio_data', {}).get('total_value_usd', 0)
            if portfolio_value > 0:
                # Placeholder för performance change detection
                pass

            # Transaction alerts
            if transactions:
                failed_txs = [tx for tx in transactions if tx.get('status') == 'failed']
                if len(failed_txs) > 2:
                    alerts.append({
                        'type': 'transactions',
                        'severity': 'warning',
                        'message': f'Multiple failed transactions detected: {len(failed_txs)}',
                        'action': 'Check transaction settings and network status'
                    })

            # Balance alerts
            balances = portfolio_data.get('portfolio_data', {}).get('balances', [])
            if balances:
                zero_balance_tokens = [b for b in balances if b.get('balance_formatted', 0) == 0]
                if len(zero_balance_tokens) > len(balances) * 0.5:
                    alerts.append({
                        'type': 'balance',
                        'severity': 'info',
                        'message': f'Many tokens have zero balance: {len(zero_balance_tokens)}/{len(balances)}',
                        'action': 'Consider consolidating or removing zero-balance tokens'
                    })

        except Exception as e:
            logger.warning(f"Monitoring alerts generation misslyckades: {e}")

        return alerts

    async def _calculate_risk_optimized_allocation(self, wallet_address: str) -> Dict[str, Any]:
        """Beräkna risk-optimized portfolio allocation."""
        try:
            # Hämta current portfolio data
            portfolio_data = await self.portfolio_analytics.get_portfolio_snapshot(wallet_address)
            balances = portfolio_data.get('portfolio_data', {}).get('balances', [])

            # Hämta risk preferences (simulerad)
            risk_preferences = {
                'max_position_weight': 0.25,
                'risk_tolerance': 0.6,  # 0-1 scale
                'diversification_preference': 0.8,
                'liquidity_preference': 0.7
            }

            # Beräkna optimal weights baserat på risk metrics
            total_value = sum(b.get('value_usd', 0) for b in balances)

            optimized_allocation = {}
            for balance in balances:
                symbol = balance.get('token_symbol', 'UNKNOWN')
                current_value = balance.get('value_usd', 0)

                if total_value > 0:
                    current_weight = current_value / total_value

                    # Risk-adjusted target weight
                    risk_factor = balance.get('risk_score', 0.5)
                    if risk_factor > 0.7:
                        target_weight = max(current_weight * 0.7, 0.05)  # Reduce high-risk positions
                    elif risk_factor < 0.3:
                        target_weight = min(current_weight * 1.2, 0.25)  # Increase low-risk positions
                    else:
                        target_weight = current_weight

                    optimized_allocation[symbol] = {
                        'current_weight': current_weight,
                        'target_weight': target_weight,
                        'current_value': current_value,
                        'target_value': target_weight * total_value,
                        'adjustment_needed': target_weight * total_value - current_value
                    }

            return {
                'wallet_address': wallet_address,
                'total_portfolio_value': total_value,
                'optimized_allocation': optimized_allocation,
                'risk_preferences': risk_preferences,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"Risk-optimized allocation calculation misslyckades: {e}")
            return {}

    async def _generate_optimization_actions(self, wallet_address: str,
                                          rebalancing_data: Dict[str, Any],
                                          risk_allocation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generera optimization actions."""
        actions = []

        try:
            # Generera actions från rebalancing data
            recommendations = rebalancing_data.get('recommendations', [])
            for rec in recommendations:
                actions.append({
                    'type': 'rebalancing',
                    'token_symbol': rec.get('token_symbol'),
                    'action': rec.get('action'),
                    'amount_usd': rec.get('amount_usd'),
                    'reason': rec.get('reason'),
                    'priority': rec.get('priority', 5),
                    'expected_impact': 'medium'
                })

            # Generera actions från risk allocation
            optimized = risk_allocation.get('optimized_allocation', {})
            for symbol, allocation in optimized.items():
                adjustment = allocation.get('adjustment_needed', 0)
                if abs(adjustment) > 100:  # Minsta adjustment threshold
                    actions.append({
                        'type': 'risk_optimization',
                        'token_symbol': symbol,
                        'action': 'buy' if adjustment > 0 else 'sell',
                        'amount_usd': abs(adjustment),
                        'reason': f'Risk-optimized allocation adjustment',
                        'priority': 7,
                        'expected_impact': 'high'
                    })

            # Sortera actions efter priority
            actions.sort(key=lambda x: x.get('priority', 5), reverse=True)

        except Exception as e:
            logger.warning(f"Optimization actions generation misslyckades: {e}")

        return actions

    async def _calculate_optimization_impact(self, wallet_address: str,
                                          actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Beräkna expected impact av optimization actions."""
        try:
            # Simulerad impact calculation
            total_adjustment = sum(abs(action.get('amount_usd', 0)) for action in actions)
            high_impact_actions = len([a for a in actions if a.get('expected_impact') == 'high'])

            return {
                'total_portfolio_impact_usd': total_adjustment,
                'high_impact_actions': high_impact_actions,
                'total_actions': len(actions),
                'estimated_completion_time': len(actions) * 30,  # 30 sekunder per action
                'expected_risk_reduction': high_impact_actions * 0.1,  # 10% risk reduction per high-impact action
                'expected_return_improvement': high_impact_actions * 0.05  # 5% return improvement per high-impact action
            }

        except Exception as e:
            logger.warning(f"Optimization impact calculation misslyckades: {e}")
            return {}

    async def _generate_recommendations_summary(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generera recommendations summary."""
        try:
            if not actions:
                return {'summary': 'No optimization actions needed', 'urgency': 'low'}

            high_priority = [a for a in actions if a.get('priority', 5) >= 8]
            medium_priority = [a for a in actions if 5 <= a.get('priority', 5) < 8]

            urgency = 'critical' if len(high_priority) > 3 else 'high' if len(high_priority) > 0 else 'medium'

            return {
                'summary': f'Portfolio optimization recommended: {len(actions)} actions ({len(high_priority)} high priority)',
                'urgency': urgency,
                'high_priority_actions': len(high_priority),
                'medium_priority_actions': len(medium_priority),
                'estimated_time': f'{len(actions) * 30} seconds',
                'expected_benefit': 'Risk reduction and performance improvement'
            }

        except Exception as e:
            logger.warning(f"Recommendations summary generation misslyckades: {e}")
            return {'summary': 'Unable to generate recommendations summary', 'urgency': 'unknown'}

    async def _calculate_overall_health_score(self, merged_data: Dict[str, Any]) -> float:
        """Beräkna overall health score från merged data."""
        try:
            score = 0.5  # Base score

            # Portfolio health (40% weight)
            portfolio_data = merged_data.get('portfolio_data', {})
            if portfolio_data:
                total_value = portfolio_data.get('total_value_usd', 0)
                if total_value > 0:
                    score += 0.2

                balances = portfolio_data.get('balances', [])
                if len(balances) > 3:
                    score += 0.2

            # Risk health (35% weight)
            risk_data = merged_data.get('risk_analysis', {})
            if risk_data:
                risk_score = risk_data.get('overall_risk_score', 0.5)
                score += (1 - risk_score) * 0.35

            # Transaction health (25% weight)
            transactions = merged_data.get('live_transactions', [])
            if transactions:
                success_rate = sum(1 for tx in transactions if tx.get('status') == 'success') / len(transactions)
                score += success_rate * 0.25

            return max(0, min(1, score))  # Clamp to 0-1

        except Exception as e:
            logger.warning(f"Overall health score calculation misslyckades: {e}")
            return 0.5

    async def clear_cache(self) -> None:
        """Rensa integration cache."""
        self.integration_cache.clear()
        if self.portfolio_analytics:
            await self.portfolio_analytics.clear_cache()
        if self.bigquery_service:
            await self.bigquery_service.clear_cache()
        logger.info("Web3 BigQuery Integration cache rensad")

    async def health_check(self) -> Dict[str, Any]:
        """Utför comprehensive health check."""
        try:
            # Kontrollera alla services
            checks = []

            if self.bigquery_service:
                checks.append(self.bigquery_service.get_service_status())

            if self.portfolio_analytics:
                checks.append(self.portfolio_analytics.health_check())

            if self.web3_provider:
                checks.append(self.web3_provider.health_check())

            # Kör alla health checks parallellt
            health_results = await asyncio.gather(*checks, return_exceptions=True)

            # Sammanfatta results
            overall_status = 'healthy'
            service_statuses = {}

            for i, result in enumerate(health_results):
                if isinstance(result, Exception):
                    overall_status = 'degraded'
                    service_statuses[f'service_{i}'] = {'status': 'error', 'error': str(result)}
                else:
                    if result.get('status') != 'healthy':
                        overall_status = 'degraded'
                    service_statuses[f'service_{i}'] = result

            return {
                'integration_service': 'web3_bigquery_integration',
                'overall_status': overall_status,
                'service_statuses': service_statuses,
                'supported_chains': self.supported_chains,
                'cache_size': len(self.integration_cache),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'integration_service': 'web3_bigquery_integration',
                'overall_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global integration instance
_web3_bigquery_integration: Optional[Web3BigQueryIntegration] = None

def get_web3_bigquery_integration(project_id: str,
                                web3_provider: Optional[GoogleCloudWeb3Provider] = None,
                                credentials_path: Optional[str] = None) -> Web3BigQueryIntegration:
    """Hämta global Web3 BigQuery integration instans."""
    global _web3_bigquery_integration
    if _web3_bigquery_integration is None:
        _web3_bigquery_integration = Web3BigQueryIntegration(project_id, web3_provider, credentials_path)
    return _web3_bigquery_integration

async def get_wallet_analysis(wallet_address: str, project_id: str,
                            credentials_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function för att hämta comprehensive wallet analysis.

    Args:
        wallet_address: Wallet address
        project_id: Google Cloud project ID
        credentials_path: Path till credentials

    Returns:
        Comprehensive wallet analysis
    """
    integration = get_web3_bigquery_integration(project_id, credentials_path=credentials_path)
    async with integration:
        return await integration.get_comprehensive_wallet_analysis(wallet_address)