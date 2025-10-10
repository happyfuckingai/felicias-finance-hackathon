"""
Tekniska indikatorer för trend-following strategi.
Implementerar klassiska tekniska analys indikatorer för kryptohandel.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Samling tekniska indikatorer för trend-following analys."""

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """
        Beräkna Simple Moving Average (SMA).

        Args:
            prices: Lista med prisdata
            period: Period för medelvärde (t.ex. 20, 50)

        Returns:
            Lista med SMA värden
        """
        if len(prices) < period:
            return []

        sma_values = []
        for i in range(len(prices) - period + 1):
            sma = sum(prices[i:i + period]) / period
            sma_values.append(sma)

        return sma_values

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """
        Beräkna Exponential Moving Average (EMA).

        Args:
            prices: Lista med prisdata
            period: Period för EMA

        Returns:
            Lista med EMA värden
        """
        if len(prices) < period:
            return []

        # Beräkna SMA först för första värdet
        sma = sum(prices[:period]) / period
        ema_values = [sma]

        # Använd EMA formeln: EMA = (Close * multiplier) + (EMA_prev * (1 - multiplier))
        multiplier = 2 / (period + 1)

        for price in prices[period:]:
            ema = (price * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)

        return ema_values

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """
        Beräkna Relative Strength Index (RSI).

        Args:
            prices: Lista med prisdata
            period: Period för RSI (vanligtvis 14)

        Returns:
            Lista med RSI värden (0-100)
        """
        if len(prices) < period + 1:
            return []

        # Beräkna prisändringar
        deltas = []
        for i in range(1, len(prices)):
            deltas.append(prices[i] - prices[i-1])

        rsi_values = []
        gains = []
        losses = []

        # Initiera med första perioden
        for i in range(period):
            if deltas[i] > 0:
                gains.append(deltas[i])
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(deltas[i]))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)

        # Beräkna för resten av datan
        for i in range(period, len(deltas)):
            delta = deltas[i]

            if delta > 0:
                gain = delta
                loss = 0
            else:
                gain = 0
                loss = abs(delta)

            # Smooth med Wilder's smoothing
            avg_gain = ((avg_gain * (period - 1)) + gain) / period
            avg_loss = ((avg_loss * (period - 1)) + loss) / period

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            rsi_values.append(rsi)

        return rsi_values

    @staticmethod
    def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
        """
        Beräkna MACD (Moving Average Convergence Divergence).

        Args:
            prices: Lista med prisdata
            fast_period: Period för fast EMA (vanligtvis 12)
            slow_period: Period för slow EMA (vanligtvis 26)
            signal_period: Period för signal line EMA (vanligtvis 9)

        Returns:
            Dict med MACD line, signal line, och histogram
        """
        if len(prices) < slow_period:
            return {'macd': [], 'signal': [], 'histogram': []}

        # Beräkna fast och slow EMA
        fast_ema = TechnicalIndicators.calculate_ema(prices, fast_period)
        slow_ema = TechnicalIndicators.calculate_ema(prices, slow_period)

        # MACD line = Fast EMA - Slow EMA
        macd_line = []
        start_idx = slow_period - fast_period

        for i in range(len(slow_ema)):
            macd_line.append(fast_ema[start_idx + i] - slow_ema[i])

        # Signal line = EMA av MACD line
        signal_line = TechnicalIndicators.calculate_ema(macd_line, signal_period)

        # Histogram = MACD line - Signal line
        histogram = []
        signal_start_idx = signal_period - 1

        for i in range(len(signal_line)):
            histogram.append(macd_line[signal_start_idx + i] - signal_line[i])

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
        """
        Beräkna Bollinger Bands.

        Args:
            prices: Lista med prisdata
            period: Period för SMA
            std_dev: Antal standardavvikelser för bands

        Returns:
            Dict med upper band, middle band (SMA), och lower band
        """
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}

        sma = TechnicalIndicators.calculate_sma(prices, period)

        upper_band = []
        lower_band = []

        for i in range(len(sma)):
            start_idx = i
            end_idx = i + period
            window = prices[start_idx:end_idx]

            std = np.std(window)
            upper = sma[i] + (std_dev * std)
            lower = sma[i] - (std_dev * std)

            upper_band.append(upper)
            lower_band.append(lower)

        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }

    @staticmethod
    def detect_trend_direction(prices: List[float], short_period: int = 20, long_period: int = 50) -> str:
        """
        Detektera trendriktning baserat på moving averages.

        Args:
            prices: Lista med prisdata
            short_period: Kort period MA
            long_period: Lång period MA

        Returns:
            'bullish', 'bearish', eller 'sideways'
        """
        if len(prices) < long_period:
            return 'insufficient_data'

        short_ma = TechnicalIndicators.calculate_sma(prices, short_period)
        long_ma = TechnicalIndicators.calculate_sma(prices, long_period)

        if len(short_ma) == 0 or len(long_ma) == 0:
            return 'insufficient_data'

        # Jämför senaste värdena
        short_latest = short_ma[-1]
        long_latest = long_ma[-1]

        # Beräkna slope för att avgöra styrka
        short_slope = short_ma[-1] - short_ma[-2] if len(short_ma) > 1 else 0
        long_slope = long_ma[-1] - long_ma[-2] if len(long_ma) > 1 else 0

        if short_latest > long_latest and short_slope > 0 and long_slope > 0:
            return 'bullish'
        elif short_latest < long_latest and short_slope < 0 and long_slope < 0:
            return 'bearish'
        else:
            return 'sideways'


