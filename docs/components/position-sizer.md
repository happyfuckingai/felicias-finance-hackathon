# 📏 Position Sizer - Position Sizing Algoritmer

## Översikt

Position Sizer är kärnkomponenten för optimal position sizing i Risk Management System. Modulen tillhandahåller flera olika algoritmer för att beräkna optimala positionstorlekar baserat på risktolerans och marknadsförhållanden.

## 🎯 Funktioner

- **Kelly Criterion**: Optimal sizing baserat på sannolikhet för vinst/förlust
- **Fixed Fractional**: Risk-baserad sizing som fast andel av portföljvärde
- **Risk Parity**: Jämn riskfördelning mellan tillgångar
- **Minimum Variance**: Minimerar portföljvolatilitet
- **Maximum Sharpe**: Maximerar riskjusterad avkastning
- **Volatility Adjustment**: Volatilitetsjusterad position sizing

## 📈 Matematiska Grundformler

### Kelly Criterion
```
f = (b × p - q) / b
```
Där:
- `f` = Fraction av kapital att satsa
- `b` = Win/loss ratio = |Avg Win| / |Avg Loss|
- `p` = Sannolikhet för vinst
- `q` = Sannolikhet för förlust (1 - p)

**Konservativ Kelly**: Använd hälften av Kelly-värdet för att reducera risken.

### Fixed Fractional
```
Position Size = Risk per Trade × Portfolio Value
```

Eller med volatilitetsjustering:
```
Position Size = (Risk per Trade / Volatility) × Portfolio Value
```

### Risk Parity
```
w_i = 1 / σ_i
w = w / Σw_i  (normaliserad)
```
Där:
- `w_i` = Vikt för tillgång i
- `σ_i` = Volatilitet för tillgång i

## 💻 API Referens

### Klassdefinition

```python
class PositionSizer:
    """Position sizing algoritmer för riskjusterad trading."""
```

#### Konstruktor
```python
__init__(self,
         max_portfolio_risk: float = 0.02,
         max_single_position: float = 0.10,
         risk_free_rate: float = 0.02)
```

**Parametrar:**
- `max_portfolio_risk` (float): Maximum risk per trade som fraction (default: 0.02)
- `max_single_position` (float): Maximum single position size (default: 0.10)
- `risk_free_rate` (float): Risk-free rate för beräkningar (default: 0.02)

#### Metoder

##### `kelly_criterion()`
```python
def kelly_criterion(self,
                   win_rate: float,
                   avg_win_return: float,
                   avg_loss_return: float,
                   current_portfolio: float) -> Dict[str, float]
```

**Beräknar optimal position size med Kelly Criterion.**

**Parametrar:**
- `win_rate`: Sannolikhet för vinst (0-1)
- `avg_win_return`: Genomsnittlig vinstavkastning
- `avg_loss_return`: Genomsnittlig förlustavkastning (negativ)
- `current_portfolio`: Nuvarande portföljvärde

**Returnerar:** Dictionary med Kelly-resultat:
```python
{
    'kelly_fraction': float,        # Optimal Kelly fraction
    'conservative_kelly': float,    # Konservativ Kelly (hälften)
    'position_size': float,         # Rekommenderad position size
    'position_value': float,        # Positionvärde i dollar
    'expected_risk': float,         # Förväntad risk
    'max_portfolio_risk': float     # Maximum tillåten risk
}
```

---

##### `fixed_fractional()`
```python
def fixed_fractional(self,
                   portfolio_value: float,
                   risk_per_trade: Optional[float] = None,
                   volatility: Optional[float] = None) -> float
```

**Beräknar Fixed Fractional position size.**

**Parametrar:**
- `portfolio_value`: Nuvarande portföljvärde
- `risk_per_trade`: Risk per trade (använder max_portfolio_risk om None)
- `volatility`: Asset volatility för justering (optional)

**Returnerar:** Position size som fraction av portfölj

---

##### `risk_parity_allocation()`
```python
def risk_parity_allocation(self,
                          asset_returns: pd.DataFrame,
                          target_volatility: Optional[float] = None) -> Dict[str, float]
```

**Beräknar Risk Parity portföljvikter.**

**Parametrar:**
- `asset_returns`: DataFrame med historiska avkastningar per tillgång
- `target_volatility`: Målvolatilitet för portföljen (optional)

**Returnerar:** Dictionary med asset weights {asset: weight}

---

##### `minimum_variance_allocation()`
```python
def minimum_variance_allocation(self,
                               asset_returns: pd.DataFrame,
                               bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]
```

