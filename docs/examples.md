# 💡 Kodexempel - Risk Management System

Praktiska kodexempel för att använda Risk Management System i olika scenarier.

## 🏁 Grundläggande Användning

### 1. Enkel Riskbedömning

```python
import asyncio
from handlers.risk import RiskHandler

async def basic_example():
    # Skapa riskhanterare
    risk_handler = RiskHandler()

    # Definiera portfölj
    portfolio = {
        'BTC': 0.6,   # 60% Bitcoin
        'ETH': 0.4    # 40% Ethereum
    }

    # Nuvarande priser
    prices = {
        'BTC': 45000,
        'ETH': 3000
    }

    # Genomför riskbedömning
    assessment = await risk_handler.assess_portfolio_risk(portfolio, prices)

    print("Riskbedömning Resultat:"    print(f"• Risknivå: {assessment.overall_risk_level}")
    print(f"• VaR (95%): ${assessment.var_95:,.2f}")
    print(f"• Expected Shortfall: ${assessment.expected_shortfall:,.2f}")
    print(f"• Sharpe Ratio: {assessment.sharpe_ratio:.2f}")

    return assessment

# Kör exemplet
result = asyncio.run(basic_example())
```

### 2. Position Sizing Optimization

```python
async def position_sizing_example():
    risk_handler = RiskHandler()

    # Använd Kelly Criterion
    kelly_result = await risk_handler.calculate_optimal_position_size(
        token='BTC',
        entry_price=45000,
        portfolio_value=100000,
        risk_tolerance=0.02,
        method='kelly',
        win_rate=0.65,           # 65% win rate
        avg_win_return=0.08,     # 8% average win
        avg_loss_return=-0.04    # 4% average loss
    )

    print("Kelly Criterion Resultat:"    print(f"• Rekommenderad position: {kelly_result['position_size']:.1%}")
    print(f"• Positionvärde: ${kelly_result['position_value']:,.2f}")
    print(f"• Förväntad risk: {kelly_result.get('expected_risk', 0):.1%}")

    # Använd Fixed Fractional
    fixed_result = await risk_handler.calculate_optimal_position_size(
        token='ETH',
        entry_price=3000,
        portfolio_value=100000,
        risk_tolerance=0.02,
        method='fixed_fractional'
    )

    print("\nFixed Fractional Resultat:"    print(f"• Rekommenderad position: {fixed_result['position_size']:.1%}")
    print(f"• Positionvärde: ${fixed_result['position_value']:,.2f}")

# Kör exemplet
asyncio.run(position_sizing_example())
```

## 🛡️ Avancerad Risk Management

### 3. Risk-aware Strategiskapning

```python
from handlers.strategy import StrategyHandler

async def risk_aware_strategy():
    # Skapa strategy handler (inkluderar nu risk management)
    strategy_handler = StrategyHandler()

    # Skapa strategi med riskparametrar
    result = await strategy_handler.handle({
        'action': 'create',
        'command': 'skapa momentum strategi med medium risk för btc och eth',
        'fields': {},
        'user_id': 'demo_user'
    })

    print("Strategi skapad med risk management:")
    print(result['message'])

    if 'risk_assessment' in result:
        risk = result['risk_assessment']
        print("
Riskbedömning:"        print(f"• Nivå: {risk.get('overall_risk_level', 'unknown').title()}")
        print(f"• VaR (95%): ${risk.get('var_95', 0):,.2f}")

# Kör exemplet
asyncio.run(risk_aware_strategy())
```

### 4. Realtids Risk Monitoring

