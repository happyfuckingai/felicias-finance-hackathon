# 🚀 Användarhandledning - Risk Management System

Denna guide visar hur du använder Risk Management System för praktisk riskhantering i dina kryptohandelsaktiviteter.

## 📋 Förutsättningar

### Installation
```bash
# Klona och navigera till projektet
cd /home/mr/friday_jarvis2

# Installera beroenden
cd crypto
pip install -r requirements.txt
pip install pyportfolioopt>=1.5.0
```

### Grundläggande Imports
```python
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime

# Risk Management komponenter
from handlers.risk import RiskHandler, RiskLimits
from core.var_calculator import VaRCalculator
from core.position_sizer import PositionSizer
from core.portfolio_risk import PortfolioRisk
```

## 🏁 Snabbstart

### 1. Grundläggande Riskbedömning

```python
async def basic_risk_assessment():
    """Grundläggande portfölj-riskbedömning."""

    # Skapa riskhanterare
    risk_handler = RiskHandler()

    # Definiera din portfölj
    portfolio = {
        'BTC': 0.5,   # 50% i Bitcoin
        'ETH': 0.3,   # 30% i Ethereum
        'USDC': 0.2   # 20% i stablecoin
    }

    # Nuvarande priser
    prices = {
        'BTC': 45000,
        'ETH': 3000,
        'USDC': 1.0
    }

    # Genomför riskbedömning
    assessment = await risk_handler.assess_portfolio_risk(portfolio, prices)

    # Visa resultat
    print("🛡️ PORTFÖLJ RISKANALYS"    print("=" * 40)
    print(".1%"    print(".2f"    print(".1%"    print(".1%"    print(".1%"    print(".1%"
    print(f"\n💡 Rekommendationer:")
    for rec in assessment.recommendations[:3]:
        print(f"• {rec}")

    return assessment

# Kör exemplet
assessment = await basic_risk_assessment()
```

### 2. Position Size Optimization

```python
async def optimize_position_size():
    """Optimera positionstorlek med olika metoder."""

    risk_handler = RiskHandler()

    # Parametrar för position
    token = 'BTC'
    entry_price = 45000
    portfolio_value = 100000  # $100,000 portfölj
    risk_tolerance = 0.02     # 2% risk per trade

    print("📏 POSITION SIZE OPTIMERING"    print("=" * 40)

    # Metod 1: Kelly Criterion
    kelly_result = await risk_handler.calculate_optimal_position_size(
        token=token,
        entry_price=entry_price,
        portfolio_value=portfolio_value,
        risk_tolerance=risk_tolerance,
        method='kelly',
        win_rate=0.65,           # 65% win rate
        avg_win_return=0.08,     # 8% average win
        avg_loss_return=-0.04    # 4% average loss
    )

    print("🎯 Kelly Criterion:"    print(".2f"    print(".2f"    print(".1%"
    # Metod 2: Fixed Fractional
    fixed_result = await risk_handler.calculate_optimal_position_size(
        token=token,
        entry_price=entry_price,
        portfolio_value=portfolio_value,
        risk_tolerance=risk_tolerance,
        method='fixed_fractional'
    )

    print("📊 Fixed Fractional:"    print(".2f"    print(".2f"    print(".1%"
    return kelly_result, fixed_result

# Kör exemplet
kelly_result, fixed_result = await optimize_position_size()
```

## 🛡️ Avancerade Riskstrategier

### 3. Risk-baserad Strategiskapning