**Beräknar Minimum Variance portföljvikter.**

**Parametrar:**
- `asset_returns`: DataFrame med historiska avkastningar
- `bounds`: Bounds för individuella vikter (min, max)

**Returnerar:** Dictionary med optimala weights för minsta volatilitet

---

##### `maximum_sharpe_allocation()`
```python
def maximum_sharpe_allocation(self,
                             asset_returns: pd.DataFrame,
                             bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]
```

**Beräknar Maximum Sharpe portföljvikter.**

**Parametrar:**
- `asset_returns`: DataFrame med historiska avkastningar
- `bounds`: Bounds för individuella vikter (min, max)

**Returnerar:** Dictionary med optimala weights för högsta Sharpe ratio

---

##### `equal_risk_contribution()`
```python
def equal_risk_contribution(self,
                           asset_returns: pd.DataFrame,
                           bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]
```

**Beräknar Equal Risk Contribution vikter.**

**Parametrar:**
- `asset_returns`: DataFrame med historiska avkastningar
- `bounds`: Bounds för individuella vikter (min, max)

**Returnerar:** Dictionary med ERC weights

---

##### `volatility_targeted_allocation()`
```python
def volatility_targeted_allocation(self,
                                  asset_returns: pd.DataFrame,
                                  target_volatility: float,
                                  bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]
```

**Beräknar vikter för specifik målvolatilitet.**

**Parametrar:**
- `asset_returns`: DataFrame med historiska avkastningar
- `target_volatility`: Målvolatilitet för portföljen
- `bounds`: Bounds för individuella vikter

**Returnerar:** Dictionary med volatility-targeted weights

## 🧮 Beräkningsexempel

### 1. Kelly Criterion

```python
from core.position_sizer import PositionSizer

sizer = PositionSizer()

# Exempel: Trading system med 60% win rate
# Average win: +8%, Average loss: -4%
kelly_result = sizer.kelly_criterion(
    win_rate=0.60,
    avg_win_return=0.08,
    avg_loss_return=-0.04,
    current_portfolio=100000
)

print(f"Optimal Kelly: {kelly_result['kelly_fraction']:.1%}")
print(f"Konservativ Kelly: {kelly_result['conservative_kelly']:.1%}")
print(f"Rekommenderad position: ${kelly_result['position_value']:,.2f}")
```

### 2. Risk Parity Allocation

```python
import pandas as pd
import numpy as np

# Skapa exempeldata
np.random.seed(42)
dates = pd.date_range('2023-01-01', periods=252, freq='D')
assets = ['BTC', 'ETH', 'ADA', 'DOT']

# Generera korrelerade avkastningar
returns_data = {}
for asset in assets:
    # Olika volatiliteter för olika tillgångar
    vol = {'BTC': 0.05, 'ETH': 0.06, 'ADA': 0.08, 'DOT': 0.07}[asset]
    returns_data[asset] = np.random.normal(0.001, vol, 252)

asset_returns = pd.DataFrame(returns_data, index=dates)

# Beräkna Risk Parity weights
weights = sizer.risk_parity_allocation(asset_returns)

print("Risk Parity Weights:")
for asset, weight in weights.items():
    print(f"{asset}: {weight:.1%}")
```

### 3. Minimum Variance Optimization

```python
# Använd historiska data för optimering
optimal_weights = sizer.minimum_variance_allocation(
    asset_returns,
    bounds=(0, 0.3)  # Max 30% per tillgång
)

print("Minimum Variance Portfolio:")
total_weight = 0
for asset, weight in optimal_weights.items():
    print(f"{asset}: {weight:.1%}")
    total_weight += weight

print(f"Total weight: {total_weight:.1%}")
```

## 📊 Jämförelse av Metoder

| Metod | Fördelar | Nackdelar | Bästa användningsområde |
|-------|----------|-----------|-------------------------|
| **Kelly Criterion** | Matematiskt optimal<br>Maximerar långsiktig tillväxt | Kräver noggrann estimering<br>Kan vara volatil | Erfarna traders<br>Långsiktig portfölj |
| **Fixed Fractional** | Enkelt att implementera<br>Konsekvent risk | Ej optimal matematiskt<br>Ignorerar marknadsförhållanden | Beginners<br>Riskmedvetna traders |
| **Risk Parity** | Jämn riskfördelning<br>Bra diversifiering | Kan underprestera i bull markets<br>Komplex implementation | Institutionella<br>Riskfokuserade portföljer |
| **Min Variance** | Minsta möjliga volatilitet<br>Stabil | Låg förväntad avkastning<br>Känslig för inputs | Konservativa investerare<br>Kapitalbevarande |
| **Max Sharpe** | Optimal risk/avkastning<br>Teoretiskt solid | Historiska antaganden<br>Estimering error | Moderna portföljteori<br>Avkastningsfokuserade |

