"""
Trend-Following Trading System - Huvud orchestrator.
Kombinerar tekniska signaler, DEX-integration och automatisk trading.
"""
import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from ..crypto.core.automatic_trader import AutomaticTrader
from ..crypto.core.trend_signal_generator import TrendSignalGenerator
from ..crypto.core.risk_management import RiskManager
from ..crypto.core.analytics import MarketAnalyzer
from ..crypto.core.error_handling import ErrorHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TradingSystem:
    """Huvudsystem för trend-following trading."""

    def __init__(self):
        self.trader = AutomaticTrader()
        self.signal_generator = TrendSignalGenerator()
        self.risk_manager = RiskManager()
        self.market_analyzer = MarketAnalyzer()
        self.error_handler = ErrorHandler()

        self.is_initialized = False
        logger.info("Trading System initialized")

    async def initialize(self, private_key: Optional[str] = None, rpc_url: Optional[str] = None):
        """Initiera hela trading systemet."""
        try:
            logger.info("Initializing Trading System...")

            # Ladda environment variables
            private_key = private_key or os.getenv('CRYPTO_PRIVATE_KEY')
            rpc_url = rpc_url or os.getenv('WEB3_RPC_URL') or 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID'

            # Initiera trader
            success = await self.trader.initialize(private_key, rpc_url)

            if success:
                self.is_initialized = True
                logger.info("✅ Trading System initialized successfully")

                # Visa system status
                await self.show_system_status()
                return True
            else:
                logger.error("❌ Failed to initialize trading system")
                return False

        except Exception as e:
            logger.error(f"Error initializing trading system: {e}")
            return False

    async def start_automated_trading(self):
        """Starta automatisk trading."""
        if not self.is_initialized:
            logger.error("Trading system not initialized")
            return

        try:
            logger.info("🚀 Starting automated trend-following trading...")
            print("\n" + "="*60)
            print("🤖 AUTOMATED TREND-FOLLOWING TRADING ACTIVE")
            print("="*60)
            print("• Monitoring market trends 24/7")
            print("• Executing trades on DEX automatically")
            print("• Managing risk and position sizes")
            print("• Backtesting and optimizing strategies")
            print("="*60)

            await self.trader.start_trading()

        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
            await self.stop_trading()
        except Exception as e:
            logger.error(f"Error in automated trading: {e}")
            await self.error_handler.handle_error(e, "automated_trading")

    async def stop_trading(self):
        """Stoppa trading system."""
        try:
            logger.info("Stopping trading system...")
            await self.trader.stop_trading()
            await self.show_final_report()
            logger.info("✅ Trading system stopped")
        except Exception as e:
            logger.error(f"Error stopping trading system: {e}")

    async def show_system_status(self):
        """Visa nuvarande system status."""
        try:
            print("\n" + "="*60)
            print("📊 TRADING SYSTEM STATUS")
            print("="*60)

            # Trader status
            trader_status = self.trader.get_status()
            print(f"🤖 Trading Bot: {'🟢 ACTIVE' if trader_status['is_running'] else '🔴 INACTIVE'}")
            print(f"💰 Live Trading: {'✅ ENABLED' if trader_status['trading_enabled'] else '❌ SIMULATION'}")
            print(f"📊 Open Positions: {trader_status['positions_count']}")
            print(f"💰 Portfolio Balance: ${trader_status['portfolio_balance']:.2f}")
            print(f"📈 Daily P&L: ${trader_status['daily_pnl']:.2f}")
            print(f"🎯 Total P&L: ${trader_status['total_pnl']:.2f}")

            if trader_status['positions']:
                print("\n📋 Current Positions:")
                for pos in trader_status['positions'][:3]:  # Visa max 3
                    pnl_color = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
                    print(f"  • {pos['token_id'].upper()}: {pos['side']} @ ${pos['entry_price']:.4f} | {pnl_color} P&L: ${pos['unrealized_pnl']:.2f}")

            # Risk assessment
            risk_report = self.risk_manager.get_risk_report()
            risk_level = risk_report.get('risk_assessment', {}).get('overall_risk_level', 'unknown')
            risk_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk_level, "⚪")
            print(f"\n🛡️ Risk Level: {risk_color} {risk_level.upper()}")

            if risk_report.get('risk_assessment', {}).get('risk_warnings'):
                print("⚠️ Risk Warnings:")
                for warning in risk_report['risk_assessment']['risk_warnings'][:2]:
                    print(f"  • {warning}")

            print("="*60)

        except Exception as e:
            logger.error(f"Error showing system status: {e}")
            print(f"❌ Error displaying status: {e}")

    async def show_final_report(self):
        """Visa slutrapport när system stoppas."""
        try:
            print("\n" + "="*60)
            print("📈 TRADING SESSION REPORT")
            print("="*60)

            trader_status = self.trader.get_status()
            risk_report = self.risk_manager.get_risk_report()

            print(f"💰 Final Balance: ${trader_status['portfolio_balance']:.2f}")
            print(f"📊 Session P&L: ${trader_status['daily_pnl']:.2f}")
            print(f"🎯 Total P&L: ${trader_status['total_pnl']:.2f}")

            if trader_status['trade_history']:
                print(f"\n📋 Total Trades: {len(trader_status['trade_history'])}")

                # Visa senaste 5 trades
                recent_trades = trader_status['trade_history'][-5:]
                print("🔄 Recent Trades:")
                for trade in recent_trades:
                    if trade['action'] in ['BUY', 'SELL']:
                        print(f"  • {trade['action']} {trade['token_id'].upper()} @ ${trade.get('price', trade.get('entry_price', 0)):.4f}")
                    elif trade['action'] == 'CLOSE':
                        pnl = trade.get('pnl', 0)
                        pnl_color = "🟢" if pnl >= 0 else "🔴"
                        print(f"  • CLOSE {trade['token_id'].upper()} | {pnl_color} P&L: ${pnl:.2f}")

            # Risk metrics
            if 'max_drawdown' in risk_report:
                print(f"\n📉 Max Drawdown: {risk_report['max_drawdown']:.2%}")

            print("="*60)

        except Exception as e:
            logger.error(f"Error showing final report: {e}")

    async def run_manual_analysis(self, token_ids: Optional[list] = None):
        """Kör manuell analys för specifika tokens."""
        if token_ids is None:
            token_ids = ['bitcoin', 'ethereum', 'solana']

        try:
            print(f"\n🔍 Running manual trend analysis for: {', '.join(token_ids)}")
            print("="*60)

            for token_id in token_ids:
                print(f"\n📊 Analyzing {token_id.upper()}...")
                try:
                    signal = await self.signal_generator.generate_trend_signal(token_id, use_llm=True)

                    if signal['success']:
                        trend_analysis = signal['trend_analysis']
                        recommendation = signal['trading_recommendation']

                        trend_emoji = {"bullish": "🟢", "bearish": "🔴", "sideways": "🟡"}.get(
                            trend_analysis['trend_direction'], "⚪"
                        )

                        print(f"  📈 Trend: {trend_emoji} {trend_analysis['trend_direction'].title()}")
                        print(f"  🎯 Signal: {recommendation['action']} (Confidence: {recommendation['confidence']:.1%})")
                        print(f"  💰 Price: ${signal['market_data']['current_price']:.4f}")

                        if recommendation['action'] != 'HOLD' and recommendation['confidence'] > 0.7:
                            print("  ✅ HIGH CONFIDENCE SIGNAL - Ready for execution"                        elif recommendation['action'] != 'HOLD':
                            print("  ⚠️ MEDIUM CONFIDENCE - Monitor closely"                        else:
                            print("  ⏸️ HOLD - No clear trend signal"
                        # Visa tekniska indikatorer
                        indicators = trend_analysis.get('indicators', {})
                        if indicators:
                            print("  📊 Key Indicators:"                            if 'rsi' in indicators and indicators['rsi']:
                                rsi_signal = "🟢 OVERBOUGHT" if indicators['rsi'] > 70 else "🔴 OVERSOLD" if indicators['rsi'] < 30 else "🟡 NEUTRAL"
                                print(f"    • RSI: {indicators['rsi']:.1f} - {rsi_signal}")
                            if 'macd' in indicators and indicators['macd']['line']:
                                macd_line = indicators['macd']['line']
                                signal_line = indicators['macd']['signal']
                                macd_signal = "🟢 BULLISH" if macd_line > signal_line else "🔴 BEARISH"
                                print(f"    • MACD: {macd_line:.6f} vs Signal: {signal_line:.6f} - {macd_signal}")
                    else:
                        print(f"  ❌ Analysis failed: {signal.get('error', 'Unknown error')}")

                except Exception as e:
                    print(f"  ❌ Error analyzing {token_id}: {e}")

                await asyncio.sleep(1)  # Undvik rate limiting

            print("\n" + "="*60)

        except Exception as e:
            logger.error(f"Error in manual analysis: {e}")

    async def run_dashboard(self):
        """Visa trading dashboard."""
        try:
            print("\n📊 TREND-FOLLOWING TRADING DASHBOARD")
            print("="*60)

            # Hämta dashboard data
            token_ids = ['bitcoin', 'ethereum', 'solana', 'avalanche-2', 'polygon-pos']
            dashboard = await self.signal_generator.get_trend_dashboard(token_ids)

            if dashboard['success']:
                print(f"📈 Market Summary:")
                print(f"  🟢 Bullish Trends: {dashboard['market_summary']['bullish_trends']}")
                print(f"  🔴 Bearish Trends: {dashboard['market_summary']['bearish_trends']}")
                print(f"  🟡 Sideways: {dashboard['market_summary']['sideways_markets']}")
                print(f"  🎯 High Confidence Signals: {dashboard['market_summary']['high_confidence_signals']}")

                print("
📋 Token Analysis:"                for token_id, data in dashboard['tokens'].items():
                    trend_emoji = {"bullish": "🟢", "bearish": "🔴", "sideways": "🟡"}.get(
                        data['trend_direction'], "⚪"
                    )
                    signal_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⏸️"}.get(
                        data['recommendation'], "❓"
                    )

                    print(f"  {token_id.upper()}: {trend_emoji} {data['trend_direction'].title()} | "
                          f"{signal_emoji} {data['recommendation']} | "
                          f"${data['current_price']:.2f}")
            else:
                print("❌ Failed to load dashboard data")

            # Visa system status
            await self.show_system_status()

        except Exception as e:
            logger.error(f"Error displaying dashboard: {e}")

async def main():
    """Huvudfunktion för CLI."""
    parser = argparse.ArgumentParser(description='Trend-Following Trading System')
    parser.add_argument('--mode', choices=['auto', 'manual', 'dashboard', 'status'],
                       default='dashboard', help='Trading mode')
    parser.add_argument('--tokens', nargs='+', help='Tokens to analyze (for manual mode)')
    parser.add_argument('--private-key', help='Private key for live trading')
    parser.add_argument('--rpc-url', help='RPC URL for blockchain connection')

    args = parser.parse_args()

    # Skapa och initiera system
    system = TradingSystem()

    # Initiera med credentials
    initialized = await system.initialize(args.private_key, args.rpc_url)

    if not initialized:
        print("❌ Failed to initialize trading system")
        return

    try:
        if args.mode == 'auto':
            await system.start_automated_trading()
        elif args.mode == 'manual':
            await system.run_manual_analysis(args.tokens)
        elif args.mode == 'dashboard':
            await system.run_dashboard()
        elif args.mode == 'status':
            await system.show_system_status()

    except KeyboardInterrupt:
        print("\n⏹️ Shutting down...")
    finally:
        await system.stop_trading()

if __name__ == "__main__":
    asyncio.run(main())