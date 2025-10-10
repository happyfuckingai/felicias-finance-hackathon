"""
Omfattande tester för Crypto System.
Enhetstester och integrationstester för alla komponenter.
"""
import asyncio
import unittest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Lägg till projektroot i path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from crypto.core.analytics import MarketAnalyzer, TradingSignalGenerator
from crypto.core.dex_integration import RealDexIntegration
from crypto.core.llm_integration import LLMIntegration
from crypto.core.error_handling import CryptoError, CircuitBreaker, RetryManager
from crypto.core.news_integration import NewsAPIIntegration
from crypto.handlers.wallet import WalletHandler
from crypto.handlers.research import ResearchHandler
from crypto.microservices.backtesting_service import HistoricalDataProvider
from crypto.rules.intent_processor import IntentProcessor

class TestMarketAnalyzer(unittest.TestCase):
    """Tester för MarketAnalyzer."""

    def setUp(self):
        self.analyzer = MarketAnalyzer()

    @patch('crypto.core.analytics.requests.get')
    def test_get_token_price_success(self, mock_get):
        """Test framgångsrik pris-hämtning."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'bitcoin': {
                'usd': 50000,
                'usd_24h_change': 5.2,
                'usd_24h_vol': 1000000
            }
        }
        mock_get.return_value = mock_response

        result = asyncio.run(self.analyzer.get_token_price('bitcoin'))

        self.assertTrue(result['success'])
        self.assertEqual(result['price'], 50000)
        self.assertEqual(result['price_change_24h'], 5.2)

    def test_get_token_price_not_found(self):
        """Test när token inte hittas."""
        result = asyncio.run(self.analyzer.get_token_price('nonexistent'))

        self.assertFalse(result['success'])
        self.assertIn('hittades inte', result['error'])

class TestTradingSignalGenerator(unittest.TestCase):
    """Tester för TradingSignalGenerator."""

    def setUp(self):
        self.market_analyzer = MarketAnalyzer()
        self.signal_generator = TradingSignalGenerator(self.market_analyzer)

    @patch('crypto.core.analytics.MarketAnalyzer.get_token_price')
    @patch('crypto.core.analytics.MarketAnalyzer.analyze_token_performance')
    def test_generate_signal_buy(self, mock_performance, mock_price):
        """Test BUY-signal generering."""
        mock_price.return_value = {
            'success': True,
            'price': 50000,
            'price_change_24h': 6.0
        }
        mock_performance.return_value = {
            'success': True,
            'price_change_percent': 12.0,
            'volatility_percent': 3.0
        }

        result = asyncio.run(self.signal_generator.generate_signal('bitcoin'))

        self.assertTrue(result['success'])
        self.assertEqual(result['signal'], 'BUY')
        self.assertGreater(result['confidence'], 0.7)

    def test_basic_signal_logic(self):
        """Test grundläggande signal-logik."""
        # Test BUY conditions
        signal, confidence, reasoning = self.signal_generator._generate_basic_signal(6.0, 12.0, 3.0)
        self.assertEqual(signal, 'BUY')
        self.assertGreater(confidence, 0.7)

        # Test SELL conditions
        signal, confidence, reasoning = self.signal_generator._generate_basic_signal(-6.0, -12.0, 3.0)
        self.assertEqual(signal, 'SELL')
        self.assertGreater(confidence, 0.6)

        # Test HOLD conditions (high volatility)
        signal, confidence, reasoning = self.signal_generator._generate_basic_signal(1.0, 2.0, 60.0)
        self.assertEqual(signal, 'HOLD')
        self.assertLess(confidence, 0.4)

class TestDexIntegration(unittest.TestCase):
    """Tester för DEX-integration."""

    def setUp(self):
        self.dex_integration = RealDexIntegration()

    @patch('crypto.core.dex_integration.aiohttp.ClientSession.get')
    async def test_get_dex_data_success(self, mock_get):
        """Test framgångsrik DEX-data hämtning."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'pairs': [
                {
                    'dexId': 'uniswap',
                    'priceUsd': '3000',
                    'liquidity': {'usd': 1000000},
                    'volume': {'h24': 500000},
                    'priceChange': {'h24': 2.5}
                }
            ]
        }

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_get.return_value = mock_context

        async with self.dex_integration.dexscreener as api:
            result = await api.get_token_pairs('0x123')

        self.assertTrue(result['success'])
        self.assertIn('dex_data', result)
        self.assertIn('uniswap_v3', result['dex_data'])

class TestErrorHandling(unittest.TestCase):
    """Tester för felhantering."""

    def test_circuit_breaker(self):
        """Test circuit breaker funktion."""
        cb = CircuitBreaker(failure_threshold=3)

        # Bör vara CLOSED initialt
        self.assertTrue(cb.can_execute())

        # Registrera 2 failures - fortfarande CLOSED
        cb.record_failure()
        cb.record_failure()
        self.assertTrue(cb.can_execute())

        # Tredje failure - OPEN
        cb.record_failure()
        self.assertFalse(cb.can_execute())

        # Success - CLOSED
        cb.record_success()
        self.assertTrue(cb.can_execute())

    def test_retry_manager(self):
        """Test retry manager."""
        retry_manager = RetryManager(max_retries=2)

        call_count = 0
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = asyncio.run(retry_manager.execute_with_retry(failing_function))
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)

