"""
Token Providers för Dynamic Token Resolution.
Implementerar providers som hämtar token-information från olika API:er.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import aiohttp
import json

logger = logging.getLogger(__name__)

class TokenInfo:
    """Standardiserad token-information struktur."""

    def __init__(self, symbol: str, name: str, address: str, chain: str, decimals: int = 18,
                 logo_url: str = "", description: str = "", coingecko_id: str = ""):
        self.symbol = symbol.upper()
        self.name = name
        self.address = address.lower()
        self.chain = chain.lower()
        self.decimals = decimals
        self.logo_url = logo_url
        self.description = description
        self.coingecko_id = coingecko_id

    def to_dict(self) -> Dict[str, Any]:
        """Konvertera till dictionary."""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'address': self.address,
            'chain': self.chain,
            'decimals': self.decimals,
            'logo_url': self.logo_url,
            'description': self.description,
            'coingecko_id': self.coingecko_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenInfo':
        """Skapa från dictionary."""
        return cls(
            symbol=data.get('symbol', ''),
            name=data.get('name', ''),
            address=data.get('address', ''),
            chain=data.get('chain', ''),
            decimals=data.get('decimals', 18),
            logo_url=data.get('logo_url', ''),
            description=data.get('description', ''),
            coingecko_id=data.get('coingecko_id', '')
        )

class TokenProvider(ABC):
    """Abstrakt basklass för token providers."""

    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @abstractmethod
    async def search_token(self, query: str) -> Optional[TokenInfo]:
        """
        Sök efter token baserat på symbol, namn eller address.

        Args:
            query: Sökterm (symbol, namn eller address)

        Returns:
            TokenInfo om hittad, annars None
        """
        pass

    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Hjälpmetod för HTTP-requests."""
        if not self.session:
            raise RuntimeError("Provider session not initialized")

        url = f"{self.base_url}{endpoint}"
        headers = {}

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            async with self.session.get(url, params=params, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"API request failed: {response.status} - {url}")
                    return {}
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            return {}

class DexScreenerProvider(TokenProvider):
    """Provider för DexScreener API."""

    def __init__(self):
        super().__init__("https://api.dexscreener.com/latest/dex")

    async def search_token(self, query: str) -> Optional[TokenInfo]:
        """
        Sök token på DexScreener.

        Args:
            query: Token symbol, namn eller address

        Returns:
            TokenInfo eller None
        """
        # Försök först med address lookup
        if self._is_address(query):
            result = await self._make_request(f"/tokens/{query}")
            if result and 'pairs' in result and result['pairs']:
                return self._parse_dexscreener_pair(result['pairs'][0])

        # Försök med search
        result = await self._make_request("/search", {"q": query})
        if result and 'pairs' in result and result['pairs']:
            # Returnera den första matchningen
            return self._parse_dexscreener_pair(result['pairs'][0])

        return None

    def _is_address(self, query: str) -> bool:
        """Kontrollera om query ser ut som en address."""
        return len(query) == 42 and query.startswith('0x')

    def _parse_dexscreener_pair(self, pair_data: Dict[str, Any]) -> Optional[TokenInfo]:
        """Parse DexScreener pair data till TokenInfo."""
        try:
            base_token = pair_data.get('baseToken', {})
            chain = pair_data.get('chainId', 'ethereum')

            # Map chain IDs
            chain_mapping = {
                'ethereum': 'ethereum',
                'bsc': 'bsc',
                'polygon': 'polygon',
                'arbitrum': 'arbitrum',
                'optimism': 'optimism'
            }

            return TokenInfo(
                symbol=base_token.get('symbol', ''),
                name=base_token.get('name', ''),
                address=base_token.get('address', ''),
                chain=chain_mapping.get(chain, chain),
                decimals=18,  # DexScreener ger inte alltid decimals
                logo_url=""  # DexScreener har inte alltid logo
            )
        except Exception as e:
            logger.error(f"Failed to parse DexScreener pair: {e}")
            return None

