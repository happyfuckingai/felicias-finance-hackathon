"""
Dynamic Token Resolver - Huvudkomponent för dynamisk token-upplösning.
Kombinerar caching, providers och fallback-system för robust token resolution.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from .token_cache import TokenCache
from .token_providers import (
    TokenProvider, TokenInfo, DexScreenerProvider,
    OneInchProvider, CoinGeckoProvider, FallbackTokenProvider
)

logger = logging.getLogger(__name__)

class TokenNotFoundError(Exception):
    """Exception när token inte hittas."""
    pass

class DynamicTokenResolver:
    """
    Huvudklass för dynamisk token resolution med cache och flera providers.

    Features:
    - Multi-provider support (DexScreener, 1inch, CoinGecko, Fallback)
    - Intelligent caching för prestanda
    - Fallback-system för hög tillförlitlighet
    - Async support för skalbarhet
    - Chain-agnostic design
    """

    def __init__(self, cache_duration: int = 3600, max_concurrent_requests: int = 3):
        """
        Initiera DynamicTokenResolver.

        Args:
            cache_duration: Cache-varaktighet i sekunder (default 1 timme)
            max_concurrent_requests: Max antal samtidiga API-requests
        """
        self.cache = TokenCache(cache_duration=cache_duration)
        self.max_concurrent = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

        # Initiera providers
        self.providers = [
            DexScreenerProvider(),
            OneInchProvider(),
            CoinGeckoProvider(),
            FallbackTokenProvider()  # Alltid sist för fallback
        ]

        # Statistik
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'errors': 0,
            'last_cleanup': datetime.now()
        }

        logger.info("DynamicTokenResolver initialized with providers: " +
                   ", ".join([p.__class__.__name__ for p in self.providers]))

    async def __aenter__(self):
        """Async context manager entry."""
        # Öppna alla provider sessions
        for provider in self.providers:
            if hasattr(provider, '__aenter__'):
                await provider.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Stäng alla provider sessions
        for provider in self.providers:
            if hasattr(provider, '__aexit__'):
                await provider.__aexit__(exc_type, exc_val, exc_tb)

    async def resolve_token(self, query: str, force_refresh: bool = False) -> TokenInfo:
        """
        Lös upp token från symbol, namn eller address.

        Args:
            query: Sökterm (symbol, namn, address eller contract address)
            force_refresh: Tvinga nytt API-anrop även om cache finns

        Returns:
            TokenInfo för hittad token

        Raises:
            TokenNotFoundError: Om token inte hittas i någon provider
        """
        # Normalisera query
        normalized_query = self._normalize_query(query)

        # Försök cache först (om inte force_refresh)
        if not force_refresh:
            cached_result = self.cache.get(normalized_query)
            if cached_result:
                token_info = TokenInfo.from_dict(cached_result)
                self.stats['cache_hits'] += 1
                logger.debug(f"Cache hit for query: {query}")
                return token_info

        self.stats['cache_misses'] += 1

        # Försök alla providers
        async with self.semaphore:  # Begränsa samtidiga requests
            for provider in self.providers:
                try:
                    self.stats['api_calls'] += 1
                    token_info = await provider.search_token(normalized_query)

                    if token_info:
                        # Cache resultatet
                        self.cache.set(normalized_query, token_info.to_dict())

                        logger.info(f"Token resolved via {provider.__class__.__name__}: {token_info.symbol}")
                        return token_info

                except Exception as e:
                    self.stats['errors'] += 1
                    logger.warning(f"Provider {provider.__class__.__name__} failed for {query}: {e}")
                    continue

        # Ingen provider hittade token
        error_msg = f"Token '{query}' not found in any provider"
        logger.error(error_msg)
        raise TokenNotFoundError(error_msg)

    async def resolve_multiple_tokens(self, queries: List[str], force_refresh: bool = False) -> Dict[str, TokenInfo]:
        """
        Lös upp flera tokens samtidigt.

        Args:
            queries: Lista med söktermer
            force_refresh: Tvinga refresh för alla

        Returns:
            Dictionary med query -> TokenInfo mapping
        """
        tasks = []
        for query in queries:
            task = asyncio.create_task(self.resolve_token(query, force_refresh))
            tasks.append(task)

        # Vänta på alla tasks att slutföra
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Bearbeta resultat
        resolved_tokens = {}
        for i, result in enumerate(results):
            query = queries[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to resolve {query}: {result}")
            else:
                resolved_tokens[query] = result

        return resolved_tokens

    async def search_similar_tokens(self, query: str, limit: int = 5) -> List[TokenInfo]:
        """
        Sök efter liknande tokens i cache och providers.

        Args:
            query: Sökterm
            limit: Max antal resultat

        Returns:
            Lista med matchande TokenInfo
        """
        # Försök först cache
        similar_from_cache = self.cache.search_similar(query, limit)

        if similar_from_cache:
            return [TokenInfo.from_dict(item['data']) for item in similar_from_cache]

        # Försök providers för fuzzy search
        similar_tokens = []

        for provider in self.providers[:-1]:  # Skippa fallback provider
            try:
                # Försök olika variationer av query
                variations = self._generate_search_variations(query)

                for variation in variations:
                    token_info = await provider.search_token(variation)
                    if token_info and token_info not in similar_tokens:
                        similar_tokens.append(token_info)
                        if len(similar_tokens) >= limit:
                            break

                if len(similar_tokens) >= limit:
                    break

            except Exception as e:
                logger.debug(f"Provider {provider.__class__.__name__} search failed: {e}")
                continue

        return similar_tokens[:limit]

    def _normalize_query(self, query: str) -> str:
        """Normalisera sökterm för bättre matching."""
        # Konvertera till lowercase och trimma
        normalized = query.lower().strip()

        # Ta bort vanliga prefix/suffix
        normalized = normalized.replace('token', '').replace('coin', '').strip()

        # Hantera contract addresses
        if normalized.startswith('0x') and len(normalized) == 42:
            return normalized  # Behåll som address

        return normalized

    def _generate_search_variations(self, query: str) -> List[str]:
        """Generera sökvariationer för bättre matching."""
        variations = [query]

        # Lägg till uppercase version
        variations.append(query.upper())

        # Lägg till vanliga suffix
        if not query.endswith('token'):
            variations.append(f"{query} token")

        # Förkortningar
        if len(query) > 3:
            variations.append(query[:3])  # Första 3 bokstäver
            variations.append(query[:4])  # Första 4 bokstäver

        # Vanliga stavfel eller variationer
        replacements = {
            'ethereum': ['eth', 'ether'],
            'bitcoin': ['btc', 'bitc'],
            'tether': ['usdt', 'teth'],
            'binance': ['bnb', 'bina'],
            'cardano': ['ada', 'card'],
            'polygon': ['matic', 'poly'],
            'chainlink': ['link', 'chai'],
            'uniswap': ['uni', 'unis']
        }

        for key, alts in replacements.items():
            if key in query.lower():
                variations.extend(alts)
            for alt in alts:
                if alt in query.lower():
                    variations.append(key)

        # Ta bort duplicat och returnera unika
        return list(set(variations))

    async def preload_popular_tokens(self) -> None:
        """
        Förladda populära tokens för bättre prestanda.
        Detta kan köras vid startup för att fylla cache.
        """
        popular_tokens = [
            'ETH', 'BTC', 'USDC', 'USDT', 'DAI', 'WBTC',
            'MATIC', 'BNB', 'ADA', 'SOL', 'DOT', 'AVAX',
            'LINK', 'UNI', 'AAVE', 'CAKE', 'SUSHI'
        ]

        logger.info(f"Preloading {len(popular_tokens)} popular tokens...")

        # Ladda i grupper för att inte överbelasta API:erna
        batch_size = 5
        for i in range(0, len(popular_tokens), batch_size):
            batch = popular_tokens[i:i + batch_size]

            try:
                await self.resolve_multiple_tokens(batch)
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.warning(f"Batch preload failed for {batch}: {e}")

        logger.info("Popular token preload completed")

    def get_stats(self) -> Dict[str, Any]:
        """Hämta resolver-statistik."""
        cache_stats = self.cache.get_stats()

        return {
            'resolver_stats': self.stats,
            'cache_stats': cache_stats,
            'total_providers': len(self.providers),
            'provider_names': [p.__class__.__name__ for p in self.providers],
            'uptime': str(datetime.now() - self.stats.get('start_time', datetime.now()))
        }

    def clear_cache(self) -> None:
        """Rensa hela cachen."""
        self.cache.clear()
        logger.info("Token resolver cache cleared")

    async def cleanup_expired_cache(self) -> int:
        """
        Rensa utgångna cache-entries.

        Returns:
            Antal rensade entries
        """
        return self.cache.cleanup_expired()

    async def health_check(self) -> Dict[str, Any]:
        """
        Utför health check på alla providers.

        Returns:
            Health status för varje provider
        """
        health_results = {}

        for provider in self.providers:
            try:
                # Snabb test - försök resolve en känd token
                test_token = await provider.search_token('ETH')
                health_results[provider.__class__.__name__] = {
                    'status': 'healthy' if test_token else 'degraded',
                    'response_time': None,  # Kan läggas till senare
                    'last_check': datetime.now().isoformat()
                }
            except Exception as e:
                health_results[provider.__class__.__name__] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }

        return health_results

# Global instans för enkel användning
_default_resolver: Optional[DynamicTokenResolver] = None

def get_default_resolver() -> DynamicTokenResolver:
    """Hämta global default resolver instans."""
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = DynamicTokenResolver()
    return _default_resolver

async def resolve_token(query: str, force_refresh: bool = False) -> TokenInfo:
    """
    Enkel funktion för token resolution med global resolver.

    Args:
        query: Token sökterm
        force_refresh: Tvinga refresh från API

    Returns:
        TokenInfo för hittad token
    """
    resolver = get_default_resolver()
    async with resolver:
        return await resolver.resolve_token(query, force_refresh)