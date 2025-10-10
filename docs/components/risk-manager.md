# 🛡️ Risk Manager - Risk Monitoring & Controls

## Översikt

Risk Manager är kärnkomponenten för realtids risk monitoring och automatiska riskkontroller i Risk Management System. Modulen hanterar position-specifika riskgränser, trailing stops, daily loss limits och emergency stop mekanismer.

## 🎯 Funktioner

- **Stop-Loss/Take-Profit**: Automatiska gränser för positioner
- **Trailing Stops**: Dynamiska stop-loss nivåer som följer priset
- **Daily Loss Limits**: Dagliga förlustgränser för portföljen
- **Position Size Limits**: Begränsningar för enskilda positioners storlek
- **Emergency Stops**: Automatiska avvecklingsmekanismer
- **Real-time Monitoring**: Kontinuerlig riskbedömning
- **Alert System**: Konfigurerbara riskvarningar

## 💻 API Referens

### Klassdefinitioner

```python
@dataclass
class Position:
    """Represents a trading position with risk management parameters."""
    token: str
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: bool = False
    trailing_percentage: float = 0.05
    highest_price: Optional[float] = None
    max_drawdown: float = 0.0
    unrealized_pnl: float = 0.0

@dataclass
class RiskLimits:
    """Risk limits configuration."""
    max_daily_loss: float = 0.05        # 5% max daily loss
    max_single_position: float = 0.10   # 10% max single position
    max_portfolio_var: float = 0.15     # 15% max portfolio VaR
    max_correlation: float = 0.8        # Max correlation between positions
    max_concentration: float = 0.25     # Max concentration in single asset
```

```python
class RiskManager:
    """Risk management med stop-loss, take-profit och limit controls."""
```

### Konstruktor
```python
__init__(self, risk_limits: Optional[RiskLimits] = None)
```

**Parametrar:**
- `risk_limits`: Risk limits configuration (optional, uses defaults if None)

### Metoder

#### `add_position()`
```python
def add_position(self,
                token: str,
                entry_price: float,
                quantity: float,
                stop_loss_percentage: Optional[float] = None,
                take_profit_percentage: Optional[float] = None,
                trailing_stop: bool = False,
                trailing_percentage: float = 0.05) -> bool
```

**Lägger till position för risk monitoring.**

**Parametrar:**
- `token`: Asset token/symbol
- `entry_price`: Entry price för positionen
- `quantity`: Position quantity
- `stop_loss_percentage`: Stop loss som percentage från entry price
- `take_profit_percentage`: Take profit som percentage från entry price
- `trailing_stop`: Enable trailing stop functionality
- `trailing_percentage`: Trailing stop percentage

**Returnerar:** True om position tillagd framgångsrikt

---

#### `update_position_price()`
```python
def update_position_price(self, token: str, current_price: float) -> Dict[str, bool]
```

**Uppdaterar position med nya priser och checkar risk triggers.**

**Parametrar:**
- `token`: Asset token
- `current_price`: Current market price

**Returnerar:** Dictionary med aktiverade triggers:
```python
{
    'stop_loss': bool,      # True if stop loss triggered
    'take_profit': bool,    # True if take profit triggered
    'trailing_stop': bool   # True if trailing stop updated
}
```

---

#### `remove_position()`
```python
def remove_position(self, token: str, exit_price: Optional[float] = None) -> bool
```

**Tar bort position från risk monitoring.**

**Parametrar:**
- `token`: Asset token
- `exit_price`: Exit price (optional, för P&L beräkning)

**Returnerar:** True om position borttagen

---

#### `check_daily_risk_limits()`
```python
def check_daily_risk_limits() -> bool
```

**Checkar om dagliga riskgränser överskridits.**

**Returnerar:** True om gränser överskridna

---

#### `check_portfolio_concentration()`
```python
def check_portfolio_concentration() -> bool
```

**Checkar portföljkoncentration risk.**

**Returnerar:** True om koncentrationsgränser överskridna

---

#### `get_portfolio_value()`
```python
def get_portfolio_value() -> float
```

