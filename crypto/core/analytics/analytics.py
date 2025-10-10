"""
Marknadsanalys och prisdata för HappyOS Crypto.
"""
import requests
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Hanterar marknadsdata och analys."""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, _): # exc_tb renamed to _
        if self.session:
            await self.session.close()
    
    async def get_token_price(self, token_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """
        Hämta aktuellt pris för token från CoinGecko.
        
        Args:
            token_id: CoinGecko token ID (t.ex. "ethereum", "bitcoin")
            vs_currency: Valuta att jämföra mot (default: "usd")
            
        Returns:
            Dict med prisdata och metadata
        """
        try:
            url = f"{self.coingecko_base}/simple/price"
            params = {
                'ids': token_id,
                'vs_currencies': vs_currency,
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    data = await response.json()
            else:
                response = requests.get(url, params=params)
                data = response.json()
            
            if token_id in data:
                token_data = data[token_id]
                return {
                    'success': True,
                    'token_id': token_id,
                    'price': token_data.get(vs_currency),
                    'price_change_24h': token_data.get(f'{vs_currency}_24h_change'),
                    'volume_24h': token_data.get(f'{vs_currency}_24h_vol'),
                    'market_cap': token_data.get(f'{vs_currency}_market_cap'),
                    'currency': vs_currency,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'Token {token_id} hittades inte'
                }
                
        except Exception as e:
            logger.error(f"Fel vid hämtning av prisdata: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_trending_tokens(self, limit: int = 10) -> Dict[str, Any]:
        """
        Hämta trending tokens från CoinGecko.
        
        Args:
            limit: Antal tokens att returnera
            
        Returns:
            Lista med trending tokens
        """
        try:
            url = f"{self.coingecko_base}/search/trending"
            
            if self.session:
                async with self.session.get(url) as response:
                    data = await response.json()
            else:
                response = requests.get(url)
                data = response.json()
            
            trending = data.get('coins', [])[:limit]
            
            return {
                'success': True,
                'trending_tokens': [
                    {
                        'id': coin['item']['id'],
                        'name': coin['item']['name'],
                        'symbol': coin['item']['symbol'],
                        'market_cap_rank': coin['item']['market_cap_rank'],
                        'price_btc': coin['item']['price_btc']
                    }
                    for coin in trending
                ],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fel vid hämtning av trending tokens: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_token_performance(self, token_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Analysera token-prestanda över tid.
        
        Args:
            token_id: CoinGecko token ID
            days: Antal dagar att analysera
            
        Returns:
            Analys av token-prestanda
        """
        try:
            url = f"{self.coingecko_base}/coins/{token_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    data = await response.json()
            else:
                response = requests.get(url, params=params)
                data = response.json()
            
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            
            if not prices:
                return {
                    'success': False,
                    'error': 'Ingen prisdata tillgänglig'
                }
            
            # Beräkna statistik
            price_values = [price[1] for price in prices]
            volume_values = [vol[1] for vol in volumes]
            
            start_price = price_values[0]
            end_price = price_values[-1]
            max_price = max(price_values)
            min_price = min(price_values)
            avg_price = sum(price_values) / len(price_values)
            avg_volume = sum(volume_values) / len(volume_values)
            
            price_change = ((end_price - start_price) / start_price) * 100
            volatility = (max_price - min_price) / avg_price * 100
            
            return {
                'success': True,
                'token_id': token_id,
                'analysis_period_days': days,
                'start_price': start_price,
                'end_price': end_price,
                'max_price': max_price,
                'min_price': min_price,
                'avg_price': avg_price,
                'avg_volume': avg_volume,
                'price_change_percent': price_change,
                'volatility_percent': volatility,
                'trend': 'bullish' if price_change > 0 else 'bearish',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fel vid analys av token-prestanda: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_dex_data(self, token_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Hämta verkliga DEX-data för en token via DexScreener API.

        Args:
            token_address: Token contract address
            chain: Blockchain (ethereum, polygon, base)

        Returns:
            Verkliga DEX trading data
        """
        try:
            # Använd verklig DEX-integration
            from .dex_integration import RealDexIntegration
            dex_integration = RealDexIntegration()

            result = await dex_integration.get_dex_data(token_address, chain)

            return result

        except Exception as e:
            logger.error(f"Fel vid hämtning av DEX-data: {e}")
            return {
                'success': False,
                'error': str(e),
                'token_address': token_address,
                'chain': chain
            }


class TradingSignalGenerator:
    """Genererar trading-signaler baserat på marknadsdata och LLM-analys."""

    def __init__(self, market_analyzer: MarketAnalyzer, llm_integration: Optional['LLMIntegration'] = None):
        self.market_analyzer = market_analyzer
        self.llm = llm_integration

        # Initiera LLM om API key finns
        if not self.llm and os.getenv('OPENAI_API_KEY'):
            try:
                from .llm_integration import LLMIntegration
                self.llm = LLMIntegration()
            except ImportError:
                logger.warning("LLM integration not available")
    
    async def generate_signal(self, token_id: str, use_llm: bool = True) -> Dict[str, Any]:
        """
        Generera trading-signal för en token med optional LLM-förstärkning.

        Args:
            token_id: CoinGecko token ID
            use_llm: Om LLM ska användas för analys

        Returns:
            Trading signal med rekommendation
        """
        try:
            # Hämta grundläggande marknadsdata
            price_data = await self.market_analyzer.get_token_price(token_id)
            performance = await self.market_analyzer.analyze_token_performance(token_id, 7)

            if not price_data['success'] or not performance['success']:
                return {
                    'success': False,
                    'error': 'Kunde inte hämta marknadsdata'
                }

            # Grundläggande teknisk analys
            price_change_24h = price_data.get('price_change_24h', 0)
            price_change_7d = performance.get('price_change_percent', 0)
            volatility = performance.get('volatility_percent', 0)
            current_price = price_data.get('price', 0)

            # Traditionell signal-logik som fallback
            signal, confidence, reasoning = self._generate_basic_signal(
                price_change_24h, price_change_7d, volatility
            )

            result = {
                'success': True,
                'token_id': token_id,
                'signal': signal,
                'confidence': confidence,
                'reasoning': reasoning,
                'analysis_method': 'technical',
                'market_data': {
                    'price_change_24h': price_change_24h,
                    'price_change_7d': price_change_7d,
                    'volatility': volatility,
                    'current_price': current_price
                },
                'timestamp': datetime.now().isoformat()
            }

            # Förbättra med LLM-analys om tillgängligt
            if use_llm and self.llm:
                try:
                    llm_enhanced = await self._enhance_with_llm(token_id, result)
                    if llm_enhanced['success']:
                        result.update({
                            'signal': llm_enhanced['signal'],
                            'confidence': llm_enhanced['confidence'],
                            'reasoning': llm_enhanced['reasoning'] + reasoning,  # Kombinera reasoning
                            'analysis_method': 'llm_enhanced',
                            'llm_insights': llm_enhanced.get('insights', {}),
                            'sentiment_score': llm_enhanced.get('sentiment_score')
                        })
                except Exception as llm_error:
                    logger.warning(f"LLM enhancement failed: {llm_error}")
                    # Fortsätt med grundläggande analys

            return result

        except Exception as e:
            logger.error(f"Fel vid generering av trading-signal: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_basic_signal(self, price_change_24h: float, price_change_7d: float, volatility: float) -> tuple:
        """Generera grundläggande signal baserat på teknisk analys."""
        signal = 'HOLD'
        confidence = 0.5
        reasoning = []

        # Momentum-baserade signaler
        if price_change_24h > 5 and price_change_7d > 10:
            signal = 'BUY'
            confidence = 0.8
            reasoning.append('Stark uppåtgående momentum')
        elif price_change_24h < -5 and price_change_7d < -10:
            signal = 'SELL'
            confidence = 0.7
            reasoning.append('Stark nedåtgående momentum')

        # Volatilitetsbaserade signaler
        elif volatility > 50:
            signal = 'HOLD'
            confidence = 0.3
            reasoning.append('Extrem volatilitet - risk för falska signaler')

        # Låg volatilitet = stabil marknad
        if abs(price_change_24h) < 2:
            reasoning.append('Låg daglig volatilitet indikerar marknad i balans')
            confidence = max(0.6, confidence)

        return signal, confidence, reasoning

    async def _enhance_with_llm(self, token_id: str, basic_result: Dict[str, Any]) -> Dict[str, Any]:
        """Förbättra signal med LLM-analys."""
        try:
            # Förbered context för LLM
            market_data = basic_result['market_data']

            # Simulera nyhetsdata (i verkligheten skulle detta komma från en nyhets-API)
            mock_news = [
                {
                    'title': f'{token_id.upper()} visar stark utveckling',
                    'content': f'Marknadsanalys visar att {token_id} har ökat med {market_data["price_change_7d"]:+.1f}% den senaste veckan.',
                    'sentiment': 'positive' if market_data['price_change_7d'] > 0 else 'negative'
                },
                {
                    'title': f'Volatilitet i {token_id.upper()} kräver uppmärksamhet',
                    'content': f'Analytiker noterar {market_data["volatility"]:.1f}% volatilitet för {token_id}.',
                    'sentiment': 'neutral'
                }
            ]

            # Utför sentiment-analys
            sentiment_analysis = await self.llm.analyze_market_sentiment(token_id, mock_news)

            if not sentiment_analysis['success']:
                return {'success': False, 'error': 'Sentiment analysis failed'}

            # Kombinera teknisk och sentiment-analys
            technical_signal = basic_result['signal']
            sentiment_score = sentiment_analysis['sentiment_score']
            technical_confidence = basic_result['confidence']

            # LLM-baserad beslutslögik
            final_signal = technical_signal
            final_confidence = technical_confidence

            # Justera baserat på sentiment
            if sentiment_score > 0.3 and technical_signal == 'HOLD':
                final_signal = 'BUY'
                final_confidence = min(0.7, technical_confidence + 0.2)
            elif sentiment_score < -0.3 and technical_signal == 'HOLD':
                final_signal = 'SELL'
                final_confidence = min(0.7, technical_confidence + 0.2)

            # Om starkt motstridiga signaler, håll
            if (sentiment_score > 0.5 and technical_signal == 'SELL') or \
               (sentiment_score < -0.5 and technical_signal == 'BUY'):
                final_signal = 'HOLD'
                final_confidence = 0.4

            return {
                'success': True,
                'signal': final_signal,
                'confidence': final_confidence,
                'reasoning': [
                    f"Teknisk analys: {technical_signal} ({technical_confidence:.1f})",
                    f"Sentiment analys: {sentiment_score:.2f} ({sentiment_analysis['recommendation']})",
                    f"LLM-insikt: {sentiment_analysis['explanation']}"
                ],
                'insights': {
                    'sentiment_score': sentiment_score,
                    'sentiment_recommendation': sentiment_analysis['recommendation'],
                    'key_sentiment_indicators': sentiment_analysis['key_indicators']
                }
            }

        except Exception as e:
            logger.error(f"LLM enhancement error: {e}")
            return {'success': False, 'error': str(e)}
