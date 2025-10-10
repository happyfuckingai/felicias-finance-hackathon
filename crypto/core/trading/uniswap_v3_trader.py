"""
Uniswap V3 Integration för automatisk trading.
Implementerar swap-funktionalitet med Uniswap V3 router.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from web3 import Web3
from eth_account import Account
import asyncio
from decimal import Decimal

logger = logging.getLogger(__name__)

class UniswapV3Trader:
    """
    Uniswap V3 trader för automatiska token-swaps.
    Använder Uniswap V3 router för optimala vägar och slippage-skydd.
    """

    # Uniswap V3 Router address på Ethereum mainnet
    UNISWAP_V3_ROUTER = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
    # Uniswap V3 Factory address
    UNISWAP_V3_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    # Quoter contract för prisberäkningar
    UNISWAP_V3_QUOTER = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"

    # Standard tokens
    WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    USDC_ADDRESS = "0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5"

    # Router ABI (minimal för swap-funktioner)
    ROUTER_ABI = [
        {
            "inputs": [
                {
                    "components": [
                        {"internalType": "address", "name": "tokenIn", "type": "address"},
                        {"internalType": "address", "name": "tokenOut", "type": "address"},
                        {"internalType": "uint24", "name": "fee", "type": "uint24"},
                        {"internalType": "address", "name": "recipient", "type": "address"},
                        {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                        {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                    ],
                    "internalType": "struct ISwapRouter.ExactInputSingleParams",
                    "name": "params",
                    "type": "tuple"
                }
            ],
            "name": "exactInputSingle",
            "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [
                {
                    "components": [
                        {"internalType": "bytes", "name": "path", "type": "bytes"},
                        {"internalType": "address", "name": "recipient", "type": "address"},
                        {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}
                    ],
                    "internalType": "struct ISwapRouter.ExactInputParams",
                    "name": "params",
                    "type": "tuple"
                }
            ],
            "name": "exactInput",
            "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ]

    # Quoter ABI för prisberäkningar
    QUOTER_ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "tokenIn", "type": "address"},
                {"internalType": "address", "name": "tokenOut", "type": "address"},
                {"internalType": "uint24", "name": "fee", "type": "uint24"},
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
            ],
            "name": "quoteExactInputSingle",
            "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    # ERC20 ABI för approvals
    ERC20_ABI = [
        {
            "constant": False,
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]

    def __init__(self, web3_provider: Web3, private_key: str):
        """
        Initiera Uniswap V3 trader.

        Args:
            web3_provider: Web3 provider instance
            private_key: Private key för trading wallet
        """
        self.w3 = web3_provider
        self.account = Account.from_key(private_key)
        self.w3.eth.default_account = self.account.address

        # Initiera contracts
        self.router = self.w3.eth.contract(
            address=self.UNISWAP_V3_ROUTER,
            abi=self.ROUTER_ABI
        )
        self.quoter = self.w3.eth.contract(
            address=self.UNISWAP_V3_QUOTER,
            abi=self.QUOTER_ABI
        )

        logger.info(f"UniswapV3Trader initialiserad för {self.account.address}")

    def _get_token_contract(self, token_address: str):
        """Hämta ERC20 contract för given address."""
        return self.w3.eth.contract(address=token_address, abi=self.ERC20_ABI)

    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        fee: int = 3000  # 0.3% standard fee
    ) -> Optional[Dict[str, Any]]:
        """
        Hämta prisquote från Uniswap V3.

        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount in (wei/smallest unit)
            fee: Pool fee tier (500, 3000, 10000)

        Returns:
            Quote information eller None om misslyckad
        """
        try:
            # Anropa quoter contract
            quote_result = await self.quoter.functions.quoteExactInputSingle(
                token_in,
                token_out,
                fee,
                amount_in,
                0  # sqrtPriceLimitX96 = 0 (no limit)
            ).call()

            amount_out = quote_result

            return {
                'amount_out': amount_out,
                'amount_in': amount_in,
                'token_in': token_in,
                'token_out': token_out,
                'fee': fee,
                'price_impact': self._calculate_price_impact(amount_in, amount_out),
                'success': True
            }

        except Exception as e:
            logger.error(f"Quote failed: {e}")
            return None

    def _calculate_price_impact(self, amount_in: int, amount_out: int) -> float:
        """Beräkna uppskattad price impact (enkel approximation)."""
        # Detta är en förenklad beräkning - i praktiken behöver mer komplex logik
        # för att beräkna verklig price impact från pool-state
        return 0.001  # 0.1% placeholder

    def _encode_path(self, tokens: List[str], fees: List[int]) -> bytes:
        """
        Encoda path för multi-hop swaps.

        Args:
            tokens: Lista av token addresses
            fees: Lista av fees mellan tokens

        Returns:
            Encodad path bytes
        """
        if len(tokens) != len(fees) + 1:
            raise ValueError("Invalid path: tokens and fees length mismatch")

        path = b""
        for i, token in enumerate(tokens):
            # Lägg till token address (20 bytes)
            path += bytes.fromhex(token[2:])  # Remove 0x prefix

            # Lägg till fee om inte sista token
            if i < len(fees):
                fee_bytes = fees[i].to_bytes(3, 'big')  # uint24
                path += fee_bytes

        return path

    async def approve_token(
        self,
        token_address: str,
        amount: int,
        gas_price: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Approva router att spendera tokens.

        Args:
            token_address: Token att approva
            amount: Amount att approva
            gas_price: Gas price i wei

        Returns:
            Transaction result
        """
        try:
            token_contract = self._get_token_contract(token_address)

            # Sätt gas price
            if gas_price is None:
                gas_price = self.w3.eth.gas_price

            # Bygg approve transaction
            approve_txn = token_contract.functions.approve(
                self.UNISWAP_V3_ROUTER,
                amount
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })

            # Signera och skicka
            signed_txn = self.w3.eth.account.sign_transaction(approve_txn, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Vänta på receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'gas_used': tx_receipt.gasUsed,
                'token_address': token_address,
                'approved_amount': amount
            }

        except Exception as e:
            logger.error(f"Token approval failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def swap_exact_input_single(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        amount_out_min: int,
        fee: int = 3000,
        deadline: Optional[int] = None,
        gas_price: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Utför single-hop swap på Uniswap V3.

        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount in (wei)
            amount_out_min: Minimum amount out (slippage protection)
            fee: Pool fee tier
            deadline: Transaction deadline
            gas_price: Gas price i wei

        Returns:
            Swap result
        """
        try:
            # Sätt deadline (20 min från nu om inte specifierad)
            if deadline is None:
                deadline = self.w3.eth.get_block('latest')['timestamp'] + 1200

            # Sätt gas price
            if gas_price is None:
                gas_price = self.w3.eth.gas_price

            # Förbered swap params
            swap_params = {
                'tokenIn': token_in,
                'tokenOut': token_out,
                'fee': fee,
                'recipient': self.account.address,
                'deadline': deadline,
                'amountIn': amount_in,
                'amountOutMinimum': amount_out_min,
                'sqrtPriceLimitX96': 0  # No price limit
            }

            # Approva tokens först om nödvändigt
            token_contract = self._get_token_contract(token_in)
            current_allowance = await token_contract.functions.allowance(
                self.account.address,
                self.UNISWAP_V3_ROUTER
            ).call()

            if current_allowance < amount_in:
                approve_result = await self.approve_token(token_in, amount_in, gas_price)
                if not approve_result['success']:
                    return approve_result

            # Bygg swap transaction
            swap_txn = self.router.functions.exactInputSingle(swap_params).build_transaction({
                'from': self.account.address,
                'gas': 300000,  # Uniswap swaps behöver mer gas
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })

            # Signera och skicka
            signed_txn = self.w3.eth.account.sign_transaction(swap_txn, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Vänta på receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            # Hämta amount out från event logs (om möjligt)
            amount_out = 0
            if tx_receipt.logs:
                # Parse Swap event för amount out
                for log in tx_receipt.logs:
                    if len(log['topics']) >= 3:  # Swap event har minst 3 topics
                        try:
                            # Event signature för Swap
                            amount0Out = int(log['data'][2:66], 16)  # amount0Out
                            amount1Out = int(log['data'][66:130], 16)  # amount1Out
                            amount_out = max(amount0Out, amount1Out)
                            break
                        except:
                            continue

            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'gas_used': tx_receipt.gasUsed,
                'token_in': token_in,
                'token_out': token_out,
                'amount_in': amount_in,
                'amount_out': amount_out,
                'amount_out_min': amount_out_min,
                'fee': fee
            }

        except Exception as e:
            logger.error(f"Single-hop swap failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def swap_tokens(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        max_slippage_percent: float = 0.5,
        fee: int = 3000
    ) -> Dict[str, Any]:
        """
        Högnivå funktion för att swappa tokens med automatisk slippage-beräkning.

        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount in (wei)
            max_slippage_percent: Max tillåten slippage i procent
            fee: Pool fee tier

        Returns:
            Swap result
        """
        try:
            # Hämta quote först
            quote = await self.get_quote(token_in, token_out, amount_in, fee)
            if not quote:
                return {
                    'success': False,
                    'error': 'Could not get quote from Uniswap'
                }

            # Beräkna minimum amount out baserat på slippage
            slippage_multiplier = 1 - (max_slippage_percent / 100)
            amount_out_min = int(quote['amount_out'] * slippage_multiplier)

            # Utför swap
            swap_result = await self.swap_exact_input_single(
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                amount_out_min=amount_out_min,
                fee=fee
            )

            # Lägg till quote info till resultatet
            if swap_result['success']:
                swap_result.update({
                    'expected_amount_out': quote['amount_out'],
                    'price_impact': quote['price_impact'],
                    'actual_slippage': ((quote['amount_out'] - swap_result.get('amount_out', 0)) / quote['amount_out']) * 100 if swap_result.get('amount_out') else 0
                })

            return swap_result

        except Exception as e:
            logger.error(f"Token swap failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_token_balance(self, token_address: str) -> int:
        """
        Hämta token balance för trading wallet.

        Args:
            token_address: Token contract address

        Returns:
            Balance i smallest unit
        """
        try:
            if token_address.lower() == "0x0000000000000000000000000000000000000000":  # ETH
                return self.w3.eth.get_balance(self.account.address)

            token_contract = self._get_token_contract(token_address)
            balance = await token_contract.functions.balanceOf(self.account.address).call()
            return balance

        except Exception as e:
            logger.error(f"Failed to get token balance: {e}")
            return 0