**Beräknar total portföljvärde baserat på entry prices.**

**Returnerar:** Total portföljvärde

---

#### `get_portfolio_risk_metrics()`
```python
def get_portfolio_risk_metrics() -> Dict[str, float]
```

**Beräknar portfölj risk metrics.**

**Returnerar:** Dictionary med risk metrics:
```python
{
    'portfolio_value': float,
    'unrealized_pnl': float,
    'pnl_percentage': float,
    'max_drawdown': float,
    'concentration_index': float,  # Herfindahl index
    'num_positions': int
}
```

---

#### `emergency_stop()`
```python
def emergency_stop(self, reason: str = "Manual emergency stop")
```

**Triggerar emergency stop för alla positioner.**

**Parametrar:**
- `reason`: Anledning till emergency stop

---

#### `reset_daily_pnl()`
```python
def reset_daily_pnl()
```

**Återställer daily P&L tracking.**

---

#### `get_alerts()`
```python
def get_alerts(self, clear: bool = False) -> List[Dict]
```

**Hämtar aktuella risk alerts.**

**Parametrar:**
- `clear`: Whether to clear alerts after retrieval

**Returnerar:** List of alert dictionaries

## 🧮 Risk Control Mekanismer

### Stop-Loss Implementation
```python
def _trigger_stop_loss(self, token: str, current_price: float):
    """Handle stop loss trigger."""
    position = self.positions[token]
    loss = (current_price - position.entry_price) * position.quantity

    # Log the event
    logger.warning(f"Stop loss triggered for {token} @ ${current_price}")

    # Record the loss
    self.daily_pnl_history.append(loss)

    # Create alert
    alert = {
        'timestamp': datetime.now(),
        'message': f'Stop loss triggered for {token}',
        'severity': 'warning',
        'details': {
            'token': token,
            'entry_price': position.entry_price,
            'exit_price': current_price,
            'loss': loss
        }
    }
    self.alerts.append(alert)

    # Remove position
    self.remove_position(token, current_price)

    # Notify external systems
    if self.on_stop_loss_triggered:
        self.on_stop_loss_triggered(token, current_price, loss)
```

### Trailing Stop Logic
```python
def _update_trailing_stop(self, token: str, current_price: float):
    """Update trailing stop if price moves favorably."""
    position = self.positions[token]

    if not position.trailing_stop:
        return False

    # Track highest price for trailing stop
    if position.highest_price is None or current_price > position.highest_price:
        position.highest_price = current_price

        # Calculate new trailing stop
        new_stop = position.highest_price * (1 - position.trailing_percentage)

        # Only update if new stop is higher than current stop
        if new_stop > position.stop_loss:
            position.stop_loss = new_stop
            return True

    return False
```

### Daily Loss Limit Monitoring
```python
def _check_daily_loss_limit(self) -> bool:
    """Check if daily loss limit has been exceeded."""
    if not self.daily_pnl_history:
        return False

    # Calculate total daily P&L
    daily_pnl = sum(self.daily_pnl_history)
    portfolio_value = self.get_portfolio_value()

    if portfolio_value <= 0:
        return False

    # Calculate loss percentage
    daily_loss_percentage = -daily_pnl / portfolio_value

    # Check against limit
    if daily_loss_percentage > self.risk_limits.max_daily_loss:
        # Create critical alert
        alert = {
            'timestamp': datetime.now(),
            'message': 'Daily loss limit exceeded',
            'severity': 'critical',
            'details': {
                'daily_loss': daily_loss_percentage,
                'limit': self.risk_limits.max_daily_loss,
                'total_pnl': daily_pnl
            }
        }
        self.alerts.append(alert)

        # Trigger emergency stop
        self.emergency_stop("Daily loss limit exceeded")
        return True

    return False
```

## 📊 Risk Metrics Beräkningar