class OneInchProvider(TokenProvider):
    """Provider för 1inch API."""

    def __init__(self):
        super().__init__("https://api.1inch.dev")

    async def search_token(self, query: str) -> Optional[TokenInfo]:
        """
        Sök token på 1inch.

        Args:
            query: Token symbol eller address

        Returns:
            TokenInfo eller None
        """
        # 1inch kräver API key för många endpoints, men har några fria
        # För enkelhet, använd deras token list endpoint

        # Försök först med Ethereum
        result = await self._make_request("/v5.2/1/tokens")
        if result and 'tokens' in result:
            tokens = result['tokens']

            # Sök efter exakt match på symbol
            query_upper = query.upper()
            for address, token_data in tokens.items():
                if (token_data.get('symbol', '').upper() == query_upper or
                    token_data.get('name', '').upper() == query_upper or
                    address.lower() == query.lower()):
                    return TokenInfo(
                        symbol=token_data.get('symbol', ''),
                        name=token_data.get('name', ''),
                        address=address,
                        chain='ethereum',
                        decimals=token_data.get('decimals', 18),
                        logo_url=token_data.get('logoURI', '')
                    )

        return None

class CoinGeckoProvider(TokenProvider):
    """Provider för CoinGecko API."""

    def __init__(self, api_key: str = None):
        super().__init__("https://api.coingecko.com/api/v3")
        self.api_key = api_key

    async def search_token(self, query: str) -> Optional[TokenInfo]:
        """
        Sök token på CoinGecko.

        Args:
            query: Token ID, symbol eller namn

        Returns:
            TokenInfo eller None
        """
        # Försök först med coin list för att hitta ID
        result = await self._make_request("/coins/list")
        if result:
            # Sök efter match
            query_lower = query.lower()
            for coin in result:
                if (coin.get('id', '').lower() == query_lower or
                    coin.get('symbol', '').lower() == query_lower or
                    coin.get('name', '').lower() == query_lower):

                    # Hämta detaljerad info
                    coin_id = coin['id']
                    details = await self._make_request(f"/coins/{coin_id}")

                    if details:
                        return self._parse_coingecko_coin(details)

        return None

    def _parse_coingecko_coin(self, coin_data: Dict[str, Any]) -> Optional[TokenInfo]:
        """Parse CoinGecko coin data till TokenInfo."""
        try:
            # Hitta kontrakt address (prioritera Ethereum)
            contract_address = ""
            chain = "ethereum"

            if 'platforms' in coin_data and coin_data['platforms']:
                platforms = coin_data['platforms']
                # Prioritera Ethereum
                if 'ethereum' in platforms and platforms['ethereum']:
                    contract_address = platforms['ethereum']
                    chain = 'ethereum'
                elif platforms:  # Ta första tillgängliga
                    first_platform = next(iter(platforms.keys()))
                    if platforms[first_platform]:
                        contract_address = platforms[first_platform]
                        chain = first_platform

            return TokenInfo(
                symbol=coin_data.get('symbol', '').upper(),
                name=coin_data.get('name', ''),
                address=contract_address,
                chain=chain,
                decimals=18,  # CoinGecko ger sällan decimals
                logo_url=coin_data.get('image', {}).get('large', ''),
                description=coin_data.get('description', {}).get('en', ''),
                coingecko_id=coin_data.get('id', '')
            )
        except Exception as e:
            logger.error(f"Failed to parse CoinGecko coin: {e}")
            return None