class TestIntentProcessor(unittest.TestCase):
    """Tester för Intent Processor."""

    def setUp(self):
        self.processor = IntentProcessor()

    def test_wallet_creation_intent(self):
        """Test wallet creation intent recognition."""
        result = asyncio.run(self.processor.process_intent("Skapa en ny wallet"))

        self.assertTrue(result['success'])
        self.assertEqual(result['intent'], 'create_wallet')
        self.assertGreater(result['confidence'], 0.8)

    def test_transaction_intent(self):
        """Test transaction intent recognition."""
        result = asyncio.run(self.processor.process_intent("Skicka 0.01 ETH till 0x123456789"))

        self.assertTrue(result['success'])
        self.assertEqual(result['intent'], 'send_transaction')
        self.assertIn('amount', result['fields'])
        self.assertIn('to_address', result['fields'])

    def test_price_check_intent(self):
        """Test price check intent recognition."""
        result = asyncio.run(self.processor.process_intent("Vad kostar bitcoin?"))

        self.assertTrue(result['success'])
        self.assertEqual(result['intent'], 'check_price')
        self.assertEqual(result['fields']['token_id'], 'bitcoin')

class TestNewsIntegration(unittest.TestCase):
    """Tester för nyhetsintegration."""

    def setUp(self):
        self.news_api = NewsAPIIntegration()

    @patch('crypto.core.news_integration.aiohttp.ClientSession.get')
    async def test_get_crypto_news_success(self, mock_get):
        """Test framgångsrik nyhetshämtning."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'articles': [
                {
                    'title': 'Bitcoin surges to new highs',
                    'content': 'Bitcoin reached new all-time highs today...',
                    'url': 'https://example.com/news1',
                    'publishedAt': '2024-01-01T10:00:00Z',
                    'source': {'name': 'CryptoNews'}
                }
            ]
        }

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_get.return_value = mock_context

        async with self.news_api as api:
            articles = await api.get_crypto_news()

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], 'Bitcoin surges to new highs')
        self.assertEqual(articles[0]['sentiment'], 'positive')

class TestHistoricalDataProvider(unittest.TestCase):
    """Tester för historisk data provider."""

    def setUp(self):
        self.provider = HistoricalDataProvider()

    @patch('crypto.core.news_integration.requests.get')
    def test_get_real_base_prices(self, mock_get):
        """Test hämtning av verkliga baspriser."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'bitcoin': {'usd': 50000, 'usd_24h_vol': 1000000}
        }
        mock_get.return_value = mock_response

        base_prices = self.provider._get_real_base_prices('BTC')

        self.assertEqual(base_prices['BTC'], 50000)
        self.assertEqual(base_prices['BTC_volume'], 1000000)

class IntegrationTest(unittest.TestCase):
    """Integrationstester för hela systemet."""

    def setUp(self):
        self.market_analyzer = MarketAnalyzer()
        self.signal_generator = TradingSignalGenerator(self.market_analyzer)

    @patch('crypto.core.analytics.requests.get')
    async def test_full_signal_generation_flow(self, mock_get):
        """Test komplett signalgenereringsflöde."""
        # Mock alla API-calls
        mock_response = Mock()
        mock_response.json.side_effect = [
            # CoinGecko price
            {'bitcoin': {'usd': 50000, 'usd_24h_change': 5.2}},
            # CoinGecko market chart
            {'prices': [[1640995200000, 47000]], 'total_volumes': [[1640995200000, 1000000]]}
        ]
        mock_get.return_value = mock_response

        # Generera signal
        result = await self.signal_generator.generate_signal('bitcoin', use_llm=False)

        self.assertTrue(result['success'])
        self.assertIn('signal', result)
        self.assertIn('confidence', result)
        self.assertIn('market_data', result)

class PerformanceTest(unittest.TestCase):
    """Prestandatester."""

    def test_signal_generation_performance(self):
        """Test prestanda för signalgenerering."""
        import time

        analyzer = MarketAnalyzer()
        signal_generator = TradingSignalGenerator(analyzer)

        start_time = time.time()

        # Kör flera signalgenereringar
        async def run_multiple_signals():
            tasks = []
            for i in range(10):
                tasks.append(signal_generator.generate_signal('bitcoin', use_llm=False))
            return await asyncio.gather(*tasks)

        results = asyncio.run(run_multiple_signals())
        end_time = time.time()

        total_time = end_time - start_time

        # Alla ska lyckas (även om API misslyckas, ska fallback fungera)
        successful_results = [r for r in results if r['success']]
        self.assertGreater(len(successful_results), 0)

        # Prestandakrav: Max 30 sekunder för 10 samtidiga requests
        self.assertLess(total_time, 30.0)

if __name__ == '__main__':
    # Kör testerna
    unittest.main(verbosity=2)