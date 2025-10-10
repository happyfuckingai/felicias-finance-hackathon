"""
Intent Processing för naturlig språkförståelse.
Tolkar naturliga kommandon till strukturerade intents.
"""
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class IntentProcessor:
    """Bearbetar naturliga språkkommandon till strukturerade intents."""

    def __init__(self):
        self.intents = self._load_intent_patterns()

    def _load_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Ladda intent patterns och deras matchningsregler."""
        return {
            'create_wallet': {
                'patterns': [
                    r'(?:skapa|generera|create|make|new)\s+(?:ny|en)?\s*(?:wallet|plån|konto)',
                    r'(?:jag\s+vill\s+ha|give\s+me)\s+(?:en\s+)?(?:ny\s+)?(?:wallet|plån)',
                    r'(?:set\s+up|skaffa)\s+(?:en\s+)?(?:ny\s+)?(?:wallet|plån)'
                ],
                'action': 'create_wallet',
                'confidence_boost': 0.9
            },

            'show_balance': {
                'patterns': [
                    r'(?:visa|show|kolla|check)\s+(?:saldo|balance|plån|wallet)',
                    r'(?:hur\s+många|how\s+much)\s+(?:eth|tokens?|krypta|crypto)\s+(?:har\s+jag|do\s+i\s+have)',
                    r'(?:mitt|my)\s+(?:saldo|balance|plån)'
                ],
                'action': 'show_balance',
                'confidence_boost': 0.8
            },

            'send_transaction': {
                'patterns': [
                    r'(?:skicka|send|transfer|flytta)\s+(\d+(?:\.\d+)?)\s+(?:eth|tokens?)\s+(?:till|to)\s+([0-9a-fx]+)',
                    r'(?:skicka|send)\s+(\d+(?:\.\d+)?)\s+(?:eth|ethereum)\s+(?:till|to)\s+(0x[0-9a-fA-F]{40})',
                    r'(?:transfer|flytta)\s+(\d+(?:\.\d+)?)\s+(?:eth|tokens?)\s+(?:till|to)\s+([0-9a-fx]+)'
                ],
                'action': 'send_transaction',
                'extract_fields': ['amount', 'to_address'],
                'confidence_boost': 0.95
            },

            'deploy_token': {
                'patterns': [
                    r'(?:deploya|deploy|skapa|create)\s+(?:en\s+)?(?:ny\s+)?(?:token|erc20)',
                    r'(?:jag\s+vill\s+)?(?:deploya|deploy)\s+(?:en\s+)?(?:token|erc20)\s+(?:med\s+namn\s+)?(\w+)\s+(?:och\s+symbol\s+)?(\w+)',
                    r'(?:launch|starta)\s+(?:en\s+)?(?:ny\s+)?(?:token|erc20)'
                ],
                'action': 'deploy_token',
                'extract_fields': ['token_name', 'token_symbol', 'total_supply'],
                'confidence_boost': 0.85
            },

            'check_price': {
                'patterns': [
                    r'(?:kolla|check|visa|show)\s+(?:pris|price|värde|value)\s+(?:på|of|för|for)\s+(\w+)',
                    r'(?:vad\s+)?(?:kostar|costs|är\s+priset)\s+(?:på|of|för|for)\s+(\w+)',
                    r'(?:hur\s+många|how\s+much)\s+(?:usd|kr|dollar)\s+(?:är|is)\s+(\w+)',
                    r'(\w+)\s+(?:pris|price|värde|value)'
                ],
                'action': 'check_price',
                'extract_fields': ['token_id'],
                'confidence_boost': 0.9
            },

            'analyze_token': {
                'patterns': [
                    r'(?:analysera|analyze|granska|review)\s+(\w+)\s+(?:över|over)\s+(\d+)\s+(?:dagar|days)',
                    r'(?:visa|show)\s+(?:trend|utveckling|development)\s+(?:för|of)\s+(\w+)',
                    r'(?:hur\s+har|how\s+has)\s+(\w+)\s+(?:utvecklats|developed)\s+(?:den\s+sista\s+tiden|recently)'
                ],
                'action': 'analyze_token',
                'extract_fields': ['token_id', 'days'],
                'confidence_boost': 0.85
            },

            'get_trending': {
                'patterns': [
                    r'(?:visa|show|kolla|check)\s+(?:trending|trendande|populära|popular)\s+(?:tokens?|krypta|crypto)',
                    r'(?:vad\s+är|what\s+is)\s+(?:hett|hot|trending)\s+(?:just\s+nu|right\s+now|nu)',
                    r'(?:vilka\s+tokens|which\s+tokens)\s+(?:är\s+heta|are\s+hot)'
                ],
                'action': 'get_trending',
                'confidence_boost': 0.8
            },

            'generate_signal': {
                'patterns': [
                    r'(?:generera|generate|ge|get)\s+(?:signal|signals)\s+(?:för|of|on)\s+(\w+)',
                    r'(?:ska\s+jag|should\s+i)\s+(?:köpa|buy|sälja|sell|hâlla|hold)\s+(\w+)',
                    r'(?:vad\s+säger|what\s+does)\s+(?:analysen|analysis)\s+(?:säga|say)\s+(?:om|about)\s+(\w+)'
                ],
                'action': 'generate_signal',
                'extract_fields': ['token_id'],
                'confidence_boost': 0.8
            },

            'swap_tokens': {
                'patterns': [
                    r'(?:swappa|swap|byta|trade|växla)\s+(\d+(?:\.\d+)?)\s+(\w+)\s+(?:till|to|för|for)\s+(\w+)',
                    r'(?:swappa|swap)\s+(\d+(?:\.\d+)?)\s+(\w+)\s+(?:mot|against)\s+(\w+)',
                    r'(?:jag\s+vill\s+)?(?:byta|trade)\s+(\d+(?:\.\d+)?)\s+(\w+)\s+(?:till|to)\s+(\w+)'
                ],
                'action': 'swap_tokens',
                'extract_fields': ['amount', 'from_token', 'to_token'],
                'confidence_boost': 0.9
            },

            'research_token': {
                'patterns': [
                    r'(?:research|forska|granska|analyze)\s+(\w+)\s+(?:fundamentals|grunderna|projektet)',
                    r'(?:berätta|tell\s+me)\s+(?:mer\s+om|about)\s+(\w+)\s+(?:projekt|project)',
                    r'(?:vad\s+veta|what\s+to\s+know)\s+(?:om|about)\s+(\w+)'
                ],
                'action': 'research_token',
                'extract_fields': ['token_id'],
                'confidence_boost': 0.8
            },

            'analyze_sentiment': {
                'patterns': [
                    r'(?:sentiment|känsla|stämning)\s+(?:för|of|on)\s+(\w+)',
                    r'(?:hur\s+ känns|how\s+does)\s+(?:marknaden|market)\s+(?:känna|feel)\s+(?:för|about)\s+(\w+)',
                    r'(?:vad\s+är|what\s+is)\s+(?:sentiment|känsla)\s+(?:för|of)\s+(\w+)'
                ],
                'action': 'analyze_sentiment',
                'extract_fields': ['token_id'],
                'confidence_boost': 0.8
            }
        }

    async def process_intent(self, command: str) -> Dict[str, Any]:
        """
        Bearbeta ett naturligt språkkommando till strukturerad intent.

        Args:
            command: Naturligt språkkommando

        Returns:
            Strukturerad intent med action, fields och confidence
        """
        try:
            # Normalisera kommandot
            command = self._normalize_command(command)

            # Hitta bästa matchande intent
            best_match = self._find_best_intent(command)

            if best_match:
                # Extrahera fält från kommandot
                fields = self._extract_fields(command, best_match)

                return {
                    'success': True,
                    'intent': best_match['action'],
                    'fields': fields,
                    'confidence': best_match['confidence'],
                    'original_command': command,
                    'matched_pattern': best_match.get('matched_pattern', ''),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'intent': 'unknown',
                    'fields': {},
                    'confidence': 0.0,
                    'original_command': command,
                    'error': 'Could not understand command',
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error processing intent: {e}")
            return {
                'success': False,
                'intent': 'error',
                'fields': {},
                'confidence': 0.0,
                'original_command': command,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _normalize_command(self, command: str) -> str:
        """Normalisera kommandot för bättre matchning."""
        # Konvertera till lowercase
        command = command.lower()

        # Ta bort extra whitespace
        command = ' '.join(command.split())

        # Ersätt svenska tecken
        replacements = {
            'å': 'a', 'ä': 'a', 'ö': 'o',
            'Å': 'a', 'Ä': 'a', 'Ö': 'o'
        }

        for old, new in replacements.items():
            command = command.replace(old, new)

        return command

    def _find_best_intent(self, command: str) -> Optional[Dict[str, Any]]:
        """Hitta bästa matchande intent för kommandot."""
        best_match = None
        best_confidence = 0.0

        for intent_name, intent_config in self.intents.items():
            for pattern in intent_config['patterns']:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    # Beräkna confidence baserat på match-kvalitet
                    confidence = self._calculate_confidence(command, pattern, match)

                    # Tillämpa confidence boost från config
                    confidence *= intent_config.get('confidence_boost', 0.8)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {
                            'action': intent_config['action'],
                            'confidence': confidence,
                            'matched_pattern': pattern,
                            'extract_fields': intent_config.get('extract_fields', []),
                            'match_groups': match.groups() if match else ()
                        }

        return best_match if best_confidence > 0.3 else None

    def _calculate_confidence(self, command: str, pattern: str, match: re.Match) -> float:
        """Beräkna confidence för en match."""
        # Grund-confidence baserat på match-längd
        match_length = len(match.group(0))
        command_length = len(command)

        length_ratio = match_length / command_length

        # Bonus för exakta matches
        exact_bonus = 1.5 if match.group(0).strip() == command.strip() else 1.0

        # Bonus för många capture groups (bättre struktur)
        group_bonus = 1.0 + (len(match.groups()) * 0.1)

        confidence = min(length_ratio * exact_bonus * group_bonus, 1.0)

        return confidence

    def _extract_fields(self, command: str, intent_match: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahera fält från kommandot baserat på intent."""
        fields = {}
        extract_fields = intent_match.get('extract_fields', [])
        match_groups = intent_match.get('match_groups', ())

        # Map extract fields to match groups
        for i, field_name in enumerate(extract_fields):
            if i < len(match_groups) and match_groups[i]:
                fields[field_name] = self._clean_field_value(match_groups[i], field_name)

        # Fallback extraction för vanliga fält
        if not fields.get('token_id'):
            fields['token_id'] = self._extract_token_id(command)

        if not fields.get('amount') and 'amount' in extract_fields:
            fields['amount'] = self._extract_amount(command)

        if not fields.get('to_address') and 'to_address' in extract_fields:
            fields['to_address'] = self._extract_address(command)

        if not fields.get('days') and 'days' in extract_fields:
            fields['days'] = self._extract_days(command)

        return fields

    def _clean_field_value(self, value: str, field_name: str) -> Any:
        """Rensa och validera extraherade fältvärden."""
        try:
            if field_name == 'amount':
                # Extrahera numeriskt värde
                numbers = re.findall(r'\d+(?:\.\d+)?', str(value))
                return float(numbers[0]) if numbers else 0.0

            elif field_name == 'token_id':
                return self._normalize_token_id(str(value))

            elif field_name == 'to_address':
                # Validera Ethereum-adress
                addr = str(value).strip()
                if re.match(r'^0x[0-9a-fA-F]{40}$', addr):
                    return addr
                return None

            elif field_name == 'days':
                return int(re.findall(r'\d+', str(value))[0])

            else:
                return str(value).strip()

        except Exception as e:
            logger.warning(f"Error cleaning field {field_name}: {e}")
            return str(value).strip()

    def _extract_token_id(self, command: str) -> str:
        """Extrahera token ID från kommando med hjälp av ordbok."""
        token_keywords = {
            'bitcoin': 'bitcoin',
            'btc': 'bitcoin',
            'ethereum': 'ethereum',
            'eth': 'ethereum',
            'cardano': 'cardano',
            'ada': 'cardano',
            'solana': 'solana',
            'sol': 'solana',
            'polygon': 'matic-network',
            'matic': 'matic-network',
            'chainlink': 'chainlink',
            'link': 'chainlink',
            'polkadot': 'polkadot',
            'dot': 'polkadot',
            'avalanche': 'avalanche-2',
            'avax': 'avalanche-2',
            'uniswap': 'uniswap',
            'uni': 'uniswap'
        }

        for keyword, token_id in token_keywords.items():
            if keyword in command:
                return token_id

        return 'bitcoin'  # Default

    def _extract_amount(self, command: str) -> float:
        """Extrahera numeriskt belopp från kommando."""
        numbers = re.findall(r'\d+(?:\.\d+)?', command)
        return float(numbers[0]) if numbers else 1.0

    def _extract_address(self, command: str) -> Optional[str]:
        """Extrahera Ethereum-adress från kommando."""
        address_match = re.search(r'0x[0-9a-fA-F]{40}', command)
        return address_match.group(0) if address_match else None

    def _extract_days(self, command: str) -> int:
        """Extrahera antal dagar från kommando."""
        day_match = re.search(r'(\d+)\s*(?:dagar|days|dag|day)', command, re.IGNORECASE)
        if day_match:
            return int(day_match.group(1))
        return 7  # Default

    def _normalize_token_id(self, token: str) -> str:
        """Normalisera token identifierare."""
        token = token.lower().strip()

        # Map common abbreviations
        token_mapping = {
            'btc': 'bitcoin',
            'eth': 'ethereum',
            'ada': 'cardano',
            'sol': 'solana',
            'matic': 'matic-network',
            'dot': 'polkadot',
            'avax': 'avalanche-2',
            'uni': 'uniswap',
            'link': 'chainlink'
        }

        return token_mapping.get(token, token)

    async def get_supported_commands(self) -> List[Dict[str, Any]]:
        """Returnera lista över alla supporterade kommandon."""
        commands = []

        for intent_name, config in self.intents.items():
            commands.append({
                'intent': intent_name,
                'action': config['action'],
                'examples': [pattern for pattern in config['patterns'][:2]],  # Visa 2 exempel
                'confidence_boost': config.get('confidence_boost', 0.8)
            })

        return commands