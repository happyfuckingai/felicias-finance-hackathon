#!/usr/bin/env python3

import math
import os
import sys
import logging
import secrets
from mcp.server import FastMCP
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

# Configure detailed logging for full terminal output
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG for more detail
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to DEBUG for detailed output
logging.getLogger('crypto').setLevel(logging.DEBUG)
logging.getLogger('crypto_mcp_server').setLevel(logging.DEBUG)
logging.getLogger('mcp').setLevel(logging.DEBUG)  # Add MCP library logging
logging.getLogger('uvicorn').setLevel(logging.DEBUG)  # Add HTTP server logging

# Reduce noise from some libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("Starting Crypto MCP Server with full logging enabled")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
    logger.info(f"OPENROUTER_API_KEY available: {bool(os.getenv('OPENROUTER_API_KEY'))}")
except ImportError:
    logger.warning("python-dotenv not available, environment variables may not be loaded")

# Generate or load API key for SSE authentication
API_KEY = os.getenv('MCP_API_KEY') or secrets.token_urlsafe(32)
if not os.getenv('MCP_API_KEY'):
    logger.warning(f"Generated new MCP API key: {API_KEY[:10]}...")
    logger.warning("Set MCP_API_KEY environment variable for persistent key")

# Add parent directory to Python path to find crypto module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our crypto managers
from crypto_managers import WalletManager, TokenManager, MarketAnalyzer

# Import handlers for additional functionality
from crypto.handlers.research import ResearchHandler
from crypto.handlers.risk import RiskHandler
from crypto.core.var_calculator import VaRCalculator
from crypto.core.position_sizer import PositionSizer
from crypto.core.portfolio_risk import PortfolioRisk

# Initialize managers
wallet_manager = WalletManager()
token_manager = TokenManager()
market_analyzer = MarketAnalyzer()
research_handler = ResearchHandler()
risk_handler = RiskHandler()
var_calculator = VaRCalculator()
position_sizer = PositionSizer()
portfolio_risk = PortfolioRisk()

# Create MCP server
mcp = FastMCP("Crypto MCP Server")

# For SSE transport, we'll create a separate FastAPI app
from fastapi import FastAPI

sse_app = FastAPI(title="Crypto MCP Server", version="1.0.0")

# Add CORS middleware
sse_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for SSE requests"""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials

# WALLET TOOLS

@mcp.tool()
async def create_wallet() -> str:
    """Skapa en ny Ethereum wallet"""
    result = await wallet_manager.create_wallet()

    if result['success']:
        return f"""✅ **Ny Wallet Skapad!**

📍 **Adress:** `{result['address']}`
🔐 **Private Key:** `{result['private_key']}`

⚠️ **VIKTIGT:** Spara private key säkert!"""
    else:
        return f"❌ Fel vid wallet-skapande: {result['error']}"

@mcp.tool()
async def show_balance(private_key: str) -> str:
    """Visa saldo för en Ethereum wallet"""
    result = await wallet_manager.show_balance(private_key)

    if result['success']:
        return f"""💰 **Wallet Balance**

📍 Adress: `{result['address']}`
💎 ETH: {result['balance_eth']:.6f}
🔗 Chain: Base Testnet"""
    else:
        return f"❌ Fel vid balance-check: {result['error']}"

@mcp.tool()
async def send_transaction(private_key: str, to_address: str, amount_eth: float) -> str:
    """Skicka ETH till en annan adress"""
    result = await wallet_manager.send_transaction(private_key, to_address, amount_eth)

    if result.get('success'):
        return f"""✅ **Transaktion Skickad!**

📤 Till: `{to_address}`
💰 Belopp: {amount_eth} ETH
🔗 TX: `{result['transaction_hash']}`
⛽ Gas: {result.get('gas_used', 'N/A')}"""
    else:
        return f"❌ Fel vid transaktion: {result.get('error', 'Okänt fel')}"

# TOKEN TOOLS

@mcp.tool()
async def deploy_token(
    private_key: str,
    name: str,
    symbol: str,
    total_supply: int,
    chain: str = "base"
) -> str:
    """Deploya ERC20 token på blockchain"""
    result = await token_manager.deploy_token(private_key, name, symbol, total_supply, chain)

    if result.get('success'):
        return f"""🚀 **Token Deployad!**

🪙 Namn: {name} ({symbol})
📊 Supply: {total_supply:,}
📍 Contract: `{result['contract_address']}`
🔗 Chain: {chain.title()} Testnet"""
    else:
        return f"❌ Fel vid token-deployment: {result.get('error', 'Okänt fel')}"

# MARKET ANALYSIS TOOLS

@mcp.tool()
async def check_price(token_id: str) -> str:
    """Kolla aktuellt pris på en token"""
    result = await market_analyzer.check_price(token_id)

    if result['success']:
        price = result['price']
        change_24h = result.get('price_change_24h', 0)
        volume_24h = result.get('volume_24h', 0)

        change_emoji = "📈" if change_24h > 0 else "📉"

        return f"""💰 **{token_id.upper()} Pris**

