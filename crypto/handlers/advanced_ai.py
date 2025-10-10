"""
Avancerad AI-handler för naturlig språk-interaktion med crypto-systemet.
Integrerar LLM-driven analys och konversationell trading-assistent.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvancedAIHandler:
    """Handler för avancerad AI-funktionalitet"""

    def __init__(self):
        self.llm_advisor = None
        self.conversational_assistant = None
        self._initialize_ai_components()

    def _initialize_ai_components(self):
        """Initiera AI-komponenter"""
        try:
            from crypto.core.advanced_llm_integration import (
                AdvancedLLMTradingAdvisor,
                ConversationalTradingAssistant
            )
            self.llm_advisor = AdvancedLLMTradingAdvisor()
            self.conversational_assistant = ConversationalTradingAssistant()
            logger.info("Advanced AI components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI components: {e}")

    async def get_ai_trading_analysis(self, token_id: str) -> Dict[str, Any]:
        """
        Hämta omfattande AI-driven trading-analys för en token

        Args:
            token_id: Token-symbol (t.ex. 'bitcoin', 'ethereum')

        Returns:
            Dict med komplett analys inklusive:
            - Tekniska indikatorer
            - Sentiment-analys
            - AI-rekommendationer
            - Riskbedömningar
            - Marknadskontext
        """
        try:
            if not self.llm_advisor:
                return {
                    'success': False,
                    'error': 'AI trading advisor inte tillgänglig',
                    'token_id': token_id
                }

            result = await self.llm_advisor.generate_comprehensive_trading_signal(token_id)

            if result['success']:
                # Formatera för bättre användarupplevelse
                formatted_result = self._format_ai_analysis(result)
                return formatted_result
            else:
                return result

        except Exception as e:
            logger.error(f"AI trading analysis failed for {token_id}: {e}")
            return {
                'success': False,
                'error': f'AI-analys misslyckades: {str(e)}',
                'token_id': token_id
            }

    async def ask_ai_assistant(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fråga AI-assistenten på naturligt språk

        Args:
            question: Naturlig språk-fråga (t.ex. "Ska jag köpa Bitcoin?")
            context: Ytterligare kontext (valfritt)

        Returns:
            AI-genererat svar med analys och rekommendationer
        """
        try:
            if not self.conversational_assistant:
                return {
                    'success': False,
                    'error': 'Konversationell AI-assistent inte tillgänglig',
                    'question': question
                }

            # Lägg till tidsstämpel och användarkontext
            enhanced_context = context or {}
            enhanced_context.update({
                'timestamp': datetime.now().isoformat(),
                'user_query': question,
                'system_capabilities': self._get_system_capabilities()
            })

            result = await self.conversational_assistant.process_natural_language_query(
                question, enhanced_context
            )

            if result['success']:
                # Lägg till metadata
                result['metadata'] = {
                    'response_type': result.get('response_type', 'general'),
                    'processing_time': datetime.now().isoformat(),
                    'ai_model': 'Advanced LLM Integration'
                }

            return result

        except Exception as e:
            logger.error(f"AI assistant query failed: {e}")
            return {
                'success': False,
                'error': f'AI-assistent svarade inte: {str(e)}',
                'question': question
            }

    async def get_ai_portfolio_advice(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Få AI-driven portföljanalys och råd

        Args:
            portfolio: Portföljdata med innehav, värden, etc.

        Returns:
            AI-analys av portfölj med förbättringsförslag
        """
        try:
            if not self.llm_advisor:
                return {
                    'success': False,
                    'error': 'AI portföljrådgivare inte tillgänglig'
                }

            # Analysera varje innehav
            portfolio_analysis = []
            total_value = 0

            for holding in portfolio.get('holdings', []):
                token_id = holding.get('token_id', '')
                if token_id:
                    analysis = await self.llm_advisor.generate_comprehensive_trading_signal(token_id)
                    if analysis['success']:
                        holding_analysis = {
                            'token_id': token_id,
                            'current_allocation': holding.get('allocation', 0),
                            'ai_recommendation': analysis['trading_recommendation'],
                            'risk_assessment': analysis['trading_recommendation'].get('risk_assessment', {}),
                            'current_value': holding.get('value', 0)
                        }
                        portfolio_analysis.append(holding_analysis)
                        total_value += holding.get('value', 0)

            # Generera övergripande portföljråd
            portfolio_advice = await self._generate_portfolio_recommendations(portfolio_analysis, total_value)

            return {
                'success': True,
                'portfolio_analysis': portfolio_analysis,
                'overall_advice': portfolio_advice,
                'total_value': total_value,
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"AI portfolio advice failed: {e}")
            return {
                'success': False,
                'error': f'Portföljananalys misslyckades: {str(e)}'
            }

    async def get_market_prediction(self, token_id: str, timeframe: str = 'medium') -> Dict[str, Any]:
        """
        Få AI-driven marknadsprediktion

        Args:
            token_id: Token att förutsäga
            timeframe: 'short', 'medium', eller 'long'

        Returns:
            AI-prediktion med sannolikheter och scenarier
        """
        try:
            if not self.llm_advisor:
                return {
                    'success': False,
                    'error': 'AI predictions inte tillgängliga',
                    'token_id': token_id
                }

            # Hämta omfattande data för prediktion
            market_data = await self.llm_advisor._gather_market_intelligence(token_id)

            # Generera prediktion baserat på data
            prediction = await self._generate_market_prediction(token_id, market_data, timeframe)

            return {
                'success': True,
                'token_id': token_id,
                'timeframe': timeframe,
                'prediction': prediction,
                'confidence': prediction.get('confidence', 0),
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Market prediction failed for {token_id}: {e}")
            return {
                'success': False,
                'error': f'Marknadsprediktion misslyckades: {str(e)}',
                'token_id': token_id
            }

    def _format_ai_analysis(self, raw_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Formatera AI-analys för bättre användarupplevelse"""
        try:
            analysis = raw_analysis.get('ai_analysis', {})
            recommendation = raw_analysis.get('trading_recommendation', {})

            formatted = {
                'success': True,
                'token_id': raw_analysis.get('token_id'),
                'timestamp': raw_analysis.get('timestamp'),
                'executive_summary': self._create_executive_summary(analysis, recommendation),
                'trend_analysis': analysis.get('trend_analysis', {}),
                'sentiment_summary': self._summarize_sentiment(analysis.get('sentiment_assessment', {})),
                'key_recommendation': {
                    'action': recommendation.get('action', 'HOLD'),
                    'confidence': recommendation.get('confidence', 0),
                    'rationale': recommendation.get('rationale', ''),
                    'position_size': recommendation.get('position_size', 'moderate')
                },
                'risk_assessment': recommendation.get('risk_assessment', {}),
                'technical_highlights': self._extract_technical_highlights(analysis),
                'catalysts': analysis.get('catalysts', {}),
                'next_steps': self._generate_next_steps(recommendation)
            }

            return formatted

        except Exception as e:
            logger.error(f"Analysis formatting failed: {e}")
            return raw_analysis

    def _create_executive_summary(self, analysis: Dict[str, Any], recommendation: Dict[str, Any]) -> str:
        """Skapa koncist executive summary"""
        try:
            trend = analysis.get('trend_analysis', {})
            action = recommendation.get('action', 'HOLD')
            confidence = recommendation.get('confidence', 0)

            summary = f"""
            {trend.get('primary_trend', 'neutral').title()} trend med {trend.get('trend_strength', 'moderate')} styrka.
            Rekommenderar {action} med {confidence:.0%} tillförlitlighet.
            """

            return summary.strip()

        except Exception as e:
            return "AI-analys genomförd - se detaljer nedan"

    def _summarize_sentiment(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summera sentiment-data"""
        try:
            overall = sentiment_data.get('overall_sentiment', 'neutral')
            drivers = sentiment_data.get('sentiment_drivers', [])

            return {
                'overall_sentiment': overall,
                'key_drivers': drivers[:3],  # Top 3 drivers
                'sentiment_strength': self._assess_sentiment_strength(sentiment_data)
            }

        except Exception as e:
            return {'overall_sentiment': 'unknown', 'key_drivers': [], 'sentiment_strength': 'unknown'}

    def _assess_sentiment_strength(self, sentiment_data: Dict[str, Any]) -> str:
        """Bedöm styrkan på sentiment"""
        try:
            sentiment = sentiment_data.get('overall_sentiment', 'neutral')
            social_volume = sentiment_data.get('social_volume', 'medium')

            if sentiment in ['very_positive', 'very_negative'] and social_volume == 'high':
                return 'strong'
            elif sentiment in ['positive', 'negative']:
                return 'moderate'
            else:
                return 'weak'

        except Exception:
            return 'unknown'

    def _extract_technical_highlights(self, analysis: Dict[str, Any]) -> List[str]:
        """Extrahera viktiga tekniska observationer"""
        highlights = []

        try:
            # RSI highlights
            rsi_data = analysis.get('quantitative_signals', {}).get('rsi', {})
            if rsi_data:
                if rsi_data < 30:
                    highlights.append("RSI indikerar översålt marknad (< 30)")
                elif rsi_data > 70:
                    highlights.append("RSI indikerar överköpt marknad (> 70)")

            # MACD highlights
            macd_data = analysis.get('quantitative_signals', {}).get('macd', {})
            if macd_data and macd_data.get('line') and macd_data.get('signal'):
                macd_line = macd_data['line']
                signal_line = macd_data['signal']
                if macd_line > signal_line:
                    highlights.append("MACD visar bullish momentum")
                else:
                    highlights.append("MACD visar bearish momentum")

            # Trend highlights
            trend_analysis = analysis.get('trend_analysis', {})
            if trend_analysis.get('primary_trend'):
                trend = trend_analysis['primary_trend']
                strength = trend_analysis.get('trend_strength', 'moderate')
                highlights.append(f"{trend.title()} trend med {strength} styrka")

        except Exception as e:
            logger.warning(f"Technical highlights extraction failed: {e}")

        return highlights

    def _generate_next_steps(self, recommendation: Dict[str, Any]) -> List[str]:
        """Generera handlingsbara nästa steg"""
        next_steps = []

        try:
            action = recommendation.get('action', 'HOLD')
            position_size = recommendation.get('position_size', 'moderate')

            if action == 'BUY':
                next_steps.extend([
                    f"Överväg {position_size} position sizing",
                    "Sätt stop-loss enligt riskhantering",
                    "Övervaka nyckelnivåer för exit"
                ])
            elif action == 'SELL':
                next_steps.extend([
                    "Identifiera optimal exit-pris",
                    "Överväg delvis exit för riskhantering",
                    "Analysera alternativa investeringar"
                ])
            else:  # HOLD
                next_steps.extend([
                    "Fortsätt övervaka marknaden",
                    "Vänta på bättre ingångspunkt",
                    "Granska portföljutjämning"
                ])

            # Risk-specifika steg
            risk_assessment = recommendation.get('risk_assessment', {})
            if risk_assessment.get('overall_risk') == 'high':
                next_steps.append("⚠️ Hög risk - överväg minska position size")

        except Exception as e:
            logger.warning(f"Next steps generation failed: {e}")
            next_steps = ["Fortsätt övervaka marknaden", "Konsultera med finansiell rådgivare"]

        return next_steps

    async def _generate_portfolio_recommendations(self, holdings_analysis: List[Dict], total_value: float) -> Dict[str, Any]:
        """Generera portföljråd baserat på AI-analys"""
        try:
            # Beräkna övergripande portföljhälsa
            total_risk_score = sum(
                1 if h.get('ai_recommendation', {}).get('action') in ['SELL', 'HOLD'] else 0
                for h in holdings_analysis
            ) / len(holdings_analysis) if holdings_analysis else 0

            # Identifiera hög-risk innehav
            high_risk_holdings = [
                h for h in holdings_analysis
                if h.get('ai_recommendation', {}).get('risk_assessment', {}).get('overall_risk') == 'high'
            ]

            # Generera råd
            recommendations = []

            if total_risk_score > 0.6:
                recommendations.append("🚨 Hög risk-nivå i portfölj - överväg rebalansering")
            elif total_risk_score < 0.3:
                recommendations.append("✅ Portfölj ser stabil ut")

            if high_risk_holdings:
                recommendations.append(f"⚠️ {len(high_risk_holdings)} innehav har hög risk")

            # Diversifieringsråd
            token_count = len(holdings_analysis)
            if token_count < 3:
                recommendations.append("💡 Överväg diversifiering till fler tillgångar")

            return {
                'overall_health': 'good' if total_risk_score < 0.5 else 'needs_attention',
                'risk_score': total_risk_score,
                'recommendations': recommendations,
                'high_risk_count': len(high_risk_holdings),
                'total_holdings': token_count
            }

        except Exception as e:
            logger.error(f"Portfolio recommendations failed: {e}")
            return {
                'overall_health': 'unknown',
                'recommendations': ['Konsultera professionell rådgivning']
            }

    async def _generate_market_prediction(self, token_id: str, market_data: Dict[str, Any], timeframe: str) -> Dict[str, Any]:
        """Generera marknadsprediktion baserat på data"""
        try:
            # Enkel prediktionslogik baserat på tekniska indikatorer
            technical = market_data.get('technical_indicators', {})
            sentiment = market_data.get('sentiment_data', {})

            # Beräkna prediktionssannolikhet
            bullish_signals = 0
            total_signals = 0

            # Tekniska signaler
            if technical.get('sma_20') and technical.get('sma_50'):
                if technical['sma_20'] > technical['sma_50']:
                    bullish_signals += 1
                total_signals += 1

            if technical.get('rsi'):
                rsi = technical['rsi']
                if rsi < 30:
                    bullish_signals += 1  # Översålt = potentiellt bullish
                elif rsi > 70:
                    pass  # Överköpt = potentiellt bearish
                else:
                    bullish_signals += 0.5  # Neutral
                total_signals += 1

            # Sentiment signaler
            if sentiment.get('overall_sentiment') == 'positive':
                bullish_signals += 1
            elif sentiment.get('overall_sentiment') == 'negative':
                pass
            else:
                bullish_signals += 0.5
            total_signals += 1

            # Beräkna sannolikhet
            probability = bullish_signals / total_signals if total_signals > 0 else 0.5

            # Prediktion baserat på timeframe
            if timeframe == 'short':
                confidence = min(probability, 0.7)  # Kort sikt har lägre förutsägbarhet
            elif timeframe == 'long':
                confidence = max(probability, 0.6)  # Lång sikt har högre förutsägbarhet
            else:  # medium
                confidence = probability

            prediction = {
                'direction': 'bullish' if probability > 0.6 else 'bearish' if probability < 0.4 else 'sideways',
                'probability': probability,
                'confidence': confidence,
                'timeframe': timeframe,
                'key_factors': self._extract_prediction_factors(market_data),
                'scenarios': self._generate_prediction_scenarios(probability, timeframe)
            }

            return prediction

        except Exception as e:
            logger.error(f"Market prediction generation failed: {e}")
            return {
                'direction': 'unknown',
                'probability': 0.5,
                'confidence': 0.3,
                'timeframe': timeframe,
                'error': str(e)
            }

    def _extract_prediction_factors(self, market_data: Dict[str, Any]) -> List[str]:
        """Extrahera viktiga prediktionsfaktorer"""
        factors = []

        try:
            technical = market_data.get('technical_indicators', {})

            if technical.get('sma_20') and technical.get('sma_50'):
                if technical['sma_20'] > technical['sma_50']:
                    factors.append("SMA20 över SMA50 (bullish)")
                else:
                    factors.append("SMA20 under SMA50 (bearish)")

            if technical.get('rsi'):
                rsi = technical['rsi']
                if rsi < 30:
                    factors.append("RSI översålt (< 30)")
                elif rsi > 70:
                    factors.append("RSI överköpt (> 70)")
                else:
                    factors.append("RSI neutral")

        except Exception as e:
            logger.warning(f"Prediction factors extraction failed: {e}")

        return factors or ["Begränsad teknisk data tillgänglig"]

    def _generate_prediction_scenarios(self, probability: float, timeframe: str) -> Dict[str, Any]:
        """Generera olika prediktionsscenarier"""
        try:
            if probability > 0.6:
                # Bullish scenario
                return {
                    'bull_case': {
                        'probability': probability,
                        'description': f'Stark bullish trend förväntas inom {timeframe} sikt',
                        'target_price': '15-25% högre'
                    },
                    'base_case': {
                        'probability': 1 - probability,
                        'description': 'Moderat uppgång eller sideways',
                        'target_price': '5-15% högre'
                    },
                    'bear_case': {
                        'probability': 0.1,
                        'description': 'Trendvändning eller korrektion',
                        'target_price': '5-10% lägre'
                    }
                }
            elif probability < 0.4:
                # Bearish scenario
                return {
                    'bull_case': {
                        'probability': 0.1,
                        'description': 'Potentiell rebound',
                        'target_price': '5-10% högre'
                    },
                    'base_case': {
                        'probability': 1 - probability,
                        'description': 'Sidledes rörelse eller måttlig nedgång',
                        'target_price': 'neutral till -5%'
                    },
                    'bear_case': {
                        'probability': probability,
                        'description': f'Bearish trend förväntas inom {timeframe} sikt',
                        'target_price': '10-20% lägre'
                    }
                }
            else:
                # Neutral scenario
                return {
                    'bull_case': {
                        'probability': 0.35,
                        'description': 'Moderat uppgång möjligt',
                        'target_price': '5-10% högre'
                    },
                    'base_case': {
                        'probability': 0.5,
                        'description': f'Sidledes rörelse förväntas inom {timeframe} sikt',
                        'target_price': '-5% till +5%'
                    },
                    'bear_case': {
                        'probability': 0.35,
                        'description': 'Moderat nedgång möjlig',
                        'target_price': '5-10% lägre'
                    }
                }

        except Exception as e:
            logger.error(f"Prediction scenarios failed: {e}")
            return {
                'error': 'Kunde inte generera scenarier',
                'fallback': 'Se tekniska indikatorer för vägledning'
            }

    def _get_system_capabilities(self) -> Dict[str, Any]:
        """Returnera systemets kapabiliteter"""
        return {
            'trading_analysis': True,
            'market_prediction': True,
            'portfolio_advice': True,
            'sentiment_analysis': True,
            'technical_indicators': True,
            'natural_language': True,
            'risk_management': True
        }

# Global instans
advanced_ai_handler = AdvancedAIHandler()