### Concentration Risk
```python
def _calculate_concentration_risk(self, portfolio: Dict[str, float],
                                 prices: Dict[str, float],
                                 portfolio_value: float) -> float:
    """Calculate portfolio concentration risk using Herfindahl index."""
    if portfolio_value == 0:
        return 0.0

    position_values = [
        quantity * prices.get(token, 0)
        for token, quantity in portfolio.items()
    ]

    # Herfindahl-Hirschman Index (HHI)
    # HHI = Σ(w_i²) där w_i är positionens vikt i portföljen
    total_value = sum(position_values)
    concentration_index = sum((value / total_value) ** 2 for value in position_values)

    return concentration_index
```

### Drawdown Tracking
```python
def _update_drawdown_tracking(self, token: str, current_price: float):
    """Update drawdown tracking for position."""
    position = self.positions[token]

    # Track highest price for drawdown calculation
    if position.highest_price is None or current_price > position.highest_price:
        position.highest_price = current_price
        position.max_drawdown = 0.0
    else:
        # Calculate current drawdown
        drawdown = (position.highest_price - current_price) / position.highest_price

        # Update max drawdown
        position.max_drawdown = max(position.max_drawdown, drawdown)
```

### Portfolio Risk Aggregation
```python
def _aggregate_portfolio_risk(self) -> Dict[str, float]:
    """Aggregate risk across all positions."""
    if not self.positions:
        return {}

    total_unrealized_pnl = 0
    max_individual_drawdown = 0
    position_values = []

    for position in self.positions.values():
        # Calculate position value at entry price
        position_value = position.entry_price * position.quantity
        position_values.append(position_value)

        # Sum unrealized P&L
        total_unrealized_pnl += position.unrealized_pnl

        # Track maximum drawdown
        max_individual_drawdown = max(max_individual_drawdown, position.max_drawdown)

    portfolio_value = sum(position_values)

    # Calculate concentration index
    concentration_index = sum((v / portfolio_value) ** 2 for v in position_values)

    return {
        'portfolio_value': portfolio_value,
        'unrealized_pnl': total_unrealized_pnl,
        'pnl_percentage': total_unrealized_pnl / portfolio_value if portfolio_value > 0 else 0,
        'max_drawdown': max_individual_drawdown,
        'concentration_index': concentration_index,
        'num_positions': len(self.positions)
    }
```

## 🚨 Alert System

### Alert Severity Levels
```python
ALERT_LEVELS = {
    'info': {'level': 1, 'color': 'blue', 'action_required': False},
    'warning': {'level': 2, 'color': 'yellow', 'action_required': True},
    'critical': {'level': 3, 'color': 'red', 'action_required': True},
    'emergency': {'level': 4, 'color': 'red', 'action_required': True}
}
```

### Alert Types
```python
ALERT_TYPES = {
    'stop_loss_triggered': {
        'severity': 'warning',
        'message_template': 'Stop loss triggered for {token} at ${price}',
        'action': 'close_position'
    },
    'take_profit_triggered': {
        'severity': 'info',
        'message_template': 'Take profit triggered for {token} at ${price}',
        'action': 'close_position'
    },
    'daily_loss_limit_exceeded': {
        'severity': 'critical',
        'message_template': 'Daily loss limit exceeded: {loss:.1%} > {limit:.1%}',
        'action': 'emergency_stop'
    },
    'concentration_risk_high': {
        'severity': 'warning',
        'message_template': 'High concentration risk: {concentration:.1%}',
        'action': 'rebalance'
    },
    'position_size_limit_exceeded': {
        'severity': 'warning',
        'message_template': 'Position size limit exceeded for {token}',
        'action': 'reduce_position'
    }
}
```

### Alert Processing
```python
def _process_alert(self, alert_type: str, **kwargs) -> Dict:
    """Process and format risk alert."""
    if alert_type not in ALERT_TYPES:
        return None

    alert_config = ALERT_TYPES[alert_type]

    # Format message
    message = alert_config['message_template'].format(**kwargs)

    # Create alert
    alert = {
        'timestamp': datetime.now(),
        'type': alert_type,
        'message': message,
        'severity': alert_config['severity'],
        'action_required': alert_config['action'],
        'details': kwargs
    }

    # Add to alerts list
    self.alerts.append(alert)

    # Log alert
    log_level = {'info': 20, 'warning': 30, 'critical': 50, 'emergency': 50}
    logger.log(log_level.get(alert_config['severity'], 20), message)

    return alert
```