₿ Pris: ${price:,.4f}
{change_emoji} 24h: {change_24h:+.2f}%
📊 Volym: ${volume_24h:,.0f}"""
    else:
        return f"❌ Fel vid prischeck: {result['error']}"

@mcp.tool()
async def analyze_token(token_id: str, days: int = 7) -> str:
    """Analysera token-prestanda över tid"""
    result = await market_analyzer.analyze_token(token_id, days)

    if result['success']:
        trend_emoji = "🚀" if result['trend'] == 'bullish' else "📉"

        return f"""{trend_emoji} **{token_id.upper()} Analys ({days} dagar)**

📊 Trend: {result['trend'].title()}
📈 Förändring: {result['price_change_percent']:+.2f}%
⚡ Volatilitet: {result['volatility_percent']:.1f}%
💰 Högsta: ${result['max_price']:,.4f}
💸 Lägsta: ${result['min_price']:,.4f}
📊 Genomsnitt: ${result['avg_price']:,.4f}"""
    else:
        return f"❌ Fel vid analys: {result['error']}"

@mcp.tool()
async def get_trending(limit: int = 5) -> str:
    """Visa trending tokens"""
    result = await market_analyzer.get_trending(limit)

    if result['success']:
        message = "🔥 **Trending Tokens**\n\n"

        for i, token in enumerate(result['trending_tokens'], 1):
            message += f"{i}. **{token['name']}** ({token['symbol'].upper()})\n"
            message += f"   ₿ Pris: {token['price_btc']:.8f} BTC\n\n"

        return message
    else:
        return f"❌ Fel vid hämtning av trending: {result['error']}"

@mcp.tool()
async def generate_signal(token_id: str) -> str:
    """Generera trading-signal för en token (med LLM-förstärkning om tillgängligt)"""
    result = await market_analyzer.generate_signal(token_id)

    if result['success']:
        signal = result['signal']
        confidence = result['confidence']
        reasoning = result['reasoning']
        analysis_method = result.get('analysis_method', 'technical')

        signal_emoji = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "🟡"

        message = f"""{signal_emoji} **{token_id.upper()} Trading Signal**

📊 Signal: **{signal}**
🎯 Confidence: {confidence:.1%}
🤖 Metod: {analysis_method.replace('_', ' ').title()}

📝 **Analys:**
"""

        for reason in reasoning:
            message += f"• {reason}\n"

        # Lägg till LLM-specifika insikter om tillgängliga
        if 'llm_insights' in result:
            insights = result['llm_insights']
            if 'sentiment_score' in insights:
                sentiment = insights['sentiment_score']
                message += f"\n📊 Sentiment Score: {sentiment:.2f}\n"

        return message
    else:
        return f"❌ Fel vid signalgenerering: {result['error']}"

# RISK MANAGEMENT TOOLS

@mcp.tool()
async def assess_portfolio_risk(portfolio_json: str) -> str:
    """Bedöm portföljrisk med avancerade VaR-modeller"""
    try:
        import json
        portfolio = json.loads(portfolio_json)

        result = await risk_handler.assess_portfolio_risk(portfolio, {})

        if result['success']:
            assessment = result['assessment']
            response = f"""
🛡️ **Portfölj Riskbedömning**

📊 **Övergripande Risknivå:** {assessment.get('overall_risk_level', 'unknown').title()}
📈 **VaR (95%):** {assessment.get('var_95', 0):.1%}
🛑 **Max Drawdown:** {assessment.get('max_drawdown', 0):.1%}

⚠️ **Riskvarningar:**
"""
            for warning in assessment.get('risk_warnings', []):
                response += f"• {warning}\n"

            response += f"\n💡 **Rekommendationer:**\n"
            for rec in assessment.get('recommendations', []):
                response += f"• {rec}\n"

            return response.strip()
        else:
            return f"❌ Riskbedömning misslyckades: {result.get('error', 'Okänt fel')}"

    except Exception as e:
        return f"❌ Fel vid riskbedömning: {e}"

@mcp.tool()
async def calculate_var(token_id: str, confidence_level: float = 0.95, method: str = "historical") -> str:
    """Beräkna Value-at-Risk för en token"""
    try:
        # Mock returns data för demonstration
        import numpy as np
        returns = np.random.normal(0.001, 0.02, 252)  # 252 trading days

        if method == "historical":
            var_value = await var_calculator.calculate_historical_var(returns, 10000)
        elif method == "parametric":
            var_value = await var_calculator.calculate_parametric_var(returns, 10000)
        elif method == "monte_carlo":
            var_value = await var_calculator.calculate_monte_carlo_var(returns, 10000)
        else:
            var_value = await var_calculator.calculate_historical_var(returns, 10000)

        return f"""