```python
async def real_time_monitoring():
    risk_handler = RiskHandler()

    # Sätt upp positioner
    positions = {
        'BTC': {'entry_price': 45000, 'quantity': 1.0},
        'ETH': {'entry_price': 3000, 'quantity': 10.0}
    }

    # Konfigurera riskkontroller
    for token, position in positions.items():
        await risk_handler.setup_risk_management(
            token=token,
            entry_price=position['entry_price'],
            quantity=position['quantity'],
            stop_loss_percentage=0.05,      # 5% stop loss
            take_profit_percentage=0.10,    # 10% take profit
            trailing_stop=True              # Aktivera trailing stop
        )

    print("Risk monitoring aktiverat för:")
    for token, pos in positions.items():
        value = pos['entry_price'] * pos['quantity']
        print(f"• {token}: ${value:,.2f} ({pos['quantity']} units)")

    # Simulera prisuppdateringar
    price_updates = {
        'BTC': 46750,  # +4% (ingen trigger)
        'ETH': 2850    # -5% (aktiverar stop loss)
    }

    print("
Simulerade prisuppdateringar:"    triggers = await risk_handler.update_position_prices(price_updates)

    for token, trigger in triggers.items():
        if trigger.get('stop_loss'):
            print(f"🚨 {token}: STOP LOSS AKTIVERAD!")
        elif trigger.get('take_profit'):
            print(f"🎯 {token}: TAKE PROFIT AKTIVERAD!")
        else:
            print(f"✅ {token}: Inga triggers aktiverade")

# Kör exemplet
asyncio.run(real_time_monitoring())
```

## 📊 Risk Analytics

### 5. Detaljerad Portföljanalys

```python
async def detailed_portfolio_analysis():
    risk_handler = RiskHandler()

    # Exempelportfölj
    portfolio = {
        'BTC': 0.4,
        'ETH': 0.35,
        'ADA': 0.15,
        'DOT': 0.1
    }

    prices = {
        'BTC': 45000,
        'ETH': 3000,
        'ADA': 0.50,
        'DOT': 8.50
    }

    # Hämta detaljerad riskprofil
    profile = await risk_handler.get_portfolio_risk_profile(portfolio, prices)

    print("📊 Detaljerad Portföljanalys"    print("=" * 50)

    print("💰 Portföljöversikt:"    print(f"• Totalvärde: ${profile['portfolio_value']:,.2f}")
    print(f"• Antal positioner: {profile['num_positions']}")

    if profile.get('risk_metrics'):
        metrics = profile['risk_metrics']
        print("
📈 Riskmått:"        print(f"• Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A'):.2f}")
        print(f"• Sortino Ratio: {metrics.get('sortino_ratio', 'N/A'):.2f}")
        print(f"• Max Drawdown: {metrics.get('max_drawdown', 0):.1%}")
        print(f"• VaR (95%): ${metrics.get('value_at_risk', 0):,.2f}")

    print("
🎯 Diversifiering:"    print(f"• Diversifieringspoäng: {profile.get('diversification_score', 0):.2f}")

# Kör exemplet
asyncio.run(detailed_portfolio_analysis())
```

## 🔧 Direkt Användning av Core Components

### 6. VaR-beräkningar

```python
from core.var_calculator import VaRCalculator
import numpy as np

def var_calculations():
    # Skapa VaR-beräknare
    calculator = VaRCalculator(confidence_level=0.95, time_horizon=1)

    # Generera exempeldata
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 1000)  # 1000 dagars avkastningar
    portfolio_value = 100000

    print("🧮 VaR-beräkningar"    print("=" * 30)

    # Olika VaR-metoder
    methods = [
        ('Historisk', calculator.calculate_historical_var),
        ('Parametrisk', calculator.calculate_parametric_var),
        ('Monte Carlo', lambda r, v: calculator.calculate_monte_carlo_var(r, v, simulations=5000))
    ]

    for name, method in methods:
        try:
            var = method(returns, portfolio_value)
            print(".2f"        except Exception as e:
            print(f"❌ {name}: {e}")

    # Expected Shortfall
    try:
        es = calculator.calculate_expected_shortfall(returns, portfolio_value)
        print(".2f"    except Exception as e:
        print(f"❌ Expected Shortfall: {e}")

# Kör exemplet
var_calculations()
```

### 7. Position Sizing Algoritmer

