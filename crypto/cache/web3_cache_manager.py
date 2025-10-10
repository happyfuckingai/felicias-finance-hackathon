"""
Web3 Cache Manager - Central cache-hanterare för alla Web3-data.
Intelligent cache invalidation och cross-chain cache synchronization.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

from ..core.errors.error_handling import handle_errors, CryptoError, CacheError, ValidationError
from .web3_cache import Web3Cache, CacheLevel, CacheType, CacheEntry

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache-strategier."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptiv strategi

class CacheInvalidationType(Enum):
    """Typer av cache invalidation."""
    EXPLICIT = "explicit"
    TIME_BASED = "time_based"
    DEPENDENCY_BASED = "dependency_based"
    CROSS_CHAIN = "cross_chain"

@dataclass
class CachePolicy:
    """Cache-policy för olika datatyper."""
    cache_type: CacheType
    strategy: CacheStrategy
    ttl_seconds: int
    max_size: int
    prefetch_enabled: bool = False
    cross_chain_sync: bool = False
    invalidation_rules: List[str] = field(default_factory=list)

@dataclass
class CacheDependency:
    """Cache-beroenden."""
    source_key: str
    dependent_keys: List[str]
    dependency_type: str
    last_updated: datetime = field(default_factory=datetime.now)

class Web3CacheManager:
    """
    Central cache-hanterare för Web3-data.

    Funktioner:
    - Intelligent cache invalidation
    - Cross-chain cache synchronization
    - Performance monitoring och optimization
    - Cache strategy management
    - Dependency tracking
    - Background cache warming
    """

    def __init__(self, redis_client=None, firestore_client=None):
        """
        Initiera Web3 Cache Manager.

        Args:
            redis_client: Redis client
            firestore_client: Firestore client
        """
        # Underliggande cache
        self.cache = Web3Cache(redis_client, firestore_client)

        # Cache policies
        self.policies = {}
        self._initialize_default_policies()

        # Cache dependencies
        self.dependencies = {}

        # Cache warming
        self.warming_tasks = {}
        self.prefetch_queue = asyncio.Queue()

        # Performance monitoring
        self.performance_metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'invalidation_count': 0,
            'prefetch_count': 0,
            'average_response_time': 0.0
        }

        # Background task management
        self.background_executor = ThreadPoolExecutor(max_workers=4)
        self.background_tasks = set()

        # Cache statistics per type
        self.cache_stats = {cache_type: {
            'hits': 0,
            'misses': 0,
            'prefetch_count': 0
        } for cache_type in CacheType}

        # Adaptive cache sizing
        self.adaptive_cache_size = {}
        self._initialize_adaptive_sizes()

        logger.info("Web3 Cache Manager initierad")

    def _initialize_default_policies(self):
        """Initiera default cache policies."""
        policies = [
            CachePolicy(
                cache_type=CacheType.TOKEN_INFO,
                strategy=CacheStrategy.ADAPTIVE,
                ttl_seconds=3600,
                max_size=10000,
                prefetch_enabled=True,
                cross_chain_sync=True
            ),
            CachePolicy(
                cache_type=CacheType.BALANCE,
                strategy=CacheStrategy.LRU,
                ttl_seconds=300,
                max_size=50000,
                prefetch_enabled=False
            ),
            CachePolicy(
                cache_type=CacheType.CROSS_CHAIN_BALANCE,
                strategy=CacheStrategy.TTL,
                ttl_seconds=180,
                max_size=10000,
                prefetch_enabled=False,
                cross_chain_sync=True
            ),
            CachePolicy(
                cache_type=CacheType.TRANSACTION_HISTORY,
                strategy=CacheStrategy.LFU,
                ttl_seconds=600,
                max_size=100000,
                prefetch_enabled=True
            ),
            CachePolicy(
                cache_type=CacheType.PRICE_DATA,
                strategy=CacheStrategy.TTL,
                ttl_seconds=60,
                max_size=1000,
                prefetch_enabled=True
            ),
            CachePolicy(
                cache_type=CacheType.ANALYTICS,
                strategy=CacheStrategy.ADAPTIVE,
                ttl_seconds=1800,
                max_size=5000,
                prefetch_enabled=False
            ),
            CachePolicy(
                cache_type=CacheType.CONTRACT_DATA,
                strategy=CacheStrategy.LRU,
                ttl_seconds=7200,
                max_size=20000,
                prefetch_enabled=True
            )
        ]

        for policy in policies:
            self.policies[policy.cache_type] = policy

    def _initialize_adaptive_sizes(self):
        """Initiera adaptive cache sizes."""
        base_size = 1000
        for cache_type in CacheType:
            self.adaptive_cache_size[cache_type] = {
                'current_size': base_size,
                'max_size': base_size * 2,
                'min_size': base_size // 2,
                'growth_factor': 1.2,
                'shrink_factor': 0.8
            }

    @handle_errors(service_name="web3_cache_manager")
    async def get(self, key: str, cache_type: CacheType) -> Optional[Any]:
        """
        Hämta värde från cache med intelligent strategi.

        Args:
            key: Cache key
            cache_type: Typ av cache data

        Returns:
            Cache värde eller None
        """
        start_time = datetime.now()

        try:
            # Kontrollera cache policy
            policy = self.policies.get(cache_type)
            if not policy:
                raise ValidationError(f"Ingen policy för cache type: {cache_type.value}",
                                    "CACHE_POLICY_NOT_FOUND")

            # Hämta från underliggande cache
            value = await self.cache.get(key, cache_type)

            # Uppdatera metrics
            response_time = (datetime.now() - start_time).total_seconds()
            await self._update_performance_metrics(cache_type, value is not None, response_time)

            # Trigger prefetch om miss och prefetch är aktiverat
            if value is None and policy.prefetch_enabled:
                await self._trigger_prefetch(key, cache_type)

            logger.debug(f"Cache get: {key} -> {'hit' if value is not None else 'miss'}")
            return value

        except Exception as e:
            logger.error(f"Cache manager get misslyckades för {key}: {e}")
            return None

    @handle_errors(service_name="web3_cache_manager")
    async def set(self, key: str, value: Any, cache_type: CacheType,
                ttl_seconds: int = None, dependencies: List[str] = None) -> bool:
        """
        Sätt värde i cache med intelligent strategi.

        Args:
            key: Cache key
            value: Värde att cacha
            cache_type: Typ av cache data
            ttl_seconds: TTL i sekunder
            dependencies: Beroende keys

        Returns:
            True om lyckades
        """
        try:
            # Kontrollera cache policy
            policy = self.policies.get(cache_type)
            if not policy:
                raise ValidationError(f"Ingen policy för cache type: {cache_type.value}",
                                    "CACHE_POLICY_NOT_FOUND")

            # Kontrollera storleksgräns
            if not await self._check_size_limits(cache_type):
                await self._evict_entries(cache_type)

            # Använd policy TTL om inte specificerad
            if ttl_seconds is None:
                ttl_seconds = policy.ttl_seconds

            # Sätt i underliggande cache
            success = await self.cache.set(key, value, cache_type, ttl_seconds)

            if success:
                # Registrera dependencies
                if dependencies:
                    await self._register_dependencies(key, dependencies)

                # Uppdatera adaptive size
                await self._update_adaptive_size(cache_type, 'increase')

                logger.debug(f"Cache set: {key}")

            return success

        except Exception as e:
            logger.error(f"Cache manager set misslyckades för {key}: {e}")
            return False

    async def _check_size_limits(self, cache_type: CacheType) -> bool:
        """Kontrollera om cache storlek är inom gränser."""
        adaptive_size = self.adaptive_cache_size[cache_type]['current_size']
        return adaptive_size > 0  # Enkel kontroll

    async def _evict_entries(self, cache_type: CacheType):
        """Evict cache entries baserat på strategi."""
        policy = self.policies[cache_type]

        if policy.strategy == CacheStrategy.LRU:
            await self._evict_lru(cache_type)
        elif policy.strategy == CacheStrategy.LFU:
            await self._evict_lfu(cache_type)
        elif policy.strategy == CacheStrategy.TTL:
            await self._evict_ttl(cache_type)
        elif policy.strategy == CacheStrategy.ADAPTIVE:
            await self._evict_adaptive(cache_type)

    async def _evict_lru(self, cache_type: CacheType):
        """Evict LRU entries."""
        # Enkel implementation - i produktion skulle detta använda mer sofistikerad logik
        logger.debug(f"LRU eviction för {cache_type.value}")

    async def _evict_lfu(self, cache_type: CacheType):
        """Evict LFU entries."""
        # Enkel implementation
        logger.debug(f"LFU eviction för {cache_type.value}")

    async def _evict_ttl(self, cache_type: CacheType):
        """Evict TTL entries."""
        # Enkel implementation
        logger.debug(f"TTL eviction för {cache_type.value}")

    async def _evict_adaptive(self, cache_type: CacheType):
        """Evict adaptive entries."""
        # Adaptiv eviction baserat på access patterns
        logger.debug(f"Adaptive eviction för {cache_type.value}")

    @handle_errors(service_name="web3_cache_manager")
    async def invalidate_by_dependency(self, source_key: str, invalidation_type: CacheInvalidationType = CacheInvalidationType.DEPENDENCY_BASED):
        """
        Invalidera cache baserat på dependencies.

        Args:
            source_key: Källa key som ändrats
            invalidation_type: Typ av invalidation
        """
        try:
            invalidated_keys = []

            # Hitta alla beroende keys
            for dependency_key, dependency in self.dependencies.items():
                if dependency.source_key == source_key:
                    for dependent_key in dependency.dependent_keys:
                        # Invalidera dependent key
                        policy = await self._get_policy_for_key(dependent_key)
                        if policy:
                            await self.cache.delete(dependent_key, policy.cache_type)
                            invalidated_keys.append(dependent_key)

            # Logga invalidation
            await self._log_cache_invalidation(source_key, invalidated_keys, invalidation_type)

            # Uppdatera metrics
            self.performance_metrics['invalidation_count'] += len(invalidated_keys)

            logger.info(f"Dependency-based invalidation: {source_key} -> {len(invalidated_keys)} keys")
            return len(invalidated_keys)

        except Exception as e:
            logger.error(f"Dependency invalidation misslyckades för {source_key}: {e}")
            return 0

    async def _get_policy_for_key(self, key: str) -> Optional[CachePolicy]:
        """Hämta policy för key."""
        # Enkel key-till-cache-type mapping
        for policy in self.policies.values():
            if f"{policy.cache_type.value}_" in key:
                return policy
        return None

    async def _register_dependencies(self, key: str, dependencies: List[str]):
        """Registrera cache dependencies."""
        dependency_id = hashlib.sha256(f"{key}_{'_'.join(dependencies)}".encode()).hexdigest()[:16]

        self.dependencies[dependency_id] = CacheDependency(
            source_key=key,
            dependent_keys=dependencies,
            dependency_type="manual"
        )

        logger.debug(f"Dependencies registrerade för {key}: {len(dependencies)} dependencies")

    @handle_errors(service_name="web3_cache_manager")
    async def invalidate_cross_chain(self, wallet_address: str, chain_from: str, chain_to: str = None):
        """
        Invalidera cross-chain cache data.

        Args:
            wallet_address: Wallet address
            chain_from: Källa chain
            chain_to: Mål chain (None för alla)
        """
        try:
            patterns = []

            if chain_to:
                patterns.extend([
                    f"balance_{wallet_address}_{chain_from}",
                    f"balance_{wallet_address}_{chain_to}",
                    f"cross_chain_{wallet_address}_{chain_from}_{chain_to}"
                ])
            else:
                patterns.extend([
                    f"balance_{wallet_address}_{chain_from}",
                    f"cross_chain_{wallet_address}_{chain_from}_"
                ])

            total_invalidated = 0
            for pattern in patterns:
                # Hitta policy för pattern
                policy = await self._find_policy_for_pattern(pattern)
                if policy:
                    invalidated = await self.cache.invalidate_by_pattern(pattern, policy.cache_type)
                    total_invalidated += invalidated

            # Logga cross-chain invalidation
            await self._log_cache_invalidation(
                f"cross_chain_{wallet_address}_{chain_from}_{chain_to}",
                [f"pattern_{p}" for p in patterns],
                CacheInvalidationType.CROSS_CHAIN
            )

            logger.info(f"Cross-chain invalidation: {wallet_address} {chain_from}->{chain_to}: {total_invalidated} entries")
            return total_invalidated

        except Exception as e:
            logger.error(f"Cross-chain invalidation misslyckades: {e}")
            return 0

    async def _find_policy_for_pattern(self, pattern: str) -> Optional[CachePolicy]:
        """Hitta policy för pattern."""
        for policy in self.policies.values():
            if f"{policy.cache_type.value}_" in pattern:
                return policy
        return None

    async def _log_cache_invalidation(self, source: str, targets: List[str], invalidation_type: CacheInvalidationType):
        """Logga cache invalidation."""
        logger.info(f"Cache invalidation - Source: {source}, Type: {invalidation_type.value}, Targets: {len(targets)}")

    @handle_errors(service_name="web3_cache_manager")
    async def prefetch_data(self, keys: List[Tuple[str, CacheType]], fetch_func: Callable):
        """
        Prefetch data för flera keys.

        Args:
            keys: Lista med (key, cache_type) tuples
            fetch_func: Funktion för att hämta data
        """
        try:
            prefetch_id = f"prefetch_{datetime.now().timestamp()}"
            self.warming_tasks[prefetch_id] = {
                'keys': keys,
                'start_time': datetime.now(),
                'status': 'running'
            }

            successful_prefetch = 0
            failed_prefetch = 0

            for key, cache_type in keys:
                try:
                    # Kontrollera om redan i cache
                    cached_value = await self.cache.get(key, cache_type)
                    if cached_value is not None:
                        continue

                    # Hämta data
                    value = await fetch_func(key)

                    if value is not None:
                        # Cache data
                        await self.cache.set(key, value, cache_type)
                        successful_prefetch += 1
                    else:
                        failed_prefetch += 1

                    # Vänta för att inte överbelasta
                    await asyncio.sleep(0.05)

                except Exception as e:
                    logger.warning(f"Prefetch misslyckades för {key}: {e}")
                    failed_prefetch += 1

            # Uppdatera task status
            self.warming_tasks[prefetch_id]['status'] = 'completed'
            self.warming_tasks[prefetch_id]['successful'] = successful_prefetch
            self.warming_tasks[prefetch_id]['failed'] = failed_prefetch
            self.warming_tasks[prefetch_id]['end_time'] = datetime.now()

            # Uppdatera metrics
            self.performance_metrics['prefetch_count'] += successful_prefetch

            logger.info(f"Prefetch completed: {successful_prefetch}/{len(keys)} successful")
            return successful_prefetch

        except Exception as e:
            logger.error(f"Prefetch misslyckades: {e}")
            return 0

    async def _trigger_prefetch(self, key: str, cache_type: CacheType):
        """Trigger prefetch för relaterade keys."""
        try:
            # Enkel prefetch - kan utökas med mer sofistikerad logik
            related_keys = await self._get_related_keys(key, cache_type)

            if related_keys:
                await self.prefetch_queue.put((related_keys, self._dummy_fetch_func))

            logger.debug(f"Prefetch triggered för {key}: {len(related_keys)} related keys")

        except Exception as e:
            logger.error(f"Prefetch trigger misslyckades för {key}: {e}")

    async def _get_related_keys(self, key: str, cache_type: CacheType) -> List[Tuple[str, CacheType]]:
        """Hämta relaterade keys för prefetch."""
        # Enkel implementation - kan utökas baserat på cache type
        related_keys = []

        if cache_type == CacheType.TOKEN_INFO:
            # För token info, prefetch relaterade tokens
            if 'ethereum_' in key:
                related_keys.append((key.replace('ethereum_', 'bsc_'), cache_type))
                related_keys.append((key.replace('ethereum_', 'polygon_'), cache_type))

        elif cache_type == CacheType.BALANCE:
            # För balance, prefetch cross-chain balance
            if 'ethereum_' in key:
                related_keys.append((key.replace('balance_', 'cross_chain_balance_'), CacheType.CROSS_CHAIN_BALANCE))

        return related_keys

    async def _dummy_fetch_func(self, key: str):
        """Dummy fetch function för prefetch."""
        # I produktion skulle detta vara en riktig fetch funktion
        return {"dummy": "data", "key": key}

    async def _update_performance_metrics(self, cache_type: CacheType, hit: bool, response_time: float):
        """Uppdatera performance metrics."""
        self.performance_metrics['total_requests'] += 1

        if hit:
            self.performance_metrics['cache_hits'] += 1
            self.cache_stats[cache_type]['hits'] += 1
        else:
            self.performance_metrics['cache_misses'] += 1
            self.cache_stats[cache_type]['misses'] += 1

        # Uppdatera genomsnittlig svarstid
        total_requests = self.performance_metrics['total_requests']
        current_avg = self.performance_metrics['average_response_time']
        self.performance_metrics['average_response_time'] = (current_avg * (total_requests - 1) + response_time) / total_requests

    async def _update_adaptive_size(self, cache_type: CacheType, operation: str):
        """Uppdatera adaptive cache size."""
        adaptive_info = self.adaptive_cache_size[cache_type]

        if operation == 'increase':
            new_size = min(adaptive_info['current_size'] * adaptive_info['growth_factor'],
                         adaptive_info['max_size'])
        elif operation == 'decrease':
            new_size = max(adaptive_info['current_size'] * adaptive_info['shrink_factor'],
                         adaptive_info['min_size'])
        else:
            return

        adaptive_info['current_size'] = int(new_size)

    async def get_cache_dashboard(self) -> Dict[str, Any]:
        """Hämta cache dashboard."""
        try:
            # Hämta underliggande cache stats
            cache_stats = await self.cache.get_cache_stats()

            # Beräkna hit rate
            total_requests = self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']
            hit_rate = (self.performance_metrics['cache_hits'] / total_requests * 100) if total_requests > 0 else 0

            # Cache efficiency per type
            efficiency_by_type = {}
            for cache_type, stats in self.cache_stats.items():
                type_requests = stats['hits'] + stats['misses']
                type_hit_rate = (stats['hits'] / type_requests * 100) if type_requests > 0 else 0
                efficiency_by_type[cache_type.value] = type_hit_rate

            dashboard = {
                **self.performance_metrics,
                'hit_rate_percentage': hit_rate,
                'cache_stats_by_type': efficiency_by_type,
                'policies': {
                    cache_type.value: {
                        'strategy': policy.strategy.value,
                        'ttl_seconds': policy.ttl_seconds,
                        'max_size': policy.max_size,
                        'prefetch_enabled': policy.prefetch_enabled,
                        'cross_chain_sync': policy.cross_chain_sync
                    }
                    for cache_type, policy in self.policies.items()
                },
                'adaptive_sizes': {
                    cache_type.value: info['current_size']
                    for cache_type, info in self.adaptive_cache_size.items()
                },
                'active_warming_tasks': len(self.warming_tasks),
                'dependency_count': len(self.dependencies),
                'supported_strategies': [s.value for s in CacheStrategy],
                'supported_invalidation_types': [it.value for it in CacheInvalidationType],
                'timestamp': datetime.now().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Cache dashboard misslyckades: {e}")
            return {'error': str(e)}

    async def set_cache_policy(self, cache_type: CacheType, policy: CachePolicy):
        """Sätt cache policy."""
        self.policies[cache_type] = policy
        logger.info(f"Cache policy uppdaterad för {cache_type.value}")

    async def cleanup_inactive_tasks(self):
        """Rensa inaktiva background tasks."""
        current_time = datetime.now()
        completed_tasks = []

        for task_id, task_info in self.warming_tasks.items():
            if task_info['status'] == 'completed':
                completed_tasks.append(task_id)

        for task_id in completed_tasks:
            del self.warming_tasks[task_id]

        logger.debug(f"Rensade {len(completed_tasks)} completed tasks")

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på cache manager."""
        try:
            cache_health = await self.cache.health_check()

            return {
                'service': 'web3_cache_manager',
                'status': 'healthy',
                'performance_metrics': self.performance_metrics,
                'policies_count': len(self.policies),
                'dependencies_count': len(self.dependencies),
                'warming_tasks_count': len(self.warming_tasks),
                'cache_service': cache_health,
                'supported_cache_types': [ct.value for ct in CacheType],
                'supported_strategies': [cs.value for cs in CacheStrategy],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_cache_manager',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }