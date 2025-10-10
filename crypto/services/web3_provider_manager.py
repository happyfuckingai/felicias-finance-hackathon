"""
Web3 Provider Manager - Smart provider manager som väljer rätt provider.
Fallback-system mellan Google Cloud Web3 och externa providers med provider abstraction.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..core.errors.error_handling import handle_errors, CryptoError, ValidationError
from ..core.errors.fail_safe import global_fail_safe
from .google_cloud_web3_provider import GoogleCloudWeb3Provider
from ..core.token.token_providers import TokenProvider, TokenInfo

logger = logging.getLogger(__name__)

class ProviderPriority(Enum):
    """Provider prioritet för fallback."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    FALLBACK = "fallback"

class OperationType(Enum):
    """Typer av Web3 operationer."""
    TOKEN_INFO = "token_info"
    BALANCE_CHECK = "balance_check"
    TRANSACTION_HISTORY = "transaction_history"
    CROSS_CHAIN_SWAP = "cross_chain_swap"
    CONTRACT_DEPLOYMENT = "contract_deployment"
    BATCH_OPERATIONS = "batch_operations"

@dataclass
class ProviderConfig:
    """Konfiguration för provider."""
    provider_type: str
    priority: ProviderPriority
    enabled: bool = True
    rate_limit: int = 100  # operations per minute
    timeout_seconds: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 60  # seconds
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"  # healthy, degraded, unhealthy
    error_count: int = 0
    success_count: int = 0

@dataclass
class ProviderMetrics:
    """Metrics för provider prestanda."""
    provider_type: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_used: Optional[datetime] = None
    error_rate: float = 0.0
    uptime_percentage: float = 100.0

