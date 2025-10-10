"""
Web3 Redis Cache - Redis cache-implementation för Web3-data.
Connection pooling, optimization och avancerade Redis-funktioner.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
import json
import pickle
import hashlib
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
try:
    from redis.asyncio.retry import Retry
    from redis.asyncio.backoff import ExponentialBackoff
except ImportError:
    # Fallback for older Redis versions
    class Retry:
        def __init__(self, backoff=None, retries=3):
            self.backoff = backoff
            self.retries = retries

    class ExponentialBackoff:
        pass

from ..core.errors.error_handling import handle_errors, CryptoError, CacheError, ValidationError

logger = logging.getLogger(__name__)

class RedisConnectionConfig:
    """Redis connection konfiguration."""
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0,
                 password: str = None, ssl: bool = False, connection_pool_size: int = 10,
                 socket_timeout: int = 10, socket_connect_timeout: int = 5,
                 retry_on_timeout: bool = True, max_connections: int = 20):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ssl = ssl
        self.connection_pool_size = connection_pool_size
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.max_connections = max_connections

class Web3RedisCache:
    """
    Redis cache-implementation för Web3-data.

    Funktioner:
    - Connection pooling och optimization
    - Cache key generation strategies
    - Redis cluster support
    - Pipeline operations
    - Pub/Sub för cache invalidation
    - Redis Lua scripting för atomic operations
    """

    def __init__(self, config: RedisConnectionConfig):
        """
        Initiera Web3 Redis Cache.

        Args:
            config: Redis connection konfiguration
        """
        self.config = config
        self.connection_pool = None
        self.redis_client = None
        self.pubsub_client = None

        # Cache prefixes för olika datatyper
        self.key_prefixes = {
            'token_info': 'web3:token:',
            'balance': 'web3:balance:',
            'cross_chain_balance': 'web3:crosschain:',
            'transaction_history': 'web3:tx:',
            'price_data': 'web3:price:',
            'analytics': 'web3:analytics:',
            'contract_data': 'web3:contract:'
        }

        # Connection health
        self.connection_health = {
            'connected': False,
            'last_ping': None,
            'connection_errors': 0,
            'total_operations': 0,
            'failed_operations': 0
        }

        # Pipeline cache
        self.pipelines = {}

        logger.info(f"Web3 Redis Cache initierad för {config.host}:{config.port}")

    async def connect(self) -> bool:
        """Anslut till Redis."""
        try:
            # Skapa connection pool
            self.connection_pool = ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=self.config.retry_on_timeout,
                max_connections=self.config.max_connections,
                retry=Retry(retries=3)
            )

            # Skapa Redis client
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)

            # Skapa Pub/Sub client
            self.pubsub_client = redis.Redis(connection_pool=self.connection_pool)

            # Testa connection
            await self.redis_client.ping()
            self.connection_health['connected'] = True
            self.connection_health['last_ping'] = datetime.now()

            logger.info(f"Ansluten till Redis: {self.config.host}:{self.config.port}")
            return True

        except Exception as e:
            logger.error(f"Redis connection misslyckades: {e}")
            self.connection_health['connection_errors'] += 1
            return False

    async def disconnect(self):
        """Koppla från Redis."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.pubsub_client:
                await self.pubsub_client.close()
            if self.connection_pool:
                await self.connection_pool.disconnect()

            self.connection_health['connected'] = False
            logger.info("Kopplat från Redis")
        except Exception as e:
            logger.error(f"Redis disconnect misslyckades: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på Redis connection."""
        try:
            if not self.redis_client:
                return {
                    'service': 'web3_redis_cache',
                    'status': 'error',
                    'error': 'Not connected',
                    'timestamp': datetime.now().isoformat()
                }

            start_time = datetime.now()
            ping_result = await self.redis_client.ping()
            ping_time = (datetime.now() - start_time).total_seconds()

            # Hämta Redis info
            info = await self.redis_client.info()

            return {
                'service': 'web3_redis_cache',
                'status': 'healthy' if ping_result else 'error',
                'ping_time_seconds': ping_time,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_mb': info.get('used_memory', 0) // (1024 * 1024),
                'total_connections_received': info.get('total_connections_received', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'connection_errors': self.connection_health['connection_errors'],
                'total_operations': self.connection_health['total_operations'],
                'failed_operations': self.connection_health['failed_operations'],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_redis_cache',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @handle_errors(service_name="web3_redis_cache")
    async def get(self, key: str, data_type: str = 'generic') -> Optional[Any]:
        """
        Hämta värde från Redis.

        Args:
            key: Cache key
            data_type: Typ av data för prefix

        Returns:
            Cache värde eller None
        """
        try:
            full_key = self._get_full_key(key, data_type)

            # Använd pipeline för flera operationer
            async with self.redis_client.pipeline(transaction=True) as pipe:
                pipe.get(full_key)
                pipe.ttl(full_key)
                results = await pipe.execute()

            value = results[0]
            ttl = results[1]

            if value is None:
                self.connection_health['total_operations'] += 1
                return None

            # Deserialisera baserat på data type
            deserialized_value = await self._deserialize_value(value, data_type)

            # Uppdatera access timestamp
            await self._update_access_time(full_key)

            self.connection_health['total_operations'] += 1
            logger.debug(f"Redis get: {full_key}")
            return deserialized_value

        except Exception as e:
            logger.error(f"Redis get misslyckades för {key}: {e}")
            self.connection_health['failed_operations'] += 1
            self.connection_health['total_operations'] += 1
            return None

    @handle_errors(service_name="web3_redis_cache")
    async def set(self, key: str, value: Any, ttl_seconds: int = 300,
                data_type: str = 'generic') -> bool:
        """
        Sätt värde i Redis.

        Args:
            key: Cache key
            value: Värde att cacha
            ttl_seconds: TTL i sekunder
            data_type: Typ av data för prefix

        Returns:
            True om lyckades
        """
        try:
            full_key = self._get_full_key(key, data_type)

            # Serialisera värde
            serialized_value = await self._serialize_value(value, data_type)

            # Använd pipeline för atomic operations
            async with self.redis_client.pipeline(transaction=True) as pipe:
                pipe.setex(full_key, ttl_seconds, serialized_value)
                pipe.set(f"{full_key}:access_time", datetime.now().isoformat())
                pipe.set(f"{full_key}:access_count", 1)
                await pipe.execute()

            self.connection_health['total_operations'] += 1
            logger.debug(f"Redis set: {full_key}")
            return True

        except Exception as e:
            logger.error(f"Redis set misslyckades för {key}: {e}")
            self.connection_health['failed_operations'] += 1
            self.connection_health['total_operations'] += 1
            return False

    def _get_full_key(self, key: str, data_type: str) -> str:
        """Skapa full Redis key med prefix."""
        prefix = self.key_prefixes.get(data_type, 'web3:generic:')
        return f"{prefix}{key}"

    async def _serialize_value(self, value: Any, data_type: str) -> str:
        """Serialisera värde baserat på data type."""
        if data_type in ['token_info', 'analytics', 'contract_data']:
            return json.dumps(value, default=str)
        else:
            return pickle.dumps(value).decode('latin1')

    async def _deserialize_value(self, value: str, data_type: str) -> Any:
        """Deserialisera värde baserat på data type."""
        if data_type in ['token_info', 'analytics', 'contract_data']:
            return json.loads(value)
        else:
            return pickle.loads(value.encode('latin1'))

    async def _update_access_time(self, full_key: str):
        """Uppdatera access timestamp och counter."""
        try:
            async with self.redis_client.pipeline(transaction=True) as pipe:
                pipe.incr(f"{full_key}:access_count")
                pipe.set(f"{full_key}:last_access", datetime.now().isoformat())
                await pipe.execute()
        except Exception as e:
            logger.warning(f"Access time update misslyckades för {full_key}: {e}")

    @handle_errors(service_name="web3_redis_cache")
    async def delete(self, key: str, data_type: str = 'generic') -> bool:
        """
        Ta bort värde från Redis.

        Args:
            key: Cache key
            data_type: Typ av data

        Returns:
            True om lyckades
        """
        try:
            full_key = self._get_full_key(key, data_type)

            # Ta bort key och metadata
            deleted_count = await self.redis_client.delete(
                full_key,
                f"{full_key}:access_time",
                f"{full_key}:access_count",
                f"{full_key}:last_access"
            )

            success = deleted_count > 0
            self.connection_health['total_operations'] += 1

            logger.debug(f"Redis delete: {full_key} -> {success}")
            return success

        except Exception as e:
            logger.error(f"Redis delete misslyckades för {key}: {e}")
            self.connection_health['failed_operations'] += 1
            self.connection_health['total_operations'] += 1
            return False

    @handle_errors(service_name="web3_redis_cache")
    async def batch_get(self, keys: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Hämta flera värden i batch.

        Args:
            keys: Lista med (key, data_type) tuples

        Returns:
            Dictionary med key -> value mapping
        """
        try:
            if not keys:
                return {}

            # Skapa full keys
            key_mapping = {}
            redis_keys = []

            for key, data_type in keys:
                full_key = self._get_full_key(key, data_type)
                redis_keys.append(full_key)
                key_mapping[full_key] = (key, data_type)

            # Batch get
            values = await self.redis_client.mget(redis_keys)

            # Process results
            results = {}
            for full_key, value in zip(redis_keys, values):
                if value is not None:
                    original_key, data_type = key_mapping[full_key]
                    deserialized_value = await self._deserialize_value(value, data_type)
                    results[original_key] = deserialized_value

            self.connection_health['total_operations'] += 1
            logger.debug(f"Redis batch get: {len(keys)} keys -> {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Redis batch get misslyckades: {e}")
            self.connection_health['failed_operations'] += 1
            self.connection_health['total_operations'] += 1
            return {}

    @handle_errors(service_name="web3_redis_cache")
    async def batch_set(self, key_values: List[Tuple[str, Any, str, int]]) -> int:
        """
        Sätt flera värden i batch.

        Args:
            key_values: Lista med (key, value, data_type, ttl) tuples

        Returns:
            Antal framgångsrikt satta värden
        """
        try:
            if not key_values:
                return 0

            # Förbered pipeline operations
            pipe = self.redis_client.pipeline(transaction=False)

            for key, value, data_type, ttl in key_values:
                full_key = self._get_full_key(key, data_type)
                serialized_value = await self._serialize_value(value, data_type)

                pipe.setex(full_key, ttl, serialized_value)
                pipe.set(f"{full_key}:access_time", datetime.now().isoformat())
                pipe.set(f"{full_key}:access_count", 1)

            # Kör pipeline
            results = await pipe.execute()
            success_count = len([r for r in results if r])

            self.connection_health['total_operations'] += 1
            logger.debug(f"Redis batch set: {len(key_values)} items -> {success_count} success")
            return success_count

        except Exception as e:
            logger.error(f"Redis batch set misslyckades: {e}")
            self.connection_health['failed_operations'] += 1
            self.connection_health['total_operations'] += 1
            return 0

    @handle_errors(service_name="web3_redis_cache")
    async def get_with_metadata(self, key: str, data_type: str = 'generic') -> Optional[Dict[str, Any]]:
        """
        Hämta värde med metadata.

        Args:
            key: Cache key
            data_type: Typ av data

        Returns:
            Dictionary med value och metadata eller None
        """
        try:
            full_key = self._get_full_key(key, data_type)

            # Hämta alla metadata
            metadata_keys = [f"{full_key}:access_time", f"{full_key}:access_count", f"{full_key}:last_access"]

            async with self.redis_client.pipeline(transaction=True) as pipe:
                pipe.get(full_key)
                pipe.ttl(full_key)
                pipe.mget(metadata_keys)
                results = await pipe.execute()

            value = results[0]
            ttl = results[1]
            metadata_values = results[2]

            if value is None:
                return None

            # Skapa metadata dict
            metadata = {
                'ttl': ttl,
                'access_time': metadata_values[0],
                'access_count': int(metadata_values[1]) if metadata_values[1] else 0,
                'last_access': metadata_values[2]
            }

            deserialized_value = await self._deserialize_value(value, data_type)

            result = {
                'value': deserialized_value,
                'metadata': metadata,
                'key': key,
                'data_type': data_type
            }

            self.connection_health['total_operations'] += 1
            logger.debug(f"Redis get with metadata: {full_key}")
            return result

        except Exception as e:
            logger.error(f"Redis get with metadata misslyckades för {key}: {e}")
            self.connection_health['failed_operations'] += 1
            self.connection_health['total_operations'] += 1
            return None

    @handle_errors(service_name="web3_redis_cache")
    async def increment_counter(self, key: str, amount: int = 1, data_type: str = 'generic') -> Optional[int]:
        """
        Inkrementera counter atomically.

        Args:
            key: Counter key
            amount: Belopp att inkrementera
            data_type: Typ av data

        Returns:
            Nytt värde eller None
        """
        try:
            full_key = self._get_full_key(key, data_type)

            # Använd Lua script för atomic increment
            lua_script = """
            local current = redis.call('get', KEYS[1]) or '0'
            local new_value = tonumber(current) + ARGV[1]
            redis.call('setex', KEYS[1], ARGV[2], tostring(new_value))
            return new_value
            """

            new_value = await self.redis_client.eval(
                lua_script, 1, full_key, amount, 3600  # Default TTL 1h
            )

            self.connection_health['total_operations'] += 1
            logger.debug(f"Redis counter increment: {full_key} -> {new_value}")
            return int(new_value)

        except Exception as e:
            logger.error(f"Redis counter increment misslyckades för {key}: {e}")
            self.connection_health['failed_operations'] += 1
            self.connection_health['total_operations'] += 1
            return None

    @handle_errors(service_name="web3_redis_cache")
    async def publish_cache_invalidation(self, channel: str, message: Dict[str, Any]):
        """
        Publicera cache invalidation message.

        Args:
            channel: Pub/Sub channel
            message: Message att publicera
        """
        try:
            if not self.pubsub_client:
                logger.warning("Pub/Sub client not available")
                return

            await self.pubsub_client.publish(
                f"cache_invalidation:{channel}",
                json.dumps(message, default=str)
            )

            logger.debug(f"Cache invalidation publicerad: {channel}")
        except Exception as e:
            logger.error(f"Cache invalidation publish misslyckades: {e}")

    async def subscribe_to_invalidation(self, channel: str, callback_func):
        """
        Prenumerera på cache invalidation messages.

        Args:
            channel: Channel att prenumerera på
            callback_func: Callback funktion för messages
        """
        try:
            if not self.pubsub_client:
                logger.warning("Pub/Sub client not available")
                return

            pubsub = self.pubsub_client.pubsub()
            await pubsub.subscribe(f"cache_invalidation:{channel}")

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await callback_func(data)
                    except Exception as e:
                        logger.error(f"Invalidation callback misslyckades: {e}")

        except Exception as e:
            logger.error(f"Cache invalidation subscription misslyckades: {e}")

    @handle_errors(service_name="web3_redis_cache")
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Hämta Redis cache statistik.

        Returns:
            Cache statistik
        """
        try:
            if not self.redis_client:
                return {'error': 'Not connected'}

            info = await self.redis_client.info()

            # Beräkna hit rate
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0

            stats = {
                'total_keys': sum(info.get(f'db{i}', {}).get('keys', 0) for i in range(16)),
                'used_memory_mb': info.get('used_memory', 0) // (1024 * 1024),
                'memory_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': hits,
                'keyspace_misses': misses,
                'hit_rate_percentage': hit_rate,
                'evicted_keys': info.get('evicted_keys', 0),
                'expired_keys': info.get('expired_keys', 0),
                'connection_health': self.connection_health,
                'key_prefixes': self.key_prefixes,
                'timestamp': datetime.now().isoformat()
            }

            return stats

        except Exception as e:
            logger.error(f"Redis stats misslyckades: {e}")
            return {'error': str(e)}

    async def flush_cache(self) -> bool:
        """
        Rensa all cache data.

        Returns:
            True om lyckades
        """
        try:
            result = await self.redis_client.flushdb()
            logger.warning("Redis cache flushed")
            return result
        except Exception as e:
            logger.error(f"Redis flush misslyckades: {e}")
            return False

    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Hämta memory usage information.

        Returns:
            Memory usage information
        """
        try:
            if not self.redis_client:
                return {'error': 'Not connected'}

            # Hämta memory info
            memory_info = await self.redis_client.info('memory')

            # Hämta key count per prefix
            prefix_stats = {}
            for prefix_name, prefix_value in self.key_prefixes.items():
                keys = await self.redis_client.keys(f"{prefix_value}*")
                prefix_stats[prefix_name] = len(keys)

            return {
                'used_memory_mb': memory_info.get('used_memory', 0) // (1024 * 1024),
                'peak_memory_mb': memory_info.get('used_memory_peak', 0) // (1024 * 1024),
                'memory_fragmentation_ratio': memory_info.get('mem_fragmentation_ratio', 0),
                'total_keys_by_prefix': prefix_stats,
                'lua_scripts_loaded': memory_info.get('number_of_cached_scripts', 0),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Memory usage check misslyckades: {e}")
            return {'error': str(e)}