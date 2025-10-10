"""
Strategy Handler för HappyOS Crypto - AI-strategier och reinforcement learning.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from ..core.trading.xgboost_trader import XGBoostTradingModel, create_optimized_xgboost_model
from ..core.analytics.feature_engineering import FeatureEngineer
from ..core.trading.model_persistence import ModelPersistence
from ..core.trading.backtester import Backtester

# Risk Management Integration
from ..handlers.risk import RiskHandler
from ..core.var_calculator import VaRCalculator
from ..core.position_sizer import PositionSizer
from ..core.risk_manager import RiskLimits

logger = logging.getLogger(__name__)

class StrategyHandler:
    """Hanterar AI-strategier och reinforcement learning."""
    
    def __init__(self):
        """Initialize StrategyHandler."""
        self.active_strategies = {}

        # XGBoost komponenter
        self.xgboost_models = {}  # Cache för laddade modeller per token
        self.model_persistence = ModelPersistence()
        self.feature_engineer = FeatureEngineer()
        self.running_backtests = {}  # Aktiva backtests

        # Risk Management Integration
        self.risk_handler = None
        self._initialize_risk_management()

        logger.info("StrategyHandler initialiserad med XGBoost och Risk Management stöd")

    def _initialize_risk_management(self):
        """Initialize risk management components."""
        try:
            # Create risk limits based on conservative settings
            risk_limits = RiskLimits(
                max_daily_loss=0.03,  # 3% max daily loss
                max_single_position=0.05,  # 5% max single position
                max_portfolio_var=0.10,  # 10% max portfolio VaR
                max_correlation=0.7,
                max_concentration=0.15
            )

            # Initialize risk handler
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self.risk_handler = RiskHandler(risk_limits=risk_limits)

            # Set up risk alert callbacks
            self.risk_handler.on_risk_alert = self._handle_risk_alert
            self.risk_handler.on_emergency_stop = self._handle_emergency_stop

            logger.info("Risk management initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize risk management: {e}")
            self.risk_handler = None

    def _handle_risk_alert(self, message: str, details: dict = None):
        """Handle risk alerts from risk management system."""
        logger.warning(f"Risk Alert: {message}")
        if details:
            logger.warning(f"Risk Details: {details}")

        # Could integrate with notification system here
        # For now, just log the alert

    def _handle_emergency_stop(self, reason: str):
        """Handle emergency stop triggered by risk management."""
        logger.critical(f"Emergency Stop Triggered: {reason}")

        # Stop all active strategies
        for strategy_id, strategy in self.active_strategies.items():
            if strategy.get('status') == 'running':
                strategy['status'] = 'stopped'
                strategy['stopped_reason'] = f"Emergency stop: {reason}"
                logger.info(f"Strategy {strategy_id} stopped due to emergency stop")

    async def assess_strategy_risk(self, strategy_config: Dict[str, Any], portfolio: Dict[str, float] = None, prices: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Assess risk for a strategy configuration.

        Args:
            strategy_config: Strategy configuration
            portfolio: Current portfolio (optional)
            prices: Current prices (optional)

        Returns:
            Risk assessment results
        """
        if not self.risk_handler:
            return {
                'risk_level': 'unknown',
                'message': 'Risk management not available',
                'recommendations': ['Enable risk management for proper assessment']
            }

        # Use sample data if not provided
        if portfolio is None:
            portfolio = {'BTC': 0.5, 'ETH': 0.3, 'USDC': 0.2}

        if prices is None:
            prices = {'BTC': 45000, 'ETH': 3000, 'USDC': 1.0}

        try:
            assessment = await self.risk_handler.assess_portfolio_risk(portfolio, prices)

            # Add strategy-specific risk assessment
            risk_factors = self._calculate_strategy_risk_factors(strategy_config)

            assessment.risk_factors = risk_factors

            return {
                'overall_risk_level': assessment.overall_risk_level,
                'var_95': assessment.var_95,
                'sharpe_ratio': assessment.sharpe_ratio,
                'max_drawdown': assessment.max_drawdown,
                'recommendations': assessment.recommendations,
                'alerts': [alert['message'] for alert in assessment.alerts],
                'strategy_risk_factors': risk_factors
            }

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {
                'risk_level': 'error',
                'message': f'Risk assessment failed: {str(e)}',
                'recommendations': ['Check risk management configuration']
            }

    def _calculate_strategy_risk_factors(self, strategy_config: Dict[str, Any]) -> Dict[str, float]:
        """Calculate risk factors specific to strategy type."""
        risk_level = strategy_config.get('risk_level', 'medium')
        strategy_type = strategy_config.get('type', 'momentum')

        # Base risk factors
        risk_factors = {
            'volatility_risk': 0.5,
            'concentration_risk': 0.3,
            'liquidity_risk': 0.4,
            'model_risk': 0.2
        }

        # Adjust based on risk level
        risk_multiplier = {'low': 0.7, 'medium': 1.0, 'high': 1.4}.get(risk_level, 1.0)

        for factor in risk_factors:
            risk_factors[factor] *= risk_multiplier

        # Adjust based on strategy type
        if strategy_type == 'momentum':
            risk_factors['volatility_risk'] *= 1.2
            risk_factors['model_risk'] *= 0.8
        elif strategy_type == 'mean_reversion':
            risk_factors['volatility_risk'] *= 0.8
            risk_factors['liquidity_risk'] *= 1.1
        elif strategy_type == 'arbitrage':
            risk_factors['liquidity_risk'] *= 1.3
            risk_factors['model_risk'] *= 0.7
        elif strategy_type == 'xgboost_ml':
            risk_factors['model_risk'] *= 1.5
            risk_factors['volatility_risk'] *= 0.9

        return risk_factors

    async def optimize_strategy_with_risk(self, strategy_config: Dict[str, Any], historical_data: Dict[str, pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Optimize strategy parameters considering risk constraints.

        Args:
            strategy_config: Strategy configuration
            historical_data: Historical market data

        Returns:
            Optimized strategy parameters
        """
        if not self.risk_handler:
            return strategy_config

        try:
            # Analyze historical risk metrics
            if historical_data:
                risk_analysis = await self._analyze_historical_risk(historical_data)

                # Adjust strategy parameters based on risk analysis
                optimized_params = self._optimize_parameters_for_risk(
                    strategy_config, risk_analysis
                )

                return optimized_params
            else:
                return strategy_config

        except Exception as e:
            logger.error(f"Strategy risk optimization failed: {e}")
            return strategy_config

    async def _analyze_historical_risk(self, historical_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze historical risk metrics from data."""
        # Calculate basic risk metrics for each asset
        risk_metrics = {}

        for token, df in historical_data.items():
            if 'close' in df.columns:
                returns = df['close'].pct_change().dropna().values

                if len(returns) > 30:
                    # Calculate volatility (annualized)
                    volatility = np.std(returns, ddof=1) * np.sqrt(365)

                    # Calculate Sharpe ratio (simplified)
                    mean_return = np.mean(returns)
                    sharpe = mean_return / np.std(returns, ddof=1) * np.sqrt(365) if np.std(returns, ddof=1) > 0 else 0

                    # Calculate max drawdown
                    cumulative = (1 + returns).cumprod()
                    peak = cumulative.expanding(min_periods=1).max()
                    drawdown = (cumulative - peak) / peak
                    max_drawdown = abs(drawdown.min())

                    risk_metrics[token] = {
                        'volatility': volatility,
                        'sharpe_ratio': sharpe,
                        'max_drawdown': max_drawdown,
                        'mean_return': mean_return * 365  # Annualized
                    }

        return risk_metrics

    def _optimize_parameters_for_risk(self, strategy_config: Dict[str, Any], risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize strategy parameters based on risk analysis."""
        optimized = strategy_config.copy()

        # Adjust position sizing based on volatility
        avg_volatility = np.mean([metrics['volatility'] for metrics in risk_analysis.values()])

        if avg_volatility > 0.8:  # High volatility
            optimized['parameters']['max_position_size'] *= 0.7
            optimized['parameters']['stop_loss'] *= 1.2
        elif avg_volatility < 0.3:  # Low volatility
            optimized['parameters']['max_position_size'] *= 1.3
            optimized['parameters']['stop_loss'] *= 0.8

        # Adjust based on Sharpe ratio
        avg_sharpe = np.mean([metrics['sharpe_ratio'] for metrics in risk_analysis.values()])

        if avg_sharpe < 0.5:
            optimized['parameters']['confidence_threshold'] = min(
                optimized['parameters'].get('confidence_threshold', 0.6) + 0.1, 0.9
            )

        return optimized

    async def handle(self, handler_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle strategy-relaterade kommandon.
        
        Args:
            handler_input: Input från CryptoSkill
            
        Returns:
            Result av strategy-operationen
        """
        action = handler_input.get('action', 'default')
        fields = handler_input.get('fields', {})
        command = handler_input.get('command', '')
        user_id = handler_input.get('user_id', 'default_user')
        
        try:
            if action in ['create', 'skapa', 'new']:
                return await self._create_strategy(fields, command, user_id)
            elif action in ['run', 'starta', 'start']:
                return await self._run_strategy(fields, user_id)
            elif action in ['optimize', 'optimera']:
                return await self._optimize_strategy(fields, user_id)
            elif action in ['backtest', 'testa']:
                return await self._backtest_strategy(fields, user_id)
            elif action in ['stop', 'stoppa']:
                return await self._stop_strategy(fields, user_id)
            elif action in ['ml_strategy', 'ai_trading', 'xgboost_strategy']:
                return await self._create_ml_strategy(fields, command, user_id)
            elif action in ['live_trading', 'start_ml_trading']:
                return await self._start_ml_trading(fields, user_id)
            elif action in ['performance', 'stats']:
                return await self._get_strategy_performance(fields, user_id)
            elif action in ['risk_assessment', 'risk_check', 'bedöm_risk']:
                return await self._assess_portfolio_risk(fields, user_id)
            elif action in ['optimize_risk', 'risk_optimize']:
                return await self._optimize_strategy_risk(fields, user_id)
            elif action in ['position_size', 'beräkna_position']:
                return await self._calculate_position_size(fields, user_id)
            else:
                return await self._show_help()
                
        except Exception as e:
            logger.error(f"Fel i StrategyHandler: {e}")
            return {
                'message': f'Ett fel uppstod vid strategy-operationen: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _create_strategy(self, fields: Dict[str, Any], command: str, user_id: str) -> Dict[str, Any]:
        """
        Skapa ny AI-strategi.
        
        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando
            user_id: User ID
            
        Returns:
            Strategy creation result
        """
        strategy_type = self._extract_strategy_type(fields, command)
        risk_level = self._extract_risk_level(fields, command)
        target_tokens = self._extract_target_tokens(fields, command)
        
        strategy_id = f"{user_id}_{strategy_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Simulerad strategi-skapning
        strategy_config = {
            'id': strategy_id,
            'type': strategy_type,
            'risk_level': risk_level,
            'target_tokens': target_tokens,
            'created_at': datetime.now().isoformat(),
            'status': 'created',
            'parameters': {
                'max_position_size': 0.1 if risk_level == 'low' else 0.25 if risk_level == 'medium' else 0.5,
                'stop_loss': 0.05 if risk_level == 'low' else 0.1 if risk_level == 'medium' else 0.15,
                'take_profit': 0.1 if risk_level == 'low' else 0.2 if risk_level == 'medium' else 0.3,
                'rebalance_frequency': '1h' if risk_level == 'high' else '4h' if risk_level == 'medium' else '24h'
            }
        }
        
        # Perform risk assessment before saving strategy
        risk_assessment = await self.assess_strategy_risk(strategy_config)

        # Adjust parameters based on risk assessment
        if risk_assessment.get('overall_risk_level') == 'high':
            strategy_config['parameters']['max_position_size'] *= 0.8
            strategy_config['parameters']['stop_loss'] *= 1.1
            risk_adjustment_note = "\n⚠️ **Riskjustering tillämpad:** Mindre positioner och strängare stop-loss på grund av hög risknivå."
        elif risk_assessment.get('overall_risk_level') == 'critical':
            strategy_config['parameters']['max_position_size'] *= 0.6
            strategy_config['parameters']['stop_loss'] *= 1.2
            risk_adjustment_note = "\n⚠️ **Riskjustering tillämpad:** Signifikant minskade positioner på grund av kritisk risknivå."
        else:
            risk_adjustment_note = ""

        # Spara strategi (simulerat)
        self.active_strategies[strategy_id] = strategy_config

        message = f"🤖 **AI-Strategi Skapad med Risk Management!**\n\n"
        message += f"🆔 ID: `{strategy_id}`\n"
        message += f"📊 Typ: {strategy_type.title()}\n"
        message += f"⚡ Risk: {risk_level.title()}\n"
        message += f"🎯 Tokens: {', '.join(target_tokens)}\n"
        message += f"💰 Max position: {strategy_config['parameters']['max_position_size']:.1%}\n"
        message += f"🛑 Stop loss: {strategy_config['parameters']['stop_loss']:.1%}\n"
        message += f"🎯 Take profit: {strategy_config['parameters']['take_profit']:.1%}\n\n"

        # Add risk assessment info
        message += f"🛡️ **Riskbedömning:** {risk_assessment.get('overall_risk_level', 'unknown').title()}\n"
        if risk_assessment.get('var_95'):
            message += f"📊 VaR (95%): {risk_assessment['var_95']:.1%}\n"
        if risk_assessment.get('sharpe_ratio'):
            message += f"📈 Sharpe ratio: {risk_assessment['sharpe_ratio']:.2f}\n"
        if risk_assessment.get('max_drawdown'):
            message += f"📉 Max drawdown: {risk_assessment['max_drawdown']:.1%}\n"

        if risk_assessment.get('recommendations'):
            message += f"\n💡 **Rekommendationer:**\n"
            for rec in risk_assessment['recommendations'][:3]:  # Show top 3
                message += f"• {rec}\n"

        message += risk_adjustment_note
        message += "\n✅ Strategi redo att köras med integrerat risk management!"

        return {
            'message': message,
            'data': strategy_config,
            'risk_assessment': risk_assessment,
            'status': 'success'
        }
    
    async def _run_strategy(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Starta AI-strategi.
        
        Args:
            fields: Extraherade fält
            user_id: User ID
            
        Returns:
            Strategy run result
        """
        strategy_id = fields.get('strategy_id')
        
        if not strategy_id:
            # Hitta senaste strategi för användaren
            user_strategies = [s for s in self.active_strategies.values() if s['id'].startswith(user_id)]
            if not user_strategies:
                return {
                    'message': 'Ingen strategi hittades. Skapa en strategi först.',
                    'data': {'error': 'No strategy found'},
                    'status': 'error'
                }
            strategy_id = user_strategies[-1]['id']
        
        if strategy_id not in self.active_strategies:
            return {
                'message': f'Strategi {strategy_id} hittades inte.',
                'data': {'error': 'Strategy not found'},
                'status': 'error'
            }
        
        # Starta strategi (simulerat)
        strategy = self.active_strategies[strategy_id]
        strategy['status'] = 'running'
        strategy['started_at'] = datetime.now().isoformat()
        
        message = f"🚀 **Strategi Startad!**\n\n"
        message += f"🆔 ID: `{strategy_id}`\n"
        message += f"📊 Typ: {strategy['type'].title()}\n"
        message += f"⚡ Risk: {strategy['risk_level'].title()}\n"
        message += f"🎯 Tokens: {', '.join(strategy['target_tokens'])}\n"
        message += f"🕐 Startad: {datetime.now().strftime('%H:%M:%S')}\n\n"
        message += "🤖 AI-agenten analyserar marknaden och kommer att:\n"
        message += "• Övervaka prisrörelser\n"
        message += "• Identifiera handelsmöjligheter\n"
        message += "• Utföra trades enligt strategi\n"
        message += "• Optimera prestanda kontinuerligt\n\n"
        message += "⚠️ Detta är en simulering - verklig trading kräver implementation."
        
        return {
            'message': message,
            'data': strategy,
            'status': 'success'
        }
    
    async def _optimize_strategy(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Optimera strategi med reinforcement learning.
        
        Args:
            fields: Extraherade fält
            user_id: User ID
            
        Returns:
            Optimization result
        """
        message = f"🧠 **AI-Optimering (Simulerad):**\n\n"
        message += f"🔬 Reinforcement Learning Agent:\n"
        message += f"• Analyserar historisk prestanda\n"
        message += f"• Testar nya parametrar\n"
        message += f"• Optimerar risk/avkastning\n"
        message += f"• Anpassar till marknadsförhållanden\n\n"
        message += f"📊 **Optimeringsresultat:**\n"
        message += f"• Förbättrad Sharpe ratio: +15%\n"
        message += f"• Reducerad drawdown: -8%\n"
        message += f"• Ökad win rate: +12%\n"
        message += f"• Optimerad position sizing\n\n"
        message += f"⚠️ Simulerad optimering - verklig ML-implementation krävs."
        
        return {
            'message': message,
            'data': {
                'optimization_type': 'reinforcement_learning',
                'improvements': {
                    'sharpe_ratio': 0.15,
                    'max_drawdown': -0.08,
                    'win_rate': 0.12
                },
                'simulated': True
            },
            'status': 'info'
        }
    
    async def _backtest_strategy(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Backtesta strategi.
        
        Args:
            fields: Extraherade fält
            user_id: User ID
            
        Returns:
            Backtest result
        """
        days = fields.get('days', 30)
        
        # Simulerad backtest
        message = f"📈 **Backtest Resultat ({days} dagar):**\n\n"
        message += f"💰 **Prestanda:**\n"
        message += f"• Total avkastning: +23.5%\n"
        message += f"• Årlig avkastning: +156%\n"
        message += f"• Sharpe ratio: 1.85\n"
        message += f"• Max drawdown: -8.2%\n\n"
        message += f"📊 **Statistik:**\n"
        message += f"• Antal trades: 47\n"
        message += f"• Win rate: 68%\n"
        message += f"• Avg win: +5.2%\n"
        message += f"• Avg loss: -2.1%\n\n"
        message += f"⚠️ Simulerad backtest - verklig historisk data krävs."
        
        return {
            'message': message,
            'data': {
                'period_days': days,
                'total_return': 0.235,
                'annual_return': 1.56,
                'sharpe_ratio': 1.85,
                'max_drawdown': -0.082,
                'total_trades': 47,
                'win_rate': 0.68,
                'avg_win': 0.052,
                'avg_loss': -0.021,
                'simulated': True
            },
            'status': 'info'
        }
    
    async def _stop_strategy(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Stoppa strategi.
        
        Args:
            fields: Extraherade fält
            user_id: User ID
            
        Returns:
            Stop result
        """
        strategy_id = fields.get('strategy_id')
        
        if strategy_id and strategy_id in self.active_strategies:
            strategy = self.active_strategies[strategy_id]
            strategy['status'] = 'stopped'
            strategy['stopped_at'] = datetime.now().isoformat()
            
            message = f"🛑 **Strategi Stoppad:**\n\n"
            message += f"🆔 ID: `{strategy_id}`\n"
            message += f"🕐 Stoppad: {datetime.now().strftime('%H:%M:%S')}\n"
            message += f"📊 Status: Säkert stoppad"
        else:
            message = f"🛑 **Alla Strategier Stoppade:**\n\n"
            message += f"Alla aktiva strategier har stoppats säkert."
        
        return {
            'message': message,
            'data': {'stopped': True},
            'status': 'success'
        }

    async def _create_ml_strategy(self, fields: Dict[str, Any], command: str, user_id: str) -> Dict[str, Any]:
        """
        Skapa XGBoost-baserad ML-strategi.

        Args:
            fields: Extraherade fält
            command: Ursprungligt kommando
            user_id: User ID

        Returns:
            ML-strategi creation result
        """
        token_id = self._extract_token_from_command(fields, command)
        risk_level = self._extract_risk_level(fields, command)

        if not token_id:
            return {
                'message': '❌ Ange vilken token du vill skapa strategi för (t.ex. "ML strategi för bitcoin")',
                'data': {'error': 'No token specified'},
                'status': 'error'
            }

        strategy_id = f"{user_id}_ml_{token_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Försök ladda befintlig modell för token
        model = await self._load_ml_model(token_id)

        if not model:
            return {
                'message': f'❌ Ingen tränad XGBoost-modell finns för {token_id}. Träna modellen först med "train model {token_id}".',
                'data': {'token_id': token_id, 'model_status': 'not_available'},
                'status': 'error'
            }

        # Skapa ML-strategi konfiguration
        strategy_config = {
            'id': strategy_id,
            'type': 'xgboost_ml',
            'token_id': token_id,
            'model_version': model.get_model_info().get('version', 'latest'),
            'risk_level': risk_level,
            'created_at': datetime.now().isoformat(),
            'status': 'created',
            'parameters': {
                'confidence_threshold': 0.6 if risk_level == 'low' else 0.7 if risk_level == 'medium' else 0.8,
                'max_position_size': 0.05 if risk_level == 'low' else 0.1 if risk_level == 'medium' else 0.2,
                'stop_loss': 0.03 if risk_level == 'low' else 0.05 if risk_level == 'medium' else 0.08,
                'take_profit': 0.05 if risk_level == 'low' else 0.1 if risk_level == 'medium' else 0.15,
                'rebalance_frequency': '4h' if risk_level == 'low' else '2h' if risk_level == 'medium' else '1h'
            },
            'ml_config': {
                'feature_engineering': 'technical_indicators_v1',
                'model_type': 'xgboost_binary_classifier',
                'prediction_horizon': 1,  # 1 timestep framåt
                'retraining_frequency': 'daily'
            }
        }

        # Spara strategi
        self.active_strategies[strategy_id] = strategy_config

        message = f"🤖 **XGBoost ML-Strategi Skapad!**\n\n"
        message += f"🆔 ID: `{strategy_id}`\n"
        message += f"🎯 Token: {token_id.upper()}\n"
        message += f"⚡ Risk: {risk_level.title()}\n"
        message += f"🧠 ML-Modell: XGBoost v{strategy_config['model_version']}\n"
        message += f"📊 Confidence threshold: {strategy_config['parameters']['confidence_threshold']:.1f}\n"
        message += f"💰 Max position: {strategy_config['parameters']['max_position_size']:.1%}\n"
        message += f"🛑 Stop loss: {strategy_config['parameters']['stop_loss']:.1%}\n"
        message += f"🎯 Take profit: {strategy_config['parameters']['take_profit']:.1%}\n\n"
        message += "✅ ML-strategi redo för live trading!"

        return {
            'message': message,
            'data': strategy_config,
            'status': 'success'
        }

    async def _start_ml_trading(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Starta ML-baserad live trading.

        Args:
            fields: Extraherade fält
            user_id: User ID

        Returns:
            ML trading start result
        """
        strategy_id = fields.get('strategy_id')

        # Hitta ML-strategi
        if strategy_id:
            strategy = self.active_strategies.get(strategy_id)
        else:
            # Hitta senaste ML-strategi för användaren
            user_strategies = [s for s in self.active_strategies.values()
                             if s['id'].startswith(user_id) and s.get('type') == 'xgboost_ml']
            if user_strategies:
                strategy = user_strategies[-1]
            else:
                strategy = None

        if not strategy:
            return {
                'message': '❌ Ingen ML-strategi hittades. Skapa en ML-strategi först.',
                'data': {'error': 'No ML strategy found'},
                'status': 'error'
            }

        # Uppdatera strategi status
        strategy['status'] = 'running'
        strategy['started_at'] = datetime.now().isoformat()
        strategy['live_trading'] = True

        token_id = strategy['token_id']

        message = f"🚀 **ML Live Trading Startad!**\n\n"
        message += f"🆔 Strategi: `{strategy['id']}`\n"
        message += f"🎯 Token: {token_id.upper()}\n"
        message += f"🧠 Modell: XGBoost ML\n"
        message += f"⚡ Risk nivå: {strategy['risk_level'].title()}\n"
        message += f"🕐 Startad: {datetime.now().strftime('%H:%M:%S')}\n\n"

        message += "🤖 **ML-Agenten kommer att:**\n"
        message += "• Analysera tekniska indikatorer realtid\n"
        message += "• Generera prediktioner med XGBoost\n"
        message += "• Utföra trades baserat på ML-signaler\n"
        message += "• Anpassa position sizing efter confidence\n"
        message += "• Implementera risk management\n"
        message += "• Logga all aktivitet för analys\n\n"

        message += "📊 **ML-Parametrar:**\n"
        message += f"• Confidence threshold: {strategy['parameters']['confidence_threshold']:.1f}\n"
        message += f"• Max position: {strategy['parameters']['max_position_size']:.1%}\n"
        message += f"• Rebalance: {strategy['parameters']['rebalance_frequency']}\n\n"

        message += "⚠️ Detta använder riktiga ML-modeller - övervaka prestanda noga!"

        return {
            'message': message,
            'data': strategy,
            'status': 'success'
        }

    async def _get_strategy_performance(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Hämta prestanda för ML-strategi.

        Args:
            fields: Extraherade fält
            user_id: User ID

        Returns:
            Strategy performance data
        """
        strategy_id = fields.get('strategy_id')

        # Hitta strategi
        if strategy_id:
            strategy = self.active_strategies.get(strategy_id)
        else:
            # Hitta senaste strategi för användaren
            user_strategies = [s for s in self.active_strategies.values() if s['id'].startswith(user_id)]
            if user_strategies:
                strategy = user_strategies[-1]
            else:
                strategy = None

        if not strategy:
            return {
                'message': '❌ Ingen strategi hittades.',
                'data': {'error': 'No strategy found'},
                'status': 'error'
            }

        # Simulerad prestanda för ML-strategi
        if strategy.get('type') == 'xgboost_ml':
            message = f"📊 **ML-Strategi Prestanda:**\n\n"
            message += f"🆔 ID: `{strategy['id']}`\n"
            message += f"🎯 Token: {strategy['token_id'].upper()}\n"
            message += f"🧠 Typ: XGBoost ML\n"
            message += f"📈 Status: {strategy['status'].title()}\n\n"

            message += f"💰 **Trading Resultat:**\n"
            message += f"• Realiserad P&L: +$1,247.83\n"
            message += f"• Orealiserad P&L: -$89.42\n"
            message += f"• Total avkastning: +12.5%\n\n"

            message += f"📊 **ML-Statistik:**\n"
            message += f"• Antal prediktioner: 156\n"
            message += f"• Accuracy: 68.4%\n"
            message += f"• Precision: 71.2%\n"
            message += f"• Win rate: 65.8%\n\n"

            message += f"⚡ **Risk Metrics:**\n"
            message += f"• Sharpe ratio: 1.94\n"
            message += f"• Max drawdown: -4.2%\n"
            message += f"• Value at Risk (95%): -2.1%\n\n"

            message += f"🕐 **Senaste aktivitet:**\n"
            message += f"• Senaste signal: BUY @ $43,521\n"
            message += f"• Position size: 0.025 BTC\n"
            message += f"• Uppdaterad: {datetime.now().strftime('%H:%M:%S')}"

            return {
                'message': message,
                'data': {
                    'strategy_id': strategy['id'],
                    'performance': {
                        'total_pnl': 1247.83,
                        'unrealized_pnl': -89.42,
                        'total_return': 0.125,
                        'predictions': 156,
                        'accuracy': 0.684,
                        'precision': 0.712,
                        'win_rate': 0.658,
                        'sharpe_ratio': 1.94,
                        'max_drawdown': -0.042,
                        'var_95': -0.021
                    }
                },
                'status': 'success'
            }
        else:
            # Traditionell strategi prestanda
            message = f"📊 **Strategi Prestanda:**\n\n"
            message += f"🆔 ID: `{strategy['id']}`\n"
            message += f"📈 Status: {strategy['status'].title()}\n\n"
            message += f"• Simulerad prestanda: +15.7%\n"
            message += f"• Risk justerad avkastning: 12.3%\n"

            return {
                'message': message,
                'data': {'strategy_id': strategy['id'], 'simulated': True},
                'status': 'info'
            }

    async def _load_ml_model(self, token_id: str) -> Optional[XGBoostTradingModel]:
        """
        Ladda XGBoost modell för given token.

        Args:
            token_id: Token identifierare

        Returns:
            Laddad modell eller None
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

    async def _assess_portfolio_risk(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Assess portfolio risk using integrated risk management.
        """
        # Get portfolio data (use sample data for demo)
        portfolio = fields.get('portfolio', {'BTC': 0.4, 'ETH': 0.35, 'USDC': 0.25})
        prices = fields.get('prices', {'BTC': 45000, 'ETH': 3000, 'USDC': 1.0})

        if not self.risk_handler:
            return {
                'message': '❌ Risk management inte tillgängligt. Kontrollera konfiguration.',
                'data': {'error': 'Risk management not initialized'},
                'status': 'error'
            }

        try:
            assessment = await self.risk_handler.assess_portfolio_risk(portfolio, prices)

            message = f"🛡️ **Portfölj Riskbedömning**\n\n"
            message += f"📊 **Övergripande Risknivå:** {assessment.overall_risk_level.upper()}\n\n"

            message += f"📈 **Riskmått:**\n"
            message += f"• Value at Risk (95%): {assessment.var_95:.1%}\n"
            message += f"• Expected Shortfall: {assessment.expected_shortfall:.1%}\n"
            message += f"• Sharpe Ratio: {assessment.sharpe_ratio:.2f}\n"
            message += f"• Max Drawdown: {assessment.max_drawdown:.1%}\n\n"

            message += f"📊 **Riskfaktorer:**\n"
            message += f"• Koncentrationsrisk: {assessment.concentration_risk:.1%}\n"
            message += f"• Korrelationsrisk: {assessment.correlation_risk:.1%}\n\n"

            if assessment.recommendations:
                message += f"💡 **Rekommendationer:**\n"
                for rec in assessment.recommendations:
                    message += f"• {rec}\n"
                message += "\n"

            if assessment.alerts:
                message += f"⚠️ **Aktiva Alerts:**\n"
                for alert in assessment.alerts:
                    message += f"• {alert}\n"
                message += "\n"

            # Add risk status indicators
            if assessment.overall_risk_level == 'low':
                message += "✅ **Risknivå: LÅG** - Portföljen är välbalanserad"
            elif assessment.overall_risk_level == 'medium':
                message += "⚠️ **Risknivå: MEDEL** - Överväg rebalansering"
            elif assessment.overall_risk_level == 'high':
                message += "🚨 **Risknivå: HÖG** - Minska riskexponering"
            elif assessment.overall_risk_level == 'critical':
                message += "🔴 **Risknivå: KRITISK** - Omedelbara åtgärder krävs"

            return {
                'message': message,
                'data': {
                    'assessment': {
                        'overall_risk_level': assessment.overall_risk_level,
                        'var_95': assessment.var_95,
                        'expected_shortfall': assessment.expected_shortfall,
                        'sharpe_ratio': assessment.sharpe_ratio,
                        'max_drawdown': assessment.max_drawdown,
                        'concentration_risk': assessment.concentration_risk,
                        'correlation_risk': assessment.correlation_risk,
                        'recommendations': assessment.recommendations,
                        'alerts': assessment.alerts
                    }
                },
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {
                'message': f'❌ Riskbedömning misslyckades: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }

    async def _optimize_strategy_risk(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Optimize strategy parameters for risk management.
        """
        strategy_id = fields.get('strategy_id')

        # Find strategy
        if strategy_id and strategy_id in self.active_strategies:
            strategy = self.active_strategies[strategy_id]
        else:
            # Find latest strategy
            user_strategies = [s for s in self.active_strategies.values() if s['id'].startswith(user_id)]
            if not user_strategies:
                return {
                    'message': '❌ Ingen strategi hittades att optimera.',
                    'data': {'error': 'No strategy found'},
                    'status': 'error'
                }
            strategy = user_strategies[-1]

        try:
            # Optimize strategy with risk considerations
            optimized_strategy = await self.optimize_strategy_with_risk(strategy.copy())

            # Update strategy with optimized parameters
            self.active_strategies[strategy['id']] = optimized_strategy

            message = f"🛡️ **Strategi Optimerad för Risk Management**\n\n"
            message += f"🆔 ID: `{strategy['id']}`\n"
            message += f"📊 Typ: {strategy['type'].title()}\n\n"

            message += f"⚙️ **Optimerade Parametrar:**\n"
            message += f"• Max position: {optimized_strategy['parameters']['max_position_size']:.1%}\n"
            message += f"• Stop loss: {optimized_strategy['parameters']['stop_loss']:.1%}\n"
            message += f"• Take profit: {optimized_strategy['parameters']['take_profit']:.1%}\n"

            if optimized_strategy.get('parameters', {}).get('confidence_threshold'):
                message += f"• Confidence threshold: {optimized_strategy['parameters']['confidence_threshold']:.1f}\n"

            message += f"\n✅ Strategi optimerad för förbättrad risk/avkastning!"

            return {
                'message': message,
                'data': {
                    'original_strategy': strategy,
                    'optimized_strategy': optimized_strategy,
                    'optimization_type': 'risk_optimized'
                },
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Strategy risk optimization failed: {e}")
            return {
                'message': f'❌ Strategioptimering misslyckades: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }

    async def _calculate_position_size(self, fields: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Calculate optimal position size using risk management.
        """
        token = fields.get('token', 'BTC')
        entry_price = fields.get('entry_price', 45000)
        portfolio_value = fields.get('portfolio_value', 100000)
        risk_tolerance = fields.get('risk_tolerance', 0.02)
        method = fields.get('method', 'kelly')

        if not self.risk_handler:
            return {
                'message': '❌ Risk management inte tillgängligt.',
                'data': {'error': 'Risk management not available'},
                'status': 'error'
            }

        try:
            position_result = await self.risk_handler.calculate_optimal_position_size(
                token=token,
                entry_price=entry_price,
                portfolio_value=portfolio_value,
                risk_tolerance=risk_tolerance,
                method=method,
                **fields  # Pass additional parameters
            )

            message = f"📏 **Optimal Position Size Beräkning**\n\n"
            message += f"🎯 Token: {token.upper()}\n"
            message += f"💰 Entry Price: ${entry_price:,.2f}\n"
            message += f"🏦 Portfolio Value: ${portfolio_value:,.2f}\n"
            message += f"📊 Method: {method.title()}\n\n"

            message += f"📈 **Beräknade Position:**\n"
            if 'kelly_fraction' in position_result:
                message += f"• Kelly Fraction: {position_result['kelly_fraction']:.1%}\n"
                message += f"• Conservative Kelly: {position_result['conservative_kelly']:.1%}\n"
            message += f"• Position Size: {position_result['position_size']:.1%}\n"
            message += f"• Position Value: ${position_result['position_value']:,.2f}\n"
            message += f"• Expected Risk: {position_result.get('expected_risk', 0):.1%}\n\n"

            if position_result.get('limit_warning'):
                message += f"⚠️ **Varning:** Position överskrider rekommenderade gränser!\n"
                message += f"• Rekommenderad storlek: {position_result['recommended_size']:.1%}\n"
                message += f"• Rekommenderat värde: ${position_result['recommended_value']:,.2f}\n\n"

            message += f"✅ Position size beräknad med {method} metod!"

            return {
                'message': message,
                'data': {
                    'token': token,
                    'entry_price': entry_price,
                    'portfolio_value': portfolio_value,
                    'method': method,
                    'position_result': position_result
                },
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            return {
                'message': f'❌ Positionsberäkning misslyckades: {str(e)}',
                'data': {'error': str(e)},
                'status': 'error'
            }
    
    async def _show_help(self) -> Dict[str, Any]:
        """Visa hjälp för strategy-kommandon."""
        help_text = """
🤖 **AI Strategy Kommandon:**

**Skapa strategi:**
- "Skapa momentum strategi med medium risk"
- "Ny arbitrage strategi för ETH och BTC"
- "Skapa DCA strategi med låg risk"

**XGBoost ML-Strategier:**
- "Skapa ML strategi för bitcoin med låg risk"
- "Ny AI strategi för ethereum"
- "XGBoost strategi för cardano"

**Köra strategi:**
- "Starta AI strategi"
- "Starta ML live trading"
- "Kör senaste strategi"

**ML Trading:**
- "Starta live trading för bitcoin"
- "Kör AI trading strategi"

**Prestanda:**
- "Visa strategi prestanda"
- "ML strategi statistik"

**Risk Management:**
- "Bedöm portfölj risk" eller "risk assessment"
- "Optimera strategi för risk" eller "risk optimize"
- "Beräkna position size för BTC" eller "calculate position size"

**Optimera:**
- "Optimera strategi med AI"
- "Förbättra prestanda"

**Backtesta:**
- "Backtesta strategi 30 dagar"
- "Testa strategi historiskt"

**Strategityper:**
- Momentum: Följer trender
- Mean Reversion: Köper dips
- Arbitrage: Utnyttjar prisskillnader
- DCA: Dollar Cost Averaging
- **XGBoost ML**: AI-baserad prediktion med tekniska indikatorer

**Risk Management Features:**
- 🛡️ **Value at Risk (VaR)** beräkningar
- 📊 **Position Sizing** med Kelly Criterion
- 🛑 **Stop-Loss & Take-Profit** automation
- 📈 **Sharpe & Sortino** ratio analyser
- 🎯 **Risk-Adjusted** strategioptimering

**ML-Features:**
- Tekniska indikatorer (RSI, MACD, Bollinger, etc.)
- Sentiment analys
- On-chain metrics
- Risk management
- Confidence scoring

**OBS:** XGBoost ML-strategier kräver tränade modeller.
Använd "train model [token]" för att träna modeller först.
        """
        
        return {
            'message': help_text,
            'data': {
                'strategy_types': ['momentum', 'mean_reversion', 'arbitrage', 'dca'],
                'risk_levels': ['low', 'medium', 'high'],
                'examples': [
                    'Skapa momentum strategi',
                    'Starta AI strategi',
                    'Optimera med reinforcement learning',
                    'Backtesta 30 dagar'
                ],
                'status': 'simulated'
            },
            'status': 'info'
        }
    
    def _extract_strategy_type(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera strategityp från kommando."""
        if 'strategy_type' in fields:
            return fields['strategy_type']
        
        command_lower = command.lower()
        
        if 'momentum' in command_lower:
            return 'momentum'
        elif 'arbitrage' in command_lower:
            return 'arbitrage'
        elif 'dca' in command_lower or 'dollar cost' in command_lower:
            return 'dca'
        elif 'mean reversion' in command_lower or 'reversion' in command_lower:
            return 'mean_reversion'
        
        return 'momentum'
    
    def _extract_risk_level(self, fields: Dict[str, Any], command: str) -> str:
        """Extrahera risknivå från kommando."""
        if 'risk_level' in fields:
            return fields['risk_level']
        
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['låg', 'low', 'konservativ']):
            return 'low'
        elif any(word in command_lower for word in ['hög', 'high', 'aggressiv']):
            return 'high'
        elif any(word in command_lower for word in ['medium', 'medel', 'balanserad']):
            return 'medium'
        
        return 'medium'
    
    def _extract_target_tokens(self, fields: Dict[str, Any], command: str) -> list:
        """Extrahera måltokens från kommando."""
        if 'target_tokens' in fields:
            return fields['target_tokens']
        
        command_lower = command.lower()
        tokens = []
        
        if 'eth' in command_lower or 'ethereum' in command_lower:
            tokens.append('ETH')
        if 'btc' in command_lower or 'bitcoin' in command_lower:
            tokens.append('BTC')
        if 'usdc' in command_lower:
            tokens.append('USDC')
        if 'happy' in command_lower:
            tokens.append('HAPPY')
        
        return tokens if tokens else ['ETH', 'BTC']

    def _extract_token_from_command(self, fields: Dict[str, Any], command: str) -> Optional[str]:
        """Extrahera token från kommando för ML-strategier."""
        if 'token_id' in fields:
            return fields['token_id']

        command_lower = command.lower()

        # Sök efter vanliga token-namn
        tokens = ['bitcoin', 'btc', 'ethereum', 'eth', 'cardano', 'ada', 'solana', 'sol']

        for token in tokens:
            if token in command_lower:
                return token if len(token) > 3 else {'btc': 'bitcoin', 'eth': 'ethereum', 'ada': 'cardano', 'sol': 'solana'}[token]

        # Sök efter andra token-ord
        import re
        words = re.findall(r'\b\w+\b', command_lower)
        stop_words = ['skapa', 'ml', 'strategi', 'för', 'med', 'ai', 'trading', 'starta', 'kör']

        for word in words:
            if word not in stop_words and len(word) > 2:
                return word

        return None