```python
async def create_risk_aware_strategy():
    """Skapa strategi med automatisk riskbedömning."""

    from handlers.strategy import StrategyHandler

    # Skapa strategy handler (inkluderar nu risk management)
    strategy_handler = StrategyHandler()

    # Skapa strategi med riskparametrar
    fields = {
        'strategy_type': 'momentum',
        'risk_level': 'medium',
        'target_tokens': ['BTC', 'ETH'],
        'max_position_size': 0.15,
        'stop_loss': 0.08,
        'take_profit': 0.12
    }

    # Skapa strategi (riskbedömning sker automatiskt)
    result = await strategy_handler.handle({
        'action': 'create',
        'command': 'skapa momentum strategi med medium risk för btc och eth',
        'fields': fields,
        'user_id': 'demo_user'
    })

    print("🤖 STRATEGI SKAPAD MED RISK MANAGEMENT"    print("=" * 50)
    print(result['message'])

    # Visa riskbedömning
    if 'risk_assessment' in result:
        risk = result['risk_assessment']
        print("
🛡️ Riskbedömning:"        print(f"• Nivå: {risk.get('overall_risk_level', 'unknown').title()}")
        print(".1%"        print(".2f"
    return result

# Kör exemplet
strategy_result = await create_risk_aware_strategy()
```

### 4. Realtids Risk Monitoring

```python
async def real_time_risk_monitoring():
    """Sätt upp realtids risk monitoring."""

    risk_handler = RiskHandler()

    # Sätt upp positioner att monitorera
    positions = {
        'BTC': {'entry_price': 45000, 'quantity': 1.0},
        'ETH': {'entry_price': 3000, 'quantity': 10.0}
    }

    # Konfigurera risk management för varje position
    for token, position in positions.items():
        await risk_handler.setup_risk_management(
            token=token,
            entry_price=position['entry_price'],
            quantity=position['quantity'],
            stop_loss_percentage=0.05,      # 5% stop loss
            take_profit_percentage=0.10,    # 10% take profit
            trailing_stop=True              # Aktivera trailing stop
        )

    print("🔍 REAL-TIME RISK MONITORING STARTAD"    print("=" * 50)
    print("• Stop-loss: 5% från entry")
    print("• Take-profit: 10% från entry")
    print("• Trailing stop: Aktiverad")
    print("
📊 Positioner:"    for token, position in positions.items():
        value = position['entry_price'] * position['quantity']
        print(".2f"
    # Starta monitoring
    await risk_handler.start_risk_monitoring()

    # Simulera prisuppdateringar
    price_updates = {
        'BTC': 46500,  # +3.3% (ingen trigger)
        'ETH': 2850    # -5% (trigger stop loss)
    }

    print("
📈 Simulerade prisuppdateringar:"    triggers = await risk_handler.update_position_prices(price_updates)

    for token, trigger in triggers.items():
        if trigger.get('stop_loss'):
            print(f"🚨 {token}: STOP LOSS TRIGGERED!")
        elif trigger.get('take_profit'):
            print(f"🎯 {token}: TAKE PROFIT TRIGGERED!")
        else:
            print(f"✅ {token}: Inga triggers aktiverade")

    return risk_handler

# Kör exemplet
monitor = await real_time_risk_monitoring()
```

## 📊 Risk Analytics och Rapportering

### 5. Detaljerad Portföljanalys

```python
async def detailed_portfolio_analysis():
    """Genomför detaljerad portfölj-riskanalys."""

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
    risk_profile = await risk_handler.get_portfolio_risk_profile(portfolio, prices)

    print("📊 DETALJERAD PORTFÖLJANALYS"    print("=" * 50)

    print("💰 Portföljöversikt:"    print(".2f"    print(f"• Antal positioner: {risk_profile['num_positions']}")

    if risk_profile.get('risk_metrics'):
        metrics = risk_profile['risk_metrics']
        print("
📈 Riskmått:"        print(".2f"        print(".2f"        print(".1%"        print(".2f"        print(".2f"
    print("
🎯 Diversifiering:"    print(".3f"    print(f"• Uppdaterad: {risk_profile['last_updated']}")

    return risk_profile

# Kör exemplet
analysis = await detailed_portfolio_analysis()
```

### 6. Backtesting med Risk Management