📊 **VaR Beräkning för {token_id.upper()}**

🎯 **Konfidensnivå:** {confidence_level:.0%}
📊 **Metod:** {method.title()}
💰 **VaR Värde:** ${abs(var_value):.2f}
📈 **Förväntad Shortfall:** ${abs(var_value) * 1.2:.2f}

💡 **Tolkning:** Det finns {confidence_level:.1%} sannolikhet att förlora högst ${abs(var_value):.2f} på en dag.
"""
    except Exception as e:
        return f"❌ VaR-beräkning misslyckades: {e}"

@mcp.tool()
async def optimize_position_size(token_id: str, confidence: float, capital: float = 10000) -> str:
    """Optimerad position sizing baserat på Kelly Criterion eller Risk Parity"""
    try:
        # Mock trading data
        win_rate = 0.55
        avg_win = 0.08
        avg_loss = -0.05

        # Kelly Criterion
        kelly_size = position_sizer.kelly_criterion(win_rate, avg_win, avg_loss)

        # Risk-based sizing
        risk_amount = capital * 0.02  # 2% risk per trade

        result = {
            'kelly_fraction': kelly_size,
            'risk_based_size': risk_amount,
            'recommended_size': min(kelly_size * capital, risk_amount),
            'confidence_adjustment': confidence
        }

        return f"""
📊 **Position Size Optimering för {token_id.upper()}**

🎯 **Kelly Criterion:** {result['kelly_fraction']:.1%}
💰 **Rekommenderad Position:** ${result['recommended_size']:.2f}
🛡️ **Risk-baserad Storlek:** ${result['risk_based_size']:.2f}
🎯 **Konfidens:** {result['confidence']:.1%}

💡 **Strategi:** Använd {min(result['kelly_fraction'], 0.02):.1%} av kapital per trade för optimal balans mellan risk och avkastning.
"""
    except Exception as e:
        return f"❌ Position sizing misslyckades: {e}"

@mcp.tool()
async def analyze_portfolio_metrics(portfolio_json: str) -> str:
    """Avancerad portföljanalys med Sharpe, Sortino och andra metrics"""
    try:
        import json
        portfolio = json.loads(portfolio_json)

        # Mock return data för varje innehav
        returns_data = {}
        for holding in portfolio.get('holdings', []):
            token_id = holding['token_id']
            returns_data[token_id] = {
                'returns': [0.01 * (1 + 0.1 * (i % 10 - 5)) for i in range(252)],
                'current_price': holding.get('current_price', 100)
            }

        # Beräkna portföljmetrics
        analysis = await portfolio_risk.calculate_portfolio_metrics(returns_data)

        response = f"""
📊 **Portfölj Performance Analys**

📈 **Sharpe Ratio:** {analysis.get('sharpe_ratio', 0):.2f}
🎯 **Sortino Ratio:** {analysis.get('sortino_ratio', 0):.2f}
📉 **Max Drawdown:** {analysis.get('max_drawdown', 0):.1%}
📊 **Volatilitet:** {analysis.get('volatility', 0):.1%}

💰 **Total Värde:** ${analysis.get('total_value', 0):.2f}
📈 **Total Avkastning:** {analysis.get('total_return', 0):.1%}

💡 **Riskjusterad Avkastning:** {analysis.get('sharpe_ratio', 0):.2f} (värden > 1.0 är utmärkt)
"""
        return response.strip()

    except Exception as e:
        return f"❌ Portföljanalys misslyckades: {e}"

@mcp.tool()
async def generate_risk_recommendations(portfolio_json: str) -> str:
    """Generera AI-driven riskrekommendationer"""
    try:
        import json
        portfolio = json.loads(portfolio_json)

        recommendations = await risk_handler.generate_risk_recommendations(portfolio)

        response = f"""
🛡️ **AI Riskrekommendationer**

📋 **Rekommenderade Åtgärder:**
"""

        for rec in recommendations.get('recommendations', []):
            response += f"• {rec}\n"

        response += f"""
⚠️ **Riskvarningar:**
"""
        for warning in recommendations.get('warnings', []):
            response += f"• {warning}\n"

        response += f"""
