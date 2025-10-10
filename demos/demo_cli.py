#!/usr/bin/env python3
"""
🚀 AI Crypto Trading Demo - CLI Version

Enkel CLI-demo för att testa AI-driven crypto trading system
utan att behöva Streamlit.
"""

import asyncio
import sys
import os

# Fix path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from crypto.rules.intent_processor import IntentProcessor
from crypto.core.llm_integration import LLMIntegration
from crypto.handlers.risk import RiskHandler

class AIDemoAssistant:
    """Enkel AI-assistent för demo"""

    def __init__(self):
        try:
            self.intent_processor = IntentProcessor()
            self.llm = LLMIntegration()
            self.risk_handler = RiskHandler()
            print("✅ AI Demo Assistant initialized")
        except Exception as e:
            print(f"⚠️ Some components failed to load: {e}")
            print("Running in basic mode...")

    async def chat(self, message):
        """Hantera användarmeddelande"""
        print(f"\n🤖 AI Trading Assistant: ")

        try:
            # Process intent
            intent = await self.intent_processor.process_intent(message)

            if intent['success']:
                response = await self.generate_response(message, intent)
            else:
                response = "Jag förstår inte helt. Försök säga något som 'analysera bitcoin' eller 'ge råd om risk'."
        except Exception as e:
            response = f"❌ Ett fel uppstod: {e}"

        print(response)
        print("-" * 50)

    async def generate_response(self, message, intent):
        """Generera svar baserat på intent"""
        intent_type = intent['intent']

        if 'analyze' in intent_type or 'token_id' in intent.get('fields', {}):
            token = intent.get('fields', {}).get('token_id', 'bitcoin')
            return await self.analyze_token(token)

        elif 'risk' in message.lower() or 'oro' in message.lower():
            return self.handle_risk_concerns()

        elif 'köp' in message.lower() or 'sälj' in message.lower() or 'position' in message.lower():
            return self.handle_trading_decision()

        else:
            return self.general_conversation()

    async def analyze_token(self, token):
        """Mock AI-analys"""
        # Mock data
        analysis = {
            'trend': 'bullish',
            'confidence': 0.82,
            'price': {'bitcoin': 45000, 'ethereum': 2800, 'solana': 120}.get(token, 100),
            'sentiment': 0.65,
            'recommendation': 'BUY'
        }

        response = f"""
📊 **AI-Analys av {token.upper()}:**

📈 **Trend:** {analysis['trend'].title()}
🎯 **Konfidens:** {analysis['confidence']:.1%}
💰 **Pris:** ${analysis['price']:.2f}
😊 **Sentiment:** Positiv ({analysis['sentiment']:.2f})
🎪 **Rekommendation:** {analysis['recommendation']}

🤖 *Denna analys baseras på tekniska indikatorer och AI-modellering*
"""
        return response

    def handle_risk_concerns(self):
        """Hantera riskfrågor"""
        return """🛡️ **Riskråd från AI:**

• Använd alltid stop-loss (rekommenderar 5-10%)
• Diversifiera över flera tillgångar
• Investera bara pengar du har råd att förlora
• Övervaka din totala portföljrisk

💡 **AI-tips:** Nuvarande marknadsvolatilitet är måttlig. Öka inte positioner över 5% per trade."""

    def handle_trading_decision(self):
        """Hantera trading beslut"""
        return """🎯 **AI Trading Råd:**

✅ **Innan du handlar:**
• Kontrollera alltid trend och sentiment
• Utvärdera din risktolerans
• Beräkna position size korrekt
• Sätt stop-loss och take-profit

🎪 **AI-rekommendation:** Börja smått och skala upp när du känner dig bekväm."""

    def general_conversation(self):
        """Allmän konversation"""
        responses = [
            "Jag är här för att hjälpa dig med dina trading-beslut! Vad kan jag hjälpa till med?",
            "Vad vill du veta om marknaden idag?",
            "Jag kan hjälpa med analys, riskråd eller allmänna frågor om trading."
        ]
        return responses[0]

async def main():
    """Huvudfunktion"""
    print("🚀 AI Crypto Trading Demo - CLI Version")
    print("=" * 50)
    print("Hej! Jag är din AI Trading Assistant.")
    print("Vi kan prata om allt som rör trading, risk och marknader.")
    print("")
    print("Exempel på vad du kan säga:")
    print("• 'analysera bitcoin'")
    print("• 'jag är orolig för risken'")
    print("• 'ge råd om diversification'")
    print("")
    print("Skriv 'bye' för att avsluta")
    print("=" * 50)

    assistant = AIDemoAssistant()

    while True:
        try:
            user_input = input("\nDu: ").strip()

            if user_input.lower() in ['bye', 'exit', 'quit', 'avsluta']:
                print("\n🤖 Hej då! Kom tillbaka när som helst. 📈")
                break

            if user_input:
                await assistant.chat(user_input)

        except KeyboardInterrupt:
            print("\n🤖 Hej då! Vi ses snart! 📈")
            break
        except Exception as e:
            print(f"\n❌ Oops: {e}")
            print("Försök igen!")

if __name__ == "__main__":
    asyncio.run(main())