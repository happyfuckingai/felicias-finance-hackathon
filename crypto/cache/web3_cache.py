"""
Web3 Cache - Multi-level cache (Redis + Firestore) för Web3 data.
Token balance och metadata caching med cache invalidation för cross-chain data.
"""
import asyncio
import logging
import pickle
import json
import hashlib
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict

from ..core.errors.error_handling import handle_errors, CryptoError, ValidationError

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache levels för multi-level caching."""
    MEMORY = "memory"
    REDIS = "redis"
    FIRESTORE = "firestore"

class CacheType(Enum):
    """Typer av cache data."""
    TOKEN_INFO = "token_info"
    BALANCE = "balance"
    CROSS_CHAIN_BALANCE = "cross_chain_balance"
    TRANSACTION_HISTORY = "transaction_history"
    PRICE_DATA = "price_data"
    ANALYTICS = "analytics"
    CONTRACT_DATA = "contract_data"

@dataclass
class CacheEntry:
    """Cache entry med metadata."""
    key: str
    value: Any
    cache_type: CacheType
    level: CacheLevel
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""

    def is_expired(self) -> bool:
        """Kontrollera om entry är utgången."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Konvertera till dictionary för serialisering."""
        return {
            'key': self.key,
            'value': self.value,
            'cache_type': self.cache_type.value,
            'level': self.level.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat(),
            'metadata': self.metadata,
            'checksum': self.checksum
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Skapa från dictionary."""
        return cls(
            key=data['key'],
            value=data['value'],
            cache_type=CacheType(data['cache_type']),
            level=CacheLevel(data['level']),
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
            access_count=data['access_count'],
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            metadata=data['metadata'],
            checksum=data['checksum']
        )

class CacheInvalidationEvent:
    """Cache invalidation event."""
    def __init__(self, cache_type: CacheType, pattern: str, reason: str):
        self.cache_type = cache_type
        self.pattern = pattern
        self.reason = reason
        self.timestamp = datetime.now()

class Web3Cache:
    """
    Multi-level cache för Web3 data med Redis och Firestore integration.

    Features:
    - Memory, Redis och Firestore cache levels
    - Token balance och metadata caching
    - Cache invalidation för cross-chain data
    - Integration med befintliga caching patterns
    - Automatic cache warming och prefetching
    - Cache analytics och performance monitoring
    """

    def __init__(self, redis_client=None, firestore_client=None):
        """
        Initiera Web3 Cache.

        Args:
            redis_client: Redis client (None för simulerad)
            firestore_client: Firestore client (None för simulerad)
        """
        self.memory_cache = {}  # Level 1: Memory
        self.redis_client = redis_client  # Level 2: Redis
        self.firestore_client = firestore_client  # Level 3: Firestore

        # Cache konfigurationer per typ
        self.cache_configs = {
            CacheType.TOKEN_INFO: {
                'ttl_seconds': 3600,  # 1 timme
                'levels': [CacheLevel.MEMORY, CacheLevel.REDIS, CacheLevel.FIRESTORE]
            },
            CacheType.BALANCE: {
                'ttl_seconds': 300,  # 5 minuter
                'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]
            },
            CacheType.CROSS_CHAIN_BALANCE: {
                'ttl_seconds': 180,  # 3 minuter
                'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]
            },
            CacheType.TRANSACTION_HISTORY: {
                'ttl_seconds': 600,  # 10 minuter
                'levels': [CacheLevel.MEMORY, CacheLevel.FIRESTORE]
            },
            CacheType.PRICE_DATA: {
                'ttl_seconds': 60,  # 1 minut
                'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]
            },
            CacheType.ANALYTICS: {
                'ttl_seconds': 1800,  # 30 minuter
                'levels': [CacheLevel.MEMORY, CacheLevel.FIRESTORE]
            },
            CacheType.CONTRACT_DATA: {
                'ttl_seconds': 7200,  # 2 timmar
                'levels': [CacheLevel.MEMORY, CacheLevel.FIRESTORE]
            }
        }

        # Cache invalidation subscribers
        self.invalidation_subscribers = defaultdict(set)

        # Cache warming tasks
        self.warming_tasks = set()

        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'evictions': 0,
            'writes': 0
        }

        logger.info("Web3 Cache initierad")

    @handle_errors(service_name="web3_cache")
    async def get(self, key: str, cache_type: CacheType) -> Optional[Any]:
        """
        Hämta värde från cache.

        Args:
            key: Cache key
            cache_type: Typ av cache data

        Returns:
            Cache värde eller None om inte hittat
        """
        try:
            # Kontrollera memory cache först
            memory_entry = self.memory_cache.get(key)
            if memory_entry and not memory_entry.is_expired():
                memory_entry.access_count += 1
                memory_entry.last_accessed = datetime.now()
                self.stats['hits'] += 1
                logger.debug(f"Cache hit (memory): {key}")
                return memory_entry.value

            # Kontrollera Redis cache
            if self.redis_client and cache_type in [CacheType.TOKEN_INFO, CacheType.BALANCE,
                                                   CacheType.CROSS_CHAIN_BALANCE, CacheType.PRICE_DATA]:
                redis_value = await self._get_from_redis(key)
                if redis_value:
                    # Uppdatera memory cache
                    await self._set_to_memory(key, redis_value, cache_type, CacheLevel.REDIS)
                    self.stats['hits'] += 1
                    logger.debug(f"Cache hit (Redis): {key}")
                    return redis_value

            # Kontrollera Firestore cache
            if self.firestore_client and cache_type in [CacheType.TOKEN_INFO, CacheType.TRANSACTION_HISTORY,
                                                      CacheType.ANALYTICS, CacheType.CONTRACT_DATA]:
                firestore_value = await self._get_from_firestore(key)
                if firestore_value:
                    # Uppdatera memory cache
                    await self._set_to_memory(key, firestore_value, cache_type, CacheLevel.FIRESTORE)
                    self.stats['hits'] += 1
                    logger.debug(f"Cache hit (Firestore): {key}")
                    return firestore_value

            self.stats['misses'] += 1
            logger.debug(f"Cache miss: {key}")
            return None

        except Exception as e:
            logger.error(f"Cache get misslyckades för {key}: {e}")
            self.stats['misses'] += 1
            return None

    @handle_errors(service_name="web3_cache")
    async def set(self, key: str, value: Any, cache_type: CacheType,
                ttl_seconds: int = None) -> bool:
        """
        Sätt värde i cache.

        Args:
            key: Cache key
            value: Värde att cacha
            cache_type: Typ av cache data
            ttl_seconds: TTL i sekunder (None för default)

        Returns:
            True om lyckades
        """
        try:
            if ttl_seconds is None:
                ttl_seconds = self.cache_configs[cache_type]['ttl_seconds']

            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

            # Skapa cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                cache_type=cache_type,
                level=CacheLevel.MEMORY,
                created_at=datetime.now(),
                expires_at=expires_at,
                checksum=self._calculate_checksum(str(value))
            )

            # Sätt i memory cache
            await self._set_to_memory(key, value, cache_type, CacheLevel.MEMORY)

            # Sätt i Redis om konfigurerat
            if (self.redis_client and
                CacheLevel.REDIS in self.cache_configs[cache_type]['levels']):
                await self._set_to_redis(key, value, ttl_seconds)

            # Sätt i Firestore om konfigurerat
            if (self.firestore_client and
                CacheLevel.FIRESTORE in self.cache_configs[cache_type]['levels']):
                await self._set_to_firestore(key, entry.to_dict(), ttl_seconds)

            self.stats['writes'] += 1
            logger.debug(f"Cache set: {key}")
            return True

        except Exception as e:
            logger.error(f"Cache set misslyckades för {key}: {e}")
            return False

    @handle_errors(service_name="web3_cache")
    async def delete(self, key: str, cache_type: CacheType) -> bool:
        """
        Ta bort värde från cache.

        Args:
            key: Cache key
            cache_type: Typ av cache data

        Returns:
            True om lyckades
        """
        try:
            deleted = False

            # Ta bort från memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted = True

            # Ta bort från Redis
            if self.redis_client:
                await self._delete_from_redis(key)
                deleted = True

            # Ta bort från Firestore
            if self.firestore_client:
                await self._delete_from_firestore(key)
                deleted = True

            if deleted:
                logger.debug(f"Cache delete: {key}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Cache delete misslyckades för {key}: {e}")
            return False

    @handle_errors(service_name="web3_cache")
    async def invalidate_by_pattern(self, pattern: str, cache_type: CacheType) -> int:
        """
        Invalidera cache entries som matchar pattern.

        Args:
            pattern: Pattern att matcha
            cache_type: Typ av cache data

        Returns:
            Antal invaliderade entries
        """
        try:
            invalidated_count = 0

            # Invalidera memory cache
            keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_remove:
                if self.memory_cache[key].cache_type == cache_type:
                    del self.memory_cache[key]
                    invalidated_count += 1

            # Invalidera Redis
            if self.redis_client:
                redis_keys = await self._get_redis_keys_by_pattern(pattern)
                for key in redis_keys:
                    await self._delete_from_redis(key)
                    invalidated_count += 1

            # Invalidera Firestore
            if self.firestore_client:
                firestore_keys = await self._get_firestore_keys_by_pattern(pattern, cache_type)
                for key in firestore_keys:
                    await self._delete_from_firestore(key)
                    invalidated_count += 1

            # Skicka invalidation event
            await self._notify_invalidation_subscribers(cache_type, pattern, f"Pattern: {pattern}")

            self.stats['invalidations'] += invalidated_count
            logger.info(f"Invaliderade {invalidated_count} cache entries för pattern: {pattern}")
            return invalidated_count

        except Exception as e:
            logger.error(f"Cache invalidation misslyckades för pattern {pattern}: {e}")
            return 0

    @handle_errors(service_name="web3_cache")
    async def invalidate_cross_chain_data(self, wallet_address: str, chain: str = None) -> int:
        """
        Invalidera cross-chain data för wallet.

        Args:
            wallet_address: Wallet address
            chain: Specifik chain att invalidera (None för alla)

        Returns:
            Antal invaliderade entries
        """
        try:
            patterns = []

            if chain:
                patterns.extend([
                    f"balance_{wallet_address}_{chain}",
                    f"cross_chain_{wallet_address}_{chain}",
                    f"tx_history_{wallet_address}_{chain}"
                ])
            else:
                patterns.extend([
                    f"balance_{wallet_address}_",
                    f"cross_chain_{wallet_address}_",
                    f"tx_history_{wallet_address}_"
                ])

            total_invalidated = 0
            for pattern in patterns:
                invalidated = await self.invalidate_by_pattern(pattern, CacheType.CROSS_CHAIN_BALANCE)
                total_invalidated += invalidated

            logger.info(f"Invaliderade {total_invalidated} cross-chain cache entries för {wallet_address}")
            return total_invalidated

        except Exception as e:
            logger.error(f"Cross-chain cache invalidation misslyckades för {wallet_address}: {e}")
            return 0

    @handle_errors(service_name="web3_cache")
    async def warm_cache(self, keys: List[Tuple[str, CacheType]], fetch_func) -> int:
        """
        Värm cache med prefetching.

        Args:
            keys: Lista med (key, cache_type) tuples
            fetch_func: Funktion för att hämta data

        Returns:
            Antal framgångsrikt varmade entries
        """
        try:
            warmed_count = 0
            task_id = f"warm_{datetime.now().timestamp()}"

            self.warming_tasks.add(task_id)

            for key, cache_type in keys:
                try:
                    # Kontrollera om redan i cache
                    cached_value = await self.get(key, cache_type)
                    if cached_value is not None:
                        continue

                    # Hämta data
                    value = await fetch_func(key)

                    if value is not None:
                        # Cache data
                        await self.set(key, value, cache_type)
                        warmed_count += 1

                        # Vänta lite för att inte överbelasta
                        await asyncio.sleep(0.1)

                except Exception as e:
                    logger.warning(f"Cache warming misslyckades för {key}: {e}")

            self.warming_tasks.discard(task_id)
            logger.info(f"Cache warming genomförd: {warmed_count}/{len(keys)} entries")
            return warmed_count

        except Exception as e:
            logger.error(f"Cache warming misslyckades: {e}")
            return 0

    @handle_errors(service_name="web3_cache")
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Hämta cache statistik.

        Returns:
            Cache statistik
        """
        try:
            # Beräkna memory cache storlek
            memory_size = len(self.memory_cache)

            # Redis storlek
            redis_size = 0
            if self.redis_client:
                try:
                    redis_size = await self.redis_client.dbsize()
                except Exception:
                    redis_size = 0

            # Firestore storlek (simulerad)
            firestore_size = 0
            if self.firestore_client:
                try:
                    firestore_size = 1000  # Simulerad storlek
                except Exception:
                    firestore_size = 0

            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

            # Cache efficiency per level
            efficiency_by_level = {
                'memory': 100.0,  # Memory är alltid snabbast
                'redis': 85.0,
                'firestore': 70.0
            }

            # Expiring entries
            expiring_soon = sum(1 for entry in self.memory_cache.values()
                              if entry.expires_at and entry.expires_at < datetime.now() + timedelta(minutes=5))

            return {
                'total_requests': total_requests,
                'cache_hits': self.stats['hits'],
                'cache_misses': self.stats['misses'],
                'hit_rate_percentage': hit_rate,
                'total_invalidations': self.stats['invalidations'],
                'total_evictions': self.stats['evictions'],
                'total_writes': self.stats['writes'],
                'cache_size_by_level': {
                    'memory': memory_size,
                    'redis': redis_size,
                    'firestore': firestore_size
                },
                'efficiency_by_level': efficiency_by_level,
                'entries_expiring_soon': expiring_soon,
                'warming_tasks_active': len(self.warming_tasks),
                'cache_types_config': {
                    ct.value: config for ct, config in self.cache_configs.items()
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Cache stats misslyckades: {e}")
            return {'error': str(e)}

    async def subscribe_to_invalidation(self, callback_func, cache_type: CacheType = None) -> str:
        """
        Prenumerera på cache invalidation events.

        Args:
            callback_func: Callback funktion för invalidation events
            cache_type: Specifik cache typ att prenumerera på

        Returns:
            Subscription ID
        """
        subscription_id = f"sub_{datetime.now().timestamp()}_{hash(callback_func)}"

        if cache_type:
            self.invalidation_subscribers[cache_type.value].add((subscription_id, callback_func))
        else:
            for ct in CacheType:
                self.invalidation_subscribers[ct.value].add((subscription_id, callback_func))

        logger.info(f"Cache invalidation subscription skapad: {subscription_id}")
        return subscription_id

    async def unsubscribe_from_invalidation(self, subscription_id: str) -> bool:
        """
        Avprenumerera från cache invalidation events.

        Args:
            subscription_id: Subscription ID att ta bort

        Returns:
            True om lyckades
        """
        removed = False
        for cache_type_subscribers in self.invalidation_subscribers.values():
            subscribers_to_remove = [s for s in cache_type_subscribers if s[0] == subscription_id]
            for subscriber in subscribers_to_remove:
                cache_type_subscribers.discard(subscriber)
                removed = True

        if removed:
            logger.info(f"Cache invalidation subscription borttagen: {subscription_id}")

        return removed

    async def _set_to_memory(self, key: str, value: Any, cache_type: CacheType, level: CacheLevel) -> None:
        """Sätt värde i memory cache."""
        ttl_seconds = self.cache_configs[cache_type]['ttl_seconds']
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        entry = CacheEntry(
            key=key,
            value=value,
            cache_type=cache_type,
            level=level,
            created_at=datetime.now(),
            expires_at=expires_at,
            checksum=self._calculate_checksum(str(value))
        )

        self.memory_cache[key] = entry

    async def _set_to_redis(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Sätt värde i Redis cache."""
        try:
            if self.redis_client:
                serialized_value = pickle.dumps(value)
                await self.redis_client.setex(key, ttl_seconds, serialized_value)
        except Exception as e:
            logger.error(f"Redis cache set misslyckades: {e}")

    async def _set_to_firestore(self, key: str, entry_dict: Dict[str, Any], ttl_seconds: int) -> None:
        """Sätt värde i Firestore cache."""
        try:
            if self.firestore_client:
                # Simulerad Firestore operation
                logger.debug(f"Firestore cache set simulerad för: {key}")
        except Exception as e:
            logger.error(f"Firestore cache set misslyckades: {e}")

    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Hämta värde från Redis cache."""
        try:
            if self.redis_client:
                serialized_value = await self.redis_client.get(key)
                if serialized_value:
                    return pickle.loads(serialized_value)
        except Exception as e:
            logger.error(f"Redis cache get misslyckades: {e}")
        return None

    async def _get_from_firestore(self, key: str) -> Optional[Any]:
        """Hämta värde från Firestore cache."""
        try:
            if self.firestore_client:
                # Simulerad Firestore operation
                logger.debug(f"Firestore cache get simulerad för: {key}")
                return None
        except Exception as e:
            logger.error(f"Firestore cache get misslyckades: {e}")
        return None

    async def _delete_from_redis(self, key: str) -> None:
        """Ta bort värde från Redis cache."""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis cache delete misslyckades: {e}")

    async def _delete_from_firestore(self, key: str) -> None:
        """Ta bort värde från Firestore cache."""
        try:
            if self.firestore_client:
                # Simulerad Firestore operation
                logger.debug(f"Firestore cache delete simulerad för: {key}")
        except Exception as e:
            logger.error(f"Firestore cache delete misslyckades: {e}")

    async def _get_redis_keys_by_pattern(self, pattern: str) -> List[str]:
        """Hämta Redis keys som matchar pattern."""
        try:
            if self.redis_client:
                # Simulerad pattern matchning
                return [k for k in self.memory_cache.keys() if pattern in k]
        except Exception as e:
            logger.error(f"Redis pattern match misslyckades: {e}")
        return []

    async def _get_firestore_keys_by_pattern(self, pattern: str, cache_type: CacheType) -> List[str]:
        """Hämta Firestore keys som matchar pattern."""
        try:
            if self.firestore_client:
                # Simulerad pattern matchning
                return [k for k in self.memory_cache.keys()
                       if pattern in k and self.memory_cache[k].cache_type == cache_type]
        except Exception as e:
            logger.error(f"Firestore pattern match misslyckades: {e}")
        return []

    async def _notify_invalidation_subscribers(self, cache_type: CacheType,
                                            pattern: str, reason: str) -> None:
        """Notifiera invalidation subscribers."""
        try:
            event = CacheInvalidationEvent(cache_type, pattern, reason)

            subscribers = self.invalidation_subscribers.get(cache_type.value, set())
            for subscription_id, callback in subscribers:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Invalidation callback misslyckades för {subscription_id}: {e}")

        except Exception as e:
            logger.error(f"Invalidation notification misslyckades: {e}")

    def _calculate_checksum(self, data: str) -> str:
        """Beräkna checksum för data integritet."""
        try:
            return hashlib.sha256(data.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Checksum beräkning misslyckades: {e}")
            return ""

    async def cleanup_expired_entries(self) -> int:
        """
        Rensa utgångna cache entries.

        Returns:
            Antal rensade entries
        """
        try:
            cleaned_count = 0

            # Rensa memory cache
            expired_keys = [k for k, v in self.memory_cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.memory_cache[key]
                cleaned_count += 1

            # Rensa Redis (simulerad)
            if self.redis_client:
                try:
                    # I produktion skulle detta vara en mer sofistikerad cleanup
                    logger.debug("Redis cache cleanup simulerad")
                except Exception as e:
                    logger.error(f"Redis cleanup misslyckades: {e}")

            self.stats['evictions'] += cleaned_count
            logger.info(f"Rensade {cleaned_count} utgångna cache entries")
            return cleaned_count

        except Exception as e:
            logger.error(f"Cache cleanup misslyckades: {e}")
            return 0

    async def clear_all_cache(self) -> bool:
        """
        Rensa all cache data.

        Returns:
            True om lyckades
        """
        try:
            # Rensa memory cache
            memory_count = len(self.memory_cache)
            self.memory_cache.clear()

            # Rensa Redis
            redis_count = 0
            if self.redis_client:
                try:
                    redis_count = await self.redis_client.dbsize()
                    await self.redis_client.flushdb()
                except Exception as e:
                    logger.error(f"Redis flush misslyckades: {e}")

            # Rensa Firestore
            firestore_count = 0
            if self.firestore_client:
                try:
                    firestore_count = 1000  # Simulerad storlek
                    logger.debug("Firestore cache clear simulerad")
                except Exception as e:
                    logger.error(f"Firestore clear misslyckades: {e}")

            # Återställ stats
            self.stats = {
                'hits': 0,
                'misses': 0,
                'invalidations': 0,
                'evictions': 0,
                'writes': 0
            }

            total_cleared = memory_count + redis_count + firestore_count
            logger.info(f"All cache rensad: {total_cleared} entries")
            return True

        except Exception as e:
            logger.error(f"Cache clear misslyckades: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Utför health check på cache service.

        Returns:
            Health status
        """
        try:
            # Kontrollera memory cache
            memory_entries = len(self.memory_cache)

            # Kontrollera Redis
            redis_status = 'healthy'
            redis_entries = 0
            if self.redis_client:
                try:
                    redis_entries = await self.redis_client.dbsize()
                except Exception as e:
                    redis_status = f'error: {str(e)}'
                    redis_entries = 0

            # Kontrollera Firestore
            firestore_status = 'healthy'
            firestore_entries = 0
            if self.firestore_client:
                try:
                    firestore_entries = 1000  # Simulerad storlek
                except Exception as e:
                    firestore_status = f'error: {str(e)}'
                    firestore_entries = 0

            # Beräkna overall health
            total_entries = memory_entries + redis_entries + firestore_entries
            health_components = [c for c in [redis_status, firestore_status] if c.startswith('error')]

            overall_status = 'healthy' if len(health_components) == 0 else 'degraded'

            return {
                'service': 'web3_cache',
                'status': overall_status,
                'memory_cache': {
                    'status': 'healthy',
                    'entries': memory_entries
                },
                'redis_cache': {
                    'status': redis_status,
                    'entries': redis_entries
                },
                'firestore_cache': {
                    'status': firestore_status,
                    'entries': firestore_entries
                },
                'total_entries': total_entries,
                'warming_tasks': len(self.warming_tasks),
                'cache_types': [ct.value for ct in CacheType],
                'supported_levels': [cl.value for cl in CacheLevel],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_cache',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_cache_dashboard(self) -> Dict[str, Any]:
        """
        Hämta cache dashboard.

        Returns:
            Cache dashboard data
        """
        try:
            stats = await self.get_cache_stats()

            # Cache distribution
            cache_distribution = {}
            for entry in self.memory_cache.values():
                cache_type = entry.cache_type.value
                if cache_type not in cache_distribution:
                    cache_distribution[cache_type] = 0
                cache_distribution[cache_type] += 1

            # Hit/miss rates per cache type
            hit_miss_by_type = {}
            for entry in self.memory_cache.values():
                cache_type = entry.cache_type.value
                if cache_type not in hit_miss_by_type:
                    hit_miss_by_type[cache_type] = {'hits': 0, 'misses': 0}

                if entry.access_count > 0:
                    hit_miss_by_type[cache_type]['hits'] += 1
                else:
                    hit_miss_by_type[cache_type]['misses'] += 1

            dashboard_data = {
                **stats,
                'cache_distribution': cache_distribution,
                'hit_miss_by_type': hit_miss_by_type,
                'invalidation_subscribers': {
                    cache_type: len(subscribers)
                    for cache_type, subscribers in self.invalidation_subscribers.items()
                },
                'config_summary': {
                    cache_type.value: config
                    for cache_type, config in self.cache_configs.items()
                }
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Cache dashboard misslyckades: {e}")
            return {'error': str(e)}