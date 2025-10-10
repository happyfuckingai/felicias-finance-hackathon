# 🎛️ Risk Handler - Risk Management API

## Översikt

Risk Handler är den centrala API-komponenten i Risk Management System som tillhandahåller ett enhetligt interface för alla riskrelaterade funktioner. Modulen koordinerar mellan kärnkomponenterna och tillhandahåller hög-nivå funktioner för portfölj-riskhantering.

## 🎯 Funktioner

- **Portfölj-riskbedömning**: Omfattande riskanalys av hela portföljer
- **Position Size Optimization**: Automatisk beräkning av optimala positionstorlekar
- **Risk Management Setup**: Enkelt setup av riskkontroller för positioner
- **Real-time Monitoring**: Kontinuerlig övervakning av riskmått
- **Alert System**: Konfigurerbara riskvarningar och notifikationer
- **Portfolio Analytics**: Detaljerad riskprofil och prestationsanalys
- **Integration Layer**: Enkelt interface mot andra systemkomponenter

## 💻 API Referens

### Klassdefinition

```python
class RiskHandler:
    """Huvud-API för risk management system."""
```

#### Konstruktor
```python
__init__(self,
         risk_limits: Optional[RiskLimits] = None,
         confidence_level: float = 0.95,
         risk_free_rate: float = 0.02)
```

**Parametrar:**
- `risk_limits`: Risk limits configuration (optional)
- `confidence_level`: VaR confidence level (default: 0.95)
- `risk_free_rate`: Risk-free rate för calculations (default: 0.02)

### Metoder

#### `assess_portfolio_risk()`
```python
async def assess_portfolio_risk(self,
                               portfolio: Dict[str, float],
                               current_prices: Dict[str, float],
                               historical_data: Optional[Dict[str, pd.DataFrame]] = None) -> RiskAssessment
```

**Genomför omfattande portfölj-riskbedömning.**

**Parametrar:**
- `portfolio`: Current portfolio positions {token: quantity}
- `current_prices`: Current asset prices {token: price}
- `historical_data`: Historical price data för risk calculations (optional)

**Returnerar:** RiskAssessment dataclass med komplett riskanalys

**Exempel:**
```python
assessment = await risk_handler.assess_portfolio_risk(
    portfolio={'BTC': 0.5, 'ETH': 0.3, 'USDC': 0.2},
    current_prices={'BTC': 45000, 'ETH': 3000, 'USDC': 1.0}
)

print(f"Risk Level: {assessment.overall_risk_level}")
print(f"VaR 95%: ${assessment.var_95:,.2f}")
```

---

#### `calculate_optimal_position_size()`
```python
async def calculate_optimal_position_size(self,
                                        token: str,
                                        entry_price: float,
                                        portfolio_value: float,
                                        risk_tolerance: float = 0.02,
                                        method: str = 'kelly',
                                        **kwargs) -> Dict[str, Any]
```

**Beräknar optimal position size med olika metoder.**

**Parametrar:**
- `token`: Asset token
- `entry_price`: Expected entry price
- `portfolio_value`: Current portfolio value
- `risk_tolerance`: Maximum risk per trade (default: 0.02)
- `method`: Sizing method ('kelly', 'fixed_fractional', 'risk_parity')
- `**kwargs`: Additional method-specific parameters

**Returnerar:** Dictionary med sizing results och rekommendationer

**Exempel:**
```python
# Kelly Criterion med anpassade parametrar
kelly_result = await risk_handler.calculate_optimal_position_size(
    token='BTC',
    entry_price=45000,
    portfolio_value=100000,
    method='kelly',
    win_rate=0.65,
    avg_win_return=0.08,
    avg_loss_return=-0.04
)

print(f"Optimal Position: {kelly_result['position_size']:.1%}")
print(f"Position Value: ${kelly_result['position_value']:,.2f}")
```

---

#### `setup_risk_management()`
```python
async def setup_risk_management(self,
                               token: str,
                               entry_price: float,
                               quantity: float,
                               stop_loss_percentage: float = 0.05,
                               take_profit_percentage: float = 0.10,
                               trailing_stop: bool = False) -> bool
```

**Sätter upp risk management för en position.**

