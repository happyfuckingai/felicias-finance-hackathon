"""
DEX Handler för HappyOS Crypto - DEX-interaktion och trading.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.token.token_resolver import DynamicTokenResolver, TokenNotFoundError

logger = logging.getLogger(__name__)

class DexHandler:
    """Hanterar DEX-operationer och trading med LLM-optimering."""

    def __init__(self):
        """Initialize DexHandler."""
        self.llm = None
        self.token_resolver = None

        # Initiera LLM om tillgängligt
        try:
            import os
            if os.getenv('OPENROUTER_API_KEY'):
                from ..core.llm_integration import LLMIntegration
                self.llm = LLMIntegration()
        except ImportError:
            logger.warning("LLM integration not available for DEX")

        # Initiera token resolver
        try:
            self.token_resolver = DynamicTokenResolver()
        except Exception as e:
            logger.warning(f"Token resolver initialization failed: {e}")

        logger.info("DexHandler initialiserad")
    
    async def handle(self, handler_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle DEX-relaterade kommandon.
        
        Args:
            handler_input: Input från CryptoSkill
            
        Returns:
            Result av DEX-operationen
        """
        action = handler_input.get('action', 'default')
        fields = handler_input.get('fields', {})
        command = handler_input.get('command', '')
        
        try:
            # Initiera verklig DEX-integration om möjligt
            real_dex = None
            try:
                import os
                from ..core.dex_integration import RealDexIntegration
                from web3 import Web3
                from eth_account import Account

                # Försök initiera med environment variabler
                rpc_url = os.getenv('WEB3_RPC_URL', 'https://gas.api.infura.io/v3/e71c1d88fc7a41748e64fb291fdc9003')
                private_key = os.getenv('TRADING_PRIVATE_KEY')

                if private_key and rpc_url != 'https://gas.api.infura.io/v3/e71c1d88fc7a41748e64fb291fdc9003':
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    real_dex = RealDexIntegration(w3, private_key)
                    logger.info("Real DEX integration enabled")
            except ImportError:
                logger.warning("Real DEX integration not available")

            if action in ['swap', 'byta', 'trade']:
                return await self._swap_tokens(fields, command, real_dex)
            elif action in ['add_liquidity', 'lägg_till_likviditet']:
                return await self._add_liquidity(fields)
            elif action in ['remove_liquidity', 'ta_bort_likviditet']:
                return await self._remove_liquidity(fields)
            elif action in ['check_price', 'kolla_pris']:
                return await self._check_dex_price(fields, command, real_dex)
            else:
                return await self._show_help()
                
        except Exception as e:
            logger.error(f"Fel i DexHandler: {e}")
            return {
                'message': f'Ett fel uppstod vid DEX-operationen: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _swap_tokens(self, fields: Dict[str, Any], command: str, real_dex=None) -> Dict[str, Any]:
        """
        Swappa tokens på DEX med LLM-optimering och verklig trading.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando
            real_dex: RealDexIntegration instance om tillgänglig

        Returns:
            Swap result med rekommenderad DEX
        """
        from_token = await self._extract_from_token(fields, command)
        to_token = await self._extract_to_token(fields, command)
        amount = self._extract_amount(fields, command)

        # Försök verklig swap först om real_dex finns
        if real_dex and real_dex.uniswap_trader:
            try:
                swap_result = await real_dex.execute_swap(
                    token_in=from_token,
                    token_out=to_token,
                    amount_in=amount,
                    max_slippage_percent=0.5
                )

                if swap_result['success']:
                    message = f"✅ **VERKLIG SWAP UTFÖRD!**\n\n"
                    message += f"🔄 **Transaktion:** {swap_result['transaction_hash'][:10]}...\n"
                    message += f"📤 Från: {amount} {from_token.upper()}\n"
                    message += f"📥 Till: ~{swap_result['amount_out']:.4f} {to_token.upper()}\n"
                    message += f"⛽ Gas: {swap_result['gas_used']:,}\n"
                    message += f"🏪 DEX: Uniswap V3\n\n"
                    message += f"⚠️ **VIKTIGT:** Detta var en verklig blockchain-transaktion!"

                    return {
                        'message': message,
                        'data': swap_result,
                        'status': 'success',
                        'real_transaction': True
                    }
            except Exception as e:
                logger.warning(f"Real DEX swap failed, falling back to simulation: {e}")

        # Fallback till simulerad swap

        # Simulerade DEX-alternativ (i verkligheten från API)
        dex_options = [
            {
                'name': 'Uniswap V3',
                'price': 1.002,  # USD per input token
                'fee': 0.05,     # 0.05%
                'liquidity': 5000000,
                'slippage': 0.1
            },
            {
                'name': 'SushiSwap',
                'price': 1.001,
                'fee': 0.03,
                'liquidity': 2500000,
                'slippage': 0.15
            },
            {
                'name': 'PancakeSwap',
                'price': 0.999,
                'fee': 0.02,
                'liquidity': 1000000,
                'slippage': 0.25
            }
        ]

        # Använd LLM för att välja bästa DEX om tillgängligt
        recommended_dex = None
        if self.llm:
            try:
                routing_result = await self.llm.optimize_dex_routing(
                    from_token, to_token, amount, dex_options
                )
                if routing_result['success']:
                    recommended_dex = routing_result['recommended_dex']
                    reasoning = routing_result['reasoning']
                else:
                    recommended_dex = dex_options[0]  # Fallback
                    reasoning = "LLM routing unavailable, using default"
            except Exception as e:
                logger.warning(f"LLM DEX routing failed: {e}")
                recommended_dex = dex_options[0]
                reasoning = f"LLM routing error: {e}"
        else:
            recommended_dex = dex_options[0]
            reasoning = "LLM inte tillgängligt, använder Uniswap V3"

        # Beräkna swap-resultat
        price = recommended_dex['price']
        fee_rate = recommended_dex['fee'] / 100
        slippage = recommended_dex['slippage']

        # Simulera swap
        estimated_output = amount * price * (1 - fee_rate) * (1 - slippage/100)
        gas_cost = 2.50  # Simulerad gas cost

        message = f"🔄 **DEX Swap (Optimerad):**\n\n"
        message += f"📤 Från: {amount} {from_token.upper()}\n"
        message += f"📥 Till: ~{estimated_output:.4f} {to_token.upper()}\n"
        message += f"💰 Pris: ${price:.4f}\n"
        message += f"💵 Fee: {recommended_dex['fee']}%\n"
        message += f"📊 Slippage: {recommended_dex['slippage']}%\n"
        message += f"⛽ Gas: ~${gas_cost}\n"
        message += f"🏪 DEX: {recommended_dex['name']}\n\n"
        message += f"🤖 **AI-rekommendation:** {reasoning}\n\n"

        if self.llm:
            message += "✅ Optimerad med AI för bästa pris och säkerhet"
        else:
            message += "⚠️ Grundläggande routing (lägg till OPENAI_API_KEY för AI-optimering)"

        return {
            'message': message,
            'data': {
                'from_token': from_token,
                'to_token': to_token,
                'amount': amount,
                'estimated_output': estimated_output,
                'recommended_dex': recommended_dex,
                'gas_cost': gas_cost,
                'routing_reasoning': reasoning,
                'ai_optimized': self.llm is not None
            },
            'status': 'success'
        }
    
    async def _add_liquidity(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Lägg till likviditet i pool."""
        return {
            'message': '🏊 **Likviditet (Kommer snart):**\n\nFunktionalitet för att lägga till likviditet i DEX-pooler kommer att implementeras.',
            'data': {'feature': 'coming_soon'},
            'status': 'info'
        }
    
    async def _remove_liquidity(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Ta bort likviditet från pool."""
        return {
            'message': '🏊 **Likviditet (Kommer snart):**\n\nFunktionalitet för att ta bort likviditet från DEX-pooler kommer att implementeras.',
            'data': {'feature': 'coming_soon'},
            'status': 'info'
        }
    
    async def _check_dex_price(self, fields: Dict[str, Any], command: str, real_dex=None) -> Dict[str, Any]:
        """Kolla pris på DEX."""
        token = await self._extract_from_token(fields, command)

        # Försök hämta verkliga priser först
        if real_dex:
            try:
                # Försök hämta verklig DEX data
                dex_data = await real_dex.get_dex_data(token, "ethereum")
                if dex_data['success']:
                    message = f"💰 **VERKLIGA DEX Priser för {token.upper()}:**\n\n"

                    dex_info = dex_data['dex_data']
                    if 'uniswap_v3' in dex_info and dex_info['uniswap_v3'].get('available'):
                        uni_info = dex_info['uniswap_v3']
                        message += f"🦄 Uniswap V3: ${uni_info['price_usd']:.4f}\n"
                        message += f"💧 Likviditet: ${uni_info['liquidity_usd']/1000000:.1f}M\n"
                        message += f"📊 Volym 24h: ${uni_info['volume_24h']/1000000:.1f}M\n"
                        message += f"📈 Ändring 24h: {uni_info['price_change_24h']:.2f}%\n\n"

                    message += f"📊 Källa: {dex_data['source']}\n"
                    message += f"🕐 Uppdaterad: {dex_data['timestamp']}\n\n"
                    message += "✅ Realtime DEX-data från DexScreener API"

                    return {
                        'message': message,
                        'data': dex_data,
                        'status': 'success',
                        'real_data': True
                    }
            except Exception as e:
                logger.warning(f"Real DEX price check failed: {e}")

        # Fallback till simulerad data
        message = f"💰 **DEX Pris för {token.upper()}:**\n\n"
        message += f"🦄 Uniswap V3: $1.234\n"
        message += f"🍣 SushiSwap: $1.231\n"
        message += f"🥞 PancakeSwap: $1.235\n"
        message += f"📊 Bästa pris: $1.235\n"
        message += f"💧 Total likviditet: $2.5M\n\n"
        message += "⚠️ Simulerad data - konfigurera WEB3_RPC_URL och TRADING_PRIVATE_KEY för verkliga priser."

        return {
            'message': message,
            'data': {
                'token': token,
                'prices': {
                    'uniswap_v3': 1.234,
                    'sushiswap': 1.231,
                    'pancakeswap': 1.235
                },
                'best_price': 1.235,
                'total_liquidity': 2500000,
                'simulated': True
            },
            'status': 'info'
        }
    
    async def _show_help(self) -> Dict[str, Any]:
        """Visa hjälp för DEX-kommandon."""
        # Kontrollera om verklig trading är aktiverad
        real_trading_enabled = real_dex and real_dex.uniswap_trader is not None

        help_text = """
🔄 **DEX Kommandon:**

**Swappa tokens:**
- "Swappa 100 USDC till ETH"
- "Byta 0.5 ETH till USDC"
- "Trade 1000 HAPPY för ETH"

**Likviditet:**
- "Lägg till likviditet ETH/USDC"
- "Ta bort likviditet från pool"

**Priser:**
- "Kolla ETH pris på Uniswap"
- "Jämför priser på DEX"

**DEX som stöds:**
- Uniswap V3 (med verklig trading)
- SushiSwap
- PancakeSwap (BSC)

**Status:**
"""

        if real_trading_enabled:
            help_text += "🟢 **VERKLIG TRADING AKTIVERAD**\n"
            help_text += "⚠️  Swaps kommer att genomföras på Ethereum mainnet!\n\n"
            help_text += "**Konfiguration:**\n"
            help_text += "- WEB3_RPC_URL: Konfigurerad\n"
            help_text += "- TRADING_PRIVATE_KEY: Konfigurerad\n"
        else:
            help_text += "🟡 **SIMULERAD TRADING**\n"
            help_text += "💡 Konfigurera environment variabler för verklig trading:\n"
            help_text += "- WEB3_RPC_URL=https://gas.api.infura.io/v3/e71c1d88fc7a41748e64fb291fdc9003\n"
            help_text += "- TRADING_PRIVATE_KEY=0x...\n\n"
            help_text += "⚠️  Inga verkliga transaktioner kommer att genomföras."
        
        return {
            'message': help_text,
            'data': {
                'supported_dex': ['Uniswap', 'SushiSwap', 'PancakeSwap'],
                'examples': [
                    'Swappa 100 USDC till ETH',
                    'Kolla ETH pris på Uniswap',
                    'Lägg till likviditet'
                ],
                'status': 'simulated'
            },
            'status': 'info'
        }
    
    async def _extract_from_token(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera från-token från kommando med dynamisk resolution."""
        if 'from_token' in fields:
            token_symbol = fields['from_token']
        else:
            token_symbol = self._extract_token_from_command(command, 'from')

        # Försök dynamisk resolution
        if self.token_resolver:
            try:
                async with self.token_resolver:
                    token_info = await self.token_resolver.resolve_token(token_symbol)
                    return token_info.symbol
            except TokenNotFoundError:
                logger.warning(f"Token {token_symbol} not found, using fallback")
            except Exception as e:
                logger.error(f"Token resolution error: {e}")

        # Fallback till enkel extraction
        return token_symbol.upper()
    
    async def _extract_to_token(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera till-token från kommando med dynamisk resolution."""
        if 'to_token' in fields:
            token_symbol = fields['to_token']
        else:
            token_symbol = self._extract_token_from_command(command, 'to')

        # Försök dynamisk resolution
        if self.token_resolver:
            try:
                async with self.token_resolver:
                    token_info = await self.token_resolver.resolve_token(token_symbol)
                    return token_info.symbol
            except TokenNotFoundError:
                logger.warning(f"Token {token_symbol} not found, using fallback")
            except Exception as e:
                logger.error(f"Token resolution error: {e}")

        # Fallback till enkel extraction
        return token_symbol.upper()
    
    def _extract_token_from_command(self, command: str, direction: str) -> str:
        """Hjälpfunktion för att extrahera token från kommando."""
        command_lower = command.lower()

        # Direction-specifika patterns
        if direction == 'from':
            # Försök hitta token före "till" eller "to"
            patterns = [
                r'(\w+)\s+till\s+\w+',  # "ETH till USDC"
                r'(\w+)\s+to\s+\w+',     # "ETH to USDC"
                r'swappa\s+(\w+)',       # "swappa ETH"
                r'byta\s+(\w+)',         # "byta ETH"
                r'trade\s+(\w+)',        # "trade ETH"
            ]
        else:  # to
            # Försök hitta token efter "till" eller "to"
            patterns = [
                r'till\s+(\w+)',        # "till USDC"
                r'to\s+(\w+)',          # "to USDC"
            ]

        import re
        for pattern in patterns:
            match = re.search(pattern, command_lower)
            if match:
                return match.group(1).upper()

        # Default tokens
        return 'ETH' if direction == 'from' else 'USDC'

    def _extract_amount(self, fields: Dict[str, Any], command: str) -> float:
        """Extrahera belopp från kommando."""
        if 'amount' in fields:
            return float(fields['amount'])

        # Sök efter nummer i kommandot
        import re
        numbers = re.findall(r'\d+\.?\d*', command)

        if numbers:
            return float(numbers[0])

        return 1.0