## ⚙️ Konfiguration och Parametrar

### Standardinställningar
```python
DEFAULT_CONFIG = {
    'max_portfolio_risk': 0.02,      # 2% risk per trade
    'max_single_position': 0.10,     # 10% max single position
    'risk_free_rate': 0.02,          # 2% risk-free rate
    'optimization_bounds': (0, 0.2), # 0-20% per asset
    'rebalance_threshold': 0.05      # 5% rebalancing threshold
}
```

### Risknivå-baserade inställningar
```python
RISK_LEVELS = {
    'conservative': {
        'max_portfolio_risk': 0.01,   # 1% risk per trade
        'max_single_position': 0.05,  # 5% max position
        'kelly_fraction': 0.5         # Use half Kelly
    },
    'moderate': {
        'max_portfolio_risk': 0.02,   # 2% risk per trade
        'max_single_position': 0.10,  # 10% max position
        'kelly_fraction': 0.75        # Use 3/4 Kelly
    },
    'aggressive': {
        'max_portfolio_risk': 0.05,   # 5% risk per trade
        'max_single_position': 0.25,  # 25% max position
        'kelly_fraction': 1.0         # Use full Kelly
    }
}
```

### Kelly Criterion Parametrar
```python
KELLY_CONFIG = {
    'min_win_rate': 0.50,           # Minimum acceptable win rate
    'max_kelly_fraction': 0.25,     # Maximum Kelly fraction (25%)
    'confidence_interval': 0.95,    # Confidence for parameter estimates
    'lookback_periods': 100,        # Periods to use for parameter estimation
    'conservative_multiplier': 0.5   # Conservative Kelly multiplier
}
```

## 🔍 Validering och Backtesting

### Position Size Backtesting
```python
def backtest_position_sizing(returns: np.ndarray,
                           position_sizes: np.ndarray,
                           initial_capital: float = 100000) -> Dict[str, float]:
    """
    Backtestar position sizing strategi.

    Args:
        returns: Dagliga avkastningar
        position_sizes: Position sizes per period
        initial_capital: Initial kapital

    Returns:
        Backtesting metrics
    """
    capital = initial_capital
    peak_capital = initial_capital
    max_drawdown = 0
    trades = []

    for i, (ret, size) in enumerate(zip(returns, position_sizes)):
        # Beräkna P&L för denna period
        pnl = capital * size * ret
        capital += pnl

        # Track drawdown
        if capital > peak_capital:
            peak_capital = capital
        drawdown = (peak_capital - capital) / peak_capital
        max_drawdown = max(max_drawdown, drawdown)

        # Record trade
        trades.append({
            'period': i,
            'return': ret,
            'position_size': size,
            'pnl': pnl,
            'capital': capital
        })

    total_return = (capital - initial_capital) / initial_capital

    return {
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'final_capital': capital,
        'total_trades': len(trades),
        'win_rate': sum(1 for t in trades if t['pnl'] > 0) / len(trades)
    }
```

### Kelly Criterion Validering
```python
def validate_kelly_parameters(win_rate: float,
                            avg_win: float,
                            avg_loss: float,
                            confidence_level: float = 0.95) -> Dict[str, float]:
    """
    Validerar Kelly Criterion parametrar.

    Args:
        win_rate: Estimated win rate
        avg_win: Average win return
        avg_loss: Average loss return
        confidence_level: Confidence level for validation

    Returns:
        Validation results
    """
    if win_rate <= 0 or win_rate >= 1:
        return {'valid': False, 'reason': 'Win rate must be between 0 and 1'}

    if avg_loss >= 0:
        return {'valid': False, 'reason': 'Average loss must be negative'}

    # Calculate Kelly fraction
    b = abs(avg_win) / abs(avg_loss)
    kelly = (b * win_rate - (1 - win_rate)) / b

    # Check for reasonable values
    if kelly <= 0:
        return {'valid': False, 'reason': 'Kelly fraction is negative - avoid this strategy'}

    if kelly > 0.25:
        return {'valid': False, 'reason': 'Kelly fraction too high - use conservative approach'}

    return {
        'valid': True,
        'kelly_fraction': kelly,
        'recommended_fraction': min(kelly * 0.5, 0.10),  # Conservative approach
        'confidence_interval': confidence_level
    }
```

