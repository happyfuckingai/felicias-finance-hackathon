"""
Tester för Uniswap V3 integration.
"""
import unittest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import sys
import os

# Lägg till parent directory för imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.uniswap_v3_trader import UniswapV3Trader


class TestUniswapV3Trader(unittest.IsolatedAsyncioTestCase):
    """Testfall för UniswapV3Trader."""

    def setUp(self):
        """Setup för varje test."""
        # Mock Web3 provider
        self.mock_w3 = Mock()
        self.mock_w3.eth.get_block.return_value = {'timestamp': 1000000000}
        self.mock_w3.eth.get_transaction_count.return_value = 1
        self.mock_w3.eth.gas_price = 20000000000  # 20 gwei
        self.mock_w3.eth.wait_for_transaction_receipt = AsyncMock()
        self.mock_w3.eth.send_raw_transaction = Mock(return_value=b'tx_hash_123')
        self.mock_w3.eth.account.sign_transaction = Mock()
        self.mock_w3.eth.account.sign_transaction.return_value.rawTransaction = b'signed_tx'
        self.mock_w3.to_wei = Mock(side_effect=lambda x, unit: x * (10 ** 18) if unit == 'ether' else x)

        # Mock contracts
        self.mock_router = Mock()
        self.mock_quoter = Mock()

        self.mock_w3.eth.contract = Mock(side_effect=self._mock_contract)

        # Test private key (använd aldrig i produktion!)
        self.test_private_key = "0x" + "1" * 64  # Fake private key för test

    def _mock_contract(self, address=None, abi=None):
        """Mock contract factory."""
        mock_contract = Mock()
        mock_contract.functions = Mock()

        if "quoter" in str(abi) or "Quoter" in str(abi):
            # Return quoter contract
            mock_contract.functions.quoteExactInputSingle = Mock()
            mock_quote_result = AsyncMock(return_value=1000000000000000000)  # 1 ETH worth
            mock_contract.functions.quoteExactInputSingle.return_value.call = mock_quote_result
            return mock_contract
        else:
            # Return router contract
            mock_contract.functions.exactInputSingle = Mock()
            mock_swap_result = AsyncMock(return_value=b'amount_out_data')
            mock_contract.functions.exactInputSingle.return_value.build_transaction = Mock(return_value={
                'from': '0x123',
                'to': '0x456',
                'gas': 300000,
                'gasPrice': 20000000000,
                'nonce': 1,
                'data': '0x123'
            })
            return mock_contract

    async def test_initialization(self):
        """Test att UniswapV3Trader initieras korrekt."""
        trader = UniswapV3Trader(self.mock_w3, self.test_private_key)

        self.assertIsNotNone(trader.router)
        self.assertIsNotNone(trader.quoter)
        self.assertEqual(trader.account.address, '0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf')  # Expected address för test key

    async def test_get_quote_success(self):
        """Test att quote hämtas framgångsrikt."""
        trader = UniswapV3Trader(self.mock_w3, self.test_private_key)

        quote = await trader.get_quote(
            token_in="0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5",  # USDC
            token_out="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            amount_in=1000000  # 1 USDC (6 decimals)
        )

        self.assertTrue(quote['success'])
        self.assertEqual(quote['amount_in'], 1000000)
        self.assertEqual(quote['token_in'], "0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5")
        self.assertEqual(quote['token_out'], "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    async def test_get_quote_failure(self):
        """Test quote failure hantering."""
        trader = UniswapV3Trader(self.mock_w3, self.test_private_key)

        # Mock quoter att kasta exception
        trader.quoter.functions.quoteExactInputSingle.return_value.call = AsyncMock(side_effect=Exception("Quote failed"))

        quote = await trader.get_quote(
            token_in="0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5",
            token_out="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            amount_in=1000000
        )

        self.assertIsNone(quote)

    async def test_swap_exact_input_single(self):
        """Test single-hop swap."""
        trader = UniswapV3Trader(self.mock_w3, self.test_private_key)

        # Mock token contract för allowance check
        mock_token_contract = Mock()
        mock_token_contract.functions.allowance.return_value.call = AsyncMock(return_value=0)
        mock_token_contract.functions.approve.return_value.build_transaction = Mock(return_value={
            'from': trader.account.address,
            'to': '0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5',
            'gas': 100000,
            'gasPrice': 20000000000,
            'nonce': 1,
            'data': '0xapprove'
        })
        trader._get_token_contract = Mock(return_value=mock_token_contract)

        result = await trader.swap_exact_input_single(
            token_in="0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5",
            token_out="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            amount_in=1000000,
            amount_out_min=900000,
            fee=3000
        )

        self.assertTrue(result['success'])
        self.assertIn('transaction_hash', result)
        self.assertIn('gas_used', result)

    async def test_swap_tokens_integration(self):
        """Test komplett swap_tokens funktion."""
        trader = UniswapV3Trader(self.mock_w3, self.test_private_key)

        # Setup mocks
        trader.get_quote = AsyncMock(return_value={
            'success': True,
            'amount_out': 900000000000000000,  # 0.9 ETH
            'amount_in': 1000000,
            'price_impact': 0.001
        })

        trader.swap_exact_input_single = AsyncMock(return_value={
            'success': True,
            'transaction_hash': '0x123456789',
            'gas_used': 150000,
            'amount_out': 850000000000000000  # 0.85 ETH (5% slippage)
        })

        result = await trader.swap_tokens(
            token_in="0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5",
            token_out="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            amount_in=1000000,
            max_slippage_percent=10.0
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_hash'], '0x123456789')
        self.assertIn('expected_amount_out', result)
        self.assertIn('actual_slippage', result)

    async def test_get_token_balance(self):
        """Test token balance hämtning."""
        trader = UniswapV3Trader(self.mock_w3, self.test_private_key)

        # Mock ETH balance
        self.mock_w3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH

        balance = await trader.get_token_balance("0x0000000000000000000000000000000000000000")
        self.assertEqual(balance, 1000000000000000000)

        # Mock ERC20 balance
        mock_token_contract = Mock()
        mock_token_contract.functions.balanceOf.return_value.call = AsyncMock(return_value=5000000)
        trader._get_token_contract = Mock(return_value=mock_token_contract)

        balance = await trader.get_token_balance("0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5")
        self.assertEqual(balance, 5000000)


class TestDexIntegration(unittest.IsolatedAsyncioTestCase):
    """Testfall för DEX integration."""

    def setUp(self):
        """Setup för DEX integration tester."""
        self.mock_w3 = Mock()
        self.test_private_key = "0x" + "1" * 64

    async def test_real_dex_initialization_with_trader(self):
        """Test att RealDexIntegration initieras med Uniswap trader."""
        from crypto.core.dex_integration import RealDexIntegration

        dex_integration = RealDexIntegration(self.mock_w3, self.test_private_key)
        self.assertIsNotNone(dex_integration.uniswap_trader)

    async def test_real_dex_initialization_without_trader(self):
        """Test att RealDexIntegration fungerar utan trader."""
        from crypto.core.dex_integration import RealDexIntegration

        dex_integration = RealDexIntegration()
        self.assertIsNone(dex_integration.uniswap_trader)

    @patch('crypto.core.dex_integration.aiohttp.ClientSession')
    async def test_get_dex_data_from_api(self, mock_session):
        """Test hämtning av DEX data från API."""
        from crypto.core.dex_integration import RealDexIntegration

        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'pairs': [{
                'dexId': 'uniswap',
                'priceUsd': '3000',
                'liquidity': {'usd': 5000000},
                'volume': {'h24': 1000000},
                'priceChange': {'h24': 2.5},
                'pairAddress': '0x123',
                'baseToken': {'symbol': 'WETH'},
                'quoteToken': {'symbol': 'USDC'}
            }]
        })

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        dex_integration = RealDexIntegration()
        result = await dex_integration.get_dex_data("WETH", "ethereum")

        self.assertTrue(result['success'])
        self.assertIn('uniswap_v3', result['dex_data'])
        self.assertEqual(result['best_price'], 3000)


if __name__ == '__main__':
    unittest.main()