```python
from core.position_sizer import PositionSizer

def position_sizing_demo():
    sizer = PositionSizer(max_portfolio_risk=0.02, max_single_position=0.10)

    print("📏 Position Sizing Demonstration"    print("=" * 40)

    portfolio_value = 100000

    # Kelly Criterion
    print("🎯 Kelly Criterion:"    kelly = sizer.kelly_criterion(
        win_rate=0.65,
        avg_win_return=0.08,
        avg_loss_return=-0.04,
        current_portfolio=portfolio_value
    )
    print(f"• Kelly Fraction: {kelly['kelly_fraction']:.1%}")
    print(f"• Conservative Kelly: {kelly['conservative_kelly']:.1%}")
    print(f"• Rekommenderad position: {kelly['position_size']:.1%}")
    print(f"• Positionvärde: ${kelly['position_value']:,.2f}")

    # Fixed Fractional
    print("
📊 Fixed Fractional:"    fixed = sizer.fixed_fractional(portfolio_value, risk_per_trade=0.02)
    print(f"• Position size: {fixed:.1%}")
    print(f"• Positionvärde: ${fixed * portfolio_value:,.2f}")

    # Volatility-adjusted
    print("
📈 Volatility-adjusted:"    vol_adjusted = sizer.fixed_fractional(
        portfolio_value, risk_per_trade=0.02, volatility=0.05  # 5% volatilitet
    )
    print(f"• Position size: {vol_adjusted:.1%}")
    print(f"• Positionvärde: ${vol_adjusted * portfolio_value:,.2f}")

# Kör exemplet
position_sizing_demo()
```

## 🔄 Integration med Trading System

### 8. Risk-aware Trading Bot

```python
import asyncio
from datetime import datetime
from handlers.risk import RiskHandler

class RiskAwareTradingBot:
    def __init__(self):
        self.risk_handler = RiskHandler()
        self.portfolio = {'BTC': 0.5, 'ETH': 0.3, 'USDC': 0.2}
        self.positions = {}

    async def initialize_portfolio(self):
        """Initiera portfölj med riskkontroller."""
        print("🚀 Initialiserar risk-aware trading bot...")

        # Sätt upp riskkontroller för befintliga positioner
        for token, allocation in self.portfolio.items():
            if token != 'USDC':  # Skip stablecoin
                # Simulerade priser och kvantiteter
                price = 45000 if token == 'BTC' else 3000
                quantity = allocation * 100000 / price  # $100k portfölj

                await self.risk_handler.setup_risk_management(
                    token=token,
                    entry_price=price,
                    quantity=quantity,
                    stop_loss_percentage=0.05,
                    take_profit_percentage=0.10,
                    trailing_stop=True
                )

                self.positions[token] = {
                    'entry_price': price,
                    'quantity': quantity,
                    'current_price': price
                }

        print("✅ Risk management aktiverat för alla positioner")

    async def process_market_update(self, token: str, new_price: float):
        """Processa marknadsprisuppdatering."""
        if token not in self.positions:
            return

        old_price = self.positions[token]['current_price']
        self.positions[token]['current_price'] = new_price

        # Uppdatera riskhantering
        triggers = await self.risk_handler.update_position_prices({token: new_price})

        if triggers.get(token, {}).get('stop_loss'):
            print(f"🚨 STOP LOSS aktiverad för {token}!")
            print(f"   Entry: ${old_price:,.2f} → Current: ${new_price:,.2f}")
            await self.execute_emergency_sale(token, new_price)

        elif triggers.get(token, {}).get('take_profit'):
            print(f"🎯 TAKE PROFIT aktiverad för {token}!")
            print(f"   Entry: ${old_price:,.2f} → Current: ${new_price:,.2f}")
            await self.execute_profit_taking(token, new_price)

        elif triggers.get(token, {}).get('trailing_stop'):
            print(f"🔄 Trailing stop uppdaterad för {token}")

    async def execute_emergency_sale(self, token: str, price: float):
        """Exekvera emergency försäljning."""
        position = self.positions[token]
        pnl = (price - position['entry_price']) * position['quantity']

        print(f"💸 Emergency försäljning: {token}")
        print(f"   Försäljning av {position['quantity']} units @ ${price:,.2f}")
        print(".2f"
        # Här skulle du lägga till riktig trading logik

    async def execute_profit_taking(self, token: str, price: float):
        """Exekvera profit-taking."""
        position = self.positions[token]
        pnl = (price - position['entry_price']) * position['quantity']

        print(f"💰 Profit-taking: {token}")
        print(f"   Försäljning av {position['quantity']} units @ ${price:,.2f}")
        print(".2f"
        # Här skulle du lägga till riktig trading logik

    async def get_portfolio_status(self):
        """Hämta portföljstatus."""
        # Simulerade nuvarande priser
        current_prices = {
            'BTC': 46500,  # +3.3%
            'ETH': 2940,   # -2%
            'USDC': 1.0
        }

        # Uppdatera alla positioner
        for token in ['BTC', 'ETH']:
            if token in self.positions:
                await self.process_market_update(token, current_prices[token])

        # Riskbedömning
        assessment = await self.risk_handler.assess_portfolio_risk(
            {k: v for k, v in self.portfolio.items() if k != 'USDC'},
            {k: v for k, v in current_prices.items() if k != 'USDC'}
        )

        print("
📊 Portföljstatus:"        print(f"• Risknivå: {assessment.overall_risk_level}")
        print(".1%"        print(f"• Sharpe Ratio: {assessment.sharpe_ratio:.2f}")

        return assessment

# Demo av trading bot
async def trading_bot_demo():
    bot = RiskAwareTradingBot()
    await bot.initialize_portfolio()
    await bot.get_portfolio_status()

# Kör demo
asyncio.run(trading_bot_demo())
```