## 🔧 Konfiguration

### Standard Risk Limits
```python
DEFAULT_RISK_LIMITS = RiskLimits(
    max_daily_loss=0.05,        # 5% max daily loss
    max_single_position=0.10,   # 10% max single position
    max_portfolio_var=0.15,     # 15% max portfolio VaR
    max_correlation=0.8,        # Max correlation 80%
    max_concentration=0.25      # Max concentration 25%
)
```

### Risknivå-baserade Konfigurationer
```python
RISK_LEVEL_CONFIGS = {
    'conservative': RiskLimits(
        max_daily_loss=0.02,
        max_single_position=0.05,
        max_portfolio_var=0.08,
        max_correlation=0.7,
        max_concentration=0.15
    ),
    'moderate': RiskLimits(
        max_daily_loss=0.05,
        max_single_position=0.10,
        max_portfolio_var=0.15,
        max_correlation=0.8,
        max_concentration=0.25
    ),
    'aggressive': RiskLimits(
        max_daily_loss=0.08,
        max_single_position=0.20,
        max_portfolio_var=0.20,
        max_correlation=0.9,
        max_concentration=0.35
    )
}
```

### Stop-Loss Konfiguration
```python
STOP_LOSS_CONFIG = {
    'default_percentage': 0.05,     # 5% default stop loss
    'trailing_percentage': 0.03,    # 3% trailing stop
    'min_distance': 0.01,           # Minimum 1% stop distance
    'max_distance': 0.20,           # Maximum 20% stop distance
    'volatility_adjustment': True,  # Adjust based on volatility
    'time_based_expiry': False      # No time-based expiry by default
}
```

## 📈 Realtids Monitoring

### Monitoring Loop
```python
async def _risk_monitoring_loop(self):
    """Main risk monitoring loop."""
    while self.monitoring_active:
        try:
            # Check daily loss limits
            if self.check_daily_risk_limits():
                await self._handle_emergency_stop("Daily loss limit exceeded")

            # Check portfolio concentration
            if self.check_portfolio_concentration():
                await self._handle_risk_alert("High concentration risk detected")

            # Get any new alerts
            alerts = self.get_alerts(clear=True)
            for alert in alerts:
                await self._handle_risk_alert(alert['message'], alert)

            # Sleep before next check
            await asyncio.sleep(self.monitoring_interval)

        except Exception as e:
            logger.error(f"Error in risk monitoring loop: {e}")
            await asyncio.sleep(self.monitoring_interval)
```

### Price Update Processing
```python
def process_price_updates(self, price_updates: Dict[str, float]) -> Dict[str, List[Dict]]:
    """Process multiple price updates efficiently."""
    results = {
        'triggers_activated': [],
        'positions_updated': [],
        'alerts_generated': []
    }

    for token, current_price in price_updates.items():
        if token not in self.positions:
            continue

        # Update position price
        triggers = self.update_position_price(token, current_price)

        if any(triggers.values()):
            results['triggers_activated'].append({
                'token': token,
                'triggers': triggers,
                'price': current_price
            })

        results['positions_updated'].append({
            'token': token,
            'price': current_price,
            'updated': True
        })

    # Check for new alerts
    alerts = self.get_alerts(clear=True)
    results['alerts_generated'].extend(alerts)

    return results
```

## 🧪 Tester och Validering

