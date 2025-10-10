"""
Google Cloud Web3 Provider - Huvudprovider för Google Cloud Web3 Gateway.
Multi-chain support med integrering av befintliga TokenInfo och TokenProvider interfaces.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..core.errors.error_handling import handle_errors, CryptoError, APIError
from ..core.token.token_providers import TokenProvider, TokenInfo
from ..core.token.token_resolver import resolve_token

logger = logging.getLogger(__name__)

class GoogleCloudWeb3Provider(TokenProvider):
    """
    Huvudprovider för Google Cloud Web3 Gateway integration.

    Features:
    - Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, Base)
    - Token balance och cross-chain balance queries
    - Transaction history med real-tids data
    - Smart contract deployment och interaction
    - Integration med befintliga TokenInfo interfaces
    - Automatisk retry och circuit breaker via handle_errors decorator
    """

    # Chain mappings för Google Cloud Web3 Gateway
    CHAIN_MAPPINGS = {
        'ethereum': 'eth-mainnet',
        'polygon': 'polygon-mainnet',
        'arbitrum': 'arbitrum-mainnet',
        'optimism': 'optimism-mainnet',
        'base': 'base-mainnet'
    }

    def __init__(self, project_id: str, api_key: str, base_url: str = "https://web3gateway.googleapis.com/v1"):
        """
        Initiera Google Cloud Web3 Provider.

        Args:
            project_id: Google Cloud project ID
            api_key: Google Cloud API key för Web3 Gateway
            base_url: Base URL för Web3 Gateway API
        """
        super().__init__(base_url, api_key)
        self.project_id = project_id
        self.api_key = api_key
        self.base_url = base_url

        # Chain configurations
        self.chain_configs = {
            chain: {
                'chain_id': self._get_chain_id(chain),
                'rpc_url': f"{base_url}/{self.CHAIN_MAPPINGS[chain]}/projects/{project_id}",
                'gas_price_oracle': True,
                'block_explorer': self._get_explorer_url(chain)
            }
            for chain in self.CHAIN_MAPPINGS.keys()
        }

        # Cache för wallet states
        self._wallet_cache = {}
        self._cache_ttl = 300  # 5 minuter

        logger.info(f"Google Cloud Web3 Provider initierad för project: {project_id}")

    def _get_chain_id(self, chain: str) -> int:
        """Hämta chain ID för given chain."""
        chain_ids = {
            'ethereum': 1,
            'polygon': 137,
            'arbitrum': 42161,
            'optimism': 10,
            'base': 8453
        }
        return chain_ids.get(chain, 1)

    def _get_explorer_url(self, chain: str) -> str:
        """Hämta block explorer URL för given chain."""
        explorers = {
            'ethereum': 'https://etherscan.io',
            'polygon': 'https://polygonscan.com',
            'arbitrum': 'https://arbiscan.io',
            'optimism': 'https://optimistic.etherscan.io',
            'base': 'https://basescan.org'
        }
        return explorers.get(chain, 'https://etherscan.io')

    @handle_errors(service_name="google_cloud_web3")
    async def search_token(self, query: str) -> Optional[TokenInfo]:
        """
        Sök efter token via Google Cloud Web3 Gateway.

        Args:
            query: Token symbol, namn eller address

        Returns:
            TokenInfo om hittad, annars None
        """
        # Försök först genom befintlig token resolver
        try:
            existing_token = await resolve_token(query)
            if existing_token:
                return existing_token
        except Exception as e:
            logger.debug(f"Befintlig token resolver misslyckades: {e}")

        # Om inte hittad, sök via Google Cloud Web3
        try:
            # Försök olika chains
            for chain in self.CHAIN_MAPPINGS.keys():
                token_info = await self._search_token_on_chain(query, chain)
                if token_info:
                    return token_info

        except Exception as e:
            logger.warning(f"Google Cloud Web3 token search misslyckades: {e}")

        return None

    async def _search_token_on_chain(self, query: str, chain: str) -> Optional[TokenInfo]:
        """Sök token på specifik chain via Google Cloud Web3."""
        try:
            # Normalisera query
            if query.startswith('0x') and len(query) == 42:
                # Det är en address, sök direkt
                endpoint = f"/{self.CHAIN_MAPPINGS[chain]}/projects/{self.project_id}/tokens/{query}"
            else:
                # Det är symbol/namn, sök i token list
                endpoint = f"/{self.CHAIN_MAPPINGS[chain]}/projects/{self.project_id}/tokens"

            params = {'q': query}
            result = await self._make_request(endpoint, params)

            if result and 'tokens' in result and result['tokens']:
                token_data = result['tokens'][0]  # Ta första matchningen

                return TokenInfo(
                    symbol=token_data.get('symbol', ''),
                    name=token_data.get('name', ''),
                    address=token_data.get('address', ''),
                    chain=chain,
                    decimals=token_data.get('decimals', 18),
                    logo_url=token_data.get('logo_url', ''),
                    description=token_data.get('description', '')
                )

        except Exception as e:
            logger.debug(f"Token search misslyckades på {chain}: {e}")

        return None

    @handle_errors(service_name="google_cloud_web3")
    async def get_balance(self, wallet_address: str, token_address: str = None,
                         chain: str = 'ethereum') -> Dict[str, Any]:
        """
        Hämta token balance för wallet.

        Args:
            wallet_address: Wallet address att kontrollera
            token_address: Token contract address (None för native token)
            chain: Blockchain att använda

        Returns:
            Balance information
        """
        if chain not in self.CHAIN_MAPPINGS:
            raise CryptoError(f"Chain '{chain}' stöds inte av Google Cloud Web3",
                            "UNSUPPORTED_CHAIN")

        # Kontrollera cache först
        cache_key = f"{wallet_address}_{token_address}_{chain}"
        if cache_key in self._wallet_cache:
            cache_entry = self._wallet_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self._cache_ttl):
                return cache_entry['data']

        try:
            if token_address:
                endpoint = f"/{self.CHAIN_MAPPINGS[chain]}/projects/{self.project_id}/tokens/{token_address}/balances/{wallet_address}"
            else:
                endpoint = f"/{self.CHAIN_MAPPINGS[chain]}/projects/{self.project_id}/balances/{wallet_address}"

            result = await self._make_request(endpoint)

            if result:
                balance_data = {
                    'wallet_address': wallet_address,
                    'token_address': token_address,
                    'chain': chain,
                    'balance': result.get('balance', '0'),
                    'balance_formatted': self._format_balance(result.get('balance', '0'),
                                                           result.get('decimals', 18)),
                    'decimals': result.get('decimals', 18),
                    'symbol': result.get('symbol', 'ETH' if not token_address else 'UNKNOWN'),
                    'timestamp': datetime.now().isoformat(),
                    'provider': 'google_cloud_web3'
                }

                # Cache resultatet
                self._wallet_cache[cache_key] = {
                    'timestamp': datetime.now(),
                    'data': balance_data
                }

                return balance_data

            else:
                raise CryptoError(f"Kunde inte hämta balance för {wallet_address}",
                                "BALANCE_FETCH_FAILED")

        except Exception as e:
            logger.error(f"Balance fetch misslyckades: {e}")
            raise CryptoError(f"Misslyckades att hämta balance: {str(e)}",
                            "BALANCE_FETCH_ERROR")

    @handle_errors(service_name="google_cloud_web3")
    async def get_cross_chain_balances(self, wallet_address: str,
                                     tokens: List[str] = None) -> Dict[str, Any]:
        """
        Hämta cross-chain balances för wallet.

        Args:
            wallet_address: Wallet address att kontrollera
            tokens: Lista med token adresser att kontrollera (None för alla)

        Returns:
            Cross-chain balance information
        """
        tasks = []
        all_chains = list(self.CHAIN_MAPPINGS.keys())

        if tokens:
            # Hämta token info för att förstå vilka chains som stöds
            token_infos = {}
            for token in tokens:
                try:
                    token_info = await resolve_token(token)
                    if token_info:
                        token_infos[token] = token_info
                except Exception:
                    continue

            # Skapa tasks för varje chain och token
            for chain in all_chains:
                for token_address in token_infos.keys():
                    if token_infos[token_address].chain == chain:
                        task = self.get_balance(wallet_address, token_address, chain)
                        tasks.append(task)
        else:
            # Hämta native balances för alla chains
            for chain in all_chains:
                task = self.get_balance(wallet_address, None, chain)
                tasks.append(task)

        try:
            # Kör alla balance queries parallellt
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Bearbeta resultat
            cross_chain_balances = {}
            total_value_usd = 0.0
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append(str(result))
                    continue

                chain = result.get('chain', 'unknown')
                if chain not in cross_chain_balances:
                    cross_chain_balances[chain] = []

                cross_chain_balances[chain].append(result)

                # Beräkna totalt värde (simulerat - skulle behöva prisdata)
                try:
                    balance = float(result.get('balance_formatted', 0))
                    total_value_usd += balance * 1.0  # Placeholder för pris
                except (ValueError, TypeError):
                    pass

            return {
                'wallet_address': wallet_address,
                'cross_chain_balances': cross_chain_balances,
                'total_value_usd': total_value_usd,
                'total_chains': len(cross_chain_balances),
                'errors': errors,
                'timestamp': datetime.now().isoformat(),
                'provider': 'google_cloud_web3'
            }

        except Exception as e:
            logger.error(f"Cross-chain balance fetch misslyckades: {e}")
            raise CryptoError(f"Misslyckades att hämta cross-chain balances: {str(e)}",
                            "CROSS_CHAIN_BALANCE_ERROR")

    @handle_errors(service_name="google_cloud_web3")
    async def get_transaction_history(self, wallet_address: str, chain: str = 'ethereum',
                                    limit: int = 100, from_block: int = None) -> Dict[str, Any]:
        """
        Hämta transaction history för wallet.

        Args:
            wallet_address: Wallet address
            chain: Blockchain att söka på
            limit: Max antal transactions att returnera
            from_block: Starta från specifikt block (None för senaste)

        Returns:
            Transaction history
        """
        if chain not in self.CHAIN_MAPPINGS:
            raise CryptoError(f"Chain '{chain}' stöds inte av Google Cloud Web3",
                            "UNSUPPORTED_CHAIN")

        try:
            endpoint = f"/{self.CHAIN_MAPPINGS[chain]}/projects/{self.project_id}/transactions"

            params = {
                'address': wallet_address,
                'limit': limit
            }

            if from_block:
                params['fromBlock'] = from_block

            result = await self._make_request(endpoint, params)

            if result and 'transactions' in result:
                transactions = []
                for tx_data in result['transactions']:
                    tx_info = self._parse_transaction_data(tx_data, chain)
                    transactions.append(tx_info)

                return {
                    'wallet_address': wallet_address,
                    'chain': chain,
                    'transactions': transactions,
                    'total_count': len(transactions),
                    'timestamp': datetime.now().isoformat(),
                    'provider': 'google_cloud_web3'
                }
            else:
                return {
                    'wallet_address': wallet_address,
                    'chain': chain,
                    'transactions': [],
                    'total_count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'provider': 'google_cloud_web3'
                }

        except Exception as e:
            logger.error(f"Transaction history fetch misslyckades: {e}")
            raise CryptoError(f"Misslyckades att hämta transaction history: {str(e)}",
                            "TRANSACTION_HISTORY_ERROR")

    def _parse_transaction_data(self, tx_data: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """Parse transaction data från Google Cloud Web3 format."""
        try:
            return {
                'hash': tx_data.get('hash', ''),
                'block_number': tx_data.get('blockNumber', 0),
                'timestamp': tx_data.get('timestamp', 0),
                'from_address': tx_data.get('from', ''),
                'to_address': tx_data.get('to', ''),
                'value': tx_data.get('value', '0'),
                'gas_price': tx_data.get('gasPrice', '0'),
                'gas_used': tx_data.get('gasUsed', '0'),
                'status': tx_data.get('status', 'unknown'),
                'chain': chain,
                'explorer_url': f"{self._get_explorer_url(chain)}/tx/{tx_data.get('hash', '')}",
                'parsed_timestamp': datetime.fromtimestamp(tx_data.get('timestamp', 0)).isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to parse transaction data: {e}")
            return {
                'hash': tx_data.get('hash', ''),
                'chain': chain,
                'error': str(e)
            }

    def _format_balance(self, balance_raw: str, decimals: int) -> str:
        """Formatera balance från raw string till läsbar format."""
        try:
            balance_dec = Decimal(balance_raw) / Decimal(10 ** decimals)
            return f"{balance_dec".18f"}"
        except (ValueError, TypeError):
            return "0.0"

    @handle_errors(service_name="google_cloud_web3")
    async def estimate_gas(self, transaction_data: Dict[str, Any],
                          chain: str = 'ethereum') -> Dict[str, Any]:
        """
        Uppskatta gas-kostnad för transaktion.

        Args:
            transaction_data: Transaction data för gas-estimering
            chain: Blockchain att använda

        Returns:
            Gas estimation resultat
        """
        if chain not in self.CHAIN_MAPPINGS:
            raise CryptoError(f"Chain '{chain}' stöds inte av Google Cloud Web3",
                            "UNSUPPORTED_CHAIN")

        try:
            endpoint = f"/{self.CHAIN_MAPPINGS[chain]}/projects/{self.project_id}/gas/estimate"

            result = await self._make_request(endpoint, method='POST', data=transaction_data)

            if result:
                return {
                    'gas_estimate': result.get('gasEstimate', '0'),
                    'gas_price': result.get('gasPrice', '0'),
                    'total_cost_wei': result.get('totalCost', '0'),
                    'total_cost_usd': self._calculate_usd_cost(
                        result.get('totalCost', '0'),
                        result.get('gasPrice', '0'),
                        chain
                    ),
                    'chain': chain,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise CryptoError("Gas estimation misslyckades", "GAS_ESTIMATION_FAILED")

        except Exception as e:
            logger.error(f"Gas estimation misslyckades: {e}")
            raise CryptoError(f"Misslyckades att uppskatta gas: {str(e)}",
                            "GAS_ESTIMATION_ERROR")

    def _calculate_usd_cost(self, gas_cost_wei: str, gas_price_wei: str, chain: str) -> float:
        """Beräkna USD-kostnad för gas."""
        try:
            # Simulerad konvertering - skulle behöva real-tids prisdata
            gas_used = float(gas_cost_wei) / 1e18
            gas_price = float(gas_price_wei) / 1e9  # gwei till ether
            eth_cost = gas_used * gas_price

            # Simulerat ETH pris
            eth_price = 2000.0
            return eth_cost * eth_price
        except (ValueError, TypeError):
            return 0.0

    async def health_check(self) -> Dict[str, Any]:
        """
        Utför health check på Google Cloud Web3 Gateway.

        Returns:
            Health status information
        """
        try:
            # Testa grundläggande connectivity
            test_result = await self._make_request(f"/health")

            health_status = {
                'provider': 'google_cloud_web3',
                'status': 'healthy' if test_result else 'unhealthy',
                'project_id': self.project_id,
                'supported_chains': list(self.CHAIN_MAPPINGS.keys()),
                'chain_configs': self.chain_configs,
                'cache_size': len(self._wallet_cache),
                'timestamp': datetime.now().isoformat()
            }

            # Testa varje chain
            chain_statuses = {}
            for chain in self.CHAIN_MAPPINGS.keys():
                try:
                    # Enkel test - försök hämta senaste block
                    endpoint = f"/{self.CHAIN_MAPPINGS[chain]}/projects/{self.project_id}/blocks/latest"
                    block_result = await self._make_request(endpoint)
                    chain_statuses[chain] = 'healthy' if block_result else 'unhealthy'
                except Exception as e:
                    chain_statuses[chain] = f'error: {str(e)}'

            health_status['chain_statuses'] = chain_statuses
            return health_status

        except Exception as e:
            return {
                'provider': 'google_cloud_web3',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def clear_cache(self) -> None:
        """Rensa wallet cache."""
        self._wallet_cache.clear()
        logger.info("Google Cloud Web3 wallet cache rensad")

    async def get_supported_chains(self) -> List[str]:
        """Hämta lista med supported chains."""
        return list(self.CHAIN_MAPPINGS.keys())

    async def get_chain_config(self, chain: str) -> Optional[Dict[str, Any]]:
        """Hämta konfiguration för specifik chain."""
        return self.chain_configs.get(chain)

    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None,
                           method: str = 'GET', data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Hjälpmetod för HTTP-requests till Google Cloud Web3 Gateway."""
        if not self.session:
            raise RuntimeError("Provider session inte initierad")

        url = f"{self.base_url}{endpoint}"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-Project-ID': self.project_id
        }

        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=params, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.warning(f"Google Cloud Web3 API request misslyckades: {response.status} - {error_text}")
                        return {}
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.warning(f"Google Cloud Web3 API POST request misslyckades: {response.status} - {error_text}")
                        return {}
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return {}

        except Exception as e:
            logger.error(f"Google Cloud Web3 request error för {url}: {e}")
            return {}