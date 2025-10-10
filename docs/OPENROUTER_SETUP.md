# 🔑 **OpenRouter API Setup Guide**

## Vad är OpenRouter?

OpenRouter är en unified API som ger tillgång till **100+ AI-modeller** från olika providers (Anthropic, OpenAI, Google, Meta, etc.) genom ett enda API.

## 🚀 **Steg-för-steg Setup:**

### **1. Skapa OpenRouter konto:**
1. Gå till [openrouter.ai](https://openrouter.ai)
2. Klicka på "**Sign Up**" (gratis)
3. Verifiera din email

### **2. Generera API Key:**
1. Logga in på ditt konto
2. Gå till "**API Keys**" i vänstra menyn
3. Klicka på "**Create Key**"
4. Ge nyckeln ett namn (t.ex. "Crypto Trading AI")
5. Kopiera API-nyckeln (börjar med `sk-or-v1-...`)

### **3. Konfigurera i ditt projekt:**

#### **Alternativ A: Environment Variable (Rekommenderas)**
```bash
# I terminalen:
export OPENROUTER_API_KEY="sk-or-v1-din-nyckel-här"

# Eller lägg till i din .bashrc/.zshrc:
echo 'export OPENROUTER_API_KEY="sk-or-v1-din-nyckel-här"' >> ~/.bashrc
source ~/.bashrc
```

#### **Alternativ B: .env fil**
```bash
# Kopiera och redigera .env filen:
cp crypto/.env.example crypto/.env

# Redigera crypto/.env och lägg till:
OPENROUTER_API_KEY=sk-or-v1-din-nyckel-här
```

### **4. Testa att det fungerar:**
```bash
# Testa LLM integration
python -c "
import asyncio
from crypto.core.llm_integration import LLMIntegration

async def test():
    llm = LLMIntegration()
    try:
        # Testa en enkel analys
        news = [{'title': 'Bitcoin rally', 'content': 'BTC is up 10%'}]
        result = await llm.analyze_market_sentiment('bitcoin', news)
        print('✅ OpenRouter fungerar!')
        print(f'Sentiment: {result.get(\"sentiment_score\", \"N/A\")}')
    except Exception as e:
        print(f'❌ Fel: {e}')

asyncio.run(test())
"
```

## 💰 **Prissättning:**

### **Gratis Tier:**
- **500 requests** per dag
- Tillgång till grundmodeller
- Perfekt för testing och development

### **Betalt Tier (från $5/månad):**
- **100,000+ requests** per dag
- Tillgång till premium modeller (GPT-4, Claude, etc.)
- Högre rate limits

## 🤖 **Vilka modeller används i systemet:**

Systemet använder automatiskt den bästa tillgängliga modellen:

### **Primär modell:**
- `nvidia/nemotron-nano-9b-v2:free` (gratis, snabb för enklare analyser)

### **Fallback till premium (om tillgängligt):**
- `anthropic/claude-3-haiku`
- `openai/gpt-3.5-turbo`
- `google/gemini-pro`

## 🧪 **Vad kräver AI-funktioner:**

### **AI-funktioner som fungerar utan API key:**
- ✅ Grundläggande teknisk analys
- ✅ Riskberäkningar (VaR, Sharpe, etc.)
- ✅ Position sizing algoritmer
- ✅ Stop-loss management

### **AI-funktioner som kräver OpenRouter:**
- 🤖 **Naturligt språk förståelse** (Intent Processor)
- 📊 **Avancerad sentimentanalys** (nyheter + social media)
- 🎯 **AI-driven signalgenerering**
- 🔬 **Fundamental analys** av tokens/projekt
- 💡 **Strategioptimering** och förbättringsförslag

## 🚨 **Felsökning:**

### **"OpenRouter API key required"**
```bash
# Kontrollera att nyckeln är satt:
echo $OPENROUTER_API_KEY

# Om tom, sätt den:
export OPENROUTER_API_KEY="sk-or-v1-din-nyckel"
```

### **"Rate limit exceeded"**
- Vänta några minuter
- Uppgradera till betalt tier för högre limits
- Modellen fallbacks automatiskt till enklare modeller

### **"Model not available"**
- Systemet fallbacks automatiskt till andra modeller
- Kontrollera [status.openrouter.ai](https://status.openrouter.ai) för model status

## 🔐 **Säkerhet:**

- ✅ API-nycklar lagras endast lokalt
- ✅ Ingen data skickas till andra tjänster
- ✅ Krypterad kommunikation med OpenRouter API
- ✅ Automatisk cleanup av sessioner

## 🎯 **Rekommenderade inställningar:**

För **development/testing:**
```bash
# Använd gratis tier
OPENROUTER_API_KEY=sk-or-v1-din-gratis-nyckel
```

För **production/live trading:**
```bash
# Använd betalt tier för högre reliability
OPENROUTER_API_KEY=sk-or-v1-din-premium-nyckel
```

---

## 🚀 **Redo att börja:**

1. **Skapa konto** på [openrouter.ai](https://openrouter.ai)
2. **Generera API key**
3. **Konfigurera** i ditt projekt enligt ovan
4. **Testa** med kommandot ovan
5. **Starta** ditt AI-driven crypto trading system!

```bash
# Starta systemet när allt är konfigurerat:
python crypto/run_streamlit.py
```

**Nu har du full AI-power i ditt trading system!** 🤖🚀