## 🚨 Riskvarningar och Limits

### Position Size Limits
```python
def enforce_position_limits(position_size: float,
                          portfolio_value: float,
                          limits: Dict[str, float]) -> float:
    """
    Säkerställer att position size håller sig inom gränser.

    Args:
        position_size: Calculated position size (fraction)
        portfolio_value: Current portfolio value
        limits: Position limits

    Returns:
        Adjusted position size within limits
    """
    # Check portfolio risk limit
    max_portfolio_risk = limits.get('max_portfolio_risk', 0.02)
    if position_size > max_portfolio_risk:
        print(f"⚠️ Position size {position_size:.1%} exceeds portfolio risk limit {max_portfolio_risk:.1%}")
        position_size = max_portfolio_risk

    # Check single position limit
    max_single_position = limits.get('max_single_position', 0.10)
    if position_size > max_single_position:
        print(f"⚠️ Position size {position_size:.1%} exceeds single position limit {max_single_position:.1%}")
        position_size = max_single_position

    # Check concentration limit
    max_concentration = limits.get('max_concentration', 0.25)
    if position_size > max_concentration:
        print(f"⚠️ Position size {position_size:.1%} exceeds concentration limit {max_concentration:.1%}")
        position_size = max_concentration

    return position_size
```

### Kelly Criterion Risk Assessment
```python
def assess_kelly_risk(kelly_fraction: float,
                     win_rate: float,
                     avg_win: float,
                     avg_loss: float) -> str:
    """
    Bedömer risknivå för Kelly Criterion.

    Args:
        kelly_fraction: Calculated Kelly fraction
        win_rate: Win rate
        avg_win: Average win
        avg_loss: Average loss

    Returns:
        Risk assessment ('low', 'medium', 'high', 'extreme')
    """
    # Risk factors
    risk_score = 0

    # High Kelly fraction
    if kelly_fraction > 0.10:
        risk_score += 2
    elif kelly_fraction > 0.05:
        risk_score += 1

    # Low win rate
    if win_rate < 0.55:
        risk_score += 1

    # High loss ratio
    loss_ratio = abs(avg_loss) / abs(avg_win)
    if loss_ratio > 0.8:
        risk_score += 1

    # Determine risk level
    if risk_score >= 3:
        return 'extreme'
    elif risk_score >= 2:
        return 'high'
    elif risk_score >= 1:
        return 'medium'
    else:
        return 'low'
```

## 📈 Prestandaoptimering

### Cache-strategier
```python
from functools import lru_cache
import hashlib

class CachedPositionSizer(PositionSizer):
    @lru_cache(maxsize=100)
    def _cached_risk_parity(self, returns_hash: str, target_vol: float) -> Dict[str, float]:
        """Cache Risk Parity calculations."""
        # Implementation för cache
        pass

    def risk_parity_allocation(self, asset_returns: pd.DataFrame,
                              target_volatility: Optional[float] = None) -> Dict[str, float]:
        """Cached version av risk parity."""
        # Skapa hash av data
        returns_str = str(asset_returns.values.tobytes())
        data_hash = hashlib.md5(returns_str.encode()).hexdigest()

        # Använd cache
        cache_key = f"{data_hash}_{target_volatility or 0}"
        return self._cached_risk_parity(cache_key, target_volatility or 0)
```

### Parallellisering för Optimization
```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

def parallel_portfolio_optimization(asset_returns: pd.DataFrame,
                                  methods: List[str],
                                  bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, Dict[str, float]]:
    """
    Parallell portföljoptimering för flera metoder.
    """
    def optimize_method(method):
        sizer = PositionSizer()
        if method == 'min_variance':
            return method, sizer.minimum_variance_allocation(asset_returns, bounds)
        elif method == 'max_sharpe':
            return method, sizer.maximum_sharpe_allocation(asset_returns, bounds)
        elif method == 'risk_parity':
            return method, sizer.risk_parity_allocation(asset_returns)

    with ProcessPoolExecutor(max_workers=min(len(methods), mp.cpu_count())) as executor:
        results = list(executor.map(optimize_method, methods))

    return dict(results)
```

## 🔗 Integrationer