```python
def backtest_with_risk_management():
    """Backtesta strategi med risk management."""

    from core.backtester import Backtester

    # Exempel historiska data
    dates = pd.date_range('2023-01-01', periods=365, freq='D')
    np.random.seed(42)

    # Generera syntetiska prisdata
    btc_prices = 45000 * np.exp(np.cumsum(np.random.normal(0.001, 0.03, 365)))
    eth_prices = 3000 * np.exp(np.cumsum(np.random.normal(0.0008, 0.04, 365)))

    historical_data = {
        'BTC': pd.DataFrame({'close': btc_prices}, index=dates),
        'ETH': pd.DataFrame({'close': eth_prices}, index=dates)
    }

    # Skapa riskhanterare för backtesting
    risk_handler = RiskHandler()

    # Simulera trading med riskkontroller
    capital = 100000
    position = 0
    trades = []

    for i in range(30, len(dates)):  # Starta efter 30 dagar
        current_prices = {
            'BTC': btc_prices[i],
            'ETH': eth_prices[i]
        }

        # Enkel momentum-signal
        btc_return = (btc_prices[i] - btc_prices[i-20]) / btc_prices[i-20]
        eth_return = (eth_prices[i] - eth_prices[i-20]) / eth_prices[i-20]

        if btc_return > 0.05 and position == 0:  # BTC momentum upp
            # Beräkna position size med risk management
            position_size = await risk_handler.calculate_optimal_position_size(
                token='BTC',
                entry_price=current_prices['BTC'],
                portfolio_value=capital,
                risk_tolerance=0.02,
                method='fixed_fractional'
            )

            if position_size['position_value'] <= capital:
                position = position_size['position_size']
                entry_price = current_prices['BTC']
                trades.append({
                    'type': 'BUY',
                    'token': 'BTC',
                    'price': entry_price,
                    'size': position,
                    'date': dates[i]
                })
                capital -= position_size['position_value']

        elif position > 0 and btc_return < -0.03:  # Exit signal
            exit_value = position * current_prices['BTC']
            pnl = exit_value - (position * entry_price)
            capital += exit_value

            trades.append({
                'type': 'SELL',
                'token': 'BTC',
                'price': current_prices['BTC'],
                'size': position,
                'pnl': pnl,
                'date': dates[i]
            })
            position = 0

    # Analysera resultat
    if trades:
        profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
        win_rate = len(profitable_trades) / len([t for t in trades if t['type'] == 'SELL'])

        print("📈 BACKTEST RESULTAT MED RISK MANAGEMENT"        print("=" * 50)
        print(f"• Total trades: {len([t for t in trades if t['type'] == 'SELL'])}")
        print(".1%"        print(f"• Final capital: ${capital:,.2f}")
        print(".2f"
    return trades

# Kör backtest
backtest_trades = backtest_with_risk_management()
```

## ⚙️ Anpassning och Konfiguration

### 7. Anpassade Risk Limits

```python
def custom_risk_configuration():
    """Konfigurera anpassade riskgränser."""

    from handlers.risk import RiskLimits

    # Konsekvativ konfiguration
    conservative_limits = RiskLimits(
        max_daily_loss=0.02,        # 2% max daily loss
        max_single_position=0.05,   # 5% max single position
        max_portfolio_var=0.08,     # 8% max VaR
        max_correlation=0.6,        # Strängare korrelationsgräns
        max_concentration=0.15      # 15% max concentration
    )

    # Aggressiv konfiguration
    aggressive_limits = RiskLimits(
        max_daily_loss=0.08,        # 8% max daily loss
        max_single_position=0.25,   # 25% max single position
        max_portfolio_var=0.20,     # 20% max VaR
        max_correlation=0.9,        # Högre korrelationsgräns
        max_concentration=0.35      # 35% max concentration
    )

    print("⚙️ RISK KONFIGURATIONER"    print("=" * 30)
    print("Konservativ:"    print(f"• Max daily loss: {conservative_limits.max_daily_loss:.1%}")
    print(f"• Max position: {conservative_limits.max_single_position:.1%}")
    print(f"• Max VaR: {conservative_limits.max_portfolio_var:.1%}")
    print("
Aggressiv:"    print(f"• Max daily loss: {aggressive_limits.max_daily_loss:.1%}")
    print(f"• Max position: {aggressive_limits.max_single_position:.1%}")
    print(f"• Max VaR: {aggressive_limits.max_portfolio_var:.1%}")

    return conservative_limits, aggressive_limits

# Kör konfiguration
conservative, aggressive = custom_risk_configuration()
```