**Parametrar:**
- `token`: Asset token
- `entry_price`: Entry price
- `quantity`: Position quantity
- `stop_loss_percentage`: Stop loss som percentage (default: 0.05)
- `take_profit_percentage`: Take profit som percentage (default: 0.10)
- `trailing_stop`: Enable trailing stop (default: False)

**Returnerar:** True om setup lyckades

**Exempel:**
```python
success = await risk_handler.setup_risk_management(
    token='ETH',
    entry_price=3000,
    quantity=10,
    stop_loss_percentage=0.03,
    take_profit_percentage=0.08,
    trailing_stop=True
)

if success:
    print("✅ Risk management setup complete")
```

---

#### `update_position_prices()`
```python
async def update_position_prices(self,
                               price_updates: Dict[str, float]) -> Dict[str, Dict[str, bool]]
```

**Uppdaterar positioner med nya priser och checkar triggers.**

**Parametrar:**
- `price_updates`: {token: current_price}

**Returnerar:** Dictionary med aktiverade triggers per position

**Exempel:**
```python
# Uppdatera flera positioner samtidigt
updates = {
    'BTC': 46500,  # +3.3%
    'ETH': 2940    # -2%
}

triggers = await risk_handler.update_position_prices(updates)

for token, trigger in triggers.items():
    if trigger.get('stop_loss'):
        print(f"🚨 {token}: STOP LOSS TRIGGERED!")
    if trigger.get('take_profit'):
        print(f"🎯 {token}: TAKE PROFIT TRIGGERED!")
```

---

#### `get_portfolio_risk_profile()`
```python
async def get_portfolio_risk_profile(self,
                                    portfolio: Dict[str, float],
                                    historical_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]
```

**Hämtar detaljerad portfölj-riskprofil.**

**Parametrar:**
- `portfolio`: Current portfolio positions
- `historical_data`: Historical price data (optional)

**Returnerar:** Comprehensive risk profile dictionary

**Exempel:**
```python
profile = await risk_handler.get_portfolio_risk_profile(
    portfolio={'BTC': 0.4, 'ETH': 0.4, 'ADA': 0.2}
)

print(f"Portfolio Value: ${profile['portfolio_value']:,.2f}")
print(f"Risk Metrics: {profile['risk_metrics']}")
print(f"Diversification Score: {profile['diversification_score']:.2f}")
```

---

#### `start_risk_monitoring()`
```python
async def start_risk_monitoring(self)
```

**Startar kontinuerlig risk monitoring.**

**Exempel:**
```python
await risk_handler.start_risk_monitoring()
print("🔍 Risk monitoring started")
```

---

#### `stop_risk_monitoring()`
```python
async def stop_risk_monitoring()
```

**Stoppar risk monitoring.**

---

#### `get_alerts()`
```python
def get_alerts(self, clear: bool = False) -> List[Dict]
```

**Hämtar aktuella risk alerts.**

**Parametrar:**
- `clear`: Whether to clear alerts after retrieval

**Returnerar:** List of alert dictionaries

## 🧮 Användningsexempel

### 1. Grundläggande Riskbedömning

```python
from handlers.risk import RiskHandler
import asyncio

async def basic_risk_assessment():
    """Grundläggande portfölj-riskbedömning."""

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

    print("🛡️ PORTFÖLJ RISKANALYS"    print("=" * 50)
    print(f"📊 Övergripande Risknivå: {assessment.overall_risk_level.upper()}")
    print(f"💰 VaR (95%): ${assessment.var_95:,.2f}")
    print(f"📈 Expected Shortfall: ${assessment.expected_shortfall:,.2f}")
    print(f"⭐ Sharpe Ratio: {assessment.sharpe_ratio:.2f}")
    print(f"📉 Max Drawdown: {assessment.max_drawdown:.1%}")
    print(f"📊 Koncentrationsrisk: {assessment.concentration_risk:.1%}")

    if assessment.recommendations:
        print("\n💡 Rekommendationer:"        for rec in assessment.recommendations:
            print(f"• {rec}")

    return assessment

# Kör exemplet
assessment = asyncio.run(basic_risk_assessment())
```

### 2. Position Size Optimization

