"""
HappyOS Crypto Skill - AI-driven krypto/DeFi-funktionalitet.
"""
import logging
import yaml
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import asyncio

from ..base import Skill
from app.skills.accounting.extract_fields import extract_fields
from ..crypto.handlers.wallet import WalletHandler
from ..crypto.handlers.token import TokenHandler
from ..crypto.handlers.dex import DexHandler
from ..crypto.handlers.market import MarketHandler
from ..crypto.handlers.strategy import StrategyHandler

logger = logging.getLogger(__name__)

class CryptoSkill(Skill):
    """
    AI-driven krypto/DeFi skill för HappyOS.
    
    Features:
    - Autonom wallet-hantering
    - ERC20 token deployment på valfri EVM-chain
    - DEX-interaktion och marknadsanalys
    - AI-strategier med reinforcement learning
    - Kontinuerlig optimering och testning
    """
    
    def __init__(self):
        """Initialize CryptoSkill."""
        # Load intent mapping
        self._load_intent_map()
        
        # Initialize handlers
        self.handlers = {
            'wallet': WalletHandler(),
            'token': TokenHandler(),
            'dex': DexHandler(),
            'market': MarketHandler(),
            'strategy': StrategyHandler()
        }
        
        logger.info("HappyOS CryptoSkill initialiserad")
    
    @property
    def name(self) -> str:
        return "AI Crypto & DeFi"
    
    @property
    def description(self) -> str:
        return "Autonom krypto-agent med wallet, token deployment, DEX-trading och AI-strategier"
    
    def _load_intent_map(self):
        """Load intent mapping from YAML configuration."""
        try:
            intent_map_path = Path(__file__).parent.parent / "crypto" / "rules" / "intent_map.yaml"
            with open(intent_map_path, 'r', encoding='utf-8') as f:
                self.intent_map = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load crypto intent map: {e}")
            # Fallback intent map
            self.intent_map = {
                'wallet': {
                    'patterns': ['wallet', 'plånbok', 'address', 'adress', 'balance', 'saldo'],
                    'actions': ['skapa', 'visa', 'skicka', 'ta_emot', 'importera']
                },
                'token': {
                    'patterns': ['token', 'coin', 'mynt', 'erc20', 'deploya', 'skapa_token'],
                    'actions': ['skapa', 'deploya', 'visa', 'transfer', 'approve']
                },
                'dex': {
                    'patterns': ['dex', 'swap', 'byta', 'uniswap', 'sushiswap', 'trade'],
                    'actions': ['swap', 'add_liquidity', 'remove_liquidity', 'check_price']
                },
                'market': {
                    'patterns': ['pris', 'price', 'marknad', 'market', 'analys', 'trending'],
                    'actions': ['check_price', 'analyze', 'trending', 'signals']
                },
                'strategy': {
                    'patterns': ['strategi', 'strategy', 'optimera', 'ai', 'ml', 'reinforcement'],
                    'actions': ['create', 'run', 'optimize', 'backtest', 'stop']
                }
            }
    
    async def run(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point för crypto skill.
        
        Args:
            input_data: Contains command, intent, user_id, extracted_data, etc.
            context: Current conversation context including user_context from Happy AI
            
        Returns:
            Response with message, data, and any required actions
        """
        try:
            command = input_data.get("command", "")
            user_id = input_data.get("user_id", "default_user")
            
            # Get user context from Happy AI
            user_context = context.get("user_context", {})
            
            # Use pre-extracted data from intent classifier if available
            extracted_fields = input_data.get("extracted_data", {})
            
            # If no pre-extracted data, use Happy AI's global field extractor
            if not extracted_fields:
                extracted_fields = extract_fields(command)
            
            # Get intent and action from input_data (already classified by Happy AI)
            intent = input_data.get("intent", "general")
            action = input_data.get("action", "default")
            
            # If not provided, determine intent and action using legacy method
            if intent == "general":
                intent, action = self._route_intent(command, extracted_fields)
            
            # Get appropriate handler
            handler = self.handlers.get(intent)
            if not handler:
                return self._handle_unknown_intent(command, extracted_fields)
            
            # Prepare handler input
            handler_input = {
                'command': command,
                'action': action,
                'fields': extracted_fields,
                'user_context': user_context,
                'global_context': context,
                'input_data': input_data,
                'user_id': user_id
            }
            
            # Execute handler
            result = await handler.handle(handler_input)
            
            # Prepare context updates for Happy AI's UserMemory
            update_context = {}
            
            # Add crypto-specific facts to user memory
            if result.get('data'):
                crypto_facts = {}
                
                # Store recent crypto actions
                if intent and action:
                    crypto_facts[f"last_{intent}_action"] = {
                        "action": action,
                        "timestamp": datetime.now().isoformat(),
                        "command": command,
                        "result": result.get('status', 'completed')
                    }
                
                # Store important crypto data
                if intent == 'wallet' and result.get('data', {}).get('address'):
                    crypto_facts['primary_wallet'] = result['data']['address']
                
                if intent == 'token' and result.get('data', {}).get('contract_address'):
                    crypto_facts['last_deployed_token'] = {
                        'address': result['data']['contract_address'],
                        'name': result['data'].get('token_name'),
                        'symbol': result['data'].get('token_symbol')
                    }
                
                if crypto_facts:
                    update_context['facts'] = crypto_facts
            
            # Add crypto preferences if handler suggests any
            if result.get('preferences'):
                update_context['preferences'] = result['preferences']
            
            # Add to history
            update_context['history'] = {
                "type": "crypto_action",
                "intent": intent,
                "action": action,
                "result": result.get('status', 'completed'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add metadata
            result['metadata'] = {
                'skill': 'CryptoSkill',
                'intent': intent,
                'action': action,
                'extracted_fields': extracted_fields,
                'timestamp': datetime.now().isoformat(),
                'handler': handler.__class__.__name__
            }
            
            # Include context updates for Happy AI
            if update_context:
                result['update_context'] = update_context
            
            return result
            
        except Exception as e:
            logger.error(f"Error in HappyOS CryptoSkill: {e}", exc_info=True)
            return {
                'message': 'Ett fel uppstod i krypto-systemet. Försök igen.',
                'data': {'error': str(e)},
                'status': 'error',
                'metadata': {
                    'skill': 'CryptoSkill',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
            }
    
    def _route_intent(self, command: str, fields: Dict[str, Any]) -> Tuple[str, str]:
        """
        Route command to appropriate intent and action based on patterns.
        
        Args:
            command: User command
            fields: Extracted fields
            
        Returns:
            Tuple of (intent, action)
        """
        command_lower = command.lower()
        
        # Check for explicit intent in fields
        if 'intent' in fields:
            return fields['intent'], fields.get('action', 'default')
        
        # Pattern matching against intent map
        for intent, config in self.intent_map.items():
            patterns = config.get('patterns', [])
            actions = config.get('actions', [])
            
            # Check if any pattern matches
            if any(pattern in command_lower for pattern in patterns):
                # Find specific action
                action = 'default'
                for act in actions:
                    if act in command_lower:
                        action = act
                        break
                
                return intent, action
        
        # Default fallback
        return 'market', 'help'
    
    def _handle_unknown_intent(self, command: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown intents with helpful suggestions."""
        suggestions = [
            "Skapa ny wallet",
            "Deploya ERC20 token på Base",
            "Kolla pris på ethereum",
            "Starta AI trading-strategi",
            "Visa trending tokens",
            "Swappa tokens på Uniswap"
        ]
        
        return {
            'message': 'Jag förstod inte riktigt vad du vill göra med krypto. Här är några exempel:',
            'data': {
                'suggestions': suggestions,
                'extracted_fields': fields
            },
            'status': 'clarification_needed',
            'metadata': {
                'skill': 'CryptoSkill',
                'timestamp': datetime.now().isoformat(),
                'handler': 'UnknownIntentHandler'
            }
        }
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """Return list of capabilities this skill provides."""
        return [
            {
                'name': 'Wallet Management',
                'description': 'Skapa, hantera och övervaka krypto-wallets',
                'examples': ['Skapa ny wallet', 'Visa wallet-saldo', 'Skicka ETH till adress']
            },
            {
                'name': 'Token Deployment',
                'description': 'Deploya ERC20 tokens på valfri EVM-chain',
                'examples': ['Deploya HappyToken på Base', 'Skapa token med 1M supply']
            },
            {
                'name': 'DEX Trading',
                'description': 'Interagera med decentraliserade börser',
                'examples': ['Swappa ETH till USDC', 'Lägg till likviditet på Uniswap']
            },
            {
                'name': 'Market Analysis',
                'description': 'Analysera marknadsdata och generera signaler',
                'examples': ['Kolla pris på bitcoin', 'Visa trending tokens', 'Analysera ethereum']
            },
            {
                'name': 'AI Strategies',
                'description': 'Autonoma trading-strategier med reinforcement learning',
                'examples': ['Starta AI-strategi', 'Optimera portfolio', 'Backtesta strategi']
            }
        ]
    
    def get_intents(self) -> List[str]:
        """Return list of intents this skill handles."""
        return list(self.intent_map.keys()) + ['general']