class Web3ProviderManager:
    """
    Smart provider manager för Web3 integration.

    Features:
    - Intelligent provider selection baserat på operation och prestanda
    - Fallback-system mellan Google Cloud Web3 och externa providers
    - Provider abstraction för seamless migration
    - Integration med befintlig token_resolver.py
    - Load balancing och rate limiting
    - Health monitoring och automatic failover
    """

    def __init__(self, google_cloud_provider: GoogleCloudWeb3Provider):
        """
        Initiera Web3 Provider Manager.

        Args:
            google_cloud_provider: GoogleCloudWeb3Provider instans
        """
        self.google_cloud_provider = google_cloud_provider
        self.external_providers = {}

        # Provider konfigurationer
        self.provider_configs = {
            'google_cloud_web3': ProviderConfig(
                provider_type='google_cloud_web3',
                priority=ProviderPriority.PRIMARY,
                rate_limit=1000,
                timeout_seconds=30,
                retry_attempts=2
            ),
            'infura': ProviderConfig(
                provider_type='infura',
                priority=ProviderPriority.SECONDARY,
                rate_limit=500,
                timeout_seconds=30,
                retry_attempts=3
            ),
            'alchemy': ProviderConfig(
                provider_type='alchemy',
                priority=ProviderPriority.SECONDARY,
                rate_limit=300,
                timeout_seconds=30,
                retry_attempts=3
            ),
            'quicknode': ProviderConfig(
                provider_type='quicknode',
                priority=ProviderPriority.FALLBACK,
                rate_limit=200,
                timeout_seconds=30,
                retry_attempts=3
            )
        }

        # Provider metrics
        self.provider_metrics = {
            name: ProviderMetrics(provider_type=name)
            for name in self.provider_configs.keys()
        }

        # Rate limiting cache
        self.rate_limit_cache = {}

        # Operation history för analytics
        self.operation_history = []

        logger.info("Web3 Provider Manager initierad")

    @handle_errors(service_name="web3_provider_manager")
    async def get_best_provider_for_operation(self, operation_type: OperationType,
                                            chain: str = 'ethereum',
                                            priority_override: ProviderPriority = None) -> Tuple[Any, str]:
        """
        Välj bästa provider för given operation.

        Args:
            operation_type: Typ av operation
            chain: Blockchain att använda
            priority_override: Tvinga specifik provider prioritet

        Returns:
            Tuple av (provider_instance, provider_name)
        """
        try:
            # Hämta tillgängliga providers
            available_providers = await self._get_available_providers(operation_type, chain, priority_override)

            if not available_providers:
                raise CryptoError("Inga tillgängliga providers för operationen",
                                "NO_PROVIDERS_AVAILABLE")

            # Sortera providers efter prestanda och prioritet
            sorted_providers = await self._sort_providers_by_performance(available_providers)

            # Välj bästa provider
            best_provider_name = sorted_providers[0][0]
            best_provider = await self._get_provider_instance(best_provider_name)

            # Uppdatera metrics
            await self._update_provider_metrics(best_provider_name, 'selected')

            logger.info(f"Bästa provider för {operation_type.value} på {chain}: {best_provider_name}")
            return best_provider, best_provider_name

        except Exception as e:
            logger.error(f"Provider selection misslyckades för {operation_type.value}: {e}")
            raise

    @handle_errors(service_name="web3_provider_manager")
    async def execute_with_fallback(self, operation_func, operation_type: OperationType,
                                  chain: str = 'ethereum', **kwargs) -> Dict[str, Any]:
        """
        Utför operation med automatisk fallback.

        Args:
            operation_func: Funktion att utföra
            operation_type: Typ av operation
            chain: Blockchain att använda
            **kwargs: Argument till operationen

        Returns:
            Operation resultat
        """
        start_time = datetime.now()
        provider_attempts = []
        last_error = None

        try:
            # Försök med primary provider först
            primary_provider, provider_name = await self.get_best_provider_for_operation(
                operation_type, chain, ProviderPriority.PRIMARY
            )

            try:
                result = await operation_func(provider=primary_provider, **kwargs)
                await self._update_provider_metrics(provider_name, 'success')

                # Logga lyckad operation
                await self._log_operation_success(operation_type, provider_name, datetime.now() - start_time)

                return {
                    **result,
                    'provider_used': provider_name,
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'fallback_used': False
                }

            except Exception as e:
                last_error = e
                provider_attempts.append({'provider': provider_name, 'error': str(e)})
                await self._update_provider_metrics(provider_name, 'error')

                logger.warning(f"Primary provider {provider_name} misslyckades: {e}")

        except Exception as e:
            logger.warning(f"Kunde inte hämta primary provider: {e}")

        # Försök med secondary providers
        try:
            secondary_provider, provider_name = await self.get_best_provider_for_operation(
                operation_type, chain, ProviderPriority.SECONDARY
            )

            try:
                result = await operation_func(provider=secondary_provider, **kwargs)
                await self._update_provider_metrics(provider_name, 'success')

                await self._log_operation_success(operation_type, provider_name, datetime.now() - start_time)

                return {
                    **result,
                    'provider_used': provider_name,
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'fallback_used': True,
                    'fallback_reason': f"Primary provider misslyckades: {str(last_error) if last_error else 'unknown'}"
                }

            except Exception as e:
                provider_attempts.append({'provider': provider_name, 'error': str(e)})
                await self._update_provider_metrics(provider_name, 'error')

                logger.warning(f"Secondary provider {provider_name} misslyckades: {e}")

        except Exception as e:
            logger.warning(f"Kunde inte hämta secondary provider: {e}")

        # Försök med fallback providers
        try:
            fallback_provider, provider_name = await self.get_best_provider_for_operation(
                operation_type, chain, ProviderPriority.FALLBACK
            )

            try:
                result = await operation_func(provider=fallback_provider, **kwargs)
                await self._update_provider_metrics(provider_name, 'success')

                await self._log_operation_success(operation_type, provider_name, datetime.now() - start_time)

                return {
                    **result,
                    'provider_used': provider_name,
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'fallback_used': True,
                    'fallback_reason': f"Alla tidigare providers misslyckades: {[str(pa['error']) for pa in provider_attempts]}"
                }

            except Exception as e:
                provider_attempts.append({'provider': provider_name, 'error': str(e)})
                await self._update_provider_metrics(provider_name, 'error')

                logger.error(f"Fallback provider {provider_name} misslyckades: {e}")

        except Exception as e:
            logger.warning(f"Kunde inte hämta fallback provider: {e}")

        # Alla providers misslyckades
        error_messages = [pa['error'] for pa in provider_attempts]
        final_error = f"Alla providers misslyckades: {', '.join(error_messages)}"

        logger.error(f"Operation {operation_type.value} misslyckades på alla providers: {final_error}")
        raise CryptoError(final_error, "ALL_PROVIDERS_FAILED")

    @handle_errors(service_name="web3_provider_manager")
    async def search_token(self, query: str, chain: str = 'ethereum') -> Optional[TokenInfo]:
        """
        Sök token med provider fallback.

        Args:
            query: Token symbol, namn eller address
            chain: Blockchain att söka på

        Returns:
            TokenInfo om hittad
        """
        async def _search_operation(provider, **kwargs):
            if hasattr(provider, 'search_token'):
                return await provider.search_token(kwargs.get('query'))
            else:
                # Använd Google Cloud Web3 som fallback
                return await self.google_cloud_provider.search_token(kwargs.get('query'))

        result = await self.execute_with_fallback(
            _search_operation,
            OperationType.TOKEN_INFO,
            chain,
            query=query
        )

        return result.get('result') if result else None

    @handle_errors(service_name="web3_provider_manager")
    async def get_balance(self, wallet_address: str, token_address: str = None,
                         chain: str = 'ethereum') -> Dict[str, Any]:
        """
        Hämta balance med provider fallback.

        Args:
            wallet_address: Wallet address
            token_address: Token address (None för native)
            chain: Blockchain att använda

        Returns:
            Balance data
        """
        async def _balance_operation(provider, **kwargs):
            return await provider.get_balance(
                kwargs.get('wallet_address'),
                kwargs.get('token_address'),
                kwargs.get('chain')
            )

        result = await self.execute_with_fallback(
            _balance_operation,
            OperationType.BALANCE_CHECK,
            chain,
            wallet_address=wallet_address,
            token_address=token_address,
            chain=chain
        )

        return result

    @handle_errors(service_name="web3_provider_manager")
    async def get_cross_chain_balances(self, wallet_address: str,
                                     tokens: List[str] = None) -> Dict[str, Any]:
        """
        Hämta cross-chain balances med provider fallback.

        Args:
            wallet_address: Wallet address
            tokens: Lista med tokens att kontrollera

        Returns:
            Cross-chain balance data
        """
        async def _cross_chain_operation(provider, **kwargs):
            return await provider.get_cross_chain_balances(
                kwargs.get('wallet_address'),
                kwargs.get('tokens')
            )

        result = await self.execute_with_fallback(
            _cross_chain_operation,
            OperationType.BALANCE_CHECK,
            'ethereum',  # Default chain för cross-chain
            wallet_address=wallet_address,
            tokens=tokens
        )

        return result

    async def _get_available_providers(self, operation_type: OperationType, chain: str,
                                     priority_override: ProviderPriority = None) -> List[str]:
        """Hämta tillgängliga providers för operation."""
        available_providers = []

        for provider_name, config in self.provider_configs.items():
            if not config.enabled:
                continue

            if priority_override and config.priority != priority_override:
                continue

            # Kontrollera rate limiting
            if await self._is_rate_limited(provider_name):
                continue

            # Kontrollera health status
            if config.health_status == 'unhealthy':
                continue

            # Kontrollera chain support
            if not await self._supports_chain(provider_name, chain):
                continue

            available_providers.append(provider_name)

        return available_providers

    async def _sort_providers_by_performance(self, provider_names: List[str]) -> List[Tuple[str, float]]:
        """Sortera providers efter prestanda."""
        provider_scores = []

        for provider_name in provider_names:
            metrics = self.provider_metrics[provider_name]

            # Beräkna composite score
            success_rate = (metrics.successful_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0
            error_rate_score = (1 - metrics.error_rate) * 100
            response_time_score = max(0, 100 - metrics.average_response_time * 1000)  # Convert to ms, penalize slow providers

            # Prioritets bonus
            config = self.provider_configs[provider_name]
            priority_bonus = {'primary': 20, 'secondary': 10, 'fallback': 0}[config.priority.value]

            composite_score = (success_rate * 0.4 +
                             error_rate_score * 0.3 +
                             response_time_score * 0.2 +
                             priority_bonus)

            provider_scores.append((provider_name, composite_score))

        # Sortera efter score (högst först)
        provider_scores.sort(key=lambda x: x[1], reverse=True)
        return provider_scores

    async def _get_provider_instance(self, provider_name: str) -> Any:
        """Hämta provider instans."""
        if provider_name == 'google_cloud_web3':
            return self.google_cloud_provider
        else:
            # Simulerad externa provider
            # I produktion skulle detta initiera riktiga provider instanser
            return self._create_mock_provider(provider_name)

    def _create_mock_provider(self, provider_name: str) -> Any:
        """Skapa mock provider för externa providers."""
        class MockProvider:
            def __init__(self, name: str):
                self.name = name

            async def search_token(self, query: str):
                # Simulerad token search
                await asyncio.sleep(0.1)  # Simulate API call
                return None

            async def get_balance(self, wallet: str, token: str = None, chain: str = 'ethereum'):
                # Simulerad balance check
                await asyncio.sleep(0.1)
                return {
                    'balance': '1000000000000000000',
                    'balance_formatted': '1.0',
                    'symbol': 'ETH' if not token else 'UNKNOWN'
                }

            async def get_cross_chain_balances(self, wallet: str, tokens: List[str] = None):
                # Simulerad cross-chain balance
                await asyncio.sleep(0.2)
                return {
                    'wallet_address': wallet,
                    'cross_chain_balances': {
                        'ethereum': [{'balance': '1.0', 'symbol': 'ETH'}]
                    }
                }

        return MockProvider(provider_name)

    async def _update_provider_metrics(self, provider_name: str, status: str,
                                     response_time: float = None) -> None:
        """Uppdatera provider metrics."""
        metrics = self.provider_metrics[provider_name]

        if status == 'success':
            metrics.successful_requests += 1
            if response_time:
                metrics.average_response_time = (
                    (metrics.average_response_time * metrics.successful_requests + response_time) /
                    (metrics.successful_requests + 1)
                )
        elif status == 'error':
            metrics.failed_requests += 1
        elif status == 'selected':
            metrics.last_used = datetime.now()

        metrics.total_requests = metrics.successful_requests + metrics.failed_requests
        metrics.error_rate = (metrics.failed_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0

    async def _is_rate_limited(self, provider_name: str) -> bool:
        """Kontrollera om provider är rate limited."""
        config = self.provider_configs[provider_name]
        current_minute = datetime.now().strftime('%Y%m%d%H%M')

        cache_key = f"{provider_name}_{current_minute}"

        if cache_key not in self.rate_limit_cache:
            self.rate_limit_cache[cache_key] = 0

        return self.rate_limit_cache[cache_key] >= config.rate_limit

    async def _supports_chain(self, provider_name: str, chain: str) -> bool:
        """Kontrollera om provider stöder given chain."""
        # Alla providers stöder Ethereum som default
        if chain == 'ethereum':
            return True

        # Google Cloud Web3 stöder alla chains
        if provider_name == 'google_cloud_web3':
            return True

        # Externa providers har begränsat chain-stöd
        external_provider_chains = {
            'infura': ['ethereum', 'polygon'],
            'alchemy': ['ethereum', 'polygon', 'arbitrum'],
            'quicknode': ['ethereum', 'polygon', 'bsc']
        }

        return chain in external_provider_chains.get(provider_name, [])

    async def _log_operation_success(self, operation_type: OperationType,
                                   provider_name: str, execution_time: timedelta) -> None:
        """Logga lyckad operation."""
        operation_log = {
            'operation_type': operation_type.value,
            'provider_name': provider_name,
            'execution_time_seconds': execution_time.total_seconds(),
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }

        self.operation_history.append(operation_log)

        # Behåll bara senaste 1000 operationer
        if len(self.operation_history) > 1000:
            self.operation_history = self.operation_history[-1000:]

    async def update_provider_health(self, provider_name: str, status: str) -> None:
        """
        Uppdatera provider health status.

        Args:
            provider_name: Namn på provider
            status: Health status ('healthy', 'degraded', 'unhealthy')
        """
        if provider_name in self.provider_configs:
            config = self.provider_configs[provider_name]
            config.health_status = status
            config.last_health_check = datetime.now()

            logger.info(f"Provider {provider_name} health uppdaterad till: {status}")

    async def get_provider_dashboard(self) -> Dict[str, Any]:
        """Hämta provider dashboard."""
        try:
            dashboard_data = {
                'providers': {},
                'overall_status': 'healthy',
                'total_operations': sum(m.total_requests for m in self.provider_metrics.values()),
                'success_rate': 0.0,
                'average_response_time': 0.0,
                'timestamp': datetime.now().isoformat()
            }

            total_requests = 0
            total_successes = 0
            total_response_time = 0

            for provider_name, config in self.provider_configs.items():
                metrics = self.provider_metrics[provider_name]

                provider_info = {
                    'config': {
                        'priority': config.priority.value,
                        'enabled': config.enabled,
                        'rate_limit': config.rate_limit,
                        'timeout_seconds': config.timeout_seconds,
                        'health_status': config.health_status,
                        'last_health_check': config.last_health_check.isoformat() if config.last_health_check else None
                    },
                    'metrics': {
                        'total_requests': metrics.total_requests,
                        'successful_requests': metrics.successful_requests,
                        'failed_requests': metrics.failed_requests,
                        'error_rate': metrics.error_rate,
                        'average_response_time': metrics.average_response_time,
                        'last_used': metrics.last_used.isoformat() if metrics.last_used else None,
                        'uptime_percentage': metrics.uptime_percentage
                    }
                }

                dashboard_data['providers'][provider_name] = provider_info

                total_requests += metrics.total_requests
                total_successes += metrics.successful_requests
                total_response_time += metrics.average_response_time * metrics.total_requests

            # Beräkna overall metrics
            if total_requests > 0:
                dashboard_data['success_rate'] = (total_successes / total_requests) * 100
                dashboard_data['average_response_time'] = total_response_time / total_requests

            # Bestäm overall status
            unhealthy_providers = [p for p, c in self.provider_configs.items() if c.health_status == 'unhealthy']
            if len(unhealthy_providers) == len(self.provider_configs):
                dashboard_data['overall_status'] = 'unhealthy'
            elif unhealthy_providers:
                dashboard_data['overall_status'] = 'degraded'

            return dashboard_data

        except Exception as e:
            logger.error(f"Provider dashboard misslyckades: {e}")
            return {'error': str(e)}

    async def get_operation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Hämta operation history."""
        return self.operation_history[-limit:] if self.operation_history else []

    async def clear_old_history(self, older_than_days: int = 30) -> int:
        """Rensa gammal operation history."""
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
        original_count = len(self.operation_history)

        self.operation_history = [
            op for op in self.operation_history
            if datetime.fromisoformat(op['timestamp']) > cutoff_time
        ]

        cleared_count = original_count - len(self.operation_history)
        logger.info(f"Rensade {cleared_count} gamla operationer")
        return cleared_count

    async def enable_provider(self, provider_name: str) -> bool:
        """Aktivera provider."""
        if provider_name in self.provider_configs:
            self.provider_configs[provider_name].enabled = True
            logger.info(f"Provider {provider_name} aktiverad")
            return True
        return False

    async def disable_provider(self, provider_name: str) -> bool:
        """Inaktivera provider."""
        if provider_name in self.provider_configs:
            self.provider_configs[provider_name].enabled = False
            logger.info(f"Provider {provider_name} inaktiverad")
            return True
        return False

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på provider manager."""
        try:
            # Kontrollera Google Cloud provider
            google_cloud_health = await self.google_cloud_provider.health_check()

            # Kontrollera externa providers
            external_provider_health = {}
            for provider_name in ['infura', 'alchemy', 'quicknode']:
                try:
                    # Simulerad health check för externa providers
                    external_provider_health[provider_name] = 'healthy'
                except Exception as e:
                    external_provider_health[provider_name] = f'error: {str(e)}'

            # Sammanställ health status
            all_providers = {**{'google_cloud_web3': google_cloud_health['status']}, **external_provider_health}
            healthy_count = len([p for p in all_providers.values() if p == 'healthy'])
            total_count = len(all_providers)

            overall_status = 'healthy' if healthy_count == total_count else 'degraded' if healthy_count > 0 else 'unhealthy'

            return {
                'service': 'web3_provider_manager',
                'status': overall_status,
                'google_cloud_web3_health': google_cloud_health,
                'external_provider_health': external_provider_health,
                'total_providers': total_count,
                'healthy_providers': healthy_count,
                'supported_operations': [op.value for op in OperationType],
                'supported_chains': list(self.google_cloud_provider.CHAIN_MAPPINGS.keys()),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_provider_manager',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }