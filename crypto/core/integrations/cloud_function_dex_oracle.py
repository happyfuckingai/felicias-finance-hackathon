"""
Cloud Function DEX Oracle - Serverless DEX data oracle med real-tids price feeds.
Implementerar Pub/Sub integration för DEX data streaming.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass
from abc import ABC, abstractmethod

from google.cloud import functions_v1
from google.cloud import pubsub_v1
from google.cloud import firestore
from google.cloud import bigquery
import aiohttp
import websockets

from ..errors.error_handling import handle_errors, CryptoError, APIError, NetworkError
from ..token.token_providers import TokenInfo
from .google_cloud_web3_bridge import get_unified_bridge

logger = logging.getLogger(__name__)

@dataclass
class DEXPriceData:
    """DEX price data structure."""
    token_symbol: str
    token_address: str
    dex_name: str
    price: float
    volume_24h: float
    price_change_24h: float
    liquidity: float
    pair_address: str
    timestamp: datetime
    confidence: float
    source: str

@dataclass
class OracleConfig:
    """Oracle konfiguration."""
    project_id: str
    region: str = "us-central1"
    update_interval: int = 60  # seconds
    max_retries: int = 3
    timeout: int = 30
    enable_streaming: bool = True
    enable_firestore_cache: bool = True
    enable_bigquery_export: bool = True

class DEXDataSource(ABC):
    """Abstrakt basklass för DEX data sources."""

    def __init__(self, name: str, base_url: str, api_key: str = None):
        self.name = name
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
    async def get_price_data(self, token_address: str, base_token: str = "ETH") -> Optional[DEXPriceData]:
        """Hämta price data från DEX."""
        pass

    @abstractmethod
    async def get_supported_pairs(self) -> List[str]:
        """Hämta lista med supported pairs."""
        pass

class UniswapV3Source(DEXDataSource):
    """Uniswap V3 data source."""

    def __init__(self, api_key: str = None):
        super().__init__("uniswap_v3", "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3")
        self.api_key = api_key

    async def get_price_data(self, token_address: str, base_token: str = "ETH") -> Optional[DEXPriceData]:
        """Hämta price data från Uniswap V3."""
        try:
            query = """
            {
                token(id: "%s") {
                    id
                    symbol
                    name
                    derivedETH
                    volumeUSD
                    feesUSD
                    poolCount
                }
                bundle(id: "1") {
                    ethPriceUSD
                }
            }
            """ % token_address.lower()

            async with self.session.post(
                self.base_url,
                json={'query': query},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_uniswap_data(data, token_address)
                else:
                    logger.warning(f"Uniswap V3 API error: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Uniswap V3 data fetch failed: {e}")
            return None

    def _parse_uniswap_data(self, data: Dict[str, Any], token_address: str) -> Optional[DEXPriceData]:
        """Parse Uniswap V3 data."""
        try:
            token = data.get('data', {}).get('token', {})
            bundle = data.get('data', {}).get('bundle', {})

            if not token or not bundle:
                return None

            eth_price_usd = float(bundle.get('ethPriceUSD', 0))
            token_price_eth = float(token.get('derivedETH', 0))
            price_usd = token_price_eth * eth_price_usd

            return DEXPriceData(
                token_symbol=token.get('symbol', ''),
                token_address=token_address,
                dex_name=self.name,
                price=price_usd,
                volume_24h=float(token.get('volumeUSD', 0)),
                price_change_24h=0,  # Would calculate from historical data
                liquidity=float(token.get('feesUSD', 0)) * 100,  # Approximation
                pair_address=f"{token_address}_WETH",  # Would get actual pair address
                timestamp=datetime.now(),
                confidence=0.9,
                source=self.name
            )
        except Exception as e:
            logger.error(f"Failed to parse Uniswap V3 data: {e}")
            return None

    async def get_supported_pairs(self) -> List[str]:
        """Hämta supported pairs."""
        return ["ETH", "USDC", "USDT", "DAI", "WBTC"]

class DexScreenerSource(DEXDataSource):
    """DexScreener data source."""

    def __init__(self):
        super().__init__("dexscreener", "https://api.dexscreener.com/latest/dex")

    async def get_price_data(self, token_address: str, base_token: str = "ETH") -> Optional[DEXPriceData]:
        """Hämta price data från DexScreener."""
        try:
            async with self.session.get(f"{self.base_url}/tokens/{token_address}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data and 'pairs' in data and data['pairs']:
                        return self._parse_dexscreener_data(data['pairs'][0], token_address)
                return None

        except Exception as e:
            logger.error(f"DexScreener data fetch failed: {e}")
            return None

    def _parse_dexscreener_data(self, pair_data: Dict[str, Any], token_address: str) -> Optional[DEXPriceData]:
        """Parse DexScreener data."""
        try:
            base_token = pair_data.get('baseToken', {})
            price_usd = float(pair_data.get('priceUsd', 0))
            volume_24h = float(pair_data.get('volume', {}).get('h24', 0))
            price_change = float(pair_data.get('priceChange', {}).get('h24', 0))

            return DEXPriceData(
                token_symbol=base_token.get('symbol', ''),
                token_address=token_address,
                dex_name=self.name,
                price=price_usd,
                volume_24h=volume_24h,
                price_change_24h=price_change,
                liquidity=float(pair_data.get('liquidity', {}).get('usd', 0)),
                pair_address=pair_data.get('pairAddress', ''),
                timestamp=datetime.now(),
                confidence=0.8,
                source=self.name
            )
        except Exception as e:
            logger.error(f"Failed to parse DexScreener data: {e}")
            return None

    async def get_supported_pairs(self) -> List[str]:
        """Hämta supported pairs."""
        return ["ETH", "BSC", "POLYGON", "ARBITRUM", "OPTIMISM"]

class CloudFunctionManager:
    """Hantera Cloud Functions för serverless operations."""

    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        self._function_client = functions_v1.CloudFunctionsServiceClient()
        self._functions = {}

    async def initialize(self):
        """Initiera Cloud Function manager."""
        try:
            # List available functions
            parent = f"projects/{self.project_id}/locations/{self.region}"
            functions = self._function_client.list_functions(parent=parent)

            for function in functions:
                self._functions[function.name] = function

            logger.info(f"Cloud Function manager initialized with {len(self._functions)} functions")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Cloud Function manager: {e}")
            return False

    async def invoke_function(self, function_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anropa Cloud Function."""
        try:
            function_path = f"projects/{self.project_id}/locations/{self.region}/functions/{function_name}"

            if function_path not in self._functions:
                raise APIError(f"Function {function_name} not found", "FUNCTION_NOT_FOUND")

            # This would use Cloud Functions API to invoke
            # For now, return mock response
            return {
                'status': 'success',
                'function': function_name,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to invoke function {function_name}: {e}")
            raise APIError(f"Function invocation failed: {str(e)}", "FUNCTION_INVOCATION_ERROR")

class PubSubManager:
    """Hantera Pub/Sub för real-time data streaming."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._publisher = pubsub_v1.PublisherClient()
        self._subscriber = pubsub_v1.SubscriberClient()
        self._subscriptions = {}
        self._topics = {}

    async def initialize(self):
        """Initiera Pub/Sub manager."""
        try:
            logger.info("Pub/Sub manager initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub manager: {e}")
            return False

    async def publish_price_update(self, price_data: DEXPriceData) -> bool:
        """Publicera price update till Pub/Sub."""
        try:
            topic_name = f"crypto-price-updates-{price_data.token_symbol.lower()}"
            topic_path = self._publisher.topic_path(self.project_id, topic_name)

            # Create topic if it doesn't exist
            if topic_path not in self._topics:
                try:
                    topic = self._publisher.create_topic(name=topic_path)
                    self._topics[topic_path] = topic
                except Exception:
                    # Topic might already exist
                    pass

            # Publish message
            message_data = json.dumps({
                'token_symbol': price_data.token_symbol,
                'token_address': price_data.token_address,
                'price': price_data.price,
                'volume_24h': price_data.volume_24h,
                'price_change_24h': price_data.price_change_24h,
                'dex_name': price_data.dex_name,
                'timestamp': price_data.timestamp.isoformat(),
                'source': price_data.source
            }).encode('utf-8')

            future = self._publisher.publish(topic_path, message_data)
            result = future.result()

            logger.info(f"Price update published for {price_data.token_symbol}: {price_data.price}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish price update: {e}")
            return False

    async def subscribe_to_updates(self, token_symbol: str, callback: Callable[[DEXPriceData], None]) -> str:
        """Prenumerera på price updates för token."""
        try:
            topic_name = f"crypto-price-updates-{token_symbol.lower()}"
            subscription_name = f"price-updates-{token_symbol.lower()}-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
            subscription_path = self._subscriber.subscription_path(self.project_id, subscription_name)

            # Create subscription
            topic_path = self._publisher.topic_path(self.project_id, topic_name)
            try:
                subscription = self._subscriber.create_subscription(
                    name=subscription_path,
                    topic=topic_path
                )
            except Exception:
                # Subscription might already exist
                pass

            # Start message processing
            asyncio.create_task(self._process_messages(subscription_path, callback))

            return subscription_name

        except Exception as e:
            logger.error(f"Failed to subscribe to updates: {e}")
            return ""

    async def _process_messages(self, subscription_path: str, callback: Callable[[DEXPriceData], None]):
        """Processa incoming messages."""
        try:
            def message_callback(message):
                try:
                    data = json.loads(message.data.decode('utf-8'))
                    price_data = DEXPriceData(
                        token_symbol=data['token_symbol'],
                        token_address=data['token_address'],
                        dex_name=data.get('dex_name', 'unknown'),
                        price=data['price'],
                        volume_24h=data['volume_24h'],
                        price_change_24h=data['price_change_24h'],
                        liquidity=0,  # Not in streaming data
                        pair_address='',
                        timestamp=datetime.fromisoformat(data['timestamp']),
                        confidence=0.8,
                        source=data.get('source', 'unknown')
                    )

                    callback(price_data)
                    message.ack()

                except Exception as e:
                    logger.error(f"Failed to process message: {e}")
                    message.ack()  # Ack to prevent infinite retry

            # Start subscriber
            streaming_pull_future = self._subscriber.subscribe(
                subscription_path,
                callback=message_callback
            )

            # Keep the subscription alive
            while True:
                await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Message processing failed: {e}")

class FirestoreCache:
    """Firestore cache för oracle data."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._client = firestore.AsyncClient(project=project_id)
        self._collection = 'dex_oracle_cache'

    async def initialize(self):
        """Initiera Firestore cache."""
        try:
            logger.info("Firestore cache initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Firestore cache: {e}")
            return False

    async def get_cached_price(self, token_address: str, dex_name: str) -> Optional[DEXPriceData]:
        """Hämta cached price data."""
        try:
            doc_ref = self._client.collection(self._collection).document(f"{dex_name}_{token_address}")
            doc = await doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                return DEXPriceData(
                    token_symbol=data['token_symbol'],
                    token_address=data['token_address'],
                    dex_name=data['dex_name'],
                    price=data['price'],
                    volume_24h=data['volume_24h'],
                    price_change_24h=data['price_change_24h'],
                    liquidity=data['liquidity'],
                    pair_address=data['pair_address'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    confidence=data['confidence'],
                    source=data['source']
                )
            return None

        except Exception as e:
            logger.error(f"Failed to get cached price: {e}")
            return None

    async def cache_price_data(self, price_data: DEXPriceData) -> bool:
        """Cache price data."""
        try:
            doc_ref = self._client.collection(self._collection).document(f"{price_data.dex_name}_{price_data.token_address}")

            data = {
                'token_symbol': price_data.token_symbol,
                'token_address': price_data.token_address,
                'dex_name': price_data.dex_name,
                'price': price_data.price,
                'volume_24h': price_data.volume_24h,
                'price_change_24h': price_data.price_change_24h,
                'liquidity': price_data.liquidity,
                'pair_address': price_data.pair_address,
                'timestamp': price_data.timestamp.isoformat(),
                'confidence': price_data.confidence,
                'source': price_data.source
            }

            await doc_ref.set(data)
            return True

        except Exception as e:
            logger.error(f"Failed to cache price data: {e}")
            return False

class BigQueryExporter:
    """BigQuery exporter för oracle data."""

    def __init__(self, project_id: str, dataset_name: str = "crypto_dex_data"):
        self.project_id = project_id
        self.dataset_name = dataset_name
        self._client = bigquery.Client(project=project_id)
        self._table_name = "dex_price_data"

    async def initialize(self):
        """Initiera BigQuery exporter."""
        try:
            # Create dataset if it doesn't exist
            dataset_ref = self._client.dataset(self.dataset_name)
            try:
                self._client.get_dataset(dataset_ref)
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                self._client.create_dataset(dataset)

            logger.info("BigQuery exporter initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize BigQuery exporter: {e}")
            return False

    async def export_price_data(self, price_data: DEXPriceData) -> bool:
        """Export price data till BigQuery."""
        try:
            table_ref = self._client.dataset(self.dataset_name).table(self._table_name)

            # Create table if it doesn't exist
            try:
                self._client.get_table(table_ref)
            except Exception:
                schema = [
                    bigquery.SchemaField("token_symbol", "STRING"),
                    bigquery.SchemaField("token_address", "STRING"),
                    bigquery.SchemaField("dex_name", "STRING"),
                    bigquery.SchemaField("price", "FLOAT"),
                    bigquery.SchemaField("volume_24h", "FLOAT"),
                    bigquery.SchemaField("price_change_24h", "FLOAT"),
                    bigquery.SchemaField("liquidity", "FLOAT"),
                    bigquery.SchemaField("pair_address", "STRING"),
                    bigquery.SchemaField("timestamp", "TIMESTAMP"),
                    bigquery.SchemaField("confidence", "FLOAT"),
                    bigquery.SchemaField("source", "STRING"),
                ]
                table = bigquery.Table(table_ref, schema=schema)
                self._client.create_table(table)

            # Insert data
            rows_to_insert = [{
                'token_symbol': price_data.token_symbol,
                'token_address': price_data.token_address,
                'dex_name': price_data.dex_name,
                'price': price_data.price,
                'volume_24h': price_data.volume_24h,
                'price_change_24h': price_data.price_change_24h,
                'liquidity': price_data.liquidity,
                'pair_address': price_data.pair_address,
                'timestamp': price_data.timestamp.isoformat(),
                'confidence': price_data.confidence,
                'source': price_data.source
            }]

            errors = self._client.insert_rows_json(table_ref, rows_to_insert)
            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to export to BigQuery: {e}")
            return False

class CloudFunctionDEXOracle:
    """
    Serverless DEX Oracle med Cloud Functions och real-tids streaming.
    Implementerar comprehensive DEX data collection och distribution.
    """

    def __init__(self, config: OracleConfig):
        self.config = config
        self.data_sources = [
            UniswapV3Source(),
            DexScreenerSource()
        ]
        self.function_manager = CloudFunctionManager(config.project_id, config.region)
        self.pubsub_manager = PubSubManager(config.project_id)
        self.firestore_cache = FirestoreCache(config.project_id)
        self.bigquery_exporter = BigQueryExporter(config.project_id)
        self._initialized = False
        self._streaming_enabled = False

    async def initialize(self) -> bool:
        """Initiera oracle."""
        try:
            logger.info("Initializing Cloud Function DEX Oracle...")

            # Initialize all components
            await self.function_manager.initialize()
            await self.pubsub_manager.initialize()
            await self.firestore_cache.initialize()
            await self.bigquery_exporter.initialize()

            # Initialize data sources
            for source in self.data_sources:
                await source.__aenter__()

            self._initialized = True
            logger.info("Cloud Function DEX Oracle initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Oracle initialization failed: {e}")
            return False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for source in self.data_sources:
            if hasattr(source, '__aexit__'):
                await source.__aexit__(exc_type, exc_val, exc_tb)

    @handle_errors(service_name="cloud_function_dex_oracle")
    async def get_token_price(self, token_query: str, dex_name: str = "all") -> List[DEXPriceData]:
        """
        Hämta token price från DEX:er.

        Args:
            token_query: Token symbol eller address
            dex_name: Specific DEX eller "all" för alla

        Returns:
            Lista med price data från olika DEX:er
        """
        try:
            # Resolve token
            bridge = get_unified_bridge()
            async with bridge:
                unified_info = await bridge.create_unified_token_info(token_query, enhance_with_ai=False)

            token_info = TokenInfo.from_dict(unified_info['token_info'])

            if not token_info.address:
                raise CryptoError("Token address not found", "TOKEN_ADDRESS_MISSING")

            # Get cached data first
            cached_data = await self.firestore_cache.get_cached_price(token_info.address, dex_name)
            if cached_data:
                # Check if cache is still fresh
                if (datetime.now() - cached_data.timestamp).seconds < self.config.update_interval:
                    logger.info(f"Using cached price data for {token_info.symbol}")
                    return [cached_data]

            # Fetch fresh data
            price_data_list = []

            for source in self.data_sources:
                if dex_name != "all" and source.name != dex_name:
                    continue

                try:
                    price_data = await source.get_price_data(token_info.address)
                    if price_data:
                        # Cache the data
                        if self.config.enable_firestore_cache:
                            await self.firestore_cache.cache_price_data(price_data)

                        # Export to BigQuery
                        if self.config.enable_bigquery_export:
                            await self.bigquery_exporter.export_price_data(price_data)

                        # Publish to streaming if enabled
                        if self.config.enable_streaming:
                            await self.pubsub_manager.publish_price_update(price_data)

                        price_data_list.append(price_data)

                except Exception as e:
                    logger.warning(f"Failed to get price from {source.name}: {e}")
                    continue

            if not price_data_list:
                raise CryptoError(f"No price data found for {token_query}", "NO_PRICE_DATA")

            return price_data_list

        except Exception as e:
            logger.error(f"Failed to get token price for {token_query}: {e}")
            raise CryptoError(f"Price fetch failed: {str(e)}", "PRICE_FETCH_ERROR")

    async def start_price_streaming(self, token_symbol: str, callback: Optional[Callable[[DEXPriceData], None]] = None) -> str:
        """
        Starta real-tids price streaming för token.

        Args:
            token_symbol: Token symbol att streama
            callback: Callback för att hantera streaming data

        Returns:
            Subscription ID
        """
        try:
            if callback:
                subscription_id = await self.pubsub_manager.subscribe_to_updates(token_symbol, callback)
            else:
                subscription_id = f"stream_{token_symbol}_{datetime.now().timestamp()}"

            self._streaming_enabled = True
            logger.info(f"Price streaming started for {token_symbol}")
            return subscription_id

        except Exception as e:
            logger.error(f"Failed to start price streaming: {e}")
            return ""

    async def stop_price_streaming(self, subscription_id: str) -> bool:
        """Stoppa price streaming."""
        try:
            # This would cancel the subscription
            self._streaming_enabled = False
            logger.info("Price streaming stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop price streaming: {e}")
            return False

    async def invoke_oracle_function(self, function_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anropa Cloud Function för oracle operations.

        Args:
            function_name: Function att anropa
            data: Data att skicka till function

        Returns:
            Function response
        """
        try:
            return await self.function_manager.invoke_function(function_name, data)
        except Exception as e:
            logger.error(f"Oracle function invocation failed: {e}")
            raise APIError(f"Function invocation failed: {str(e)}", "FUNCTION_ERROR")

    async def get_oracle_status(self) -> Dict[str, Any]:
        """Hämta oracle status."""
        return {
            'initialized': self._initialized,
            'streaming_enabled': self._streaming_enabled,
            'data_sources': [source.name for source in self.data_sources],
            'supported_dexes': await self._get_supported_dexes(),
            'cache_enabled': self.config.enable_firestore_cache,
            'bigquery_export_enabled': self.config.enable_bigquery_export,
            'update_interval': self.config.update_interval,
            'project_id': self.config.project_id,
            'region': self.config.region
        }

    async def _get_supported_dexes(self) -> List[str]:
        """Hämta lista med supported DEX:er."""
        supported_dexes = []
        for source in self.data_sources:
            try:
                pairs = await source.get_supported_pairs()
                supported_dexes.append(source.name)
            except Exception:
                continue
        return supported_dexes

# Global oracle instance
_dex_oracle: Optional[CloudFunctionDEXOracle] = None

def get_dex_oracle(project_id: str = "felicia-finance-adk", region: str = "us-central1") -> CloudFunctionDEXOracle:
    """Hämta global DEX oracle instans."""
    global _dex_oracle
    if _dex_oracle is None:
        config = OracleConfig(
            project_id=project_id,
            region=region,
            enable_streaming=True,
            enable_firestore_cache=True,
            enable_bigquery_export=True
        )
        _dex_oracle = CloudFunctionDEXOracle(config)
    return _dex_oracle

async def get_dex_price(token_query: str, dex_name: str = "all") -> List[DEXPriceData]:
    """
    Enkel funktion för att hämta DEX price.

    Args:
        token_query: Token symbol eller address
        dex_name: DEX namn eller "all"

    Returns:
        Lista med DEX price data
    """
    oracle = get_dex_oracle()
    async with oracle:
        return await oracle.get_token_price(token_query, dex_name)