🎯 **Prioritet:** {recommendations.get('priority', 'medium').title()}
📊 **Konfidens:** {recommendations.get('confidence', 0):.1%}
"""

        return response.strip()

    except Exception as e:
        return f"❌ Riskrekommendationer misslyckades: {e}"

# RESEARCH TOOLS

@mcp.tool()
async def research_token(token_id: str) -> str:
    """Genomför fundamental analys av en token med AI (kräver OpenRouter API)"""
    result = await research_handler.handle({
        'action': 'research',
        'fields': {'token_id': token_id},
        'command': f'research {token_id}'
    })

    return result['message']

@mcp.tool()
async def analyze_sentiment(token_id: str) -> str:
    """Analysera marknads-sentiment för en token med AI (kräver OpenRouter API)"""
    result = await research_handler.handle({
        'action': 'sentiment',
        'fields': {'token_id': token_id},
        'command': f'sentiment {token_id}'
    })

    return result['message']

# ADVANCED AI TOOLS

@mcp.tool()
async def get_ai_trading_analysis(token_id: str) -> str:
    """Hämta avancerad AI-driven trading-analys för en token"""
    try:
        from crypto.handlers.advanced_ai import advanced_ai_handler
        result = await advanced_ai_handler.get_ai_trading_analysis(token_id)

        if result.get('success'):
            summary = result.get('executive_summary', 'Analys genomförd')
            recommendation = result.get('key_recommendation', {})

            response = f"""
🤖 **AI Trading-analys för {token_id.upper()}**

{summary}

🎯 **Rekommendation:**
• Åtgärd: **{recommendation.get('action', 'HOLD')}**
• Tillförlitlighet: {recommendation.get('confidence', 0):.1%}
• Position Size: {recommendation.get('position_size', 'moderate').title()}
• Tidshorisont: {recommendation.get('rationale', 'N/A')}

💡 **Förklaring:**
{recommendation.get('rationale', 'AI-analys baserad på tekniska och fundamentala faktorer')}

"""

            # Lägg till tekniska highlights
            highlights = result.get('technical_highlights', [])
            if highlights:
                response += "\n📊 **Tekniska Highlights:**\n"
                for highlight in highlights[:3]:  # Top 3
                    response += f"• {highlight}\n"

            # Lägg till nästa steg
            next_steps = result.get('next_steps', [])
            if next_steps:
                response += "\n🚀 **Nästa Steg:**\n"
                for step in next_steps[:3]:  # Top 3
                    response += f"• {step}\n"

            return response.strip()

        else:
            return f"❌ AI-analys misslyckades: {result.get('error', 'Okänt fel')}"

    except Exception as e:
        return f"❌ Fel vid AI-analys: {e}"


@mcp.tool()
async def ask_ai_assistant(question: str) -> str:
    """Fråga AI-assistenten på naturligt språk"""
    try:
        from crypto.handlers.advanced_ai import advanced_ai_handler

        result = await advanced_ai_handler.ask_ai_assistant(question)

        if result.get('success'):
            return f"""
🧠 **AI-assistent svarar:**

{result.get('message', 'Inget svar tillgängligt')}

📝 **Typ av svar:** {result.get('response_type', 'general').replace('_', ' ').title()}
⏰ **Genererad:** {result.get('metadata', {}).get('processing_time', 'N/A')}
"""
        else:
            return f"❌ AI-assistent svarade inte: {result.get('error', 'Okänt fel')}"

    except Exception as e:
        return f"❌ Fel vid AI-kommunikation: {e}"


@mcp.tool()
async def get_ai_portfolio_advice(portfolio_json: str) -> str:
    """Få AI-driven portföljanalys och råd"""
    try:
        import json
        from crypto.handlers.advanced_ai import advanced_ai_handler

        # Parse portföljdata
        try:
            portfolio = json.loads(portfolio_json)
        except json.JSONDecodeError:
            return "❌ Ogiltig JSON-format för portföljdata"

        result = await advanced_ai_handler.get_ai_portfolio_advice(portfolio)

        if result.get('success'):
            analysis = result.get('portfolio_analysis', [])
            advice = result.get('overall_advice', {})

            response = f"""
📊 **AI Portföljanalys**

💰 **Total Värde:** ${result.get('total_value', 0):,.2f}
🏥 **Portföljhälsa:** {advice.get('overall_health', 'unknown').replace('_', ' ').title()}
⚠️ **Risknivå:** {advice.get('risk_score', 0):.1%}

📋 **Rekommendationer:**
"""

            for rec in advice.get('recommendations', []):
                response += f"• {rec}\n"

            if analysis:
                response += f"\n📈 **Innehavsanalys ({len(analysis)} st):**\n"
                for holding in analysis[:5]:  # Top 5
                    rec = holding.get('ai_recommendation', {})
                    response += f"""
• **{holding['token_id'].upper()}**
  - Rekommendation: {rec.get('action', 'HOLD')}
  - Risk: {rec.get('risk_assessment', {}).get('overall_risk', 'medium').title()}
  - Värde: ${holding.get('current_value', 0):,.2f}
"""

            return response.strip()

        else:
            return f"❌ Portföljananalys misslyckades: {result.get('error', 'Okänt fel')}"

    except Exception as e:
        return f"❌ Fel vid portföljanalys: {e}"


@mcp.tool()
async def get_market_prediction(token_id: str, timeframe: str = "medium") -> str:
    """Få AI-driven marknadsprediktion"""
    try:
        from crypto.handlers.advanced_ai import advanced_ai_handler

        if timeframe not in ['short', 'medium', 'long']:
            timeframe = 'medium'

        result = await advanced_ai_handler.get_market_prediction(token_id, timeframe)

        if result.get('success'):
            pred = result.get('prediction', {})

            response = f"""
