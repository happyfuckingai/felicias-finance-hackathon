"""
Demo för Trend-Following Trading System.
Visar hur systemet analyserar marknader och genererar trading-signaler.
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ..trading.trading_system import TradingSystem

async def demo_trend_analysis():
    """Demonstrera trend-following analys."""
    print("🚀 TREND-FOLLOWING TRADING SYSTEM DEMO")
    print("=" * 50)
    print("Denna demo visar:")
    print("• Teknisk trendanalys")
    print("• Signalgenerering")
    print("• Riskbedömning")
    print("• DEX-integration")
    print("=" * 50)

    # Skapa system
    system = TradingSystem()

    try:
        # Initiera system (utan verkliga credentials för demo)
        success = await system.initialize()

        if success:
            print("✅ System initierat framgångsrikt")
        else:
            print("⚠️ System initierat i simuleringsläge")

        print("\n" + "=" * 50)
        print("🔍 DEMONSTRATION: TRENDANALYS")
        print("=" * 50)

        # Demo 1: Analysera några populära tokens
        demo_tokens = ['bitcoin', 'ethereum', 'solana']

        for token in demo_tokens:
            print(f"\n📊 Analyserar {token.upper()}...")
            try:
                from ..crypto.core.trend_signal_generator import TrendSignalGenerator
                signal_gen = TrendSignalGenerator()

                signal = await signal_gen.generate_trend_signal(token, use_llm=False)

                if signal['success']:
                    trend_analysis = signal['trend_analysis']
                    recommendation = signal['trading_recommendation']

                    print("  📈 Trendanalys:")
                    print(f"    • Riktning: {trend_analysis['trend_direction'].title()}")
                    print(f"    • Tillförlitlighet: {trend_analysis.get('confidence', 0):.1%}")

                    print("  🎯 Rekommendation:")
                    print(f"    • Åtgärd: {recommendation['action']}")
                    print(f"    • Konfidens: {recommendation.get('confidence', 0):.1%}")
                    print(f"    • Risk: {recommendation.get('risk_assessment', {}).get('overall_risk', 'unknown')}")

                    # Visa tekniska indikatorer
                    indicators = trend_analysis.get('indicators', {})
                    if indicators:
                        print("  📊 Tekniska Indikatorer:")
                        if 'sma_20' in indicators and 'sma_50' in indicators:
                            sma_20 = indicators['sma_20'] or 0
                            sma_50 = indicators['sma_50'] or 0
                            trend_signal = "🟢 BULLISH" if sma_20 > sma_50 else "🔴 BEARISH" if sma_20 < sma_50 else "🟡 NEUTRAL"
                            print(f"    • MA20/MA50: ${sma_20:.2f} / ${sma_50:.2f} - {trend_signal}")

                        if 'rsi' in indicators and indicators['rsi']:
                            rsi = indicators['rsi']
                            rsi_signal = "🟢 OVERSOLD" if rsi < 30 else "🔴 OVERBOUGHT" if rsi > 70 else "🟡 NEUTRAL"
                            print(f"    • RSI: {rsi:.1f} - {rsi_signal}")

                        if 'macd' in indicators:
                            macd_data = indicators['macd']
                            if macd_data.get('line') and macd_data.get('signal'):
                                macd_line = macd_data['line']
                                signal_line = macd_data['signal']
                                macd_signal = "🟢 BULLISH" if macd_line > signal_line else "🔴 BEARISH"
                                print(f"    • MACD: {macd_line:.6f} vs Signal: {signal_line:.6f} - {macd_signal}")

                    # Visa DEX data
                    dex_data = signal.get('dex_data', {})
                    if dex_data.get('success'):
                        print("  🔄 DEX Data:")
                        print(f"    • Pris: ${dex_data.get('price_usd', 0):.2f}")
                        print(f"    • Volym (24h): ${dex_data.get('volume_24h', 0):.2f}")
                        print(f"    • Likviditet: ${dex_data.get('liquidity', 0):.2f}")

                    print("  💡 Riskbedömning:")
                    risk_assessment = recommendation.get('risk_assessment', {})
                    risk_level = risk_assessment.get('overall_risk', 'unknown')
                    risk_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk_level, "⚪")
                    print(f"    • Risknivå: {risk_color} {risk_level.upper()}")

                else:
                    print(f"  ❌ Analys misslyckades: {signal.get('error', 'Okänt fel')}")

            except Exception as e:
                print(f"  ❌ Fel vid analys av {token}: {e}")

            await asyncio.sleep(2)  # Undvik rate limiting

        print("\n" + "=" * 50)
        print("📊 DEMONSTRATION: DASHBOARD")
        print("=" * 50)

        # Visa dashboard
        await system.run_dashboard()

        print("\n" + "=" * 50)
        print("🎯 DEMONSTRATION: RISK MANAGEMENT")
        print("=" * 50)

        # Demo risk management
        from ..crypto.core.risk_management import RiskManager
        risk_manager = RiskManager()

        # Simulera några positioner
        risk_manager.add_position('bitcoin', {
            'value': 5000,
            'risk_amount': 250,
            'volatility': 0.6
        })

        risk_manager.add_position('ethereum', {
            'value': 3000,
            'risk_amount': 180,
            'volatility': 0.5
        })

        # Visa risk rapport
        risk_report = risk_manager.get_risk_report()

        print("📋 Portfolio Risk Assessment:")
        assessment = risk_report.get('risk_assessment', {})
        print(f"  • Total Exposure: ${assessment.get('total_exposure', 0):.2f}")
        print(f"  • Total Risk: ${assessment.get('total_risk', 0):.2f}")
        risk_ratio = assessment.get('total_risk', 0) / assessment.get('total_exposure', 1) if assessment.get('total_exposure', 1) > 0 else 0
        print(f"  • Risk Ratio: {risk_ratio:.1%}")
        print(f"  • Risk Level: {assessment.get('overall_risk_level', 'unknown').upper()}")

        if assessment.get('risk_warnings'):
            print("  ⚠️ Risk Warnings:")
            for warning in assessment['risk_warnings']:
                print(f"    • {warning}")

        # Visa stress test
        stress_test = risk_manager.get_stress_test_results()
        if stress_test.get('worst_case_loss', 0) > 0:
            print("\n🧪 Stress Test Results:")
            print(f"  • Worst Case Loss: ${stress_test.get('worst_case_loss', 0):.1%}")

        print("\n" + "=" * 50)
        print("✅ DEMO KOMPLETT!")
        print("=" * 50)
        print("Trend-Following System inkluderar:")
        print("✅ Tekniska indikatorer (SMA, EMA, RSI, MACD, Bollinger Bands)")
        print("✅ Trendanalys och signalgenerering")
        print("✅ DEX-integration för verkliga trades")
        print("✅ Risk management och position sizing")
        print("✅ Realtidsmarknadsdata från CoinGecko")
        print("✅ Automatisk trading bot")
        print("✅ Backtesting och optimering")
        print("")
        print("🚀 För att starta live trading:")
        print("   1. Sätt CRYPTO_PRIVATE_KEY i .env")
        print("   2. Konfigurera WEB3_RPC_URL")
        print("   3. Kör: python -m crypto.trading_system --mode auto")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Demo fel: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Huvudfunktion för demo."""
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        # Snabb demo
        print("⚡ QUICK DEMO")
        print("Analyserar Bitcoin...")
        from ..crypto.core.trend_signal_generator import TrendSignalGenerator
        signal_gen = TrendSignalGenerator()
        signal = await signal_gen.generate_trend_signal('bitcoin', use_llm=False)
        if signal['success']:
            print(f"📈 Trend: {signal['trend_analysis']['trend_direction']}")
            print(f"🎯 Signal: {signal['trading_recommendation']['action']}")
        else:
            print("❌ Analys misslyckades")
    else:
        # Full demo
        await demo_trend_analysis()

if __name__ == "__main__":
    asyncio.run(main())