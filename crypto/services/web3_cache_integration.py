"""
Web3 Cache Integration - Integration av alla cache-komponenter.
Unified cache management och performance monitoring.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

from ..core.errors.error_handling import handle_errors, CryptoError, CacheError, ValidationError
from ..cache.web3_cache_manager import Web3CacheManager, CacheStrategy, CacheInvalidationType, CachePolicy, CacheType
from ..cache.web3_redis_cache import Web3RedisCache, RedisConnectionConfig

logger = logging.getLogger(__name__)

class CacheOperation(Enum):
    """Cache-operationer."""
    GET = "get"
    SET = "set"
    DELETE = "delete"
    INVALIDATE = "invalidate"
    PREFETCH = "prefetch"
    WARMUP = "warmup"

class CachePerformanceLevel(Enum):
    """Cache performance-nivåer."""
    EXCELLENT = "excellent"  # > 95% hit rate
    GOOD = "good"           # 80-95% hit rate
    FAIR = "fair"           # 60-80% hit rate
    POOR = "poor"           # < 60% hit rate

@dataclass
class CachePerformanceMetrics:
    """Cache performance metrics."""
    cache_type: CacheType
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    average_response_time: float = 0.0
    total_data_size: int = 0
    invalidation_count: int = 0
    prefetch_success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class CacheOptimizationRecommendation:
    """Cache optimization rekommendation."""
    recommendation_id: str
    cache_type: CacheType
    recommendation_type: str
    description: str
    potential_impact: str
    implementation_effort: str
    priority: str
    details: Dict[str, Any] = field(default_factory=dict)

class Web3CacheIntegration:
    """
    Integration av alla cache-komponenter.

    Funktioner:
    - Unified cache management
    - Performance monitoring
    - Cache strategy optimization
    - Cross-component cache coordination
    - Intelligent cache warming
    - Performance analytics
    """

    def __init__(self, redis_config: Optional[RedisConnectionConfig] = None):
        """
        Initiera Web3 Cache Integration.

        Args:
            redis_config: Redis connection konfiguration
        """
        # Initiera cache manager
        self.cache_manager = Web3CacheManager()

        # Redis cache för avancerade funktioner
        self.redis_cache = None
        if redis_config:
            self.redis_cache = Web3RedisCache(redis_config)
            asyncio.create_task(self.redis_cache.connect())

        # Performance metrics per cache type
        self.performance_metrics = {}
        self._initialize_performance_metrics()

        # Cache optimization rules
        self.optimization_rules = {}
        self._initialize_optimization_rules()

        # Active cache warming tasks
        self.warming_tasks = {}

        # Performance monitoring
        self.performance_history = []
        self.performance_history_max_size = 1000

        # Cache health monitoring
        self.health_check_interval = 300  # 5 minuter
        self.last_health_check = None

        logger.info("Web3 Cache Integration initierad")

    def _initialize_performance_metrics(self):
        """Initiera performance metrics."""
        for cache_type in CacheType:
            self.performance_metrics[cache_type] = CachePerformanceMetrics(
                cache_type=cache_type
            )

    def _initialize_optimization_rules(self):
        """Initiera cache optimization rules."""
        self.optimization_rules = {
            'low_hit_rate': {
                'threshold': 0.6,
                'recommendations': [
                    'Consider increasing cache TTL',
                    'Review cache key strategy',
                    'Implement cache warming for frequently accessed data'
                ]
            },
            'high_memory_usage': {
                'threshold_mb': 1000,
                'recommendations': [
                    'Implement cache size limits',
                    'Consider cache eviction policies',
                    'Review data serialization strategy'
                ]
            },
            'slow_response_time': {
                'threshold_ms': 100,
                'recommendations': [
                    'Consider using Redis for frequently accessed data',
                    'Implement connection pooling',
                    'Review cache key distribution'
                ]
            }
        }

    @handle_errors(service_name="web3_cache_integration")
    async def get(self, key: str, cache_type: CacheType, use_redis: bool = True) -> Optional[Any]:
        """
        Hämta värde från cache med intelligent routing.

        Args:
            key: Cache key
            cache_type: Typ av cache data
            use_redis: Använd Redis om tillgänglig

        Returns:
            Cache värde eller None
        """
        start_time = datetime.now()

        try:
            # Kontrollera Redis först om aktiverat
            if use_redis and self.redis_cache:
                try:
                    redis_value = await self.redis_cache.get(key, cache_type.value)
                    if redis_value is not None:
                        # Uppdatera metrics
                        await self._update_performance_metrics(cache_type, True,
                                                             (datetime.now() - start_time).total_seconds())
                        logger.debug(f"Redis cache hit: {key}")
                        return redis_value
                except Exception as e:
                    logger.warning(f"Redis cache misslyckades för {key}: {e}")

            # Fallback till cache manager
            value = await self.cache_manager.get(key, cache_type)

            # Uppdatera metrics
            response_time = (datetime.now() - start_time).total_seconds()
            await self._update_performance_metrics(cache_type, value is not None, response_time)

            logger.debug(f"Cache get: {key} -> {'hit' if value is not None else 'miss'}")
            return value

        except Exception as e:
            logger.error(f"Cache integration get misslyckades för {key}: {e}")
            return None

    @handle_errors(service_name="web3_cache_integration")
    async def set(self, key: str, value: Any, cache_type: CacheType, ttl_seconds: int = None,
                use_redis: bool = True, dependencies: List[str] = None) -> bool:
        """
        Sätt värde i cache med intelligent routing.

        Args:
            key: Cache key
            value: Värde att cacha
            cache_type: Typ av cache data
            ttl_seconds: TTL i sekunder
            use_redis: Använd Redis om tillgänglig
            dependencies: Beroende keys

        Returns:
            True om lyckades
        """
        try:
            success_count = 0

            # Sätt i Redis om aktiverat
            if use_redis and self.redis_cache:
                try:
                    redis_success = await self.redis_cache.set(key, value, ttl_seconds or 300, cache_type.value)
                    if redis_success:
                        success_count += 1
                except Exception as e:
                    logger.warning(f"Redis cache set misslyckades för {key}: {e}")

            # Sätt i cache manager
            manager_success = await self.cache_manager.set(key, value, cache_type, ttl_seconds, dependencies)
            if manager_success:
                success_count += 1

            success = success_count > 0
            logger.debug(f"Cache set: {key} -> {success}")
            return success

        except Exception as e:
            logger.error(f"Cache integration set misslyckades för {key}: {e}")
            return False

    async def _update_performance_metrics(self, cache_type: CacheType, hit: bool, response_time: float):
        """Uppdatera performance metrics."""
        metrics = self.performance_metrics[cache_type]

        metrics.total_requests += 1
        if hit:
            metrics.cache_hits += 1
        else:
            metrics.cache_misses += 1

        # Uppdatera hit rate
        metrics.hit_rate = metrics.cache_hits / metrics.total_requests if metrics.total_requests > 0 else 0.0

        # Uppdatera genomsnittlig svarstid
        metrics.average_response_time = (
            (metrics.average_response_time * (metrics.total_requests - 1) + response_time) / metrics.total_requests
        )

        metrics.last_updated = datetime.now()

    @handle_errors(service_name="web3_cache_integration")
    async def invalidate_by_type(self, cache_type: CacheType, pattern: str = "*") -> int:
        """
        Invalidera cache per typ.

        Args:
            cache_type: Typ av cache att invalidera
            pattern: Pattern för keys att invalidera

        Returns:
            Antal invaliderade entries
        """
        try:
            # Invalidera i cache manager
            manager_invalidated = await self.cache_manager.cache.invalidate_by_pattern(pattern, cache_type)

            # Invalidera i Redis om aktiverat
            redis_invalidated = 0
            if self.redis_cache:
                try:
                    # Hitta keys som matchar pattern i Redis
                    redis_keys = []
                    for prefix in self.redis_cache.key_prefixes.values():
                        keys = await self.redis_cache.redis_client.keys(f"{prefix}{pattern}")
                        redis_keys.extend(keys)

                    # Ta bort keys
                    if redis_keys:
                        redis_invalidated = await self.redis_cache.redis_client.delete(*redis_keys)

                except Exception as e:
                    logger.warning(f"Redis invalidation misslyckades: {e}")

            total_invalidated = manager_invalidated + redis_invalidated

            # Uppdatera metrics
            metrics = self.performance_metrics[cache_type]
            metrics.invalidation_count += total_invalidated

            logger.info(f"Cache invalidation: {cache_type.value} -> {total_invalidated} entries")
            return total_invalidated

        except Exception as e:
            logger.error(f"Cache invalidation misslyckades för {cache_type.value}: {e}")
            return 0

    @handle_errors(service_name="web3_cache_integration")
    async def prefetch_data(self, keys: List[Tuple[str, CacheType]], fetch_func: Callable,
                          use_redis: bool = True) -> Dict[str, Any]:
        """
        Prefetch data för flera keys.

        Args:
            keys: Lista med (key, cache_type) tuples
            fetch_func: Funktion för att hämta data
            use_redis: Använd Redis för prefetch

        Returns:
            Prefetch resultat
        """
        try:
            prefetch_id = f"prefetch_{datetime.now().timestamp()}"

            self.warming_tasks[prefetch_id] = {
                'keys': keys,
                'start_time': datetime.now(),
                'status': 'running',
                'results': {}
            }

            successful_prefetch = 0
            failed_prefetch = 0
            errors = []

            for key, cache_type in keys:
                try:
                    # Kontrollera om redan i cache
                    cached_value = await self.get(key, cache_type, use_redis)
                    if cached_value is not None:
                        self.warming_tasks[prefetch_id]['results'][key] = {'status': 'already_cached'}
                        continue

                    # Hämta data
                    value = await fetch_func(key)

                    if value is not None:
                        # Cache data
                        success = await self.set(key, value, cache_type, use_redis=use_redis)
                        if success:
                            successful_prefetch += 1
                            self.warming_tasks[prefetch_id]['results'][key] = {'status': 'success'}
                        else:
                            failed_prefetch += 1
                            self.warming_tasks[prefetch_id]['results'][key] = {'status': 'cache_failed'}
                    else:
                        failed_prefetch += 1
                        self.warming_tasks[prefetch_id]['results'][key] = {'status': 'fetch_failed'}

                    # Vänta för att inte överbelasta
                    await asyncio.sleep(0.01)

                except Exception as e:
                    logger.warning(f"Prefetch misslyckades för {key}: {e}")
                    failed_prefetch += 1
                    errors.append(str(e))
                    self.warming_tasks[prefetch_id]['results'][key] = {'status': 'error', 'error': str(e)}

            # Uppdatera task status
            self.warming_tasks[prefetch_id]['status'] = 'completed'
            self.warming_tasks[prefetch_id]['successful'] = successful_prefetch
            self.warming_tasks[prefetch_id]['failed'] = failed_prefetch
            self.warming_tasks[prefetch_id]['end_time'] = datetime.now()

            result = {
                'prefetch_id': prefetch_id,
                'successful': successful_prefetch,
                'failed': failed_prefetch,
                'total': len(keys),
                'success_rate': successful_prefetch / len(keys) if keys else 0,
                'errors': errors[:10],  # Begränsa error log
                'duration_seconds': (datetime.now() - self.warming_tasks[prefetch_id]['start_time']).total_seconds()
            }

            logger.info(f"Prefetch completed: {successful_prefetch}/{len(keys)} successful")
            return result

        except Exception as e:
            logger.error(f"Prefetch misslyckades: {e}")
            return {
                'prefetch_id': f"prefetch_{datetime.now().timestamp()}",
                'successful': 0,
                'failed': len(keys) if 'keys' in locals() else 0,
                'total': 0,
                'success_rate': 0,
                'errors': [str(e)],
                'error': str(e)
            }

    @handle_errors(service_name="web3_cache_integration")
    async def optimize_cache_strategy(self, cache_type: CacheType) -> List[CacheOptimizationRecommendation]:
        """
        Optimera cache-strategi baserat på performance data.

        Args:
            cache_type: Typ av cache att optimera

        Returns:
            Lista med optimization rekommendationer
        """
        try:
            metrics = self.performance_metrics[cache_type]
            recommendations = []

            # Analysera hit rate
            if metrics.hit_rate < self.optimization_rules['low_hit_rate']['threshold']:
                recommendation = CacheOptimizationRecommendation(
                    recommendation_id=f"opt_{cache_type.value}_hit_rate_{datetime.now().timestamp()}",
                    cache_type=cache_type,
                    recommendation_type='cache_strategy',
                    description=f"Low hit rate detected: {metrics.hit_rate:.2%}",
                    potential_impact='high',
                    implementation_effort='medium',
                    priority='high',
                    details={
                        'current_hit_rate': metrics.hit_rate,
                        'recommended_actions': self.optimization_rules['low_hit_rate']['recommendations'],
                        'suggested_ttl_increase': '50%',
                        'suggested_strategy_change': 'Consider switching to ADAPTIVE strategy'
                    }
                )
                recommendations.append(recommendation)

            # Analysera svarstid
            if metrics.average_response_time > self.optimization_rules['slow_response_time']['threshold_ms'] / 1000:
                recommendation = CacheOptimizationRecommendation(
                    recommendation_id=f"opt_{cache_type.value}_response_time_{datetime.now().timestamp()}",
                    cache_type=cache_type,
                    recommendation_type='performance',
                    description=f"Slow response time detected: {metrics.average_response_time:.3f}s",
                    potential_impact='medium',
                    implementation_effort='low',
                    priority='medium',
                    details={
                        'current_response_time': metrics.average_response_time,
                        'recommended_actions': self.optimization_rules['slow_response_time']['recommendations'],
                        'suggested_redis_usage': True,
                        'suggested_connection_pool_size': 20
                    }
                )
                recommendations.append(recommendation)

            # Generera generiska rekommendationer
            if not recommendations:
                recommendation = CacheOptimizationRecommendation(
                    recommendation_id=f"opt_{cache_type.value}_general_{datetime.now().timestamp()}",
                    cache_type=cache_type,
                    recommendation_type='monitoring',
                    description="General cache performance monitoring",
                    potential_impact='low',
                    implementation_effort='low',
                    priority='low',
                    details={
                        'current_metrics': {
                            'hit_rate': metrics.hit_rate,
                            'response_time': metrics.average_response_time,
                            'total_requests': metrics.total_requests
                        },
                        'recommended_actions': [
                            'Monitor cache performance over time',
                            'Consider implementing cache warming for critical data',
                            'Review cache key naming strategy'
                        ]
                    }
                )
                recommendations.append(recommendation)

            logger.info(f"Cache optimization analysis för {cache_type.value}: {len(recommendations)} recommendations")
            return recommendations

        except Exception as e:
            logger.error(f"Cache optimization analysis misslyckades för {cache_type.value}: {e}")
            return []

    @handle_errors(service_name="web3_cache_integration")
    async def get_unified_cache_dashboard(self) -> Dict[str, Any]:
        """Hämta unified cache dashboard."""
        try:
            # Hämta cache manager dashboard
            manager_dashboard = await self.cache_manager.get_cache_dashboard()

            # Hämta Redis stats om aktiverat
            redis_stats = {}
            if self.redis_cache:
                try:
                    redis_stats = await self.redis_cache.get_cache_stats()
                except Exception as e:
                    redis_stats = {'error': str(e)}

            # Beräkna overall performance
            total_requests = sum(m.total_requests for m in self.performance_metrics.values())
            total_hits = sum(m.cache_hits for m in self.performance_metrics.values())
            overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0

            # Performance level
            if overall_hit_rate > 0.95:
                performance_level = CachePerformanceLevel.EXCELLENT
            elif overall_hit_rate > 0.8:
                performance_level = CachePerformanceLevel.GOOD
            elif overall_hit_rate > 0.6:
                performance_level = CachePerformanceLevel.FAIR
            else:
                performance_level = CachePerformanceLevel.POOR

            # Cache type performance
            cache_type_performance = {}
            for cache_type, metrics in self.performance_metrics.items():
                cache_type_performance[cache_type.value] = {
                    'hit_rate': metrics.hit_rate,
                    'response_time': metrics.average_response_time,
                    'total_requests': metrics.total_requests,
                    'performance_level': (
                        'excellent' if metrics.hit_rate > 0.95 else
                        'good' if metrics.hit_rate > 0.8 else
                        'fair' if metrics.hit_rate > 0.6 else 'poor'
                    )
                }

            # Aktiva warming tasks
            active_warming_tasks = {
                task_id: task_info for task_id, task_info in self.warming_tasks.items()
                if task_info['status'] == 'running'
            }

            dashboard = {
                'overall_performance': {
                    'hit_rate': overall_hit_rate,
                    'performance_level': performance_level.value,
                    'total_requests': total_requests,
                    'total_hits': total_hits,
                    'total_misses': total_requests - total_hits
                },
                'cache_type_performance': cache_type_performance,
                'cache_manager_dashboard': manager_dashboard,
                'redis_cache_stats': redis_stats,
                'active_warming_tasks': len(active_warming_tasks),
                'warming_tasks': {
                    task_id: {
                        'keys_count': len(task_info['keys']),
                        'start_time': task_info['start_time'].isoformat(),
                        'status': task_info['status']
                    }
                    for task_id, task_info in list(self.warming_tasks.items())[-10:]  # Senaste 10 tasks
                },
                'supported_cache_types': [ct.value for ct in CacheType],
                'supported_strategies': [cs.value for cs in CacheStrategy],
                'optimization_rules': self.optimization_rules,
                'timestamp': datetime.now().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Unified cache dashboard misslyckades: {e}")
            return {'error': str(e)}

    async def get_cache_analytics(self) -> Dict[str, Any]:
        """Hämta detaljerad cache analytics."""
        try:
            analytics = {
                'performance_trends': await self._calculate_performance_trends(),
                'optimization_recommendations': await self._get_all_optimization_recommendations(),
                'cache_efficiency_analysis': await self._analyze_cache_efficiency(),
                'resource_utilization': await self._analyze_resource_utilization(),
                'recommendations_summary': await self._generate_recommendations_summary()
            }

            return analytics

        except Exception as e:
            logger.error(f"Cache analytics misslyckades: {e}")
            return {'error': str(e)}

    async def _calculate_performance_trends(self) -> Dict[str, Any]:
        """Beräkna performance trender."""
        # Enkel trendanalys
        trends = {
            'improving_types': [],
            'declining_types': [],
            'stable_types': []
        }

        for cache_type, metrics in self.performance_metrics.items():
            if metrics.total_requests > 100:  # Tillräckligt med data
                if metrics.hit_rate > 0.8:
                    trends['improving_types'].append(cache_type.value)
                elif metrics.hit_rate < 0.4:
                    trends['declining_types'].append(cache_type.value)
                else:
                    trends['stable_types'].append(cache_type.value)

        return trends

    async def _get_all_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Hämta optimization rekommendationer för alla cache types."""
        all_recommendations = []

        for cache_type in CacheType:
            recommendations = await self.optimize_cache_strategy(cache_type)
            all_recommendations.extend([{
                'cache_type': r.cache_type.value,
                'recommendation_id': r.recommendation_id,
                'recommendation_type': r.recommendation_type,
                'description': r.description,
                'priority': r.priority,
                'potential_impact': r.potential_impact
            } for r in recommendations])

        return sorted(all_recommendations, key=lambda x: x['priority'], reverse=True)

    async def _analyze_cache_efficiency(self) -> Dict[str, Any]:
        """Analysera cache efficiency."""
        efficiency = {
            'overall_efficiency': 0.0,
            'type_efficiency': {},
            'bottlenecks': [],
            'optimization_opportunities': []
        }

        total_weighted_hit_rate = 0
        total_requests = 0

        for cache_type, metrics in self.performance_metrics.items():
            if metrics.total_requests > 0:
                efficiency['type_efficiency'][cache_type.value] = {
                    'hit_rate': metrics.hit_rate,
                    'efficiency_score': metrics.hit_rate * (metrics.total_requests / sum(m.total_requests for m in self.performance_metrics.values()))
                }
                total_weighted_hit_rate += metrics.hit_rate * metrics.total_requests
                total_requests += metrics.total_requests

        efficiency['overall_efficiency'] = total_weighted_hit_rate / total_requests if total_requests > 0 else 0

        return efficiency

    async def _analyze_resource_utilization(self) -> Dict[str, Any]:
        """Analysera resource utilization."""
        utilization = {
            'memory_usage_mb': 0,
            'connection_count': 0,
            'operation_throughput': 0,
            'utilization_trends': {}
        }

        # Enkel resource analys
        if self.redis_cache:
            try:
                memory_info = await self.redis_cache.get_memory_usage()
                utilization['memory_usage_mb'] = memory_info.get('used_memory_mb', 0)
            except Exception as e:
                logger.warning(f"Memory usage analys misslyckades: {e}")

        # Beräkna throughput
        total_requests = sum(m.total_requests for m in self.performance_metrics.values())
        time_span = (datetime.now() - min((m.last_updated for m in self.performance_metrics.values() if m.total_requests > 0), default=datetime.now())).total_seconds()
        utilization['operation_throughput'] = total_requests / max(time_span, 1)

        return utilization

    async def _generate_recommendations_summary(self) -> Dict[str, Any]:
        """Generera recommendations summary."""
        recommendations = await self._get_all_optimization_recommendations()

        summary = {
            'total_recommendations': len(recommendations),
            'high_priority': len([r for r in recommendations if r['priority'] == 'high']),
            'medium_priority': len([r for r in recommendations if r['priority'] == 'medium']),
            'low_priority': len([r for r in recommendations if r['priority'] == 'low']),
            'top_recommendations': recommendations[:5]  # Top 5
        }

        return summary

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på cache integration."""
        try:
            cache_manager_health = await self.cache_manager.health_check()

            redis_health = {'status': 'not_configured'}
            if self.redis_cache:
                redis_health = await self.redis_cache.health_check()

            # Kontrollera performance
            total_requests = sum(m.total_requests for m in self.performance_metrics.values())
            overall_status = 'healthy'

            if total_requests > 0:
                overall_hit_rate = sum(m.cache_hits for m in self.performance_metrics.values()) / total_requests
                if overall_hit_rate < 0.5:
                    overall_status = 'warning'

            return {
                'service': 'web3_cache_integration',
                'status': overall_status,
                'cache_manager': cache_manager_health.get('status', 'unknown'),
                'redis_cache': redis_health.get('status', 'unknown'),
                'total_requests': total_requests,
                'overall_hit_rate': sum(m.cache_hits for m in self.performance_metrics.values()) / total_requests if total_requests > 0 else 0,
                'active_warming_tasks': len(self.warming_tasks),
                'supported_cache_types': [ct.value for ct in CacheType],
                'supported_strategies': [cs.value for cs in CacheStrategy],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_cache_integration',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }