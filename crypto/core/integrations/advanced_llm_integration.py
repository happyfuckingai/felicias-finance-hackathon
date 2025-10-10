"""
Avancerad LLM-integration för crypto-hanteringssystemet.
Kombinerar tekniska indikatorer, sentiment-analys och AI-driven beslutsfattande.
"""
import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class AdvancedLLMTradingAdvisor:
    """AI-driven trading advisor som kombinerar teknisk analys med LLM-insikter"""

    def __init__(self):
        self.llm_client = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initiera LLM-klient för avancerade analyser"""
        try:
            from crypto.core.llm_integration import LLMClient
            self.llm_client = LLMClient()
            asyncio.run(self.llm_client.initialize())
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")
            self.llm_client = None

    async def generate_comprehensive_trading_signal(self, token_id: str) -> Dict[str, Any]:
        """
        Generera omfattande trading-signal med AI-analys
        Kombinerar tekniska indikatorer, sentiment, nyheter och marknadsinformation
        """
        try:
            # Samla all tillgänglig data
            market_data = await self._gather_market_intelligence(token_id)

            # Analysera med LLM
            if self.llm_client:
                analysis = await self._llm_comprehensive_analysis(token_id, market_data)

                # Generera trading-rekommendation
                recommendation = await self._generate_ai_recommendation(token_id, analysis)

                return {
                    'success': True,
                    'token_id': token_id,
                    'timestamp': datetime.now().isoformat(),
                    'market_data': market_data,
                    'ai_analysis': analysis,
                    'trading_recommendation': recommendation,
                    'confidence_score': recommendation.get('confidence', 0),
                    'risk_assessment': recommendation.get('risk_assessment', {})
                }

            else:
                # Fallback till grundläggande analys
                return await self._fallback_analysis(token_id)

        except Exception as e:
            logger.error(f"Comprehensive analysis failed for {token_id}: {e}")
            return {'success': False, 'error': str(e), 'token_id': token_id}

    async def _gather_market_intelligence(self, token_id: str) -> Dict[str, Any]:
        """Samla omfattande marknadsinformation"""
        intelligence = {
            'technical_indicators': {},
            'sentiment_data': {},
            'news_analysis': {},
            'on_chain_metrics': {},
            'market_context': {}
        }

        try:
            # Tekniska indikatorer
            from crypto.core.technical_indicators import TechnicalAnalyzer
            tech_analyzer = TechnicalAnalyzer()
            intelligence['technical_indicators'] = await tech_analyzer.get_all_indicators(token_id)

            # Sentiment från flera källor
            from crypto.core.news_integration import NewsAnalyzer
            news_analyzer = NewsAnalyzer()
            intelligence['sentiment_data'] = await news_analyzer.get_comprehensive_sentiment(token_id)

            # On-chain metrics
            intelligence['on_chain_metrics'] = await self._get_on_chain_data(token_id)

            # Marknadskontext
            intelligence['market_context'] = await self._get_market_context()

        except Exception as e:
            logger.warning(f"Market intelligence gathering failed: {e}")

        return intelligence

    async def _llm_comprehensive_analysis(self, token_id: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Avancerad LLM-analys av all tillgänglig data"""

        prompt = f"""
        Du är en expert crypto-trading analytiker med djup kunskap om teknisk analys,
        sentimentanalys och marknadspykologi. Analysera följande omfattande data för {token_id.upper()}:

        TEKNISKA INDIKATORER:
        {json.dumps(market_data.get('technical_indicators', {}), indent=2)}

        SENTIMENT ANALYS:
        {json.dumps(market_data.get('sentiment_data', {}), indent=2)}

        ON-CHAIN METRICS:
        {json.dumps(market_data.get('on_chain_metrics', {}), indent=2)}

        MARKNADSKONTEXT:
        {json.dumps(market_data.get('market_context', {}), indent=2)}

        Genomför en omfattande analys och svara med följande struktur:
        {{
            "trend_analysis": {{
                "primary_trend": "bullish/bearish/sideways",
                "trend_strength": "strong/moderate/weak",
                "timeframe": "short/medium/long",
                "key_levels": {{
                    "support": [prisnivåer],
                    "resistance": [prisnivåer]
                }}
            }},
            "sentiment_assessment": {{
                "overall_sentiment": "positive/negative/neutral",
                "sentiment_drivers": ["nyckelfaktorer"],
                "social_volume": "high/medium/low",
                "fear_greed_index": "nummer eller beskrivning"
            }},
            "risk_factors": {{
                "high_risk_factors": ["faktorer"],
                "medium_risk_factors": ["faktorer"],
                "low_risk_factors": ["faktorer"]
            }},
            "catalysts": {{
                "positive_catalysts": ["händelser"],
                "negative_catalysts": ["händelser"],
                "upcoming_events": ["framtida händelser"]
            }},
            "quantitative_signals": {{
                "momentum_score": "nummer",
                "volatility_score": "nummer",
                "liquidity_score": "nummer",
                "volume_analysis": "beskrivning"
            }},
            "market_context": {{
                "sector_performance": "beskrivning",
                "correlation_analysis": "beskrivning",
                "macro_factors": ["faktorer"]
            }},
            "ai_insights": {{
                "pattern_recognition": "beskrivning av mönster",
                "anomaly_detection": "eventuella anomalier",
                "predictive_elements": "förutsägelser"
            }}
        }}

        Var analytisk, objektiv och basera dina slutsatser på data.
        Fokusera på handlingsbara insikter snarare än allmänna råd.
        """

        try:
            response = await self.llm_client.analyze_market(prompt)
            return json.loads(response.get('analysis', '{}'))
        except Exception as e:
            logger.error(f"LLM comprehensive analysis failed: {e}")
            return self._generate_fallback_analysis(market_data)

    async def _generate_ai_recommendation(self, token_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generera AI-driven trading-rekommendation baserat på analys"""

        prompt = f"""
        Baserat på följande omfattande analys för {token_id.upper()},
        generera en specifik trading-rekommendation:

        ANALYS:
        {json.dumps(analysis, indent=2)}

        Ge en rekommendation med följande struktur:
        {{
            "action": "BUY/SELL/HOLD",
            "confidence": 0.0-1.0,
            "time_horizon": "kort/medel/lång",
            "position_size": "konservativ/måttlig/aggressiv",
            "entry_price_range": "prisintervall eller strategi",
            "exit_strategy": {{
                "take_profit_levels": [nivåer],
                "stop_loss_level": "nivå",
                "trailing_stop": "ja/nej"
            }},
            "rationale": "detaljerad förklaring av beslutet",
            "risk_assessment": {{
                "overall_risk": "låg/medel/hög",
                "key_risks": ["riskfaktorer"],
                "mitigation_strategies": ["strategier"]
            }},
            "alternative_scenarios": {{
                "bull_case": "beskrivning och åtgärd",
                "bear_case": "beskrivning och åtgärd",
                "base_case": "beskrivning och åtgärd"
            }}
        }}

        Var specifik och handlingsbar. Fokusera på sannolika utfall snarare än extrema scenarier.
        """

        try:
            response = await self.llm_client.generate_recommendation(prompt)
            return json.loads(response.get('recommendation', '{}'))
        except Exception as e:
            logger.error(f"AI recommendation generation failed: {e}")
            return self._generate_conservative_recommendation()

    async def _get_on_chain_data(self, token_id: str) -> Dict[str, Any]:
        """Hämta on-chain metrics"""
        try:
            # Placeholder för on-chain data
            # I verkligheten skulle detta ansluta till block explorers,
            # Whale tracking, DEX volume, etc.
            return {
                'active_addresses': 'N/A',
                'transaction_volume': 'N/A',
                'large_holder_distribution': 'N/A',
                'network_health': 'N/A',
                'developer_activity': 'N/A'
            }
        except Exception as e:
            logger.warning(f"On-chain data fetch failed: {e}")
            return {}

    async def _get_market_context(self) -> Dict[str, Any]:
        """Hämta övergripande marknadskontext"""
        try:
            # Placeholder för market context
            return {
                'bitcoin_dominance': 'N/A',
                'total_market_cap': 'N/A',
                'fear_greed_index': 'N/A',
                'sector_performance': 'N/A',
                'macro_indicators': 'N/A'
            }
        except Exception as e:
            logger.warning(f"Market context fetch failed: {e}")
            return {}

    def _generate_fallback_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback-analys när LLM inte är tillgänglig"""
        return {
            'trend_analysis': {
                'primary_trend': 'neutral',
                'trend_strength': 'moderate',
                'timeframe': 'medium'
            },
            'sentiment_assessment': {
                'overall_sentiment': 'neutral',
                'sentiment_drivers': ['Limited data available']
            },
            'risk_factors': {
                'high_risk_factors': ['Limited analysis capability'],
                'medium_risk_factors': ['Market volatility'],
                'low_risk_factors': []
            },
            'catalysts': {
                'positive_catalysts': [],
                'negative_catalysts': [],
                'upcoming_events': []
            }
        }

    def _generate_conservative_recommendation(self) -> Dict[str, Any]:
        """Konservativ rekommendation när LLM inte är tillgänglig"""
        return {
            'action': 'HOLD',
            'confidence': 0.5,
            'time_horizon': 'medium',
            'position_size': 'konservativ',
            'rationale': 'Begränsad analys tillgänglig - avvakta bättre data',
            'risk_assessment': {
                'overall_risk': 'medium',
                'key_risks': ['Limited market intelligence'],
                'mitigation_strategies': ['Diversifiera positioner', 'Använd stop-loss']
            }
        }

    async def _fallback_analysis(self, token_id: str) -> Dict[str, Any]:
        """Komplett fallback när ingenting fungerar"""
        return {
            'success': True,
            'token_id': token_id,
            'timestamp': datetime.now().isoformat(),
            'fallback': True,
            'message': 'AI-analys inte tillgänglig - använder grundläggande strategi',
            'trading_recommendation': {
                'action': 'HOLD',
                'confidence': 0.3,
                'rationale': 'System i fallback-läge'
            }
        }

class ConversationalTradingAssistant:
    """Naturlig språk-baserad trading-assistent"""

    def __init__(self):
        self.llm_client = None
        self.trading_advisor = AdvancedLLMTradingAdvisor()
        self._initialize_llm()

    def _initialize_llm(self):
        """Initiera LLM för konversation"""
        try:
            from crypto.core.llm_integration import LLMClient
            self.llm_client = LLMClient()
            asyncio.run(self.llm_client.initialize())
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")

    async def process_natural_language_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Bearbeta naturligt språk-frågor om trading
        Exempel: "Ska jag köpa mer Bitcoin?", "Vad tycker du om ETH idag?"
        """

        if not self.llm_client:
            return {'success': False, 'error': 'AI-assistent inte tillgänglig'}

        # Förstå användarens intent
        intent_analysis = await self._analyze_user_intent(user_query, context)

        # Generera lämpligt svar baserat på intent
        if intent_analysis['intent'] == 'trading_advice':
            return await self._handle_trading_query(user_query, intent_analysis)

        elif intent_analysis['intent'] == 'market_analysis':
            return await self._handle_market_query(user_query, intent_analysis)

        elif intent_analysis['intent'] == 'portfolio_management':
            return await self._handle_portfolio_query(user_query, intent_analysis)

        else:
            return await self._handle_general_query(user_query, intent_analysis)

    async def _analyze_user_intent(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analysera användarens intent från naturligt språk"""

        prompt = f"""
        Analysera följande användarfråga och identifiera intent och relevanta entiteter:

        Fråga: "{query}"

        Kontext: {json.dumps(context or {}, indent=2)}

        Svara med följande struktur:
        {{
            "intent": "trading_advice/market_analysis/portfolio_management/general",
            "confidence": 0.0-1.0,
            "entities": {{
                "tokens": ["token_symboler"],
                "actions": ["köp/sälj/håll/etc"],
                "timeframes": ["kort/medel/lång"],
                "amounts": ["värden"],
                "risk_levels": ["konservativ/aggressiv"]
            }},
            "sentiment": "positiv/negativ/neutral",
            "urgency": "hög/medel/låg"
        }}
        """

        try:
            response = await self.llm_client.analyze_intent(prompt)
            return json.loads(response.get('intent_analysis', '{}'))
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {
                'intent': 'general',
                'confidence': 0.5,
                'entities': {},
                'sentiment': 'neutral',
                'urgency': 'medium'
            }

    async def _handle_trading_query(self, query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Hantera trading-relaterade frågor"""

        tokens = intent['entities'].get('tokens', [])

        if not tokens:
            # Försök extrahera tokens från frågan
            tokens = self._extract_tokens_from_text(query)

        if tokens:
            # Ge råd för första token
            token = tokens[0].lower()
            signal = await self.trading_advisor.generate_comprehensive_trading_signal(token)

            if signal['success']:
                recommendation = signal['trading_recommendation']

                response = f"""
                📊 Trading-råd för {token.upper()}

                🎯 Rekommendation: **{recommendation['action']}**
                📈 Tillförlitlighet: {recommendation.get('confidence', 0):.1%}
                ⏰ Tidshorisont: {recommendation.get('time_horizon', 'medium')}

                💡 Förklaring:
                {recommendation.get('rationale', 'Analys baserad på tekniska och fundamentala faktorer')}

                🎚️ Risknivå: {recommendation.get('risk_assessment', {}).get('overall_risk', 'medium').upper()}

                📋 Nästa steg:
                • Överväg position sizing på {recommendation.get('position_size', 'moderate')}
                • Sätt stop-loss vid {recommendation.get('exit_strategy', {}).get('stop_loss_level', 'marknadsvärdering')}
                """

                return {
                    'success': True,
                    'response_type': 'trading_advice',
                    'message': response.strip(),
                    'signal_data': signal
                }

        return {
            'success': False,
            'response_type': 'trading_advice',
            'message': 'Jag kunde inte identifiera några specifika tokens att ge råd om. Försök nämna en kryptovaluta som Bitcoin eller Ethereum.'
        }

    def _extract_tokens_from_text(self, text: str) -> List[str]:
        """Extrahera token-namn från naturligt språk"""
        # Enkel heuristik - kan förbättras med bättre NLP
        known_tokens = {
            'bitcoin': ['bitcoin', 'btc', 'xbt'],
            'ethereum': ['ethereum', 'eth', 'ether'],
            'solana': ['solana', 'sol'],
            'cardano': ['cardano', 'ada'],
            'polygon': ['polygon', 'matic'],
            'avalanche': ['avalanche', 'avax'],
            'chainlink': ['chainlink', 'link'],
            'uniswap': ['uniswap', 'uni']
        }

        found_tokens = []
        text_lower = text.lower()

        for token, keywords in known_tokens.items():
            if any(keyword in text_lower for keyword in keywords):
                found_tokens.append(token)

        return found_tokens

    async def _handle_market_query(self, query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Hantera marknadsanalys-frågor"""
        # Implementation för marknadsfrågor
        return {
            'success': True,
            'response_type': 'market_analysis',
            'message': 'Marknadsanalys-funktionalitet är under utveckling.'
        }

    async def _handle_portfolio_query(self, query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Hantera portfölj-frågor"""
        # Implementation för portföljfrågor
        return {
            'success': True,
            'response_type': 'portfolio_management',
            'message': 'Portföljhantering är under utveckling.'
        }

    async def _handle_general_query(self, query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Hantera allmänna frågor"""
        return {
            'success': True,
            'response_type': 'general',
            'message': 'Jag är en AI-driven crypto-trading assistent. Jag kan hjälpa dig med trading-råd, marknadsanalys och portföljhantering. Vad vill du veta?'
        }

# Globala instanser
advanced_llm_advisor = AdvancedLLMTradingAdvisor()
conversational_assistant = ConversationalTradingAssistant()