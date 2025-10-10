"""
Market Handler för HappyOS Crypto - Marknadsanalys och prisdata.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from ..core.analytics import MarketAnalyzer, TradingSignalGenerator
from ..core.token.token_resolver import DynamicTokenResolver, TokenNotFoundError
from ..core.trading.xgboost_trader import XGBoostTradingModel, create_optimized_xgboost_model
from ..core.analytics.feature_engineering import FeatureEngineer
from ..core.trading.model_persistence import ModelPersistence

logger = logging.getLogger(__name__)

class MarketHandler:
    """Hanterar marknadsdata och analys."""

    def __init__(self):
        """Initialize MarketHandler."""
        self.market_analyzer = MarketAnalyzer()
        self.signal_generator = TradingSignalGenerator(self.market_analyzer)
        self.token_resolver = None

        # Initiera token resolver
        try:
            self.token_resolver = DynamicTokenResolver()
        except Exception as e:
            logger.warning(f"Token resolver initialization failed: {e}")

        # Initiera XGBoost modeller och verktyg
        self.xgboost_models = {}  # Cache för laddade modeller per token
        self.model_persistence = ModelPersistence()
        self.feature_engineer = FeatureEngineer()

        logger.info("MarketHandler initialiserad med XGBoost stöd")
    
    async def handle(self, handler_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle market-relaterade kommandon.
        
        Args:
            handler_input: Input från CryptoSkill
            
        Returns:
            Result av market-operationen
        """
        action = handler_input.get('action', 'default')
        fields = handler_input.get('fields', {})
        command = handler_input.get('command', '')
        
        try:
            if action in ['check_price', 'pris', 'price']:
                return await self._check_price(fields, command)
            elif action in ['analyze', 'analysera', 'analys']:
                return await self._analyze_token(fields, command)
            elif action in ['trending', 'trend']:
                return await self._get_trending(fields)
            elif action in ['signals', 'signal']:
                return await self._get_signals(fields, command)
            elif action in ['ml_signal', 'ai_signal', 'xgboost']:
                return await self._get_ml_signals(fields, command)
            elif action in ['train_model', 'train']:
                return await self._train_ml_model(fields, command)
            elif action in ['backtest', 'test_model']:
                return await self._run_backtest(fields, command)
            else:
                return await self._show_help()
                
        except Exception as e:
            logger.error(f"Fel i MarketHandler: {e}")
            return {
                'message': f'Ett fel uppstod vid marknadsanalys: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _check_price(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Kolla pris på en token.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando

        Returns:
            Prisdata för token
        """
        token_id = await self._extract_token_id(fields, command)
        
        async with self.market_analyzer as analyzer:
            price_data = await analyzer.get_token_price(token_id)
        
        if price_data['success']:
            price = price_data['price']
            change_24h = price_data.get('price_change_24h', 0)
            volume_24h = price_data.get('volume_24h', 0)
            market_cap = price_data.get('market_cap', 0)
            
            # Formatera change med emoji
            change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
            change_text = f"{change_24h:+.2f}%" if change_24h else "0%"
            
            message = f"💰 **{token_id.upper()} Pris:**\n\n"
            message += f"💵 Pris: ${price:,.4f}\n"
            message += f"{change_emoji} 24h: {change_text}\n"
            
            if volume_24h:
                message += f"📊 Volym 24h: ${volume_24h:,.0f}\n"
            if market_cap:
                message += f"🏦 Market Cap: ${market_cap:,.0f}\n"
            
            message += f"\n🕐 Uppdaterad: {datetime.now().strftime('%H:%M:%S')}"
            
            return {
                'message': message,
                'data': {
                    'token_id': token_id,
                    'price': price,
                    'price_change_24h': change_24h,
                    'volume_24h': volume_24h,
                    'market_cap': market_cap,
                    'timestamp': price_data['timestamp']
                },
                'status': 'success'
            }
        else:
            return {
                'message': f'Kunde inte hämta pris för {token_id}: {price_data["error"]}',
                'data': price_data,
                'status': 'error'
            }
    
    async def _analyze_token(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Analysera en token över tid.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando

        Returns:
            Analys av token-prestanda
        """
        token_id = await self._extract_token_id(fields, command)
        days = self._extract_days(fields, command)
        
        async with self.market_analyzer as analyzer:
            analysis = await analyzer.analyze_token_performance(token_id, days)
        
        if analysis['success']:
            trend_emoji = "🚀" if analysis['trend'] == 'bullish' else "📉"
            volatility_level = "Hög" if analysis['volatility_percent'] > 20 else "Medel" if analysis['volatility_percent'] > 10 else "Låg"
            
            message = f"{trend_emoji} **{token_id.upper()} Analys ({days} dagar):**\n\n"
            message += f"📊 Trend: {analysis['trend'].title()}\n"
            message += f"📈 Prisförändring: {analysis['price_change_percent']:+.2f}%\n"
            message += f"⚡ Volatilitet: {volatility_level} ({analysis['volatility_percent']:.1f}%)\n"
            message += f"💰 Högsta pris: ${analysis['max_price']:,.4f}\n"
            message += f"💸 Lägsta pris: ${analysis['min_price']:,.4f}\n"
            message += f"📊 Genomsnitt: ${analysis['avg_price']:,.4f}\n"
            message += f"🔄 Volym/dag: ${analysis['avg_volume']:,.0f}"
            
            return {
                'message': message,
                'data': analysis,
                'status': 'success'
            }
        else:
            return {
                'message': f'Kunde inte analysera {token_id}: {analysis["error"]}',
                'data': analysis,
                'status': 'error'
            }
    
    async def _get_trending(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hämta trending tokens.
        
        Args:
            fields: Extraherade fält
            
        Returns:
            Lista med trending tokens
        """
        limit = fields.get('limit', 5)
        
        async with self.market_analyzer as analyzer:
            trending = await analyzer.get_trending_tokens(limit)
        
        if trending['success']:
            message = "🔥 **Trending Tokens:**\n\n"
            
            for i, token in enumerate(trending['trending_tokens'], 1):
                rank = token.get('market_cap_rank', 'N/A')
                message += f"{i}. **{token['name']}** ({token['symbol'].upper()})\n"
                message += f"   📊 Rank: #{rank}\n"
                message += f"   ₿ Pris: {token['price_btc']:.8f} BTC\n\n"
            
            return {
                'message': message,
                'data': trending,
                'status': 'success'
            }
        else:
            return {
                'message': f'Kunde inte hämta trending tokens: {trending["error"]}',
                'data': trending,
                'status': 'error'
            }
    
    async def _get_signals(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Generera trading-signaler för en token.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando

        Returns:
            Trading signals
        """
        token_id = await self._extract_token_id(fields, command)
        
        signal_result = await self.signal_generator.generate_signal(token_id)
        
        if signal_result['success']:
            signal = signal_result['signal']
            confidence = signal_result['confidence']
            reasoning = signal_result['reasoning']
            
            # Signal emoji
            signal_emoji = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "🟡"
            
            message = f"{signal_emoji} **{token_id.upper()} Trading Signal:**\n\n"
            message += f"📊 Signal: **{signal}**\n"
            message += f"🎯 Confidence: {confidence:.1%}\n\n"
            message += "**Analys:**\n"
            
            for reason in reasoning:
                message += f"• {reason}\n"
            
            market_data = signal_result['market_data']
            message += f"\n**Marknadsdata:**\n"
            message += f"📈 24h: {market_data['price_change_24h']:+.2f}%\n"
            message += f"📊 7d: {market_data['price_change_7d']:+.2f}%\n"
            message += f"💰 Pris: ${market_data['current_price']:,.4f}"
            
            return {
                'message': message,
                'data': signal_result,
                'status': 'success'
            }
        else:
            return {
                'message': f'Kunde inte generera signal för {token_id}: {signal_result["error"]}',
                'data': signal_result,
                'status': 'error'
            }

    async def _get_ml_signals(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Generera ML-baserade trading-signaler med XGBoost.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando

        Returns:
            XGBoost-baserade trading signals
        """
        token_id = await self._extract_token_id(fields, command)

        try:
            # Ladda eller skapa modell för denna token
            model = await self._load_or_create_model(token_id)

            if not model or not model.is_trained:
                return {
                    'message': f'❌ Ingen tränad XGBoost-modell tillgänglig för {token_id}. Använd "train model" först.',
                    'data': {'token_id': token_id, 'model_status': 'not_trained'},
                    'status': 'error'
                }

            # Hämta historiska data för att skapa features
            historical_data = await self._get_historical_data_for_ml(token_id)

            if historical_data is None or len(historical_data) < 50:
                return {
                    'message': f'❌ Otillräckligt med historiska data för {token_id} ML-prediktion.',
                    'data': {'token_id': token_id, 'data_points': len(historical_data) if historical_data else 0},
                    'status': 'error'
                }

            # Skapa features från senaste data
            features_df = self.feature_engineer.create_trading_features(historical_data)
            latest_features = features_df.iloc[-1:].copy()

            # Generera ML-signal
            signal_data = model.generate_trading_signal(latest_features)

            # Bygg respons
            signal_emoji = "🟢" if signal_data['signal'] == 'BUY' else "🔴" if signal_data['signal'] == 'SELL' else "🟡"
            confidence_pct = signal_data['confidence'] * 100

            message = f"{signal_emoji} **{token_id.upper()} XGBoost ML-Signal:**\n\n"
            message += f"🤖 Signal: **{signal_data['signal']}**\n"
            message += f"🎯 ML-Confidence: {confidence_pct:.1f}%\n"
            message += f"📊 Sannolikhet upp: {signal_data['probability']:.1%}\n\n"

            # Visa top contributing features
            if 'top_features' in signal_data and signal_data['top_features']:
                message += "**Viktigaste indikatorer:**\n"
                for feature, importance in list(signal_data['top_features'].items())[:3]:
                    message += f"• {feature.replace('_', ' ').title()}\n"

            # Jämför med traditionell signal
            traditional_signal = await self.signal_generator.generate_signal(token_id)
            if traditional_signal['success']:
                message += f"\n**Jämförelse:**\n"
                message += f"Traditionell signal: {traditional_signal['signal']}\n"
                message += f"ML signal: {signal_data['signal']}\n"

                if traditional_signal['signal'] == signal_data['signal']:
                    message += "✅ Signaler överensstämmer\n"
                else:
                    message += "⚠️  Signaler skiljer sig\n"

            return {
                'message': message,
                'data': {
                    'token_id': token_id,
                    'ml_signal': signal_data,
                    'traditional_signal': traditional_signal.get('signal') if traditional_signal['success'] else None,
                    'model_version': model.get_model_info() if hasattr(model, 'get_model_info') else None
                },
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Fel vid ML-signalgenerering för {token_id}: {str(e)}")
            return {
                'message': f'❌ Fel vid ML-analys för {token_id}: {str(e)}',
                'data': {'token_id': token_id, 'error': str(e)},
                'status': 'error'
            }

    async def _train_ml_model(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Träna XGBoost modell för en token.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando

        Returns:
            Träning resultat
        """
        token_id = await self._extract_token_id(fields, command)

        try:
            # Hämta historiska data
            historical_data = await self._get_historical_data_for_training(token_id)

            if historical_data is None or len(historical_data) < 200:
                return {
                    'message': f'❌ Behov minst 200 datapunkter för träning. Hittade {len(historical_data) if historical_data else 0}.',
                    'data': {'token_id': token_id, 'data_points': len(historical_data) if historical_data else 0},
                    'status': 'error'
                }

            # Skapa features
            features_df = self.feature_engineer.create_trading_features(historical_data)

            # Förbered träningsdata
            X_train, X_test, y_train, y_test = self.feature_engineer.prepare_training_data(
                features_df.drop('target', axis=1),
                features_df['target']
            )

            # Skapa och träna modell
            model = create_optimized_xgboost_model()
            training_metrics = model.train(X_train, y_train, X_test, y_test)

            # Evaluera modell
            evaluation = model.evaluate(X_test, y_test)

            # Spara modell
            saved_path = self.model_persistence.save_model(
                model,
                token_id,
                metadata={
                    'training_data_points': len(X_train),
                    'test_data_points': len(X_test),
                    'training_period_days': len(historical_data) // 24,  # Ungefärlig
                    'evaluation_metrics': evaluation
                }
            )

            # Cache modellen
            self.xgboost_models[token_id] = model

            # Bygg respons
            message = f"✅ **XGBoost Modell Tränad för {token_id.upper()}**\n\n"
            message += f"📊 Träning Metrics:\n"
            message += f"• Accuracy: {training_metrics['train_accuracy']:.1%}\n"
            message += f"• Precision: {evaluation['precision']:.1%}\n"
            message += f"• Recall: {evaluation['recall']:.1%}\n"
            message += f"• Long Win Rate: {evaluation['long_win_rate']:.1%}\n\n"

            message += f"💾 Modell sparad: {saved_path}\n"
            message += f"🕐 Tränad: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            return {
                'message': message,
                'data': {
                    'token_id': token_id,
                    'training_metrics': training_metrics,
                    'evaluation_metrics': evaluation,
                    'model_path': saved_path,
                    'training_data_points': len(X_train) + len(X_test)
                },
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Fel vid modellträning för {token_id}: {str(e)}")
            return {
                'message': f'❌ Fel vid träning av modell för {token_id}: {str(e)}',
                'data': {'token_id': token_id, 'error': str(e)},
                'status': 'error'
            }

    async def _run_backtest(self, fields: Dict[str, Any], command: str) -> Dict[str, Any]:
        """
        Kör backtest på tränad modell.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando

        Returns:
            Backtest resultat
        """
        from ..core.trading.backtester import Backtester

        token_id = await self._extract_token_id(fields, command)

        try:
            # Ladda modell
            model = await self._load_or_create_model(token_id)
            if not model or not model.is_trained:
                return {
                    'message': f'❌ Ingen tränad modell tillgänglig för {token_id}',
                    'data': {'token_id': token_id},
                    'status': 'error'
                }

            # Hämta historiska data för backtest
            historical_data = await self._get_historical_data_for_ml(token_id, days=365)  # 1 år

            if historical_data is None or len(historical_data) < 100:
                return {
                    'message': f'❌ Otillräckligt data för backtest av {token_id}',
                    'data': {'token_id': token_id, 'data_points': len(historical_data) if historical_data else 0},
                    'status': 'error'
                }

            # Kör backtest
            backtester = Backtester(model)
            backtest_result = backtester.run_backtest(historical_data, confidence_threshold=0.6)

            # Bygg respons
            message = f"📈 **Backtest Resultat för {token_id.upper()}**\n\n"
            message += f"💰 Total Avkastning: {backtest_result.total_return:.1%}\n"
            message += f"📅 Årlig Avkastning: {backtest_result.annualized_return:.1%}\n"
            message += f"📊 Sharpe Ratio: {backtest_result.sharpe_ratio:.2f}\n"
            message += f"📉 Max Drawdown: {backtest_result.max_drawdown:.1%}\n"
            message += f"🎯 Win Rate: {backtest_result.win_rate:.1%}\n"
            message += f"🔄 Total Trades: {backtest_result.total_trades}\n"
            message += f"💪 Profit Factor: {backtest_result.profit_factor:.2f}\n"

            return {
                'message': message,
                'data': {
                    'token_id': token_id,
                    'backtest_result': backtest_result,
                    'trades_df': backtester.get_trades_df().to_dict() if hasattr(backtester, 'get_trades_df') else None
                },
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Fel vid backtest för {token_id}: {str(e)}")
            return {
                'message': f'❌ Fel vid backtest för {token_id}: {str(e)}',
                'data': {'token_id': token_id, 'error': str(e)},
                'status': 'error'
            }

    async def _load_or_create_model(self, token_id: str) -> Optional[XGBoostTradingModel]:
        """
        Ladda befintlig modell eller skapa ny från persistence.

        Args:
            token_id: Token identifierare

        Returns:
            XGBoost modell eller None
        """
        # Kolla cache först
        if token_id in self.xgboost_models:
            return self.xgboost_models[token_id]

        # Försök ladda från persistence
        try:
            model = self.model_persistence.load_latest_model(token_id)
            if model:
                self.xgboost_models[token_id] = model
                return model
        except Exception as e:
            logger.warning(f"Kunde inte ladda modell för {token_id}: {str(e)}")

        return None

    async def _get_historical_data_for_ml(self, token_id: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Hämta historiska data för ML-ändamål.

        Args:
            token_id: Token identifierare
            days: Antal dagar historisk data

        Returns:
            DataFrame med OHLCV data eller None
        """
        try:
            # Använd market_analyzer för att hämta data
            async with self.market_analyzer as analyzer:
                # Detta är en förenklad implementation - i praktiken skulle vi behöva
                # hämta riktiga historiska OHLCV data från en datakälla
                # För tillfället returnerar vi None för att indikera att detta behöver implementeras
                logger.warning("Historisk data hämtning inte implementerad ännu")
                return None

        except Exception as e:
            logger.error(f"Fel vid hämtning av historiska data för {token_id}: {str(e)}")
            return None

    async def _get_historical_data_for_training(self, token_id: str) -> Optional[pd.DataFrame]:
        """
        Hämta omfattande historiska data för modellträning.

        Args:
            token_id: Token identifierare

        Returns:
            DataFrame med minst 200 datapunkter eller None
        """
        # Använd samma som ovan men med längre period
        return await self._get_historical_data_for_ml(token_id, days=365)
    
    async def _show_help(self) -> Dict[str, Any]:
        """Visa hjälp för market-kommandon."""
        help_text = """
📊 **Market Kommandon:**

**Kolla pris:**
- "Kolla pris på bitcoin"
- "Vad kostar ethereum?"
- "Price check BTC"

**Analysera token:**
- "Analysera ethereum över 7 dagar"
- "Visa bitcoin trend"

**Trading signals:**
- "Ge signal för ethereum" (traditionell)
- "Ska jag köpa bitcoin?"

**🤖 XGBoost ML-Signaler:**
- "ML signal för ethereum" (AI-baserad)
- "AI signal bitcoin"
- "XGBoost prediction ethereum"

**🎯 Träna ML-modeller:**
- "Träna modell för bitcoin"
- "Train model ethereum"

**📈 Backtest modeller:**
- "Backtest bitcoin"
- "Testa modell ethereum"

**Trending tokens:**
- "Visa trending tokens"
- "Vad är populärt nu?"

**Tokens som stöds:**
- bitcoin, ethereum, cardano, solana, polygon-ecosystem-token
- Använd CoinGecko ID för bästa resultat
        """
        
        return {
            'message': help_text,
            'data': {
                'supported_tokens': ['bitcoin', 'ethereum', 'cardano', 'solana'],
                'examples': [
                    'Kolla pris på bitcoin',
                    'Analysera ethereum',
                    'Visa trending tokens',
                    'Ge signal för bitcoin'
                ]
            },
            'status': 'info'
        }
    
    async def _extract_token_id(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera token ID från kommando med dynamisk resolution."""
        if 'token_id' in fields:
            token_query = fields['token_id']
        else:
            token_query = self._extract_token_from_command(command)

        # Försök dynamisk resolution för att få CoinGecko ID
        if self.token_resolver:
            try:
                async with self.token_resolver:
                    token_info = await self.token_resolver.resolve_token(token_query)
                    # Returnera CoinGecko ID om tillgänglig, annars symbol
                    return token_info.coingecko_id or token_info.symbol.lower()
            except TokenNotFoundError:
                logger.warning(f"Token {token_query} not found, using fallback")
            except Exception as e:
                logger.error(f"Token resolution error: {e}")

        # Fallback till enkel extraction
        return token_query.lower()
    
    def _extract_token_from_command(self, command: str) -> str:
        """Hjälpfunktion för att extrahera token från kommando."""
        command_lower = command.lower()

        # Sök efter vanliga token-namn eller symboler
        import re

        # Försök hitta ord som ser ut som tokens
        words = re.findall(r'\b\w+\b', command_lower)

        # Prioritera längre ord och vanliga token-namn
        priority_tokens = ['bitcoin', 'ethereum', 'cardano', 'solana', 'polygon']

        for word in words:
            if word in priority_tokens:
                return word
            # Förkortningar
            if word in ['btc', 'eth', 'ada', 'sol', 'matic', 'link']:
                return word

        # Ta första ord som inte är stoppord
        stop_words = ['kolla', 'pris', 'på', 'visa', 'analysera', 'över', 'dagar', 'ge', 'signal', 'för']
        for word in words:
            if word not in stop_words and len(word) > 2:
                return word

        return 'bitcoin'  # Default

    def _extract_days(self, fields: Dict[str, Any], command: str) -> int:
        """Extrahera antal dagar från kommando."""
        if 'days' in fields:
            return int(fields['days'])

        # Sök efter nummer följt av "dag" eller "day"
        import re
        day_pattern = re.search(r'(\d+)\s*(?:dag|day)', command.lower())
        if day_pattern:
            return int(day_pattern.group(1))

        # Default
        return 7
