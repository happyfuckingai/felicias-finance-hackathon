"""
Token Handler för HappyOS Crypto - ERC20 deployment och hantering.
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.integrations.contracts import ContractDeployer, BASE_TESTNET_CONFIG, POLYGON_TESTNET_CONFIG
from ..core.token.token_resolver import DynamicTokenResolver, TokenNotFoundError

logger = logging.getLogger(__name__)

class TokenHandler:
    """Hanterar ERC20 token deployment och operationer."""

    def __init__(self):
        """Initialize TokenHandler."""
        # Hämta private key från environment (säkerhet!)
        self.private_key = os.getenv('CRYPTO_PRIVATE_KEY')
        if not self.private_key:
            logger.warning("CRYPTO_PRIVATE_KEY inte satt - token deployment kommer att misslyckas")

        # Default till Base testnet
        self.default_config = BASE_TESTNET_CONFIG

        # Initiera token resolver för discovery
        self.token_resolver = None
        try:
            self.token_resolver = DynamicTokenResolver()
        except Exception as e:
            logger.warning(f"Token resolver initialization failed: {e}")

        logger.info("TokenHandler initialiserad")
    
    async def handle(self, handler_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle token-relaterade kommandon.
        
        Args:
            handler_input: Input från CryptoSkill
            
        Returns:
            Result av token-operationen
        """
        action = handler_input.get('action', 'default')
        fields = handler_input.get('fields', {})
        command = handler_input.get('command', '')
        
        try:
            if action in ['skapa', 'deploya', 'create', 'deploy']:
                return await self._deploy_token(fields, command)
            elif action in ['visa', 'show', 'info']:
                return await self._show_token_info(fields)
            elif action in ['transfer', 'skicka', 'send']:
                return await self._transfer_token(fields)
            else:
                return await self._show_help()
                
        except Exception as e:
            logger.error(f"Fel i TokenHandler: {e}")
            return {
                'message': f'Ett fel uppstod vid token-operationen: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _deploy_token(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Deploya ERC20 token på blockchain.
        
        Args:
            fields: Extraherade fält från kommandot
            command: Ursprungligt kommando
            
        Returns:
            Deployment result
        """
        if not self.private_key:
            return {
                'message': 'Kan inte deploya token - CRYPTO_PRIVATE_KEY saknas i environment',
                'data': {'error': 'Missing private key'},
                'status': 'error'
            }
        
        # Extrahera token-parametrar från kommando
        token_name = await self._extract_token_name(fields, command)
        token_symbol = await self._extract_token_symbol(fields, command)
        total_supply = self._extract_total_supply(fields, command)
        chain = self._extract_chain(fields, command)
        
        # Välj blockchain config
        if chain.lower() in ['polygon', 'mumbai']:
            config = POLYGON_TESTNET_CONFIG
        else:
            config = BASE_TESTNET_CONFIG  # Default
        
        try:
            # Skapa deployer
            deployer = ContractDeployer(config['rpc_url'], self.private_key)
            
            # Deploya token
            result = await deployer.deploy_erc20_token(
                name=token_name,
                symbol=token_symbol,
                total_supply=total_supply
            )
            
            if result['success']:
                message = f"🚀 Token {token_name} ({token_symbol}) deployad!\n"
                message += f"📍 Contract: {result['contract_address']}\n"
                message += f"⛽ Gas: {result['gas_used']}\n"
                message += f"🔗 Chain: {config['name']}\n"
                message += f"🔍 Explorer: {config['explorer']}/address/{result['contract_address']}"
                
                return {
                    'message': message,
                    'data': {
                        'contract_address': result['contract_address'],
                        'transaction_hash': result['transaction_hash'],
                        'token_name': token_name,
                        'token_symbol': token_symbol,
                        'total_supply': total_supply,
                        'chain': config['name'],
                        'explorer_url': f"{config['explorer']}/address/{result['contract_address']}"
                    },
                    'status': 'success'
                }
            else:
                return {
                    'message': f'Token deployment misslyckades: {result["error"]}',
                    'data': result,
                    'status': 'error'
                }
                
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return {
                'message': f'Deployment misslyckades: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _show_token_info(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Visa information om en token med dynamisk discovery."""
        token_query = fields.get('token', fields.get('contract_address', ''))

        if not token_query:
            return {
                'message': 'Ange ett token-namn, symbol eller contract address för att få information.',
                'data': {'error': 'No token specified'},
                'status': 'error'
            }

        # Försök dynamisk token resolution
        if self.token_resolver:
            try:
                async with self.token_resolver:
                    token_info = await self.token_resolver.resolve_token(token_query)

                    message = f"🪙 **{token_info.name} ({token_info.symbol})**\n\n"
                    message += f"📍 Address: {token_info.address}\n"
                    message += f"🌐 Chain: {token_info.chain.title()}\n"
                    message += f"🔢 Decimals: {token_info.decimals}\n"

                    if token_info.logo_url:
                        message += f"🖼️ Logo: {token_info.logo_url}\n"

                    if token_info.description:
                        # Begränsa description till 200 tecken
                        desc = token_info.description[:200] + "..." if len(token_info.description) > 200 else token_info.description
                        message += f"\n📝 {desc}\n"

                    if token_info.coingecko_id:
                        message += f"📊 CoinGecko ID: {token_info.coingecko_id}\n"

                    message += f"\n✅ Token hittad via dynamisk resolution"

                    return {
                        'message': message,
                        'data': token_info.to_dict(),
                        'status': 'success'
                    }

            except TokenNotFoundError:
                pass
            except Exception as e:
                logger.error(f"Token resolution error: {e}")

        # Fallback om resolution misslyckas
        return {
            'message': f'Kunde inte hitta information om token "{token_query}". Försök med ett annat namn eller contract address.',
            'data': {'token_query': token_query, 'error': 'Token not found'},
            'status': 'error'
        }
    
    async def _transfer_token(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Överför tokens mellan adresser."""
        return {
            'message': 'Token transfer funktionalitet kommer snart.',
            'data': {'feature': 'coming_soon'},
            'status': 'info'
        }
    
    async def _show_help(self) -> Dict[str, Any]:
        """Visa hjälp för token-kommandon."""
        help_text = """
🪙 **Token Kommandon:**

**Deploya token:**
- "Deploya HappyToken på Base"
- "Skapa token HAPPY med 1000000 supply"
- "Deploya MyToken på Polygon"

**Exempel:**
- Token namn: HappyToken
- Symbol: HAPPY  
- Supply: 1000000
- Chain: Base (default), Polygon

**Kedjor som stöds:**
- Base Testnet (default)
- Polygon Mumbai
        """
        
        return {
            'message': help_text,
            'data': {
                'supported_chains': ['Base Testnet', 'Polygon Mumbai'],
                'examples': [
                    'Deploya HappyToken på Base',
                    'Skapa token HAPPY med 1000000 supply'
                ]
            },
            'status': 'info'
        }
    
    async def _extract_token_name(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera token namn från kommando med dynamisk resolution."""
        # Kolla fields först
        if 'token_name' in fields:
            token_name = fields['token_name']
        else:
            token_name = self._extract_token_from_command(command)

        # Försök dynamisk resolution för bättre namn
        if self.token_resolver and token_name:
            try:
                async with self.token_resolver:
                    token_info = await self.token_resolver.resolve_token(token_name)
                    return token_info.name
            except (TokenNotFoundError, Exception):
                pass

        # Fallback till enkel extraction
        command_lower = command.lower()
        if 'happytoken' in command_lower:
            return 'HappyToken'
        elif 'happy' in command_lower and 'token' in command_lower:
            return 'HappyToken'

        return token_name.title() if token_name else 'HappyToken'
    
    async def _extract_token_symbol(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera token symbol från kommando med dynamisk resolution."""
        if 'token_symbol' in fields:
            token_symbol = fields['token_symbol']
        else:
            token_symbol = self._extract_token_from_command(command)

        # Försök dynamisk resolution för symbol
        if self.token_resolver and token_symbol:
            try:
                async with self.token_resolver:
                    token_info = await self.token_resolver.resolve_token(token_symbol)
                    return token_info.symbol
            except (TokenNotFoundError, Exception):
                pass

        # Fallback
        command_lower = command.lower()
        if 'happy' in command_lower:
            return 'HAPPY'

        return token_symbol.upper() if token_symbol else 'HAPPY'

    def _extract_token_from_command(self, command: str) -> str:
        """Hjälpfunktion för att extrahera token från kommando."""
        command_lower = command.lower()

        # Sök efter token-relaterade ord
        import re
        words = re.findall(r'\b\w+\b', command_lower)

        # Exkludera stoppord
        stop_words = ['skapa', 'deploya', 'create', 'token', 'med', 'på', 'och', 'för', 'till', 'the', 'a', 'an', 'på', 'och', 'eller']

        for word in words:
            if word not in stop_words and len(word) > 2:
                return word

        return 'HappyToken'
    
    def _extract_total_supply(self, fields: Dict[str, Any], command: str) -> int:
        """Extrahera total supply från kommando."""
        if 'total_supply' in fields:
            return int(fields['total_supply'])
        
        # Sök efter nummer i kommandot
        import re
        numbers = re.findall(r'\d+', command)
        
        if numbers:
            # Ta det största numret
            return max(int(num) for num in numbers)
        
        # Default supply
        return 1000000
    
    def _extract_chain(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera blockchain från kommando."""
        if 'chain' in fields:
            return fields['chain']
        
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['polygon', 'mumbai', 'matic']):
            return 'polygon'
        elif any(word in command_lower for word in ['base', 'coinbase']):
            return 'base'
        
        return 'base'  # Default
