"""
Trend-Following Signal Generator för automatisk trading.
Kombinerar tekniska indikatorer med DEX-integration för realtids trading-signaler.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import os

from .technical_indicators import TrendFollowingStrategy, TechnicalIndicators
from .analytics import MarketAnalyzer, TradingSignalGenerator
from .dex_integration import RealDexIntegration

logger = logging.getLogger(__name__)

class TrendSignalGenerator:
    """Genererar trend-following signaler för automatisk trading."""

    def __init__(self):
        self.market_analyzer = MarketAnalyzer()
        self.trend_strategy = TrendFollowingStrategy()
        self.basic_signal_generator = TradingSignalGenerator(self.market_analyzer)

        # Initiera DEX integration för realtid data
        self.dex_integration = RealDexIntegration()

        # Konfigurationsparametrar för trend-following
        self.config = {
            'min_data_points': 50,      # Minsta antal datapunkter för analys
            'trend_confirmation_periods': 3,  # Perioder att bekräfta trend
            'rsi_overbought': 70,       # RSI överköpt nivå
            'rsi_oversold': 30,         # RSI översåld nivå
            'macd_signal_strength': 0.001,  # Min styrka för MACD signal
            'volume_confirmation': True,    # Använd volym för bekräftelse
            'risk_per_trade': 0.02,     # 2% risk per trade
            'max_position_size': 0.1    # Max 10% av portfolio
        }

    async def generate_trend_signal(self, token_id: str, use_llm: bool = True) -> Dict[str, Any]:
        """
        Generera komplett trend-following signal med teknisk analys och DEX data.

        Args:
            token_id: CoinGecko token ID (t.ex. "ethereum", "bitcoin")
            use_llm: Om LLM ska användas för förbättrad analys

        Returns:
            Komplett trading signal med alla komponenter
        """
        try:
            logger.info(f"Generating trend signal for {token_id}")

            # Hämta historiska prisdata från CoinGecko
            price_data = await self._get_historical_prices(token_id)

            if not price_data['success']:
                return {
                    'success': False,
                    'error': f'Could not fetch price data: {price_data.get("error", "Unknown error")}'
                }

            prices = price_data['prices']
            volumes = price_data.get('volumes', [])

            # Utför teknisk trendanalys
            trend_analysis = await self.trend_strategy.analyze_trend(prices, volumes)

            if not trend_analysis['success']:
                return {
                    'success': False,
                    'error': f'Trend analysis failed: {trend_analysis.get("error", "Unknown error")}'
                }

            # Hämta DEX data för likviditet och spreads
            dex_data = await self.dex_integration.get_dex_data(token_id, "ethereum")

            # Generera entry/exit signaler
            entry_signal = self.trend_strategy.get_entry_signal(trend_analysis)

            # Kombinera med grundläggande signal generator för jämförelse
            basic_signal = await self.basic_signal_generator.generate_signal(token_id, use_llm)

            # Skapa komplett trading rekommendation
            trading_recommendation = await self._generate_trading_recommendation(
                trend_analysis, entry_signal, dex_data, basic_signal
            )

            result = {
                'success': True,
                'token_id': token_id,
                'timestamp': datetime.now().isoformat(),
                'trend_analysis': trend_analysis,
                'entry_signal': entry_signal,
                'dex_data': dex_data,
                'trading_recommendation': trading_recommendation,
                'market_data': {
                    'current_price': prices[-1] if prices else None,
                    'price_change_24h': price_data.get('price_change_24h'),
                    'volume_24h': price_data.get('volume_24h'),
                    'data_points': len(prices)
                }
            }

            # Lägg till LLM-insikter om tillgängliga
            if use_llm and basic_signal.get('analysis_method') == 'llm_enhanced':
                result['llm_insights'] = basic_signal.get('llm_insights', {})

            logger.info(f"Successfully generated trend signal for {token_id}: {trading_recommendation['action']}")
            return result

        except Exception as e:
            logger.error(f"Error generating trend signal for {token_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'token_id': token_id
            }

    async def _get_historical_prices(self, token_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Hämta historiska prisdata för teknisk analys.

        Args:
            token_id: CoinGecko token ID
            days: Antal dagar historisk data

        Returns:
            Dict med pris- och volymdata
        """
        try:
            # Använd CoinGecko API för historisk data
            url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly' if days <= 90 else 'daily'
            }

            async with self.market_analyzer.session or aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        prices_data = data.get('prices', [])
                        volumes_data = data.get('total_volumes', [])

                        if not prices_data:
                            return {'success': False, 'error': 'No price data available'}

                        # Extrahera pris och volym listor
                        prices = [point[1] for point in prices_data]
                        volumes = [point[1] for point in volumes_data] if volumes_data else []

                        # Hämta senaste 24h data för jämförelse
                        current_price_data = await self.market_analyzer.get_token_price(token_id)

                        return {
                            'success': True,
                            'prices': prices,
                            'volumes': volumes,
                            'price_change_24h': current_price_data.get('price_change_24h') if current_price_data['success'] else None,
                            'volume_24h': current_price_data.get('volume_24h') if current_price_data['success'] else None,
                            'data_points': len(prices)
                        }
                    else:
                        return {'success': False, 'error': f'API returned status {response.status}'}

        except Exception as e:
            logger.error(f"Error fetching historical prices: {e}")
            return {'success': False, 'error': str(e)}

    async def _generate_trading_recommendation(
        self,
        trend_analysis: Dict[str, Any],
        entry_signal: Dict[str, Any],
        dex_data: Dict[str, Any],
        basic_signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generera slutgiltig trading rekommendation baserat på alla indata.

        Args:
            trend_analysis: Resultat från trendanalys
            entry_signal: Entry/exit signaler
            dex_data: DEX likviditetsdata
            basic_signal: Grundläggande signal från TradingSignalGenerator

        Returns:
            Slutgiltig trading rekommendation
        """
        try:
            recommendation = {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': [],
                'risk_assessment': {},
                'execution_parameters': {}
            }

            # Analysera trend styrka
            trend_direction = trend_analysis.get('trend_direction', 'sideways')
            trend_confidence = trend_analysis.get('confidence', 0.0)

            # Analysera DEX likviditet
            dex_liquidity_ok = False
            if dex_data.get('success', False):
                total_liquidity = dex_data.get('total_liquidity', 0)
                dex_liquidity_ok = total_liquidity > 1000000  # Minst $1M likviditet

            # Kombinera signaler
            signals_alignment = 0

            # Jämför trend analys med grundläggande signal
            if trend_analysis['recommendation'] == basic_signal.get('signal'):
                signals_alignment += 1
                recommendation['reasoning'].append("Trend and momentum signals aligned")
            else:
                signals_alignment -= 0.5
                recommendation['reasoning'].append("Mixed signals between trend and momentum")

            # Trend styrka
            if trend_direction in ['bullish', 'bearish'] and trend_confidence > 0.6:
                signals_alignment += 0.8
                recommendation['reasoning'].append(f"Strong {trend_direction} trend detected")
            elif trend_direction == 'sideways':
                signals_alignment -= 0.3
                recommendation['reasoning'].append("Sideways market - low conviction")

            # DEX likviditet check
            if dex_liquidity_ok:
                recommendation['reasoning'].append("Good DEX liquidity for execution")
            else:
                signals_alignment -= 0.4
                recommendation['reasoning'].append("Low DEX liquidity - execution risk")

            # Generera slutgiltig rekommendation
            final_confidence = (signals_alignment + trend_confidence) / 2

            if final_confidence > 0.6:
                recommendation['action'] = trend_analysis['recommendation']
                recommendation['confidence'] = final_confidence
            elif final_confidence < -0.4:
                recommendation['action'] = 'SELL' if trend_analysis['recommendation'] == 'BUY' else 'BUY'
                recommendation['confidence'] = abs(final_confidence)
            else:
                recommendation['action'] = 'HOLD'
                recommendation['confidence'] = 0.3

            # Risk assessment
            recommendation['risk_assessment'] = {
                'trend_strength': trend_confidence,
                'signal_alignment': signals_alignment,
                'liquidity_risk': 'low' if dex_liquidity_ok else 'high',
                'overall_risk': 'low' if final_confidence > 0.7 else 'medium' if final_confidence > 0.4 else 'high'
            }

            # Execution parameters
            if recommendation['action'] != 'HOLD':
                recommendation['execution_parameters'] = {
                    'max_slippage': 0.005,  # 0.5%
                    'min_liquidity': 1000000,  # $1M
                    'preferred_dex': 'uniswap_v3',
                    'time_in_force': 'ioc',  # Immediate or Cancel
                    'position_size': self._calculate_position_size(recommendation['confidence'])
                }

            return recommendation

        except Exception as e:
            logger.error(f"Error generating trading recommendation: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': [f'Error in recommendation generation: {str(e)}'],
                'risk_assessment': {'overall_risk': 'high'},
                'execution_parameters': {}
            }

    def _calculate_position_size(self, confidence: float) -> float:
        """
        Beräkna position size baserat på signal confidence och risk parametrar.

        Args:
            confidence: Signal confidence (0-1)

        Returns:
            Position size som andel av tillgängligt kapital (0-1)
        """
        try:
            # Base position size på confidence
            base_size = confidence * self.config['max_position_size']

            # Justera för risk per trade
            risk_adjusted_size = min(base_size, self.config['risk_per_trade'] * 5)

            # Säkerhetsmarginaler
            if confidence < 0.5:
                risk_adjusted_size *= 0.5  # Halvera för låg confidence
            elif confidence > 0.8:
                risk_adjusted_size *= 1.2  # Öka för hög confidence

            return max(0.01, min(risk_adjusted_size, self.config['max_position_size']))

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01  # Minimum size som fallback

    async def get_trend_dashboard(self, token_ids: List[str]) -> Dict[str, Any]:
        """
        Generera trend dashboard för flera tokens.

        Args:
            token_ids: Lista med token IDs att analysera

        Returns:
            Dashboard med trendanalys för alla tokens
        """
        try:
            dashboard = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'tokens': {},
                'market_summary': {
                    'bullish_trends': 0,
                    'bearish_trends': 0,
                    'sideways_markets': 0,
                    'high_confidence_signals': 0
                }
            }

            for token_id in token_ids:
                signal = await self.generate_trend_signal(token_id, use_llm=False)

                if signal['success']:
                    dashboard['tokens'][token_id] = {
                        'trend_direction': signal['trend_analysis']['trend_direction'],
                        'recommendation': signal['trading_recommendation']['action'],
                        'confidence': signal['trading_recommendation']['confidence'],
                        'current_price': signal['market_data']['current_price']
                    }

                    # Uppdatera market summary
                    trend = signal['trend_analysis']['trend_direction']
                    confidence = signal['trading_recommendation']['confidence']

                    if trend == 'bullish':
                        dashboard['market_summary']['bullish_trends'] += 1
                    elif trend == 'bearish':
                        dashboard['market_summary']['bearish_trends'] += 1
                    else:
                        dashboard['market_summary']['sideways_markets'] += 1

                    if confidence > 0.7:
                        dashboard['market_summary']['high_confidence_signals'] += 1

            return dashboard

        except Exception as e:
            logger.error(f"Error generating trend dashboard: {e}")
            return {
                'success': False,
                'error': str(e)
            }