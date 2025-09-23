"""
Alternative Data Providers för crypto-hanteringssystemet.
Fallback-datakällor när primära API:er inte fungerar.
Inkluderar DexScreener, CoinMarketCap och andra alternativa källor.
"""
import os
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DexScreenerProvider:
    """DexScreener som alternativ till CoinGecko"""

    BASE_URL = "https://api.dexscreener.com/latest/dex"

    async def get_token_price(self, token_id: str) -> Dict[str, Any]:
        """Hämta tokenpris från DexScreener"""
        try:
            # Försök först med token-adress mapping
            token_addresses = self._get_token_addresses(token_id)

            for chain, address in token_addresses.items():
                try:
                    url = f"{self.BASE_URL}/tokens/{address}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get('pairs') and len(data['pairs']) > 0:
                                    pair = data['pairs'][0]  # Ta första paret
                                    return {
                                        'success': True,
                                        'token_id': token_id,
                                        'price_usd': float(pair['priceUsd']) if pair.get('priceUsd') else 0,
                                        'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                                        'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                                        'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                                        'source': 'dexscreener',
                                        'chain': chain
                                    }
                except Exception as e:
                    logger.warning(f"DexScreener failed for {chain}:{address}: {e}")
                    continue

            # Om ingen adress fungerade
            return {'success': False, 'error': f'Ingen data hittad för {token_id}'}

        except Exception as e:
            logger.error(f"DexScreener provider failed: {e}")
            return {'success': False, 'error': str(e)}

    def _get_token_addresses(self, token_id: str) -> Dict[str, str]:
        """Map token IDs till contract addresses"""
        # Hårdkodade adresser för vanliga tokens
        address_map = {
            'bitcoin': {
                'ethereum': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',  # WBTC
                'bsc': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c'     # BTCB
            },
            'ethereum': {
                'ethereum': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
                'bsc': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8'        # ETH
            },
            'solana': {
                'solana': 'So11111111111111111111111111111111111111112'  # SOL
            },
            'cardano': {
                'ethereum': '0x6B3595068778DD592e39A122f4f5a5CF09C90fE2'    # ADA
            },
            'polygon': {
                'ethereum': '0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0',  # MATIC
                'polygon': '0x0000000000000000000000000000000000001010'     # MATIC native
            },
            'avalanche': {
                'avalanche': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7'    # AVAX
            }
        }
        return address_map.get(token_id.lower(), {})

    async def get_trending_tokens(self, limit: int = 5) -> Dict[str, Any]:
        """Hämta trending tokens från DexScreener"""
        try:
            # DexScreener har inte direkt trending endpoint, så vi använder search
            url = f"{self.BASE_URL}/search?q=*"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get('pairs', [])[:limit]

                        trending_tokens = []
                        for pair in pairs:
                            if pair.get('baseToken'):
                                token = pair['baseToken']
                                trending_tokens.append({
                                    'id': token.get('symbol', '').lower(),
                                    'name': token.get('name', ''),
                                    'symbol': token.get('symbol', ''),
                                    'price_usd': float(pair.get('priceUsd', 0)),
                                    'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                                    'volume_24h': float(pair.get('volume', {}).get('h24', 0))
                                })

                        return {
                            'success': True,
                            'trending_tokens': trending_tokens,
                            'source': 'dexscreener'
                        }

        except Exception as e:
            logger.error(f"DexScreener trending failed: {e}")

        # Fallback
        return {
            'success': True,
            'trending_tokens': [
                {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC', 'price_usd': 60000, 'price_change_24h': 2.5},
                {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH', 'price_usd': 3000, 'price_change_24h': 1.8},
                {'id': 'solana', 'name': 'Solana', 'symbol': 'SOL', 'price_usd': 150, 'price_change_24h': -0.5}
            ][:limit],
            'fallback': True,
            'source': 'dexscreener_fallback'
        }


class CoinMarketCapProvider:
    """CoinMarketCap som alternativ datakälla"""

    BASE_URL = "https://pro-api.coinmarketcap.com/v1"

    def __init__(self):
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> Optional[str]:
        """Hämta API-nyckel från environment"""
        return os.getenv('CMC_API_KEY')

    async def get_token_price(self, token_id: str) -> Dict[str, Any]:
        """Hämta tokenpris från CoinMarketCap"""
        if not self.api_key:
            return {'success': False, 'error': 'CMC API key saknas'}

        try:
            symbol = self._token_id_to_symbol(token_id)
            url = f"{self.BASE_URL}/cryptocurrency/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json'
            }
            params = {'symbol': symbol}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('data') and symbol in data['data']:
                            token_data = data['data'][symbol]
                            quote = token_data['quote']['USD']

                            return {
                                'success': True,
                                'token_id': token_id,
                                'price_usd': quote['price'],
                                'price_change_24h': quote['percent_change_24h'],
                                'volume_24h': quote['volume_24h'],
                                'market_cap': quote['market_cap'],
                                'source': 'coinmarketcap'
                            }

        except Exception as e:
            logger.error(f"CoinMarketCap provider failed: {e}")

        return {'success': False, 'error': f'CMC kunde inte hämta data för {token_id}'}

    def _token_id_to_symbol(self, token_id: str) -> str:
        """Konvertera token ID till symbol"""
        symbol_map = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH',
            'solana': 'SOL',
            'cardano': 'ADA',
            'polygon': 'MATIC',
            'avalanche': 'AVAX',
            'chainlink': 'LINK',
            'polkadot': 'DOT',
            'uniswap': 'UNI'
        }
        return symbol_map.get(token_id.lower(), token_id.upper())