class TrendFollowingStrategy:
    """Trend-following strategi som kombinerar flera tekniska indikatorer."""

    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.logger = logging.getLogger(__name__)

    async def analyze_trend(self, prices: List[float], volumes: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Genomför komplett trendanalys med flera indikatorer.

        Args:
            prices: Lista med prisdata (bör vara minst 50 punkter för bra analys)
            volumes: Optional lista med volymdata

        Returns:
            Dict med komplett trendanalys
        """
        try:
            if len(prices) < 50:
                return {
                    'success': False,
                    'error': 'Insufficient price data. Need at least 50 data points for reliable analysis.'
                }

            analysis = {
                'success': True,
                'trend_direction': self.indicators.detect_trend_direction(prices),
                'indicators': {},
                'signals': [],
                'confidence': 0.0,
                'recommendation': 'HOLD'
            }

            # Beräkna tekniska indikatorer
            sma_20 = self.indicators.calculate_sma(prices, 20)
            sma_50 = self.indicators.calculate_sma(prices, 50)
            ema_12 = self.indicators.calculate_ema(prices, 12)
            ema_26 = self.indicators.calculate_ema(prices, 26)
            rsi = self.indicators.calculate_rsi(prices, 14)
            macd = self.indicators.calculate_macd(prices)
            bb = self.indicators.calculate_bollinger_bands(prices)

            analysis['indicators'] = {
                'sma_20': sma_20[-1] if sma_20 else None,
                'sma_50': sma_50[-1] if sma_50 else None,
                'ema_12': ema_12[-1] if ema_12 else None,
                'ema_26': ema_26[-1] if ema_26 else None,
                'rsi': rsi[-1] if rsi else None,
                'macd': {
                    'line': macd['macd'][-1] if macd['macd'] else None,
                    'signal': macd['signal'][-1] if macd['signal'] else None,
                    'histogram': macd['histogram'][-1] if macd['histogram'] else None
                },
                'bollinger_bands': {
                    'upper': bb['upper'][-1] if bb['upper'] else None,
                    'middle': bb['middle'][-1] if bb['middle'] else None,
                    'lower': bb['lower'][-1] if bb['lower'] else None
                }
            }

            # Generera trading-signaler baserat på indikatorer
            signals = []
            confidence = 0.0

            # Trend signaler
            if sma_20 and sma_50:
                if sma_20[-1] > sma_50[-1]:
                    signals.append("Short MA above Long MA - Bullish trend")
                    confidence += 0.3
                else:
                    signals.append("Short MA below Long MA - Bearish trend")
                    confidence -= 0.3

            # RSI signaler
            if rsi:
                rsi_val = rsi[-1]
                if rsi_val > 70:
                    signals.append(f"RSI overbought ({rsi_val:.1f}) - Potential sell signal")
                    confidence -= 0.2
                elif rsi_val < 30:
                    signals.append(f"RSI oversold ({rsi_val:.1f}) - Potential buy signal")
                    confidence += 0.2
                else:
                    signals.append(f"RSI neutral ({rsi_val:.1f})")

            # MACD signaler
            if macd['macd'] and macd['signal']:
                macd_val = macd['macd'][-1]
                signal_val = macd['signal'][-1]
                hist_val = macd['histogram'][-1] if macd['histogram'] else 0

                if macd_val > signal_val and hist_val > 0:
                    signals.append("MACD bullish crossover - Buy signal")
                    confidence += 0.3
                elif macd_val < signal_val and hist_val < 0:
                    signals.append("MACD bearish crossover - Sell signal")
                    confidence -= 0.3

            # Bollinger Bands signaler
            if bb['upper'] and bb['lower']:
                current_price = prices[-1]
                upper = bb['upper'][-1]
                lower = bb['lower'][-1]

                if current_price > upper:
                    signals.append("Price above upper Bollinger Band - Overbought")
                    confidence -= 0.2
                elif current_price < lower:
                    signals.append("Price below lower Bollinger Band - Oversold")
                    confidence += 0.2

            # Generera rekommendation baserat på confidence
            if confidence > 0.4:
                recommendation = 'BUY'
            elif confidence < -0.4:
                recommendation = 'SELL'
            else:
                recommendation = 'HOLD'

            analysis.update({
                'signals': signals,
                'confidence': abs(confidence),
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            })

            return analysis

        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_entry_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generera entry signal baserat på trendanalys.

        Args:
            analysis: Resultat från analyze_trend

        Returns:
            Entry signal med stop loss och take profit levels
        """
        if not analysis['success']:
            return {'success': False, 'error': analysis.get('error', 'Analysis failed')}

        signal = {
            'success': True,
            'action': analysis['recommendation'],
            'confidence': analysis['confidence'],
            'entry_price': None,  # Ska sättas baserat på current price
            'stop_loss': None,
            'take_profit': None,
            'risk_reward_ratio': None
        }

        if analysis['recommendation'] in ['BUY', 'SELL']:
            # För BUY signaler
            if analysis['recommendation'] == 'BUY':
                # Stop loss baserat på recent low eller Bollinger band
                # Take profit baserat på risk-reward ratio (typiskt 1:2 eller 1:3)
                signal.update({
                    'stop_loss_type': 'percentage',
                    'stop_loss_value': 5.0,  # 5% stop loss
                    'take_profit_type': 'percentage',
                    'take_profit_value': 15.0,  # 15% take profit (1:3 ratio)
                    'risk_reward_ratio': 3.0
                })

            # För SELL signaler
            else:
                signal.update({
                    'stop_loss_type': 'percentage',
                    'stop_loss_value': 5.0,  # 5% stop loss
                    'take_profit_type': 'percentage',
                    'take_profit_value': 15.0,  # 15% take profit
                    'risk_reward_ratio': 3.0
                })

        return signal