### Med VaR Calculator
```python
# Integration med VaR för risk-justerade position sizes
def risk_adjusted_position_size(sizer: PositionSizer,
                              var_calculator: VaRCalculator,
                              asset_returns: pd.Series,
                              portfolio_value: float,
                              base_risk: float = 0.02) -> float:
    """Beräknar position size justerad för VaR."""

    # Beräkna VaR
    var_95 = var_calculator.calculate_historical_var(
        asset_returns.values, portfolio_value
    )

    # Justera position size baserat på VaR
    var_percentage = abs(var_95) / portfolio_value

    if var_percentage > base_risk:
        # Minska position size för högre risk
        adjustment_factor = base_risk / var_percentage
        adjusted_size = base_risk * adjustment_factor
    else:
        # Kan öka position size för lägre risk
        adjustment_factor = min(var_percentage / base_risk, 2.0)
        adjusted_size = base_risk * adjustment_factor

    return min(adjusted_size, sizer.max_single_position)
```

### Med Risk Manager
```python
# Integration med Risk Manager för automatiska justeringar
def dynamic_position_sizing(sizer: PositionSizer,
                          risk_manager: RiskManager,
                          token: str,
                          base_size: float) -> float:
    """Dynamisk position sizing baserat på risk status."""

    # Check current risk status
    risk_metrics = risk_manager.get_portfolio_risk_metrics()

    # Adjust size based on risk level
    if risk_metrics.get('concentration_risk', 0) > 0.20:
        # Reduce size if high concentration
        adjustment = 0.8
    elif risk_metrics.get('var_95', 0) > 0.10:
        # Reduce size if high VaR
        adjustment = 0.9
    else:
        adjustment = 1.0

    adjusted_size = base_size * adjustment

    # Ensure within limits
    return min(adjusted_size, sizer.max_single_position)
```

## 🧪 Tester och Validering

### Unit Tests
```python
def test_kelly_criterion():
    """Test Kelly Criterion calculations."""
    sizer = PositionSizer()

    # Test case 1: Standard Kelly
    result = sizer.kelly_criterion(0.6, 0.08, -0.04, 100000)

    assert 'kelly_fraction' in result
    assert 'position_size' in result
    assert result['kelly_fraction'] > 0
    assert result['position_size'] <= sizer.max_single_position

    # Test case 2: Invalid inputs
    try:
        sizer.kelly_criterion(1.5, 0.08, -0.04, 100000)  # Invalid win rate
        assert False, "Should raise ValueError"
    except ValueError:
        pass  # Expected

def test_risk_parity():
    """Test Risk Parity allocation."""
    sizer = PositionSizer()

    # Create test data
    np.random.seed(42)
    asset_returns = pd.DataFrame({
        'A': np.random.normal(0.001, 0.05, 100),
        'B': np.random.normal(0.001, 0.03, 100),
        'C': np.random.normal(0.001, 0.07, 100)
    })

    weights = sizer.risk_parity_allocation(asset_returns)

    # Verify properties
    assert len(weights) == 3
    assert abs(sum(weights.values()) - 1.0) < 0.01  # Sum to 1
    assert all(w >= 0 for w in weights.values())  # Non-negative
    assert all(w <= 1 for w in weights.values())  # Less than 1

    # Higher volatility should get lower weight
    assert weights['C'] < weights['B'] < weights['A']  # C has highest vol
```

### Integration Tests
```python
def test_full_position_sizing_workflow():
    """Test komplett position sizing workflow."""
    # Setup
    sizer = PositionSizer()
    np.random.seed(42)

    # Generate historical data
    returns = np.random.normal(0.001, 0.02, 252)

    # Test different methods
    methods = ['kelly', 'fixed_fractional', 'risk_parity']
    results = {}

    for method in methods:
        if method == 'kelly':
            results[method] = sizer.kelly_criterion(0.55, 0.06, -0.03, 100000)
        elif method == 'fixed_fractional':
            results[method] = sizer.fixed_fractional(100000, 0.02)
        elif method == 'risk_parity':
            # Would need multi-asset data
            pass

    # Verify all methods produce reasonable results
    for method, result in results.items():
        if method == 'kelly':
            assert result['position_size'] > 0
            assert result['position_value'] > 0
        elif method == 'fixed_fractional':
            assert result > 0
            assert result <= 0.02  # Should not exceed risk limit
```

## 📚 Referenser

1. **"Fortune's Formula" - William Poundstone** - Kelly Criterion förklaring
2. **"Expected Returns" - Antti Ilmanen** - Portföljoptimering
3. **"Risk Parity Fundamentals" - Edward Qian** - Risk Parity metod
4. **"The Kelly Capital Growth Criterion" - Leonard C. MacLean** - Original Kelly paper

---

*Position Sizer är fundamentalt för riskhantering genom att säkerställa optimala positionstorlekar baserat på matematiska principer och risktolerans.*