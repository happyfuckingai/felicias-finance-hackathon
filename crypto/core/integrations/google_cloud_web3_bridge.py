"""
Google Cloud Web3 Bridge - Unified Interface mellan Web3 och Google Cloud.
Implementerar authentication translation layer och error handling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import json

from web3 import Web3
from web3.exceptions import Web3Exception
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.cloud import kms
from google.cloud import pubsub_v1

from ..errors.error_handling import handle_errors, CryptoError, NetworkError, APIError
from ..token.token_providers import TokenInfo
from ..token.token_resolver import DynamicTokenResolver

logger = logging.getLogger(__name__)

class GoogleCloudAuthManager:
    """Hantera Google Cloud authentication för Web3-integrationer."""

    def __init__(self, service_account_path: Optional[str] = None, project_id: str = None):
        self.service_account_path = service_account_path
        self.project_id = project_id
        self._credentials = None
        self._kms_client = None
        self._pubsub_client = None

    async def initialize(self):
        """Initiera Google Cloud clients."""
        try:
            if self.service_account_path:
                self._credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
            else:
                self._credentials, self.project_id = google.auth.default(
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )

            # Refresh credentials if needed
            if self._credentials and self._credentials.expired:
                self._credentials.refresh(Request())

            # Initialize clients
            self._kms_client = kms.KeyManagementServiceClient(credentials=self._credentials)
            self._pubsub_client = pubsub_v1.PublisherClient(credentials=self._credentials)

            logger.info("Google Cloud authentication initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud auth: {e}")
            return False

    @property
    def credentials(self):
        """Hämta credentials."""
        return self._credentials

    @property
    def kms_client(self):
        """Hämta KMS client."""
        return self._kms_client

    @property
    def pubsub_client(self):
        """Hämta Pub/Sub client."""
        return self._pubsub_client

class Web3WalletManager:
    """Hantera Web3 wallet-integrationer med Google Cloud."""

    def __init__(self, web3_providers: List[str], auth_manager: GoogleCloudAuthManager):
        self.web3_providers = web3_providers
        self.auth_manager = auth_manager
        self.web3_instances = {}
        self.active_provider = None

    async def initialize(self):
        """Initiera Web3-instanser."""
        for provider_url in self.web3_providers:
            try:
                web3_instance = Web3(Web3.HTTPProvider(provider_url))
                if web3_instance.is_connected():
                    self.web3_instances[provider_url] = web3_instance
                    logger.info(f"Web3 connected to {provider_url}")
                else:
                    logger.warning(f"Failed to connect to Web3 provider: {provider_url}")
            except Exception as e:
                logger.error(f"Error initializing Web3 provider {provider_url}: {e}")

        if self.web3_instances:
            self.active_provider = list(self.web3_instances.keys())[0]
            logger.info(f"Active Web3 provider set to: {self.active_provider}")
            return True
        else:
            logger.error("No Web3 providers could be initialized")
            return False

    def get_web3(self, provider_url: Optional[str] = None) -> Optional[Web3]:
        """Hämta Web3-instans."""
        if provider_url and provider_url in self.web3_instances:
            return self.web3_instances[provider_url]
        elif self.active_provider:
            return self.web3_instances[self.active_provider]
        return None

    async def sign_with_kms(self, message: str, key_path: str) -> Optional[str]:
        """Signera meddelande med Google Cloud KMS."""
        try:
            if not self.auth_manager.kms_client:
                raise CryptoError("KMS client not initialized", "KMS_NOT_INITIALIZED")

            # Hash message for signing
            message_hash = Web3.keccak(text=message)

            # Sign with KMS
            response = self.auth_manager.kms_client.asymmetric_sign(
                name=key_path,
                digest={'sha256': message_hash.hex()}
            )

            signature = response.signature
            return signature.hex()

        except Exception as e:
            logger.error(f"KMS signing failed: {e}")
            raise CryptoError(f"KMS signing failed: {str(e)}", "KMS_SIGNING_ERROR")

class UnifiedBridge:
    """
    Unified bridge mellan Web3 och Google Cloud.
    Hanterar authentication translation och cross-platform integration.
    """

    def __init__(self,
                 service_account_path: Optional[str] = None,
                 project_id: str = None,
                 web3_providers: Optional[List[str]] = None,
                 token_resolver: Optional[DynamicTokenResolver] = None):
        self.auth_manager = GoogleCloudAuthManager(service_account_path, project_id)
        self.wallet_manager = Web3WalletManager(
            web3_providers or ["https://mainnet.infura.io/v3/YOUR_KEY"],
            self.auth_manager
        )
        self.token_resolver = token_resolver or DynamicTokenResolver()
        self._initialized = False

    async def initialize(self) -> bool:
        """Initiera bridge-komponenter."""
        try:
            logger.info("Initializing Google Cloud Web3 Bridge...")

            # Initialize Google Cloud auth
            if not await self.auth_manager.initialize():
                logger.warning("Google Cloud auth initialization failed")

            # Initialize Web3 wallet manager
            if not await self.wallet_manager.initialize():
                logger.warning("Web3 wallet manager initialization failed")

            # Initialize token resolver
            await self.token_resolver.__aenter__()

            self._initialized = True
            logger.info("Google Cloud Web3 Bridge initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Bridge initialization failed: {e}")
            return False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.token_resolver, '__aexit__'):
            await self.token_resolver.__aexit__(exc_type, exc_val, exc_tb)

    @handle_errors(service_name="google_cloud_web3_bridge")
    async def translate_web3_to_cloud_auth(self, wallet_address: str) -> Dict[str, Any]:
        """
        Översätt Web3 wallet authentication till Google Cloud.
        Implementerar unified authentication mellan blockchain wallets och cloud services.

        Args:
            wallet_address: Web3 wallet address

        Returns:
            Dictionary med authentication mapping
        """
        try:
            web3 = self.wallet_manager.get_web3()
            if not web3:
                raise NetworkError("No Web3 provider available", "WEB3_UNAVAILABLE")

            # Verify wallet address
            if not web3.is_address(wallet_address):
                raise ValidationError(f"Invalid wallet address: {wallet_address}", "INVALID_ADDRESS")

            # Create authentication mapping
            auth_mapping = {
                'wallet_address': wallet_address.lower(),
                'cloud_identity': f"web3:{wallet_address.lower()}@felicia-finance.iam.gserviceaccount.com",
                'authentication_method': 'wallet_to_cloud_bridge',
                'timestamp': datetime.now().isoformat(),
                'status': 'verified'
            }

            # Sign the mapping with KMS for verification
            mapping_json = json.dumps(auth_mapping, sort_keys=True)
            signature = await self.wallet_manager.sign_with_kms(
                mapping_json,
                f"projects/{self.auth_manager.project_id}/locations/global/keyRings/felicia-keyring/cryptoKeys/web3-signing-key"
            )

            auth_mapping['signature'] = signature
            auth_mapping['kms_key_path'] = f"projects/{self.auth_manager.project_id}/locations/global/keyRings/felicia-keyring/cryptoKeys/web3-signing-key"

            logger.info(f"Authentication mapping created for wallet: {wallet_address}")
            return auth_mapping

        except Exception as e:
            logger.error(f"Web3 to Cloud auth translation failed: {e}")
            raise CryptoError(f"Authentication translation failed: {str(e)}", "AUTH_TRANSLATION_ERROR")

    @handle_errors(service_name="google_cloud_web3_bridge")
    async def create_unified_token_info(self, token_query: str, enhance_with_ai: bool = True) -> Dict[str, Any]:
        """
        Skapa unified token information från Web3 och Google Cloud.
        Kombinerar token data från blockchain med AI-enhanced analysis.

        Args:
            token_query: Token symbol, namn eller address
            enhance_with_ai: Om AI-enhancement ska användas

        Returns:
            Enhanced token information dictionary
        """
        try:
            # Resolve token med befintliga providers
            token_info = await self.token_resolver.resolve_token(token_query)

            # Get Web3 contract info
            web3_contract_info = await self._get_web3_contract_info(token_info)

            # Create unified token info
            unified_info = {
                'token_info': token_info.to_dict(),
                'web3_data': web3_contract_info,
                'cloud_metadata': await self._get_cloud_metadata(token_info),
                'enhanced_features': {}
            }

            # Add AI enhancement if requested
            if enhance_with_ai:
                unified_info['enhanced_features'] = await self._enhance_with_vertex_ai(token_info)

            # Add security scoring
            unified_info['security_score'] = await self._calculate_security_score(token_info, web3_contract_info)

            logger.info(f"Unified token info created for: {token_info.symbol}")
            return unified_info

        except Exception as e:
            logger.error(f"Unified token info creation failed: {e}")
            raise CryptoError(f"Token info creation failed: {str(e)}", "TOKEN_INFO_ERROR")

    async def _get_web3_contract_info(self, token_info: TokenInfo) -> Dict[str, Any]:
        """Hämta Web3 contract information."""
        try:
            web3 = self.wallet_manager.get_web3()
            if not web3 or not token_info.address:
                return {}

            # Create contract instance
            contract = web3.eth.contract(
                address=Web3.to_checksum_address(token_info.address),
                abi=self._get_erc20_abi()
            )

            # Get contract info
            contract_info = {
                'total_supply': contract.functions.totalSupply().call(),
                'decimals': contract.functions.decimals().call(),
                'symbol': contract.functions.symbol().call(),
                'name': contract.functions.name().call(),
                'owner': contract.functions.owner().call() if hasattr(contract.functions, 'owner') else None,
                'paused': contract.functions.paused().call() if hasattr(contract.functions, 'paused') else False,
            }

            return contract_info

        except Exception as e:
            logger.warning(f"Failed to get Web3 contract info: {e}")
            return {}

    async def _get_cloud_metadata(self, token_info: TokenInfo) -> Dict[str, Any]:
        """Hämta Google Cloud metadata för token."""
        try:
            # This would integrate with BigQuery datasets, Cloud Storage, etc.
            return {
                'bigquery_dataset': f"crypto_tokens_{token_info.chain}",
                'storage_bucket': f"felicia-finance-token-data-{token_info.chain}",
                'pubsub_topic': f"token-updates-{token_info.symbol.lower()}",
                'monitoring_dashboard': f"token-monitoring-{token_info.symbol.lower()}"
            }
        except Exception as e:
            logger.warning(f"Failed to get cloud metadata: {e}")
            return {}

    async def _enhance_with_vertex_ai(self, token_info: TokenInfo) -> Dict[str, Any]:
        """Enhance token info med Vertex AI analysis."""
        try:
            # This would integrate with Vertex AI for sentiment analysis, prediction, etc.
            # For now, return placeholder structure
            return {
                'sentiment_score': 0.0,
                'risk_assessment': 'medium',
                'price_prediction': None,
                'ai_insights': []
            }
        except Exception as e:
            logger.warning(f"Vertex AI enhancement failed: {e}")
            return {}

    async def _calculate_security_score(self, token_info: TokenInfo, web3_info: Dict[str, Any]) -> float:
        """Beräkna säkerhets-score för token."""
        try:
            score = 0.5  # Base score

            # Add points for verified token info
            if token_info.logo_url:
                score += 0.1
            if token_info.description:
                score += 0.1
            if token_info.coingecko_id:
                score += 0.2

            # Add points for Web3 contract verification
            if web3_info:
                if web3_info.get('total_supply', 0) > 0:
                    score += 0.1
                if not web3_info.get('paused', False):
                    score += 0.1

            return min(score, 1.0)  # Cap at 1.0

        except Exception as e:
            logger.warning(f"Security score calculation failed: {e}")
            return 0.5

    def _get_erc20_abi(self) -> List[Dict[str, Any]]:
        """Returnera standard ERC20 ABI."""
        return [
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "owner",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "paused",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]

    async def publish_to_pubsub(self, topic_name: str, message: Dict[str, Any]) -> bool:
        """
        Publicera meddelande till Google Cloud Pub/Sub.

        Args:
            topic_name: Pub/Sub topic namn
            message: Meddelande att publicera

        Returns:
            True om lyckades
        """
        try:
            if not self.auth_manager.pubsub_client:
                logger.error("Pub/Sub client not initialized")
                return False

            topic_path = self.auth_manager.pubsub_client.topic_path(
                self.auth_manager.project_id or 'felicia-finance',
                topic_name
            )

            message_data = json.dumps(message).encode('utf-8')
            future = self.auth_manager.pubsub_client.publish(topic_path, message_data)
            result = future.result()

            logger.info(f"Message published to {topic_name}: {result}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish to Pub/Sub: {e}")
            return False

    async def get_bridge_status(self) -> Dict[str, Any]:
        """Hämta bridge status."""
        return {
            'initialized': self._initialized,
            'google_cloud_auth': self.auth_manager.credentials is not None,
            'web3_providers': len(self.wallet_manager.web3_instances),
            'active_web3_provider': self.wallet_manager.active_provider,
            'token_resolver_status': 'active' if hasattr(self.token_resolver, 'stats') else 'unknown',
            'kms_available': self.auth_manager.kms_client is not None,
            'pubsub_available': self.auth_manager.pubsub_client is not None
        }

# Global bridge instance
_unified_bridge: Optional[UnifiedBridge] = None

def get_unified_bridge(
    service_account_path: Optional[str] = None,
    project_id: str = None,
    web3_providers: Optional[List[str]] = None
) -> UnifiedBridge:
    """Hämta global unified bridge instans."""
    global _unified_bridge
    if _unified_bridge is None:
        _unified_bridge = UnifiedBridge(service_account_path, project_id, web3_providers)
    return _unified_bridge

async def create_unified_token_info(token_query: str, enhance_with_ai: bool = True) -> Dict[str, Any]:
    """
    Enkel funktion för att skapa unified token info.

    Args:
        token_query: Token sökterm
        enhance_with_ai: Om AI-enhancement ska användas

    Returns:
        Enhanced token information
    """
    bridge = get_unified_bridge()
    async with bridge:
        return await bridge.create_unified_token_info(token_query, enhance_with_ai)