🔮 **AI Marknadsprediktion för {token_id.upper()}**

📈 **Riktning:** {pred.get('direction', 'unknown').title()}
🎯 **Sannolikhet:** {pred.get('probability', 0):.1%}
📊 **Tillförlitlighet:** {pred.get('confidence', 0):.1%}
⏱️ **Tidshorisont:** {timeframe.title()}

📋 **Nyckelfaktorer:**
"""

            for factor in pred.get('key_factors', []):
                response += f"• {factor}\n"

            scenarios = pred.get('scenarios', {})
            if scenarios and 'bull_case' in scenarios:
                response += f"""
🎲 **Scenarier:**

🟢 **Bull Case** ({scenarios['bull_case'].get('probability', 0):.1%})
{scenarios['bull_case'].get('description', 'N/A')}
Target: {scenarios['bull_case'].get('target_price', 'N/A')}

🟡 **Base Case** ({scenarios['base_case'].get('probability', 0):.1%})
{scenarios['base_case'].get('description', 'N/A')}
Target: {scenarios['base_case'].get('target_price', 'N/A')}

🔴 **Bear Case** ({scenarios['bear_case'].get('probability', 0):.1%})
{scenarios['bear_case'].get('description', 'N/A')}
Target: {scenarios['bear_case'].get('target_price', 'N/A')}
"""

            return response.strip()

        else:
            return f"❌ Prediktion misslyckades: {result.get('error', 'Okänt fel')}"

    except Exception as e:
        return f"❌ Fel vid prediktion: {e}"

# RESOURCES

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello {name}! Välkommen till Crypto MCP Server!"

@mcp.resource("help://info")
def get_help() -> str:
    """Get help information"""
    return """
🛠️ **Crypto MCP Server Verktyg:**

**Wallet Management:**
- create_wallet: Skapa ny Ethereum wallet
- show_balance: Visa wallet-saldo
- send_transaction: Skicka ETH-transaktion

**Token Operations:**
- deploy_token: Deploya ERC20 token på Base/Polygon

**Market Analysis:**
- check_price: Kolla token-pris
- analyze_token: Analysera token-prestanda
- get_trending: Visa trending tokens
- generate_signal: Generera trading-signaler (med LLM om tillgängligt)

**🛡️ Risk Management System:**
- assess_portfolio_risk: Omfattande portfölj riskbedömning med VaR-modeller
- calculate_var: Beräkna Value-at-Risk för enskilda tillgångar
- optimize_position_size: Optimerad position sizing baserat på Kelly Criterion
- analyze_portfolio_metrics: Avancerad portföljanalys (Sharpe, Sortino, Drawdown)
- generate_risk_recommendations: AI-driven riskhantering och rekommendationer

**🤖 Advanced AI Trading Assistant:**
- get_ai_trading_analysis: Omfattande AI-driven trading-analys med tekniska indikatorer, sentiment och prediktioner
- ask_ai_assistant: Naturlig språk-kommunikation med AI-assistenten ("Ska jag köpa Bitcoin?")
- get_ai_portfolio_advice: AI-driven portföljanalys och rebalanseringsråd
- get_market_prediction: AI-baserade marknadsprediktioner med scenarier

**🤖 AI-Powered Research (kräver OPENAI_API_KEY):**
- research_token: Fundamental analys av token med AI
- analyze_sentiment: Sentiment-analys från nyheter och marknad

**DEX Trading (förbättrad med AI):**
- Intelligent swap-routing med LLM-baserade beslut

**Konfiguration:**
- Sätt OPENAI_API_KEY för AI-funktionalitet
- Använd testnet-adresser för säkerhet

**Användning:**
Alla verktyg returnerar strukturerad data som kan användas av AI-agenter för automatiserade trading-strategier.