class NewsProvider:
    """Alternativ nyhetsleverantör"""

    async def get_crypto_news(self, query: str = "cryptocurrency", limit: int = 10) -> Dict[str, Any]:
        """Hämta crypto-nyheter från alternativa källor"""
        try:
            # Försök med CryptoPanic först
            news = await self._get_cryptopanic_news(query, limit)
            if news:
                return news

            # Fallback till CryptoCompare
            news = await self._get_cryptocompare_news(query, limit)
            if news:
                return news

        except Exception as e:
            logger.error(f"News provider failed: {e}")

        # Slutgiltig fallback
        return {
            'success': True,
            'news': [
                {
                    'title': 'Crypto Market Update',
                    'description': 'Market analysis and updates',
                    'url': 'https://coingecko.com',
                    'published_at': datetime.now().isoformat(),
                    'source': 'fallback'
                }
            ][:limit],
            'fallback': True
        }

    async def _get_cryptopanic_news(self, query: str, limit: int) -> Optional[Dict[str, Any]]:
        """Hämta nyheter från CryptoPanic"""
        try:
            url = f"https://cryptopanic.com/api/v3/posts/?auth_token={os.getenv('CRYPTOPANIC_API_KEY', '')}&public=true"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get('results', [])[:limit]

                        news_items = []
                        for post in posts:
                            news_items.append({
                                'title': post.get('title', ''),
                                'description': post.get('body', '')[:200],
                                'url': post.get('url', ''),
                                'published_at': post.get('published_at', ''),
                                'source': 'cryptopanic'
                            })

                        return {
                            'success': True,
                            'news': news_items,
                            'source': 'cryptopanic'
                        }

        except Exception as e:
            logger.warning(f"CryptoPanic failed: {e}")

        return None

    async def _get_cryptocompare_news(self, query: str, limit: int) -> Optional[Dict[str, Any]]:
        """Hämta nyheter från CryptoCompare"""
        try:
            url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN&api_key={os.getenv('CRYPTOCOMPARE_API_KEY', '')}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('Data', [])[:limit]

                        news_items = []
                        for article in articles:
                            news_items.append({
                                'title': article.get('title', ''),
                                'description': article.get('body', '')[:200],
                                'url': article.get('url', ''),
                                'published_at': article.get('published_on', ''),
                                'source': 'cryptocompare'
                            })

                        return {
                            'success': True,
                            'news': news_items,
                            'source': 'cryptocompare'
                        }

        except Exception as e:
            logger.warning(f"CryptoCompare failed: {e}")

        return None


class AlternativeDataManager:
    """Huvudklass för alternativa datakällor"""

    def __init__(self):
        self.dexscreener = DexScreenerProvider()
        self.coinmarketcap = CoinMarketCapProvider()
        self.news_provider = NewsProvider()

    async def get_token_price_fallback(self, token_id: str) -> Dict[str, Any]:
        """Försök flera datakällor för prisdata"""
        providers = [
            self.dexscreener,
            self.coinmarketcap
        ]

        for provider in providers:
            try:
                result = await provider.get_token_price(token_id)
                if result.get('success'):
                    return result
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                continue

        # Alla providers misslyckades
        return {
            'success': False,
            'error': f'Inga datakällor kunde hämta pris för {token_id}',
            'fallback_message': 'Kontrollera token-symbol eller försök senare'
        }

    async def get_trending_fallback(self, limit: int = 5) -> Dict[str, Any]:
        """Försök flera datakällor för trending data"""
        providers = [
            self.dexscreener
        ]

        for provider in providers:
            try:
                result = await provider.get_trending_tokens(limit)
                if result.get('success'):
                    return result
            except Exception as e:
                logger.warning(f"Trending provider {provider.__class__.__name__} failed: {e}")
                continue

        # Fallback till hårdkodade data
        return {
            'success': True,
            'trending_tokens': [
                {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC', 'price_usd': 60000},
                {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH', 'price_usd': 3000},
                {'id': 'solana', 'name': 'Solana', 'symbol': 'SOL', 'price_usd': 150}
            ][:limit],
            'fallback': True,
            'message': 'Använder hårdkodade trending-data'
        }

    async def get_news_fallback(self, query: str = "cryptocurrency", limit: int = 10) -> Dict[str, Any]:
        """Försök flera datakällor för nyheter"""
        return await self.news_provider.get_crypto_news(query, limit)


# Global instans
alternative_data_manager = AlternativeDataManager()