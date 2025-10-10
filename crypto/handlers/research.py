"""
Research Handler för HappyOS Crypto - LLM-driven fundamental analys.
"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ResearchHandler:
    """Hanterar fundamental analys och research med LLM."""

    def __init__(self):
        """Initialize ResearchHandler."""
        self.llm = None

        # Load environment variables from .env file
        try:
            from dotenv import load_dotenv
            import os
            env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        except ImportError:
            logger.warning("python-dotenv not available, using system environment variables")
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")

        # Initiera LLM om tillgängligt
        try:
            import os
            if os.getenv('OPENROUTER_API_KEY'):
                from ..core.llm_integration import LLMIntegration
                self.llm = LLMIntegration()
                logger.info("LLM initialized successfully in ResearchHandler")
            else:
                logger.warning("OPENROUTER_API_KEY not found, LLM disabled")
        except ImportError:
            logger.warning("LLM integration not available for research")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")

        logger.info("ResearchHandler initialiserad - LLM tillgänglig: %s", self.llm is not None)

    async def handle(self, handler_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle research-relaterade kommandon.

        Args:
            handler_input: Input från CryptoSkill

        Returns:
            Result av research-operationen
        """
        action = handler_input.get('action', 'default')
        fields = handler_input.get('fields', {})
        command = handler_input.get('command', '')

        try:
            if action in ['research', 'analysera', 'fundamentals', 'granska']:
                return await self._research_token(fields, command)
            elif action in ['sentiment', 'känsla', 'marknadsstämning']:
                return await self._analyze_sentiment(fields, command)
            else:
                return await self._show_help()

        except Exception as e:
            logger.error(f"Fel i ResearchHandler: {e}")
            return {
                'message': f'Ett fel uppstod vid research-analys: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }

    async def _research_token(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Genomför fundamental analys av en token med LLM.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando

        Returns:
            Fundamental analys-resultat
        """
        token_id = self._extract_token_id(fields, command)

        if not self.llm:
            return {
                'message': '🤖 **LLM Research kräver OpenRouter API Key**\n\nKonfigurera OPENROUTER_API_KEY för avancerad analys.',
                'data': {'error': 'LLM not available'},
                'status': 'error'
            }

        try:
            # Hämta grundläggande token-info först
            from ..core.analytics import MarketAnalyzer
            analyzer = MarketAnalyzer()
            async with analyzer:
                price_data = await analyzer.get_token_price(token_id)

                if not price_data['success']:
                    return {
                        'message': f'Kunde inte hämta data för {token_id}',
                        'data': price_data,
                        'status': 'error'
                    }

                # Förbered token-info för LLM-analys
                token_info = {
                    'name': token_id.title(),
                    'current_price': price_data.get('price', 0),
                    'market_cap': price_data.get('market_cap', 0),
                    'volume_24h': price_data.get('volume_24h', 0),
                    'price_change_24h': price_data.get('price_change_24h', 0),
                    'description': f"{token_id.upper()} är en kryptovaluta med nuvarande pris ${price_data.get('price', 0):.4f}"
                }

                # Utför LLM-driven fundamental analys
                analysis = await self.llm.research_token_fundamentals(token_id, token_info)

                if analysis['success']:
                    rating = analysis['overall_rating']
                    recommendation = analysis['recommendation']
                    potential = analysis['investment_potential']

                    # Formatera svar
                    message = f"🔬 **Fundamental Analys: {token_id.upper()}**\n\n"
                    message += f"📊 **Övergripande Betyg:** {rating}/10\n"
                    message += f"🎯 **Rekommendation:** {self._format_recommendation(recommendation)}\n"
                    message += f"📈 **Investerings Potential:** {self._format_potential(potential)}\n\n"

                    if analysis['strengths']:
                        message += "**💪 Styrkor:**\n"
                        for strength in analysis['strengths'][:3]:
                            message += f"• {strength}\n"
                        message += "\n"

                    if analysis['weaknesses']:
                        message += "**⚠️ Svagheter:**\n"
                        for weakness in analysis['weaknesses'][:3]:
                            message += f"• {weakness}\n"
                        message += "\n"

                    if analysis['risks']:
                        message += "**🚨 Risker:**\n"
                        for risk in analysis['risks'][:3]:
                            message += f"• {risk}\n"
                        message += "\n"

                    message += f"🧠 *Analys genererad av AI - överväg alltid egen research*"

                    return {
                        'message': message,
                        'data': analysis,
                        'status': 'success'
                    }
                else:
                    return {
                        'message': f'LLM-analys misslyckades: {analysis.get("error", "Okänt fel")}',
                        'data': analysis,
                        'status': 'error'
                    }

        except Exception as e:
            logger.error(f"Research analysis error: {e}")
            return {
                'message': f'Fel vid research-analys: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }

    async def _analyze_sentiment(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Analysera marknads-sentiment för en token.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando

        Returns:
            Sentiment analys-resultat
        """
        token_id = self._extract_token_id(fields, command)

        if not self.llm:
            return {
                'message': '🤖 **Sentiment-analys kräver OpenRouter API Key**',
                'data': {'error': 'LLM not available'},
                'status': 'error'
            }

        try:
            # Hämta verkliga nyheter från NewsAggregator
            from ..core.news_integration import NewsAggregator
            news_aggregator = NewsAggregator()

            # Hämta nyheter specifikt för denna token
            real_news = await news_aggregator.get_comprehensive_news(token_symbol=token_id, days=7)

            if not real_news:
                logger.warning(f"No real news found for {token_id}, using fallback")
                real_news = self._get_fallback_news(token_id)

            sentiment_result = await self.llm.analyze_market_sentiment(token_id, real_news)

            if sentiment_result['success']:
                score = sentiment_result['sentiment_score']
                confidence = sentiment_result['confidence']
                recommendation = sentiment_result['recommendation']
                explanation = sentiment_result['explanation']

                # Emoji baserat på sentiment
                if score > 0.3:
                    emoji = "🟢"
                    color = "positivt"
                elif score < -0.3:
                    emoji = "🔴"
                    color = "negativt"
                else:
                    emoji = "🟡"
                    color = "neutralt"

                message = f"{emoji} **Marknads-sentiment: {token_id.upper()}**\n\n"
                message += f"📊 **Sentiment Score:** {score:.2f} ({color})\n"
                message += f"🎯 **Konfidens:** {confidence:.1%}\n"
                message += f"💡 **Rekommendation:** {recommendation}\n\n"
                message += f"**AI Analys:** {explanation}\n\n"

                if sentiment_result['key_indicators']:
                    message += "**Nyckelfaktorer:**\n"
                    for indicator in sentiment_result['key_indicators'][:3]:
                        message += f"• {indicator}\n"

                return {
                    'message': message,
                    'data': sentiment_result,
                    'status': 'success'
                }
            else:
                return {
                    'message': f'Sentiment-analys misslyckades: {sentiment_result.get("error", "Okänt fel")}',
                    'data': sentiment_result,
                    'status': 'error'
                }

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'message': f'Fel vid sentiment-analys: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }

    async def _show_help(self) -> Dict[str, Any]:
        """Visa hjälp för research-kommandon."""
        help_text = """
🔬 **Research Kommandon:**

**Fundamental Analys:**
- "Analysera ethereum fundamentals"
- "Research bitcoin potential"
- "Granska cardano projekt"

**Sentiment Analys:**
- "Vad är sentiment för bitcoin?"
- "Analysera marknadsstämning ethereum"
- "Hur känns marknaden för solana?"

**AI-driven Insights:**
- Kräver OpenRouter API Key (OPENROUTER_API_KEY)
- Ger djupgående projektanalys
- Sentiment-analys från nyheter
- Investeringsrekommendationer

**Funktioner:**
- 🤖 AI-driven fundamental analys
- 📊 Sentiment score (-1 till +1)
- 🎯 Konkreta rekommendationer
- ⚠️ Risk-bedömningar
- 💪 Styrke-/svaghetsanalys
        """

        return {
            'message': help_text,
            'data': {
                'capabilities': ['fundamental_analysis', 'sentiment_analysis'],
                'requirements': ['OPENROUTER_API_KEY'],
                'examples': [
                    'Analysera ethereum fundamentals',
                    'Vad är sentiment för bitcoin?'
                ]
            },
            'status': 'info'
        }

    def _extract_token_id(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera token ID från kommando."""
        if 'token_id' in fields:
            return fields['token_id']

        command_lower = command.lower()

        # Vanliga token mappings
        token_map = {
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
            'avalanche': 'avalanche-2',
            'avax': 'avalanche-2'
        }

        for key, value in token_map.items():
            if key in command_lower:
                return value

        return 'bitcoin'

    def _get_mock_news(self, token_id: str) -> list:
        """Hämta mock nyhetsdata för sentiment-analys."""
        # I verkligheten skulle detta komma från nyhets-API:er
        return [
            {
                'title': f'{token_id.upper()} Adoption Continues to Grow',
                'content': f'Institutional adoption of {token_id} has increased significantly in recent months.',
                'sentiment': 'positive'
            },
            {
                'title': f'Market Analysis: {token_id.upper()} Shows Resilience',
                'content': f'Despite market volatility, {token_id} maintains strong fundamentals.',
                'sentiment': 'neutral'
            }
        ]

    def _format_recommendation(self, rec: str) -> str:
        """Formatera rekommendation för visning."""
        formats = {
            'STRONG_BUY': '🚀 STARK KÖP',
            'BUY': '🟢 KÖP',
            'HOLD': '🟡 HÅLL',
            'SELL': '🔴 SÄLJ',
            'STRONG_SELL': '💥 STARK SÄLJ'
        }
        return formats.get(rec, rec)

    def _format_potential(self, potential: str) -> str:
        """Formatera investeringspotential."""
        formats = {
            'HIGH': '🚀 HÖG',
            'MEDIUM': '🟡 MEDEL',
            'LOW': '🔴 LÅG'
        }
        return formats.get(potential, potential)