```python
async def optimize_positions():
    """Optimera positionstorlekar med olika metoder."""

    risk_handler = RiskHandler()

    print("📏 POSITION SIZE OPTIMERING"    print("=" * 40)

    # Kelly Criterion
    kelly_result = await risk_handler.calculate_optimal_position_size(
        token='BTC',
        entry_price=45000,
        portfolio_value=100000,
        method='kelly',
        win_rate=0.65,
        avg_win_return=0.08,
        avg_loss_return=-0.04
    )

    print("🎯 Kelly Criterion:"    print(f"• Rekommenderad size: {kelly_result['position_size']:.1%}")
    print(f"• Positionvärde: ${kelly_result['position_value']:,.2f}")

    # Fixed Fractional
    fixed_result = await risk_handler.calculate_optimal_position_size(
        token='ETH',
        entry_price=3000,
        portfolio_value=100000,
        method='fixed_fractional',
        risk_per_trade=0.015  # 1.5% risk per trade
    )

    print("
📊 Fixed Fractional:"    print(f"• Rekommenderad size: {fixed_result['position_size']:.1%}")
    print(f"• Positionvärde: ${fixed_result['position_value']:,.2f}")

# Kör exemplet
asyncio.run(optimize_positions())
```

### 3. Risk-aware Trading Setup

```python
async def setup_trading_with_risk():
    """Sätt upp trading med automatiska riskkontroller."""

    risk_handler = RiskHandler()

    # Trading setup för flera tillgångar
    trading_setup = {
        'BTC': {
            'entry_price': 45000,
            'quantity': 1.0,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.10,
            'trailing_stop': True
        },
        'ETH': {
            'entry_price': 3000,
            'quantity': 5.0,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.08,
            'trailing_stop': False
        }
    }

    print("🚀 TRADING SETUP MED RISK MANAGEMENT"    print("=" * 50)

    for token, config in trading_setup.items():
        success = await risk_handler.setup_risk_management(
            token=token,
            entry_price=config['entry_price'],
            quantity=config['quantity'],
            stop_loss_percentage=config['stop_loss_pct'],
            take_profit_percentage=config['take_profit_pct'],
            trailing_stop=config['trailing_stop']
        )

        if success:
            position_value = config['entry_price'] * config['quantity']
            stop_loss_price = config['entry_price'] * (1 - config['stop_loss_pct'])
            take_profit_price = config['entry_price'] * (1 + config['take_profit_pct'])

            print(f"✅ {token}: Positionvärde ${position_value:,.2f}")
            print(f"   Stop Loss: ${stop_loss_price:,.2f}")
            print(f"   Take Profit: ${take_profit_price:,.2f}")
            print(f"   Trailing Stop: {'Aktiverad' if config['trailing_stop'] else 'Inaktiverad'}")
        else:
            print(f"❌ {token}: Setup misslyckades")

        print()

    # Starta risk monitoring
    await risk_handler.start_risk_monitoring()
    print("🔍 Risk monitoring aktiverat - alla positioner övervakas")

# Kör exemplet
asyncio.run(setup_trading_with_risk())
```

### 4. Real-time Risk Monitoring

