"""
LLM Integration för HappyOS Crypto.
Använder AI för intelligent analys och beslutsfattande.
"""
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import json

logger = logging.getLogger(__name__)

class LLMIntegration:
    """Hanterar LLM-anrop för crypto-relaterade analyser."""

    def __init__(self, api_key: Optional[str] = None, model: str = "nvidia/nemotron-nano-9b-v2:free"):
        """
        Initiera LLM-integration.

        Args:
            api_key: OpenRouter API key (kan också sättas via env)
            model: LLM-modell att använda
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.session = None
        self._initialized = False

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, _):
        if self.session:
            await self.session.close()

    async def analyze_market_sentiment(self, token_symbol: str, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analysera marknadssentiment för en token baserat på nyheter.

        Args:
            token_symbol: Token symbol (t.ex. "BTC", "ETH")
            news_data: Lista med nyhetsartiklar

        Returns:
            Sentiment analys med score och förklaring
        """
        try:
            # Förbered context för LLM
            news_text = "\n".join([
                f"Titel: {article.get('title', '')}\nInnehåll: {article.get('content', '')[:500]}..."
                for article in news_data[:5]  # Begränsa till 5 senaste nyheter
            ])

            prompt = f"""
            Analysera marknadssentiment för {token_symbol} baserat på följande nyheter från de senaste 24 timmarna:

            {news_text}

            Ge en sentiment score mellan -1 (mycket negativt) och +1 (mycket positivt).
            Förklara din analys och ge specifika indikatorer som påverkade ditt beslut.

            Format: JSON med följande fält:
            - sentiment_score: float (-1 till 1)
            - confidence: float (0-1)
            - explanation: str (kort förklaring)
            - key_indicators: list[str] (viktiga faktorer)
            - recommendation: str ("BUY", "SELL", eller "HOLD")
            """

            response = await self._call_llm(prompt)

            # Clean and parse JSON response
            # Remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Try to parse JSON
            try:
                result = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Raw response: {response[:500]}")
                # Try to extract JSON from the response if it's embedded
                import re
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise Exception(f"Could not parse JSON from LLM response: {cleaned_response[:200]}")
                else:
                    raise Exception(f"No valid JSON found in LLM response: {cleaned_response[:200]}")

            return {
                'success': True,
                'token_symbol': token_symbol,
                'sentiment_score': result.get('sentiment_score', 0),
                'confidence': result.get('confidence', 0.5),
                'explanation': result.get('explanation', 'Analysis not available'),
                'key_indicators': result.get('key_indicators', []),
                'recommendation': result.get('recommendation', 'HOLD'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"LLM sentiment analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'token_symbol': token_symbol
            }

    async def research_token_fundamentals(self, token_symbol: str, token_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Utför fundamental analys av en token med LLM.

        Args:
            token_symbol: Token symbol
            token_info: Grundläggande token-information

        Returns:
            Fundamental analys och bedömning
        """
        try:
            # Förbered context
            context = f"""
            Token: {token_symbol}
            Namn: {token_info.get('name', 'Unknown')}
            Beskrivning: {token_info.get('description', 'No description')}
            Marknadsvärde: ${token_info.get('market_cap', 0):,.0f}
            Volym 24h: ${token_info.get('volume_24h', 0):,.0f}
            Pris: ${token_info.get('current_price', 0):.4f}
            """

            prompt = f"""
            Genomför en fundamental analys av följande kryptotoken:

            {context}

            Analysera:
            1. Projektets styrkor och svagheter
            2. Teknisk implementering och innovation
            3. Marknadsposition och konkurrens
            4. Riskfaktorer och regulatoriska utmaningar
            5. Långsiktig potential och investeringsvärde

            Ge en övergripande bedömning och rekommendera om detta är ett bra investeringsobjekt.

            Format: JSON med följande fält:
            - overall_rating: float (1-10)
            - strengths: list[str]
            - weaknesses: list[str]
            - risks: list[str]
            - investment_potential: str ("HIGH", "MEDIUM", "LOW")
            - recommendation: str ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")
            - key_insights: list[str]
            """

            response = await self._call_llm(prompt)

            # Clean and parse JSON response
            # Remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Try to parse JSON
            try:
                result = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Raw response: {response[:500]}")
                # Try to extract JSON from the response if it's embedded
                import re
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise Exception(f"Could not parse JSON from LLM response: {cleaned_response[:200]}")
                else:
                    raise Exception(f"No valid JSON found in LLM response: {cleaned_response[:200]}")

            return {
                'success': True,
                'token_symbol': token_symbol,
                'overall_rating': result.get('overall_rating', 5),
                'strengths': result.get('strengths', []),
                'weaknesses': result.get('weaknesses', []),
                'risks': result.get('risks', []),
                'investment_potential': result.get('investment_potential', 'MEDIUM'),
                'recommendation': result.get('recommendation', 'HOLD'),
                'key_insights': result.get('key_insights', []),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"LLM fundamental analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'token_symbol': token_symbol
            }

    async def optimize_dex_routing(self, from_token: str, to_token: str, amount: float, dex_options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Använd LLM för att optimera DEX-val baserat på flera faktorer.

        Args:
            from_token: Från-token
            to_token: Till-token
            amount: Swap-belopp
            dex_options: Lista med DEX-alternativ med priser, fees, etc.

        Returns:
            Rekommenderad DEX och förklaring
        """
        try:
            # Förbered DEX options för LLM
            options_text = "\n".join([
                f"DEX {i+1}: {dex['name']} - Pris: {dex['price']}, Fee: {dex['fee']}%, Liquidity: {dex['liquidity']}, Slippage: {dex['slippage']}%"
                for i, dex in enumerate(dex_options)
            ])

            prompt = f"""
            Analysera följande DEX-alternativ för en swap av {amount} {from_token} till {to_token}:

            {options_text}

            Faktorer att överväga:
            1. Bästa pris (lägsta slippage)
            2. Lägsta avgifter
            3. Tillräcklig likviditet
            4. Risk för sandwich attacks
            5. Transaktionshastighet
            6. Tillförlitlighet och säkerhet

            Välj den bästa DEX för denna specifika transaktion och förklara varför.

            Format: JSON med följande fält:
            - recommended_dex_index: int (0-baserat index)
            - reasoning: str (detaljerad förklaring)
            - confidence: float (0-1)
            - alternative_options: list[int] (andra bra alternativ)
            - risk_assessment: str ("LOW", "MEDIUM", "HIGH")
            """

            response = await self._call_llm(prompt)
            result = json.loads(response)

            recommended_dex = dex_options[result.get('recommended_dex_index', 0)]

            return {
                'success': True,
                'from_token': from_token,
                'to_token': to_token,
                'amount': amount,
                'recommended_dex': recommended_dex,
                'dex_index': result.get('recommended_dex_index', 0),
                'reasoning': result.get('reasoning', 'No reasoning provided'),
                'confidence': result.get('confidence', 0.5),
                'alternative_options': [dex_options[i] for i in result.get('alternative_options', []) if i < len(dex_options)],
                'risk_assessment': result.get('risk_assessment', 'MEDIUM'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"LLM DEX routing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'from_token': from_token,
                'to_token': to_token
            }

    async def analyze_trading_strategy(self, strategy_params: Dict[str, Any], historical_performance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analysera och optimera en trading-strategi med LLM.

        Args:
            strategy_params: Strategi-parametrar
            historical_performance: Historisk prestanda-data

        Returns:
            Strategi-analys och förbättringsförslag
        """
        try:
            context = f"""
            Strategi: {strategy_params.get('name', 'Unknown')}
            Parametrar: {json.dumps(strategy_params, indent=2)}
            Prestanda:
            - Total Return: {historical_performance.get('total_return', 0):.2%}
            - Sharpe Ratio: {historical_performance.get('sharpe_ratio', 0):.3f}
            - Max Drawdown: {historical_performance.get('max_drawdown', 0):.2%}
            - Win Rate: {historical_performance.get('win_rate', 0):.1%}
            """

            prompt = f"""
            Analysera följande trading-strategi och dess historiska prestanda:

            {context}

            Ge konkreta förbättringsförslag och optimeringar. Överväg:
            1. Parameter-justeringar
            2. Risk management förbättringar
            3. Entry/exit condition optimeringar
            4. Marknadstiming förbättringar

            Format: JSON med följande fält:
            - overall_assessment: str ("EXCELLENT", "GOOD", "FAIR", "POOR")
            - strengths: list[str]
            - weaknesses: list[str]
            - parameter_suggestions: dict (nya parametrar)
            - risk_improvements: list[str]
            - expected_improvement: str (förväntad effekt)
            """

            response = await self._call_llm(prompt)
            result = json.loads(response)

            return {
                'success': True,
                'strategy_name': strategy_params.get('name'),
                'overall_assessment': result.get('overall_assessment', 'FAIR'),
                'strengths': result.get('strengths', []),
                'weaknesses': result.get('weaknesses', []),
                'parameter_suggestions': result.get('parameter_suggestions', {}),
                'risk_improvements': result.get('risk_improvements', []),
                'expected_improvement': result.get('expected_improvement', 'Moderate improvement expected'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"LLM strategy analysis error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Gör ett anrop till LLM-API:et.

        Args:
            prompt: Prompt att skicka
            max_tokens: Max antal tokens i response

        Returns:
            LLM response som sträng
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key required. Set OPENROUTER_API_KEY environment variable.")

        # Initialize session if not already done
        if self.session is None:
            logger.info("Initializing aiohttp session for LLM integration")
            self.session = aiohttp.ClientSession()
            logger.info(f"Session initialized: {self.session is not None}")

        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Du är en expert kryptovalutanalytiker med djup förståelse för blockchain, DeFi och teknisk analys. Ge alltid välgrundade, objektiva analyser."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3  # Lägre temperature för mer konsistenta analyser
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            logger.info(f"Making LLM request to {url}")
            logger.info(f"Session exists: {self.session is not None}")
            if self.session is None:
                logger.error("Session is None - this should not happen!")
                raise Exception("HTTP session not initialized")

            response = await self.session.post(url, json=payload, headers=headers)
            logger.info(f"Response status: {response.status}")

            if response.status != 200:
                error_text = await response.text()
                logger.error(f"LLM API error: {response.status} - {error_text}")
                raise Exception(f"LLM API error: {response.status} - {error_text}")

            data = await response.json()
            content = data['choices'][0]['message']['content'].strip()
            logger.info(f"LLM response received successfully: {content[:200]}...")
            return content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Close session on error if we created it
            if self.session and not self._initialized:
                await self.session.close()
                self.session = None
            raise e