**Säkerhet:**
- Använd endast testnet för utveckling
- Spara private keys säkert
- Verifiera alla transaktioner innan genomförande
"""


# MCP-UI COMPONENT GENERATION ENDPOINTS
# These endpoints return UI component definitions for dynamic rendering

@sse_app.get("/mcp-ui/portfolio-dashboard")
async def get_crypto_portfolio_dashboard(token: str = Depends(verify_api_key)):
    """Generate crypto portfolio dashboard UI components"""
    # For crypto server, we don't have user auth like banking, so we'll return demo data

    # Get some market data for demo
    trending_result = await market_analyzer.get_trending(3)
    trending_tokens = []
    if trending_result.get('success'):
        trending_tokens = trending_result.get('trending_tokens', [])[:3]

    components = []

    # Portfolio Overview Card
    components.append({
        "type": "card",
        "id": "portfolio_overview",
        "title": "Portfolio Overview",
        "content": {
            "type": "metric",
            "value": "$12,543.67",
            "label": "Total Value",
            "change": "+5.2%",
            "changeType": "positive"
        },
        "layout": {"width": "1/2", "height": "auto"}
    })

    # Risk Metrics Card
    components.append({
        "type": "card",
        "id": "risk_metrics",
        "title": "Risk Metrics",
        "content": {
            "type": "metric",
            "value": "3.2%",
            "label": "VaR (95%)",
            "change": "-0.5%",
            "changeType": "positive"
        },
        "layout": {"width": "1/2", "height": "auto"}
    })

    # Asset Allocation Chart
    allocation_data = [
        {"asset": "BTC", "percentage": 45, "value": 5654.32},
        {"asset": "ETH", "percentage": 30, "value": 3760.90},
        {"asset": "ADA", "percentage": 15, "value": 1880.45},
        {"asset": "Others", "percentage": 10, "value": 1248.00}
    ]

    components.append({
        "type": "chart",
        "id": "asset_allocation",
        "title": "Asset Allocation",
        "chartType": "pie",
        "data": allocation_data,
        "layout": {"width": "1/2", "height": "400px"}
    })

    # Price Performance Chart
    performance_data = [
        {"date": "2024-01-01", "BTC": 45000, "ETH": 2500, "ADA": 0.45},
        {"date": "2024-01-08", "BTC": 47000, "ETH": 2650, "ADA": 0.48},
        {"date": "2024-01-15", "BTC": 48500, "ETH": 2750, "ADA": 0.52},
        {"date": "2024-01-22", "BTC": 51000, "ETH": 2900, "ADA": 0.55},
        {"date": "2024-01-29", "BTC": 52000, "ETH": 2950, "ADA": 0.58}
    ]

    components.append({
        "type": "chart",
        "id": "performance_chart",
        "title": "Price Performance (30 days)",
        "chartType": "line",
        "data": performance_data,
        "xAxis": "date",
        "yAxes": ["BTC", "ETH", "ADA"],
        "layout": {"width": "1/2", "height": "400px"}
    })

    # Trending Tokens Widget
    trending_items = []
    for token in trending_tokens:
        trending_items.append({
            "symbol": token.get('symbol', 'UNKNOWN'),
            "name": token.get('name', 'Unknown Token'),
            "price_btc": token.get('price_btc', 0),
            "trend": "up"  # Mock trend
        })

    if trending_items:
        components.append({
            "type": "list",
            "id": "trending_tokens",
            "title": "Trending Tokens",
            "items": trending_items,
            "layout": {"width": "1/1", "height": "auto"}
        })

    # Quick Actions Panel
    components.append({
        "type": "actions",
        "id": "trading_actions",
        "title": "Trading Actions",
        "actions": [
            {
                "id": "analyze_portfolio",
                "label": "Analyze Portfolio",
                "icon": "analytics",
                "action": "navigate",
                "params": {"route": "/portfolio-analysis"}
            },
            {
                "id": "check_signals",
                "label": "Check Signals",
                "icon": "signal",
                "action": "navigate",
                "params": {"route": "/signals"}
            },
            {
                "id": "rebalance",
                "label": "Rebalance",
                "icon": "balance",
                "action": "navigate",
                "params": {"route": "/rebalance"}
            }
        ],
        "layout": {"width": "1/1", "height": "auto"}
    })

    return {
        "dashboard": {
            "title": "Crypto Portfolio Dashboard",
            "components": components,
            "layout": "grid",
            "refreshInterval": 60000  # 60 seconds for crypto data
        }
    }


@sse_app.get("/mcp-ui/components/price-widget/{token_id}")
async def get_price_widget(token_id: str, token: str = Depends(verify_api_key)):
    """Generate price widget component for a token"""

    result = await market_analyzer.check_price(token_id)

    if result.get('success'):
        price = result.get('price', 0)
        change_24h = result.get('price_change_24h', 0)
        volume_24h = result.get('volume_24h', 0)

        change_type = "positive" if change_24h > 0 else "negative" if change_24h < 0 else "neutral"

        return {
            "component": {
                "type": "price-card",
                "title": f"{token_id.upper()} Price",
                "price": f"${price:,.4f}",
                "change": f"{change_24h:+.2f}%",
                "changeType": change_type,
                "volume": f"${volume_24h:,.0f}",
                "lastUpdated": "2024-01-15T10:30:00Z"
            }
        }
    else:
        raise HTTPException(status_code=404, detail=f"Price data not found for {token_id}")


@sse_app.get("/mcp-ui/components/portfolio-chart")
async def get_portfolio_chart(token: str = Depends(verify_api_key)):
    """Generate portfolio performance chart component"""

    # Mock portfolio performance data
    performance_data = []
    base_value = 10000
    for i in range(30):
        date = f"2024-01-{str(i+1).zfill(2)}"
        # Simulate some volatility
        change = (i % 7 - 3) * 0.02  # -6% to +4% pattern
        value = base_value * (1 + change)
        performance_data.append({
            "date": date,
            "value": value,
            "change": change
        })

    return {
        "component": {
            "type": "chart",
            "chartType": "area",
            "title": "Portfolio Performance (30 days)",
            "data": performance_data,
            "xAxis": "date",
            "yAxis": "value",
            "color": "#10b981",
            "height": "300px",
            "showChange": True
        }
    }


@sse_app.get("/mcp-ui/components/risk-dashboard")
async def get_risk_dashboard(token: str = Depends(verify_api_key)):
    """Generate risk analysis dashboard component"""

    # Mock risk metrics
    risk_metrics = {
        "var_95": 0.032,
        "sharpe_ratio": 1.45,
        "max_drawdown": 0.085,
        "volatility": 0.024,
        "beta": 1.12
    }

    return {
        "component": {
            "type": "risk-dashboard",
            "title": "Risk Analysis Dashboard",
            "metrics": risk_metrics,
            "riskLevel": "moderate",
            "recommendations": [
                "Consider diversifying into stablecoins",
                "Reduce exposure to high-volatility altcoins",
                "Implement dollar-cost averaging strategy"
            ]
        }
    }


@sse_app.get("/mcp-ui/components/trading-signals")
async def get_trading_signals(token: str = Depends(verify_api_key)):
    """Generate trading signals component"""

    # Get trending tokens for signals
    trending_result = await market_analyzer.get_trending(5)
    signals = []

    if trending_result.get('success'):
        for token_data in trending_result.get('trending_tokens', [])[:3]:
            # Generate mock signals
            signal_result = await market_analyzer.generate_signal(token_data.get('symbol', 'BTC'))
            if signal_result.get('success'):
                signals.append({
                    "token": token_data.get('symbol', 'UNKNOWN'),
                    "signal": signal_result.get('signal', 'HOLD'),
                    "confidence": signal_result.get('confidence', 0),
                    "analysis_method": signal_result.get('analysis_method', 'technical')
                })

    return {
        "component": {
            "type": "signals-list",
            "title": "Trading Signals",
            "signals": signals,
            "lastUpdated": "2024-01-15T10:30:00Z"
        }
    }


# REAL-TIME DATA STREAMING ENDPOINTS
# SSE endpoints for real-time crypto data updates

@sse_app.get("/mcp-ui/stream/price-updates/{token_id}")
async def stream_price_updates(token_id: str, token: str = Depends(verify_api_key)):
    """Stream real-time price updates for a token"""

    from sse_starlette.sse import EventSourceResponse
    import asyncio
    import json

    async def price_update_generator():
        """Generator for price update events"""
        while True:
            try:
                # Get fresh price data
                result = await market_analyzer.check_price(token_id)

                if result.get('success'):
                    price_data = {
                        "type": "price_update",
                        "token_id": token_id.upper(),
                        "price": result.get('price', 0),
                        "change_24h": result.get('price_change_24h', 0),
                        "volume_24h": result.get('volume_24h', 0),
                        "timestamp": "2024-01-15T10:30:00Z"
                    }

                    yield {
                        "event": "price_update",
                        "data": json.dumps(price_data)
                    }

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Error in price update stream for {token_id}: {e}")
                await asyncio.sleep(30)

    return EventSourceResponse(price_update_generator())


@sse_app.get("/mcp-ui/stream/market-overview")
async def stream_market_overview(token: str = Depends(verify_api_key)):
    """Stream market overview updates (trending tokens, market sentiment)"""

    from sse_starlette.sse import EventSourceResponse
    import asyncio
    import json

    async def market_overview_generator():
        """Generator for market overview events"""
        while True:
            try:
                # Get trending tokens
                trending_result = await market_analyzer.get_trending(5)

                market_data = {
                    "type": "market_overview",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "trending_tokens": [],
                    "market_sentiment": "neutral"  # Mock sentiment
                }

                if trending_result.get('success'):
                    for token in trending_result.get('trending_tokens', [])[:3]:
                        market_data["trending_tokens"].append({
                            "symbol": token.get('symbol', 'UNKNOWN'),
                            "name": token.get('name', 'Unknown'),
                            "price_btc": token.get('price_btc', 0),
                            "trend": "up"  # Mock trend
                        })

                # Mock market sentiment changes
                import random
                sentiments = ["bullish", "bearish", "neutral", "volatile"]
                market_data["market_sentiment"] = random.choice(sentiments)

                yield {
                    "event": "market_overview",
                    "data": json.dumps(market_data)
                }

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                logger.error(f"Error in market overview stream: {e}")
                await asyncio.sleep(60)

    return EventSourceResponse(market_overview_generator())


@sse_app.get("/mcp-ui/stream/portfolio-updates")
async def stream_portfolio_updates(token: str = Depends(verify_api_key)):
    """Stream portfolio performance updates"""

    from sse_starlette.sse import EventSourceResponse
    import asyncio
    import json

    async def portfolio_update_generator():
        """Generator for portfolio update events"""
        base_value = 12543.67

        while True:
            try:
                # Mock portfolio value changes
                import random
                change_percent = random.uniform(-0.05, 0.05)  # -5% to +5%
                new_value = base_value * (1 + change_percent)

                portfolio_data = {
                    "type": "portfolio_update",
                    "total_value": new_value,
                    "change_24h": change_percent * 100,
                    "change_type": "positive" if change_percent > 0 else "negative",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "holdings": [
                        {
                            "token_id": "BTC",
                            "value": new_value * 0.45,
                            "change": random.uniform(-0.02, 0.02) * 100
                        },
                        {
                            "token_id": "ETH",
                            "value": new_value * 0.30,
                            "change": random.uniform(-0.03, 0.03) * 100
                        },
                        {
                            "token_id": "ADA",
                            "value": new_value * 0.15,
                            "change": random.uniform(-0.04, 0.04) * 100
                        }
                    ]
                }

                yield {
                    "event": "portfolio_update",
                    "data": json.dumps(portfolio_data)
                }

                await asyncio.sleep(45)  # Update every 45 seconds

            except Exception as e:
                logger.error(f"Error in portfolio update stream: {e}")
                await asyncio.sleep(45)

    return EventSourceResponse(portfolio_update_generator())


@sse_app.get("/mcp-ui/stream/trading-signals")
async def stream_trading_signals(token: str = Depends(verify_api_key)):
    """Stream trading signal updates"""

    from sse_starlette.sse import EventSourceResponse
    import asyncio
    import json

    async def trading_signals_generator():
        """Generator for trading signal events"""
        while True:
            try:
                # Get trending tokens and generate signals
                trending_result = await market_analyzer.get_trending(3)

                signals_data = {
                    "type": "trading_signals_update",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "signals": []
                }

                if trending_result.get('success'):
                    for token_data in trending_result.get('trending_tokens', []):
                        # Generate signal for this token
                        signal_result = await market_analyzer.generate_signal(token_data.get('symbol', 'BTC'))

                        if signal_result.get('success'):
                            signals_data["signals"].append({
                                "token_id": token_data.get('symbol', 'UNKNOWN'),
                                "signal": signal_result.get('signal', 'HOLD'),
                                "confidence": signal_result.get('confidence', 0),
                                "analysis_method": signal_result.get('analysis_method', 'technical'),
                                "timestamp": "2024-01-15T10:30:00Z"
                            })

                if signals_data["signals"]:
                    yield {
                        "event": "trading_signals",
                        "data": json.dumps(signals_data)
                    }

                await asyncio.sleep(120)  # Update every 2 minutes (signals don't change that often)

            except Exception as e:
                logger.error(f"Error in trading signals stream: {e}")
                await asyncio.sleep(120)

    return EventSourceResponse(trading_signals_generator())


@sse_app.get("/mcp-ui/stream/risk-alerts")
async def stream_risk_alerts(token: str = Depends(verify_api_key)):
    """Stream risk management alerts and updates"""

    from sse_starlette.sse import EventSourceResponse
    import asyncio
    import json

    async def risk_alerts_generator():
        """Generator for risk alert events"""
        alert_count = 0

        while True:
            try:
                # Mock occasional risk alerts
                import random
                if random.random() < 0.05:  # 5% chance every 30 seconds
                    alert_count += 1

                    mock_alerts = [
                        {
                            "id": f"alert_{alert_count}",
                            "type": "volatility_warning",
                            "severity": "medium",
                            "message": "High volatility detected in BTC position",
                            "recommendation": "Consider reducing position size",
                            "affected_tokens": ["BTC"]
                        },
                        {
                            "id": f"alert_{alert_count}",
                            "type": "diversification_alert",
                            "severity": "low",
                            "message": "Portfolio concentration risk detected",
                            "recommendation": "Consider adding more diverse assets",
                            "affected_tokens": ["portfolio"]
                        },
                        {
                            "id": f"alert_{alert_count}",
                            "type": "risk_limit_approaching",
                            "severity": "high",
                            "message": "VaR limit approaching 95% threshold",
                            "recommendation": "Reduce exposure or hedge positions",
                            "affected_tokens": ["portfolio"]
                        }
                    ]

                    alert = random.choice(mock_alerts)

                    yield {
                        "event": "risk_alert",
                        "data": json.dumps({
                            "type": "risk_alert",
                            "alert": alert,
                            "timestamp": "2024-01-15T10:30:00Z"
                        })
                    }

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in risk alerts stream: {e}")
                await asyncio.sleep(30)

    return EventSourceResponse(risk_alerts_generator())


# Start server