```python
async def real_time_monitoring_demo():
    """Demonstration av real-tids risk monitoring."""

    risk_handler = RiskHandler()

    # Simulera marknadsdata stream
    market_data_stream = [
        {'BTC': 45250, 'ETH': 2985},  # Små rörelser
        {'BTC': 46800, 'ETH': 2940},  # BTC upp, ETH ner
        {'BTC': 42750, 'ETH': 2910},  # BTC stop loss trigger
        {'BTC': 46500, 'ETH': 3300},  # ETH take profit trigger
    ]

    print("📈 REAL-TIME RISK MONITORING DEMO"    print("=" * 50)

    for i, price_update in enumerate(market_data_stream, 1):
        print(f"\n📊 Uppdatering {i}: {price_update}")

        # Uppdatera positioner och checka triggers
        triggers = await risk_handler.update_position_prices(price_update)

        # Visa aktiverade triggers
        for token, trigger_status in triggers.items():
            trigger_messages = []
            if trigger_status.get('stop_loss'):
                trigger_messages.append("🚨 STOP LOSS")
            if trigger_status.get('take_profit'):
                trigger_messages.append("🎯 TAKE PROFIT")
            if trigger_status.get('trailing_stop'):
                trigger_messages.append("🔄 TRAILING STOP")

            if trigger_messages:
                print(f"   {token}: {' | '.join(trigger_messages)}")
            else:
                print(f"   {token}: ✅ Inga triggers")

        # Visa alerts
        alerts = risk_handler.get_alerts(clear=True)
        if alerts:
            print("   📢 Alerts:"            for alert in alerts:
                print(f"      • {alert['message']}")

        # Kort paus för att simulera realtid
        await asyncio.sleep(0.5)

    print("
🏁 Demo komplett!"# Kör exemplet
asyncio.run(real_time_monitoring_demo())
```

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

    # Simulera historiska data för analys
    import numpy as np
    import pandas as pd

    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252, freq='D')

    # Generera historiska priser
    historical_prices = {
        'BTC': 45000 * np.exp(np.cumsum(np.random.normal(0.0005, 0.025, 252))),
        'ETH': 3000 * np.exp(np.cumsum(np.random.normal(0.0003, 0.035, 252))),
        'ADA': 0.50 * np.exp(np.cumsum(np.random.normal(0.0008, 0.045, 252))),
        'DOT': 8.50 * np.exp(np.cumsum(np.random.normal(0.0006, 0.04, 252)))
    }

    historical_data = {}
    for token, prices in historical_prices.items():
        historical_data[token] = pd.DataFrame({
            'close': prices,
            'high': prices * (1 + np.random.normal(0, 0.02, 252)),
            'low': prices * (1 - np.random.normal(0, 0.02, 252)),
            'volume': np.random.normal(1000000, 500000, 252)
        }, index=dates)

    # Nuvarande priser (senaste från historiska data)
    current_prices = {token: prices[-1] for token, prices in historical_prices.items()}

    print("📊 DETALJERAD PORTFÖLJANALYS"    print("=" * 50)

    # Hämta riskprofil
    profile = await risk_handler.get_portfolio_risk_profile(portfolio, historical_data)

    print("💰 Portföljöversikt:"    print(f"• Totalvärde: ${profile['portfolio_value']:,.2f}")
    print(f"• Antal positioner: {profile['num_positions']}")

    if profile.get('risk_metrics'):
        metrics = profile['risk_metrics']
        print("
📈 Riskmått:"        print(f"• Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A'):.2f}")
        print(f"• Sortino Ratio: {metrics.get('sortino_ratio', 'N/A'):.2f}")
        print(f"• Max Drawdown: {metrics.get('max_drawdown', 0):.1%}")
        print(f"• Volatilitet: {metrics.get('volatility', 0):.1%}")
        print(f"• Beta: {metrics.get('beta', 'N/A'):.2f}")
        print(f"• VaR (95%): ${metrics.get('value_at_risk', 0):.2f}")

    print("
🎯 Diversifiering:"    print(f"• Diversifieringspoäng: {profile.get('diversification_score', 0):.2f}")

    # Position-specifika analyser
    if profile.get('position_profiles'):
        print("
📊 Positionprofiler:"        for pos_profile in profile['position_profiles']:
            print(f"• {pos_profile['token']}:")
            print(".1%"            print(".2f"            print(".2f"            print(".1%")

    return profile

# Kör exemplet
analysis = asyncio.run(detailed_portfolio_analysis())
```

## ⚙️ Konfiguration och Anpassning

### Risk Limits Setup
```python
from handlers.risk import RiskLimits

# Anpassade riskgränser
custom_limits = RiskLimits(
    max_daily_loss=0.03,        # 3% max daily loss
    max_single_position=0.08,   # 8% max single position
    max_portfolio_var=0.12,     # 12% max VaR
    max_correlation=0.7,        # Max correlation 70%
    max_concentration=0.20      # Max concentration 20%
)

# Skapa risk handler med anpassade limits
risk_handler = RiskHandler(risk_limits=custom_limits)
```

### Alert System Configuration
```python
# Sätt upp anpassade alert callbacks
async def email_alert_handler(message, details=None):
    """Email alert handler."""
    print(f"📧 EMAIL ALERT: {message}")
    if details:
        print(f"   Details: {details}")

async def emergency_stop_handler(reason):
    """Emergency stop handler."""
    print(f"🚨 EMERGENCY STOP: {reason}")
    print("   Executing emergency protocols...")

# Registrera callbacks
risk_handler.on_risk_alert = email_alert_handler
risk_handler.on_emergency_stop = emergency_stop_handler
```

### Monitoring Configuration
```python
# Anpassa monitoring intervall
risk_handler.monitoring_interval = 30  # 30 sekunders intervall

# Starta monitoring
await risk_handler.start_risk_monitoring()
```

## 🔧 Avancerade Funktioner

### Batch Operations
```python
async def batch_risk_operations():
    """Utför batch-operationer för effektivitet."""

    risk_handler = RiskHandler()

    # Batch position setup
    positions_data = [
        ('BTC', 45000, 1.0, 0.05, 0.10, True),
        ('ETH', 3000, 5.0, 0.03, 0.08, False),
        ('ADA', 0.50, 1000, 0.04, 0.12, True)
    ]

    print("🔄 BATCH POSITION SETUP"    print("=" * 40)

    for token, price, qty, sl, tp, ts in positions_data:
        success = await risk_handler.setup_risk_management(
            token=token,
            entry_price=price,
            quantity=qty,
            stop_loss_percentage=sl,
            take_profit_percentage=tp,
            trailing_stop=ts
        )
        status = "✅" if success else "❌"
        print(f"{status} {token}: ${price * qty:,.2f}")

    # Batch price updates
    price_updates = {
        'BTC': 46750,
        'ETH': 2940,
        'ADA': 0.48
    }

    print("
📈 BATCH PRICE UPDATES"    print("=" * 40)

    triggers = await risk_handler.update_position_prices(price_updates)

    for token, trigger in triggers.items():
        if any(trigger.values()):
            print(f"🚨 {token}: Triggers activated - {trigger}")
        else:
            print(f"✅ {token}: No triggers")

# Kör exemplet
asyncio.run(batch_risk_operations())
```

### Custom Risk Assessment
```python
async def custom_risk_assessment():
    """Anpassad riskbedömning med ytterligare metrics."""

    risk_handler = RiskHandler()

    # Standardbedömning först
    portfolio = {'BTC': 0.5, 'ETH': 0.5}
    prices = {'BTC': 45000, 'ETH': 3000}

    assessment = await risk_handler.assess_portfolio_risk(portfolio, prices)

    print("🎯 CUSTOM RISK ASSESSMENT"    print("=" * 50)

    # Utöka med anpassade metrics
    custom_metrics = {
        'portfolio_beta_adjusted': assessment.beta * assessment.volatility,
        'risk_adjusted_return': assessment.sharpe_ratio * (1 - assessment.max_drawdown),
        'tail_risk_score': assessment.expected_shortfall / assessment.var_95,
        'concentration_penalty': assessment.concentration_risk * 1.5
    }

    print("📊 Standard Metrics:"    print(f"• Risk Level: {assessment.overall_risk_level}")
    print(f"• Sharpe Ratio: {assessment.sharpe_ratio:.2f}")
    print(f"• Max Drawdown: {assessment.max_drawdown:.1%}")

    print("
🧮 Custom Metrics:"    print(f"• Beta-Adjusted Risk: {custom_metrics['portfolio_beta_adjusted']:.2f}")
    print(f"• Risk-Adjusted Return: {custom_metrics['risk_adjusted_return']:.2f}")
    print(f"• Tail Risk Score: {custom_metrics['tail_risk_score']:.2f}")
    print(f"• Concentration Penalty: {custom_metrics['concentration_penalty']:.1%}")

    # Anpassad riskbedömning
    if custom_metrics['risk_adjusted_return'] > 1.0:
        custom_risk_level = 'LOW'
    elif custom_metrics['risk_adjusted_return'] > 0.5:
        custom_risk_level = 'MEDIUM'
    else:
        custom_risk_level = 'HIGH'

    print(f"\n🎖️ Custom Risk Level: {custom_risk_level}")

    return assessment, custom_metrics

# Kör exemplet
assessment, custom = asyncio.run(custom_risk_assessment())
```

## 🧪 Tester och Validering

### Unit Tests
```python
import pytest
from handlers.risk import RiskHandler, RiskLimits

def test_risk_handler_initialization():
    """Test Risk Handler initialization."""
    handler = RiskHandler()

    assert handler.confidence_level == 0.95
    assert handler.risk_free_rate == 0.02
    assert handler.risk_handler is not None

def test_custom_limits():
    """Test custom risk limits."""
    custom_limits = RiskLimits(
        max_daily_loss=0.03,
        max_single_position=0.08
    )

    handler = RiskHandler(risk_limits=custom_limits)

    assert handler.risk_handler.risk_limits.max_daily_loss == 0.03
    assert handler.risk_handler.risk_limits.max_single_position == 0.08

@pytest.mark.asyncio
async def test_portfolio_assessment():
    """Test portfolio risk assessment."""
    handler = RiskHandler()

    portfolio = {'BTC': 0.5, 'ETH': 0.5}
    prices = {'BTC': 45000, 'ETH': 3000}

    assessment = await handler.assess_portfolio_risk(portfolio, prices)

    assert hasattr(assessment, 'overall_risk_level')
    assert hasattr(assessment, 'var_95')
    assert hasattr(assessment, 'sharpe_ratio')
    assert assessment.overall_risk_level in ['low', 'medium', 'high', 'critical']
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete risk management workflow."""
    handler = RiskHandler()

    # 1. Setup positions
    success = await handler.setup_risk_management(
        token='BTC',
        entry_price=45000,
        quantity=1.0,
        stop_loss_percentage=0.05
    )
    assert success

    # 2. Update prices
    triggers = await handler.update_position_prices({'BTC': 42750})  # Trigger stop loss

    # 3. Check triggers
    assert triggers['BTC']['stop_loss'] is True

    # 4. Get alerts
    alerts = handler.get_alerts()
    assert len(alerts) > 0

    # 5. Risk assessment
    portfolio = {'BTC': 1.0}
    prices = {'BTC': 42750}
    assessment = await handler.assess_portfolio_risk(portfolio, prices)

    assert assessment is not None
```

## 📚 Error Handling

### Exception Types
```python
class RiskManagementError(Exception):
    """Base exception för risk management."""
    pass

class InvalidPortfolioError(RiskManagementError):
    """Exception för ogiltiga portföljer."""
    pass

class RiskCalculationError(RiskManagementError):
    """Exception för riskberäkningsfel."""
    pass

class InvalidParametersError(RiskManagementError):
    """Exception för ogiltiga parametrar."""
    pass
```

### Robust Error Handling
```python
async def robust_risk_operation():
    """Robust felhantering för riskoperationer."""

    risk_handler = RiskHandler()

    try:
        # Försök riskbedömning
        assessment = await risk_handler.assess_portfolio_risk(
            portfolio={'BTC': 0.5, 'ETH': 0.5},
            current_prices={'BTC': 45000, 'ETH': 3000}
        )

        return assessment

    except InvalidPortfolioError as e:
        print(f"❌ Ogiltig portfölj: {e}")
        return None

    except RiskCalculationError as e:
        print(f"❌ Riskberäkningsfel: {e}")
        # Fallback till förenklad beräkning
        return await fallback_risk_assessment()

    except Exception as e:
        print(f"❌ Oväntat fel: {e}")
        return None

async def fallback_risk_assessment():
    """Fallback riskbedömning vid fel."""
    return {
        'overall_risk_level': 'unknown',
        'var_95': 0.10,  # Konservativ uppskattning
        'recommendations': ['Manual review required']
    }
```

## 🔗 Integration Points

### Med Strategy Handler
```python
# Automatisk risk integration i strategier
from handlers.strategy import StrategyHandler

async def integrated_strategy_example():
    """Exempel på integrerad strategi med risk management."""

    strategy_handler = StrategyHandler()

    # Skapa strategi (risk management inkluderas automatiskt)
    result = await strategy_handler.handle({
        'action': 'create',
        'command': 'skapa momentum strategi med medium risk',
        'fields': {},
        'user_id': 'demo_user'
    })

    print("🤖 STRATEGI MED RISK INTEGRATION"    print("=" * 50)
    print(result['message'])

    # Riskbedömningen görs automatiskt
    if 'risk_assessment' in result:
        risk = result['risk_assessment']
        print(f"🛡️ Automatisk riskbedömning: {risk.get('overall_risk_level', 'N/A')}")

    return result
```

### Med External Systems
```python
# Integration med externa system
class RiskManagementBridge:
    """Bridge för integration med externa system."""

    def __init__(self, risk_handler: RiskHandler):
        self.risk_handler = risk_handler

    async def sync_portfolio(self, external_portfolio: dict):
        """Synkronisera portfölj från externt system."""

        # Konvertera externt format till internt
        internal_portfolio = self._convert_portfolio_format(external_portfolio)

        # Genomför riskbedömning
        assessment = await self.risk_handler.assess_portfolio_risk(
            internal_portfolio['positions'],
            internal_portfolio['prices']
        )

        # Rapportera tillbaka till externt system
        return {
            'risk_level': assessment.overall_risk_level,
            'var_95': assessment.var_95,
            'recommendations': assessment.recommendations
        }

    def _convert_portfolio_format(self, external_portfolio: dict) -> dict:
        """Konvertera externt portföljformat."""
        # Implementation för formatkonvertering
        pass
```

## 📊 Prestandaoptimering

### Async Operations
```python
# Alla operationer är async för bättre prestanda
import asyncio

async def concurrent_risk_assessments():
    """Utför flera riskbedömningar samtidigt."""

    risk_handler = RiskHandler()

    portfolios = [
        {'BTC': 0.6, 'ETH': 0.4},
        {'BTC': 0.4, 'ETH': 0.4, 'ADA': 0.2},
        {'ETH': 0.7, 'DOT': 0.3}
    ]

    prices = {'BTC': 45000, 'ETH': 3000, 'ADA': 0.50, 'DOT': 8.50}

    # Utför alla bedömningar samtidigt
    tasks = [
        risk_handler.assess_portfolio_risk(portfolio, prices)
        for portfolio in portfolios
    ]

    assessments = await asyncio.gather(*tasks)

    for i, assessment in enumerate(assessments, 1):
        print(f"Portfolio {i}: {assessment.overall_risk_level}")

    return assessments
```

### Caching Strategies
```python
from functools import lru_cache
import hashlib

class CachedRiskHandler(RiskHandler):
    """Risk Handler med caching för förbättrad prestanda."""

    @lru_cache(maxsize=100)
    def _cached_assessment(self, portfolio_hash: str, prices_hash: str) -> str:
        """Cache riskbedömningar."""
        # Implementation för cache
        pass

    async def assess_portfolio_risk(self, portfolio: Dict[str, float],
                                   current_prices: Dict[str, float],
                                   historical_data=None):
        """Cached version av riskbedömning."""

        # Skapa hash för cache-nycklar
        portfolio_str = str(sorted(portfolio.items()))
        prices_str = str(sorted(current_prices.items()))

        portfolio_hash = hashlib.md5(portfolio_str.encode()).hexdigest()
        prices_hash = hashlib.md5(prices_str.encode()).hexdigest()

        # Check cache först
        cached_result = self._cached_assessment(portfolio_hash, prices_hash)
        if cached_result:
            return cached_result

        # Utför normal bedömning
        result = await super().assess_portfolio_risk(
            portfolio, current_prices, historical_data
        )

        # Cache resultatet
        self._cached_assessment.cache[portfolio_hash + prices_hash] = result

        return result
```

## 📚 Referenser

1. **"Risk Management in Trading" - Davis Edwards** - Trading risk management
2. **"The Risk Management Handbook" - Philippe Carrel** - Comprehensive risk management
3. **"Algorithmic Trading" - Ernest P. Chan** - Quantitative trading approaches
4. **"Python for Data Analysis" - Wes McKinney** - Technical implementation
5. **"Asyncio and Concurrent Programming"** - Python documentation

---

*Risk Handler är den centrala API:n som förenar alla risk management komponenter till ett sammanhängande system för professionell portföljhantering.*