## 📋 Error Handling

### 9. Robust Error Handling

```python
async def robust_risk_management():
    """Exempel på robust felhantering."""

    risk_handler = RiskHandler()

    try:
        # Försök genomföra riskbedömning
        portfolio = {'BTC': 0.6, 'ETH': 0.4}
        prices = {'BTC': 45000, 'ETH': 3000}

        assessment = await risk_handler.assess_portfolio_risk(portfolio, prices)

        print("✅ Riskbedömning lyckades!")
        print(f"Risknivå: {assessment.overall_risk_level}")

    except Exception as e:
        print(f"❌ Riskbedömning misslyckades: {e}")

        # Fallback: Använd konservativa antaganden
        print("🔄 Använder fallback-strategi...")
        conservative_assessment = {
            'overall_risk_level': 'high',
            'var_95': 0.15,  # 15% konservativ VaR
            'recommendations': [
                'Använd mindre positioner',
                'Öka stop-loss nivåer',
                'Diversifiera portföljen'
            ]
        }

        print(f"Fallback risknivå: {conservative_assessment['overall_risk_level']}")

    finally:
        # Rensa upp resurser
        print("🧹 Rensing resurser...")

# Kör robust exempel
asyncio.run(robust_risk_management())
```

## 🔧 Anpassning och Utökning

### 10. Custom Risk Metrics

```python
from core.portfolio_risk import PortfolioRisk
import pandas as pd
import numpy as np

class CustomRiskMetrics:
    def __init__(self):
        self.base_analyzer = PortfolioRisk()

    def calculate_custom_sharpe(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Anpassad Sharpe ratio med benchmark-justering."""
        excess_returns = returns - benchmark_returns
        mean_excess = excess_returns.mean()
        volatility = excess_returns.std()

        if volatility == 0:
            return float('inf') if mean_excess > 0 else float('-inf')

        return (mean_excess / volatility) * np.sqrt(365)  # Annualiserad

    def calculate_tail_risk(self, returns: pd.Series, tail_percentile: float = 0.05) -> float:
        """Beräkna tail risk (lägre värden = högre risk)."""
        tail_threshold = np.percentile(returns, tail_percentile * 100)
        tail_returns = returns[returns <= tail_threshold]

        if len(tail_returns) == 0:
            return 0.0

        # Conditional VaR för tail
        cvar = -tail_returns.mean()
        return cvar

    def calculate_risk_adjusted_momentum(self, returns: pd.Series, volatility_window: int = 20) -> float:
        """Risk-justerad momentum score."""
        # Beräkna momentum (trend styrka)
        momentum = returns.rolling(10).mean().iloc[-1]

        # Beräkna volatilitet
        volatility = returns.rolling(volatility_window).std().iloc[-1]

        if volatility == 0:
            return float('inf') if momentum > 0 else float('-inf')

        # Risk-justerad momentum
        return momentum / volatility

# Användning
custom_metrics = CustomRiskMetrics()

# Exempeldata
np.random.seed(42)
returns = pd.Series(np.random.normal(0.001, 0.02, 252))
benchmark = pd.Series(np.random.normal(0.0005, 0.015, 252))

print("🔧 Anpassade Riskmått:"    print(".4f"    print(".4f"    print(".4f"
```

---

*Dessa exempel visar olika sätt att använda Risk Management System. Alla exempel kan anpassas efter dina specifika behov och riskpreferenser.*