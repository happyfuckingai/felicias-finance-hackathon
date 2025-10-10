"""
Demo för Advanced AI Trading Assistant
Visar naturlig språk-interaktion med AI-driven crypto-hantering
"""
import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def demo_ai_trading_analysis():
    """Demonstrera AI-driven trading-analys"""
    print("🤖 AI TRADING ANALYSIS DEMO")
    print("=" * 50)

    try:
        from ..crypto.handlers.advanced_ai import advanced_ai_handler

        # Demo 1: Bitcoin analys
        print("\n📊 Analyserar BITCOIN...")
        result = await advanced_ai_handler.get_ai_trading_analysis("bitcoin")

        if result.get('success'):
            print("✅ AI-analys genomförd!")
            print(f"📈 Rekommendation: {result.get('key_recommendation', {}).get('action', 'N/A')}")
            print(f"🎯 Tillförlitlighet: {result.get('key_recommendation', {}).get('confidence', 0):.1%}")
        else:
            print(f"❌ Analys misslyckades: {result.get('error', 'Okänt fel')}")

        await asyncio.sleep(2)  # Undvik rate limiting

    except Exception as e:
        print(f"❌ Demo fel: {e}")

async def demo_conversational_ai():
    """Demonstrera konversationell AI"""
    print("\n🗣️  KONVERSATIONELL AI DEMO")
    print("=" * 50)

    try:
        from ..crypto.handlers.advanced_ai import advanced_ai_handler

        questions = [
            "Ska jag köpa mer Bitcoin idag?",
            "Vad tycker du om Ethereum som investering?",
            "Vilka tokens är intressanta just nu?",
            "Hur ser risken ut med Solana?",
        ]

        for question in questions:
            print(f"\n🙋 Fråga: {question}")

            result = await advanced_ai_handler.ask_ai_assistant(question)

            if result.get('success'):
                print(f"🤖 Svar: {result.get('message', 'Inget svar')[:200]}...")
            else:
                print(f"❌ Svar misslyckades: {result.get('error', 'Okänt fel')}")

            await asyncio.sleep(3)  # Undvik rate limiting

    except Exception as e:
        print(f"❌ Demo fel: {e}")

async def demo_portfolio_advice():
    """Demonstrera AI portföljanalys"""
    print("\n📊 PORTFÖLJANALYS DEMO")
    print("=" * 50)

    try:
        from ..crypto.handlers.advanced_ai import advanced_ai_handler

        # Exempel portfölj
        portfolio = {
            "holdings": [
                {"token_id": "bitcoin", "allocation": 0.4, "value": 20000},
                {"token_id": "ethereum", "allocation": 0.3, "value": 15000},
                {"token_id": "solana", "allocation": 0.2, "value": 10000},
                {"token_id": "cardano", "allocation": 0.1, "value": 5000}
            ]
        }

        print("📋 Analyserar portfölj...")
        result = await advanced_ai_handler.get_ai_portfolio_advice(portfolio)

        if result.get('success'):
            print("✅ Portföljananalys genomförd!")
            print(".2f"            print(f"🏥 Hälsa: {result.get('overall_advice', {}).get('overall_health', 'unknown').title()}")
        else:
            print(f"❌ Analys misslyckades: {result.get('error', 'Okänt fel')}")

    except Exception as e:
        print(f"❌ Demo fel: {e}")

async def demo_market_prediction():
    """Demonstrera marknadsprediktion"""
    print("\n🔮 MARKNADSPREDIKTION DEMO")
    print("=" * 50)

    try:
        from ..crypto.handlers.advanced_ai import advanced_ai_handler

        print("🔍 Förutsäger BITCOIN utveckling...")
        result = await advanced_ai_handler.get_market_prediction("bitcoin", "medium")

        if result.get('success'):
            pred = result.get('prediction', {})
            print("✅ Prediktion genomförd!")
            print(f"📈 Riktning: {pred.get('direction', 'unknown').title()}")
            print(".1%"            print(".1%"        else:
            print(f"❌ Prediktion misslyckades: {result.get('error', 'Okänt fel')}")

    except Exception as e:
        print(f"❌ Demo fel: {e}")

async def main():
    """Huvudfunktion för AI-demo"""
    print("🚀 ADVANCED AI CRYPTO ASSISTANT DEMO")
    print("=" * 60)
    print("Denna demo visar:")
    print("• 🤖 AI-driven trading-analys")
    print("• 🗣️  Naturlig språk-kommunikation")
    print("• 📊 Portföljoptimering")
    print("• 🔮 Marknadsprediktion")
    print("=" * 60)

    # Kontrollera om API-nycklar finns
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_key:
        print("⚠️  OPENROUTER_API_KEY saknas - AI-funktioner kommer använda fallback")
        print("   För full AI-funktionalitet, sätt OPENROUTER_API_KEY i din .env-fil")
    else:
        print("✅ OPENROUTER_API_KEY hittad - Full AI-funktionalitet tillgänglig")

    print("\n" + "=" * 60)

    try:
        # Kör alla demos
        await demo_ai_trading_analysis()
        await demo_conversational_ai()
        await demo_portfolio_advice()
        await demo_market_prediction()

    except KeyboardInterrupt:
        print("\n⏹️  Demo avbruten av användare")

    except Exception as e:
        print(f"\n❌ Demo fel: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ AI CRYPTO ASSISTANT DEMO KOMPLETT!")
    print("=" * 60)
    print("Ny AI-funktionalitet inkluderar:")
    print("• 🤖 Omfattande trading-analys med tekniska indikatorer")
    print("• 🧠 Konversationell AI för naturliga frågor")
    print("• 📊 AI-driven portföljanalys och råd")
    print("• 🔮 Marknadsprediktioner med sannolikheter")
    print("• 🛡️ Riskhantering och position sizing")
    print("• 📈 Realtids sentiment-analys")
    print("")
    print("🚀 För att använda i praktiken:")
    print("   1. Starta MCP-server: python crypto_mcp_server.py --sse")
    print("   2. Använd AI-verktyg i Roo Code eller AI Toolkit")
    print("   3. Fråga naturligt: 'Ska jag köpa Bitcoin?'")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())