class FallbackTokenProvider(TokenProvider):
    """Fallback provider med hårdkodade populära tokens."""

    def __init__(self):
        super().__init__("")
        self.fallback_tokens = {
            'eth': TokenInfo('ETH', 'Ethereum', '0x0000000000000000000000000000000000000000', 'ethereum'),
            'btc': TokenInfo('BTC', 'Bitcoin', '', 'bitcoin'),
            'usdc': TokenInfo('USDC', 'USD Coin', '0xA0b86a33E6b5C6973e7fE8C8c4a0b3b0a6b5C8b7', 'ethereum'),
            'usdt': TokenInfo('USDT', 'Tether', '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'ethereum'),
            'dai': TokenInfo('DAI', 'Dai Stablecoin', '0x6B175474E89094C44Da98b954EedeAC495271d0F', 'ethereum'),
            'wbtc': TokenInfo('WBTC', 'Wrapped Bitcoin', '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 'ethereum'),
            'matic': TokenInfo('MATIC', 'Polygon', '0x0000000000000000000000000000000000001010', 'polygon'),
            'bnb': TokenInfo('BNB', 'Binance Coin', '', 'bsc'),
            'ada': TokenInfo('ADA', 'Cardano', '', 'cardano'),
            'sol': TokenInfo('SOL', 'Solana', '', 'solana'),
            'dot': TokenInfo('DOT', 'Polkadot', '', 'polkadot'),
            'avax': TokenInfo('AVAX', 'Avalanche', '', 'avalanche'),
            'luna': TokenInfo('LUNA', 'Terra', '', 'terra'),
            'atom': TokenInfo('ATOM', 'Cosmos', '', 'cosmos'),
            'link': TokenInfo('LINK', 'Chainlink', '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'ethereum'),
            'uni': TokenInfo('UNI', 'Uniswap', '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'ethereum'),
            'aave': TokenInfo('AAVE', 'Aave', '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', 'ethereum'),
            'cake': TokenInfo('CAKE', 'PancakeSwap', '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82', 'bsc'),
            'sushi': TokenInfo('SUSHI', 'SushiSwap', '0x6B3595068778DD592e39A122f4f5a5CF09C90fE2', 'ethereum'),
            'comp': TokenInfo('COMP', 'Compound', '0xc00e94Cb662C3520282E6f5717214004A7f26888', 'ethereum'),
            'yfi': TokenInfo('YFI', 'Yearn Finance', '0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e', 'ethereum'),
            'mkr': TokenInfo('MKR', 'Maker', '0x9f8F72AA9304c8B593d555F12eF6589cC3A579A2', 'ethereum'),
            'snx': TokenInfo('SNX', 'Synthetix', '0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F', 'ethereum'),
            'crv': TokenInfo('CRV', 'Curve DAO Token', '0xD533a949740bb3306d119CC777fa900bA034cd25', 'ethereum'),
            'bal': TokenInfo('BAL', 'Balancer', '0xba100000625a3754423978a60c9317c58a424e3D', 'ethereum'),
            'ren': TokenInfo('REN', 'Ren', '0x408e41876cCCDC0F92210600ef50372656052a38', 'ethereum'),
            'knc': TokenInfo('KNC', 'Kyber Network Crystal', '0xdd974D5C2e2928deA5F71b9825b8b646686BD200', 'ethereum'),
            'zrx': TokenInfo('ZRX', '0x', '0xE41d2489571d322189246DaFA5ebDe1F4699F498', 'ethereum'),
            'bat': TokenInfo('BAT', 'Basic Attention Token', '0x0D8775F648430679A709E98d2b0Cb6250d2887EF', 'ethereum'),
            'omg': TokenInfo('OMG', 'OMG Network', '0xd26114cd6EE289AccF82350c8d8487fedB8A0C07', 'ethereum'),
            'lrc': TokenInfo('LRC', 'Loopring', '0xBBbbCA6A901c926F240b89EacB641d8Aec7AEafD', 'ethereum'),
            'rep': TokenInfo('REP', 'Augur', '0x1985365e9f78359a9B6AD760e32412f4a445E862', 'ethereum'),
            'gnt': TokenInfo('GNT', 'Golem', '0xa74476443119A942dE498590Fe1f2454d7D4aC0d', 'ethereum'),
            'ant': TokenInfo('ANT', 'Aragon', '0x960b236A07cf122663c4303350609A66A7B288C0', 'ethereum'),
            'mln': TokenInfo('MLN', 'Melon', '0xec67005c4E498Ec7f55E092bd1d35cbC47C91892', 'ethereum'),
            'STORJ': TokenInfo('STORJ', 'Storj', '0xB64ef51C888972c908CFacf59B47C1AfBC0Ab8aC', 'ethereum'),
            'pay': TokenInfo('PAY', 'TenX', '0xB97048628DB6B661D4C2aA833e95Dbe1A905B280', 'ethereum'),
            'fun': TokenInfo('FUN', 'FunFair', '0x419D0d8BdD9aF5e606Ae2232ed285Aff190E711b', 'ethereum'),
            'weth': TokenInfo('WETH', 'Wrapped Ether', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'ethereum'),
            'wmatic': TokenInfo('WMATIC', 'Wrapped Matic', '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 'polygon'),
            'wbnb': TokenInfo('WBNB', 'Wrapped BNB', '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', 'bsc'),
            'happy': TokenInfo('HAPPY', 'Happy Token', '0x1234567890123456789012345678901234567890', 'ethereum'),
        }

    async def search_token(self, query: str) -> Optional[TokenInfo]:
        """
        Sök i hårdkodade fallback tokens.

        Args:
            query: Token symbol eller namn

        Returns:
            TokenInfo eller None
        """
        query_lower = query.lower()

        # Exakt match först
        if query_lower in self.fallback_tokens:
            return self.fallback_tokens[query_lower]

        # Partial match
        for key, token in self.fallback_tokens.items():
            if (query_lower in key or
                query_lower in token.symbol.lower() or
                query_lower in token.name.lower()):
                return token

        return None