### Unit Tests
```python
def test_stop_loss_trigger():
    """Test stop loss trigger functionality."""
    limits = RiskLimits(max_daily_loss=0.05, max_single_position=0.10)
    manager = RiskManager(limits)

    # Add position
    success = manager.add_position(
        token='BTC',
        entry_price=45000,
        quantity=1.0,
        stop_loss_percentage=0.05  # 5% stop loss
    )
    assert success

    # Update price to trigger stop loss (below 45000 * 0.95 = 42750)
    triggers = manager.update_position_price('BTC', 42000)

    assert triggers['stop_loss'] is True
    assert 'BTC' not in manager.positions  # Position should be removed

def test_daily_loss_limit():
    """Test daily loss limit monitoring."""
    limits = RiskLimits(max_daily_loss=0.05, max_single_position=0.10)
    manager = RiskManager(limits)

    # Simulate losses
    manager.daily_pnl_history = [-3000, -2000]  # Total -5000 loss
    manager.positions = {'BTC': Position('BTC', 45000, 1.0, datetime.now())}

    # Mock portfolio value
    original_get_portfolio_value = manager.get_portfolio_value
    manager.get_portfolio_value = lambda: 100000  # $100k portfolio

    # Check limits
    limit_exceeded = manager.check_daily_risk_limits()

    assert limit_exceeded is True  # 5% loss exceeds 5% limit

    # Restore original method
    manager.get_portfolio_value = original_get_portfolio_value

def test_concentration_risk():
    """Test concentration risk monitoring."""
    limits = RiskLimits(max_concentration=0.25)
    manager = RiskManager(limits)

    # Add high concentration position
    manager.add_position('BTC', 45000, 10.0)  # Very large position

    # Mock prices for concentration calculation
    portfolio = {'BTC': 10.0}
    prices = {'BTC': 45000}
    portfolio_value = 450000

    concentration = manager._calculate_concentration_risk(portfolio, prices, portfolio_value)

    assert concentration == 1.0  # 100% concentration in single asset
    assert concentration > limits.max_concentration
```

### Integration Tests
```python
def test_full_risk_workflow():
    """Test complete risk management workflow."""
    manager = RiskManager()

    # 1. Add positions with risk management
    manager.add_position('BTC', 45000, 1.0, stop_loss_percentage=0.05, trailing_stop=True)
    manager.add_position('ETH', 3000, 10.0, stop_loss_percentage=0.03, take_profit_percentage=0.10)

    # 2. Simulate price movements
    price_updates = {
        'BTC': 46500,  # +3.3% (trailing stop update)
        'ETH': 3300   # +10% (take profit trigger)
    }

    for token, price in price_updates.items():
        triggers = manager.update_position_price(token, price)
        print(f"{token}: {triggers}")

    # 3. Check remaining positions
    assert 'ETH' not in manager.positions  # Should be closed by take profit
    assert 'BTC' in manager.positions     # Should still be open

    # 4. Check alerts
    alerts = manager.get_alerts()
    assert len(alerts) >= 1  # Should have alerts for triggers

    print("✅ Full risk workflow test passed")
```

## 📚 Användningsexempel

### Grundläggande Risk Management
```python
from core.risk_manager import RiskManager, RiskLimits

# Skapa anpassade riskgränser
custom_limits = RiskLimits(
    max_daily_loss=0.03,        # 3% max daily loss
    max_single_position=0.08,   # 8% max single position
    max_portfolio_var=0.12,     # 12% max VaR
    max_concentration=0.20      # 20% max concentration
)

# Initiera risk manager
risk_manager = RiskManager(custom_limits)

# Lägg till position med riskkontroller
risk_manager.add_position(
    token='BTC',
    entry_price=45000,
    quantity=2.0,
    stop_loss_percentage=0.05,      # 5% stop loss
    take_profit_percentage=0.10,    # 10% take profit
    trailing_stop=True,             # Enable trailing stop
    trailing_percentage=0.03        # 3% trailing stop
)

# Monitor position
triggers = risk_manager.update_position_price('BTC', 46500)  # Price increase
print(f"Triggers activated: {triggers}")

# Check risk metrics
risk_metrics = risk_manager.get_portfolio_risk_metrics()
print(f"Portfolio metrics: {risk_metrics}")
```