### 8. Alert System Setup

```python
async def setup_risk_alerts():
    """Konfigurera risk alerts och notifikationer."""

    risk_handler = RiskHandler()

    # Definiera alert callbacks
    async def email_alert(message, details=None):
        """Skicka email alert."""
        print(f"📧 EMAIL ALERT: {message}")
        if details:
            print(f"   Details: {details}")

    async def slack_alert(message, details=None):
        """Skicka Slack alert."""
        print(f"💬 SLACK ALERT: {message}")
        if details:
            print(f"   Details: {details}")

    async def emergency_shutdown(message, details=None):
        """Emergency shutdown procedure."""
        print(f"🚨 EMERGENCY: {message}")
        print("   Initiating emergency shutdown...")
        # Implementera automatisk avveckling här

    # Registrera callbacks
    risk_handler.on_risk_alert = email_alert
    risk_handler.on_emergency_stop = emergency_shutdown

    print("🚨 RISK ALERT SYSTEM KONFIGURERAT"    print("=" * 40)
    print("• Email alerts: Aktiverad")
    print("• Slack alerts: Aktiverad")
    print("• Emergency shutdown: Aktiverad")

    # Testa alert system
    await risk_handler._handle_risk_alert(
        "Test alert: High VaR detected",
        {"var_value": 0.12, "threshold": 0.10}
    )

    return risk_handler

# Kör alert setup
alert_handler = await setup_risk_alerts()
```

## 📋 Troubleshooting

### Vanliga Problem och Lösningar

#### Problem: Import Errors
```python
# Lösning: Kontrollera Python path
import sys
sys.path.append('/path/to/crypto')

# Eller använd absoluta imports
from crypto.core.var_calculator import VaRCalculator
```

#### Problem: Async/Await Errors
```python
# Lösning: Använd asyncio.run() för main functions
import asyncio

async def main():
    risk_handler = RiskHandler()
    # ... din kod här

# Kör med:
asyncio.run(main())
```

#### Problem: Memory Issues med Monte Carlo
```python
# Lösning: Minska antalet simuleringar
var_mc = calculator.calculate_monte_carlo_var(
    returns, portfolio_value, simulations=1000  # Istället för 10000
)
```

#### Problem: Slow Performance
```python
# Lösning: Använd cache och optimeringar
import functools

@functools.lru_cache(maxsize=128)
def cached_var_calculation(returns_hash, method):
    # Cache expensive calculations
    pass
```

## 🎯 Bästa Practices

### 1. Risk Management Principles
- **Aldrig riskera mer än du har råd att förlora**
- **Diversifiera över olika tillgångar och strategier**
- **Använd stop-loss för alla positioner**
- **Regular risk assessments och rebalancing**
- **Backtesta strategier innan live trading**

### 2. Position Sizing Guidelines
- **Kelly Criterion**: Optimal för långsiktig tillväxt
- **Fixed Fractional**: Enkelt och konsistent
- **Risk Parity**: Balanserad riskfördelning
- **Volatility Adjustment**: Anpassa efter marknadsförhållanden

### 3. Monitoring Best Practices
- **Dagliga risk reviews**
- **Real-tids alerts för kritiska händelser**
- **Veckovis rebalancing**
- **Månatliga prestationsrapporter**

## 📞 Support och Resurser

### Hjälpmedel
- [API Reference](./api-reference.md) - Komplett API-dokumentation
- [Components](./components/) - Detaljerad komponentdokumentation
- [Examples](./examples/) - Ytterligare kodexempel

### Community och Support
- GitHub Issues för bug reports
- Dokumentation för själv-hjälp
- Community forum för diskussioner

---

*Denna användarhandledning ger praktiska exempel för att komma igång med Risk Management System. För mer avancerade användningsfall, se API-referensen och komponentdokumentationen.*