### Avancerad Risk Monitoring
```python
import asyncio

async def advanced_risk_monitoring():
    """Advanced risk monitoring with alerts."""

    risk_manager = RiskManager()

    # Set up alert callbacks
    async def email_alert(message, details=None):
        print(f"📧 EMAIL ALERT: {message}")

    async def emergency_stop(reason):
        print(f"🚨 EMERGENCY STOP: {reason}")

    risk_manager.on_risk_alert = email_alert
    risk_manager.on_emergency_stop = emergency_stop

    # Add multiple positions
    positions = [
        ('BTC', 45000, 1.0),
        ('ETH', 3000, 5.0),
        ('ADA', 0.50, 10000)
    ]

    for token, price, qty in positions:
        risk_manager.add_position(
            token=token,
            entry_price=price,
            quantity=qty,
            stop_loss_percentage=0.05
        )

    # Simulate market volatility
    price_scenarios = [
        {'BTC': 42750, 'ETH': 2850, 'ADA': 0.475},  # Stop loss triggers
        {'BTC': 47250, 'ETH': 3300, 'ADA': 0.525},  # Take profit triggers
        {'BTC': 40500, 'ETH': 2700, 'ADA': 0.450}   # Emergency stop
    ]

    for scenario in price_scenarios:
        print(f"\n📊 Testing scenario: {scenario}")

        for token, price in scenario.items():
            triggers = risk_manager.update_position_price(token, price)
            if any(triggers.values()):
                print(f"  {token}: {triggers}")

        # Check risk limits
        if risk_manager.check_daily_risk_limits():
            print("  🚨 Daily loss limit exceeded!")
            break

        await asyncio.sleep(0.1)  # Simulate time delay

# Kör avancerat exempel
asyncio.run(advanced_risk_monitoring())
```

## 🔗 Integrationer

### Med Strategy Handler
```python
# Integration med Strategy Handler för automatisk risk setup
def integrate_with_strategy(strategy_config: Dict, risk_manager: RiskManager):
    """Integrate risk management with strategy configuration."""

    # Extract risk parameters from strategy
    risk_params = {
        'stop_loss': strategy_config.get('stop_loss', 0.05),
        'take_profit': strategy_config.get('take_profit', 0.10),
        'max_position': strategy_config.get('max_position', 0.10),
        'trailing_stop': strategy_config.get('trailing_stop', False)
    }

    # Apply to all positions in strategy
    for position in strategy_config.get('positions', []):
        risk_manager.add_position(
            token=position['token'],
            entry_price=position['entry_price'],
            quantity=position['quantity'],
            stop_loss_percentage=risk_params['stop_loss'],
            take_profit_percentage=risk_params['take_profit'],
            trailing_stop=risk_params['trailing_stop']
        )

    return risk_manager
```

### Med Alert System
```python
# Integration med externt alert system
def setup_external_alerts(risk_manager: RiskManager, alert_system):
    """Set up external alert system integration."""

    async def handle_risk_alert(message, details=None):
        """Handle risk alerts through external system."""
        alert_data = {
            'type': 'risk_management',
            'severity': details.get('severity', 'warning'),
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        # Send to external system
        await alert_system.send_alert(alert_data)

    async def handle_emergency_stop(reason):
        """Handle emergency stop through external system."""
        emergency_data = {
            'type': 'emergency_stop',
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'affected_positions': list(risk_manager.positions.keys())
        }

        # Trigger emergency protocols
        await alert_system.trigger_emergency(emergency_data)

    # Connect callbacks
    risk_manager.on_risk_alert = handle_risk_alert
    risk_manager.on_emergency_stop = handle_emergency_stop

    return risk_manager
```

## 📚 Referenser

1. **"Risk Management and Financial Institutions" - John C. Hull** - Risk management fundamentals
2. **"Active Portfolio Management" - Richard Grinold & Ronald Kahn** - Portfolio risk concepts
3. **"The Risk Management of Everything" - Michael Power** - Risk management principles
4. **"Value at Risk: The New Benchmark for Managing Financial Risk" - Philippe Jorion** - VaR implementation

---

*Risk Manager är hjärtat av realtids riskhantering, som säkerställer att positioner skyddas genom automatiska kontroller och övervakning.*