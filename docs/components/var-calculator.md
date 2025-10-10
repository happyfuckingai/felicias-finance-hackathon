# 📊 VaR Calculator - Value-at-Risk Beräkningar

## Översikt

VaR Calculator är kärnkomponenten för riskmått-beräkningar i Risk Management System. Modulen tillhandahåller flera olika metoder för att beräkna Value-at-Risk (VaR) och relaterade riskmått.

## 🎯 Funktioner

- **Historisk VaR**: Empirisk fördelning baserad på historiska data
- **Parametrisk VaR**: Normalfördelningsantagande med analytiska formler
- **Monte Carlo VaR**: Simuleringsbaserad approach med stokastiska metoder
- **Expected Shortfall (ES)**: Genomsnittlig förlust utöver VaR
- **Risk Contribution**: Individuella tillgångars bidrag till portföljrisk

## 📈 Matematiska Grundformler

### Historisk VaR
```
VaR_α = -P * percentile(R, α)
```
Där:
- `P` = Portföljvärde
- `R` = Historiska avkastningar
- `α` = Konfidensnivå (vanligtvis 0.05 för 95% VaR)

### Parametrisk VaR (Normalfördelning)
```
VaR_α = -P * (μ + z_α * σ)
```
Där:
- `μ` = Medelavkastning
- `σ` = Standardavvikelse
- `z_α` = Normalfördelningens percentil för konfidensnivå α

### Monte Carlo VaR
```
VaR_α = P - percentile(S_T, α)
```
Där:
- `S_T` = Simulerade portföljvärden vid tidpunkt T
- Simuleringar genereras från historiska avkastningar

## 💻 API Referens

### Klassdefinition

```python
class VaRCalculator:
    def __init__(self, confidence_level: float = 0.95, time_horizon: int = 1):
        """
        Args:
            confidence_level: Konfidensnivå (0-1), standard 0.95 för 95% VaR
            time_horizon: Tidsperiod i dagar för VaR-beräkning
        """
```

### Metoder

#### `calculate_historical_var()`
```python
def calculate_historical_var(self,
                            returns: Union[pd.Series, np.ndarray],
                            portfolio_value: float,
                            lookback_periods: Optional[int] = None) -> float:
    """
    Beräknar historisk VaR med empirisk fördelning.

    Args:
        returns: Historiska avkastningar (dagliga)
        portfolio_value: Nuvarande portföljvärde
        lookback_periods: Antal perioder att använda (default: alla)

    Returns:
        Historisk VaR-värde (negativt för förlust)

    Example:
        >>> calculator = VaRCalculator()
        >>> var = calculator.calculate_historical_var(returns, 100000)
        >>> print(f"95% VaR: ${-var:,.2f}")  # Förlust om 1 dag
    """
```

#### `calculate_parametric_var()`
```python
def calculate_parametric_var(self,
                            returns: Union[pd.Series, np.ndarray],
                            portfolio_value: float,
                            lookback_periods: Optional[int] = None) -> float:
    """
    Beräknar parametrisk VaR med normalfördelningsantagande.

    Args:
        returns: Historiska avkastningar
        portfolio_value: Portföljvärde
        lookback_periods: Lookback-perioder

    Returns:
        Parametrisk VaR-värde

    Note:
        Antar normalfördelade avkastningar - fungerar bra för stora portföljer
        enligt Central Limit Theorem.
    """
```

#### `calculate_monte_carlo_var()`
```python
def calculate_monte_carlo_var(self,
                             returns: Union[pd.Series, np.ndarray],
                             portfolio_value: float,
                             simulations: int = 10000,
                             lookback_periods: Optional[int] = None) -> float:
    """
    Beräknar Monte Carlo VaR genom simulering.

    Args:
        returns: Historiska avkastningar
        portfolio_value: Portföljvärde
        simulations: Antal Monte Carlo simuleringar (default: 10,000)
        lookback_periods: Lookback-perioder

    Returns:
        Monte Carlo VaR-värde

    Note:
        Mer noggrann men beräkningsintensiv. Används för komplexa
        portföljer med icke-normala fördelningar.
    """
```

#### `calculate_expected_shortfall()`
```python
def calculate_expected_shortfall(self,
                                returns: Union[pd.Series, np.ndarray],
                                portfolio_value: float,
                                method: str = 'historical',
                                lookback_periods: Optional[int] = None) -> float:
    """
    Beräknar Expected Shortfall (ES) - genomsnittlig förlust utöver VaR.

    Args:
        returns: Historiska avkastningar
        portfolio_value: Portföljvärde
        method: Beräkningsmetod ('historical', 'parametric', 'monte_carlo')
        lookback_periods: Lookback-perioder

    Returns:
        Expected Shortfall-värde

    Note:
        ES är kohärent riskmått till skillnad från VaR.
        ES ≥ VaR alltid.
    """
```

#### `calculate_var_contribution()`
```python
def calculate_var_contribution(self,
                              asset_returns: pd.DataFrame,
                              weights: np.ndarray,
                              portfolio_value: float,
                              method: str = 'parametric') -> np.ndarray:
    """
    Beräknar individuella tillgångars bidrag till portfölj-VaR.

    Args:
        asset_returns: DataFrame med tillgångsavkastningar
        weights: Portföljvikter
        portfolio_value: Portföljvärde
        method: VaR-metod ('parametric', 'historical')

    Returns:
        Array med VaR-bidrag per tillgång

    Example:
        >>> contributions = calculator.calculate_var_contribution(
        ...     asset_returns, weights, 100000
        ... )
        >>> for i, contrib in enumerate(contributions):
        ...     print(f"Asset {i}: ${contrib:.2f} VaR contribution")
    """
```

## 🧮 Beräkningsexempel

### Enkelt Exempel - Historisk VaR

```python
import numpy as np
import pandas as pd
from core.var_calculator import VaRCalculator

# Skapa exempeldata
np.random.seed(42)
returns = np.random.normal(0.001, 0.02, 252)  # 1 år dagliga avkastningar
portfolio_value = 100000

# Beräkna VaR
calculator = VaRCalculator(confidence_level=0.95, time_horizon=1)
var_95 = calculator.calculate_historical_var(returns, portfolio_value)

print(f"95% VaR (1 dag): ${-var_95:,.2f}")
print(f"Det betyder att det finns 5% risk att förlora minst ${-var_95:,.2f} imorgon")
```

### Portfölj-VaR med Flera Tillgångar

```python
# Exempel med flera tillgångar
asset_returns = pd.DataFrame({
    'BTC': np.random.normal(0.002, 0.05, 252),
    'ETH': np.random.normal(0.001, 0.06, 252),
    'USDC': np.random.normal(0.00005, 0.001, 252)
})

weights = np.array([0.5, 0.3, 0.2])  # 50% BTC, 30% ETH, 20% USDC

# Beräkna portfölj-VaR
portfolio_var = calculator.calculate_portfolio_var(
    asset_returns, weights, confidence_level=0.95
)

print(f"Portfölj-VaR (95%): ${-portfolio_var * portfolio_value:,.2f}")
```

## 📊 Riskmått Jämförelse

| Metod | Fördelar | Nackdelar | Användningsområde |
|-------|----------|-----------|------------------|
| **Historisk VaR** | Ingen fördelningsantagande<br>Inkorporerar historiska extremvärden | Förutsätter att historia upprepar sig<br>Känslig för lookback-period | Traditionella portföljer<br>Kortsiktig risk |
| **Parametrisk VaR** | Snabb beräkning<br>Analytiska formler | Antar normalfördelning<br>Ignorerar "fat tails" | Stora portföljer<br>Daglig riskhantering |
| **Monte Carlo VaR** | Flexibel fördelningsantagande<br>Hanterar komplexa produkter | Beräkningsintensiv<br>Konvergensproblem | Komplexa derivatinstrument<br>Långsiktig risk |
| **Expected Shortfall** | Kohärent riskmått<br>Bättre för extremrisk | Mer konservativ än VaR<br>Svårare att förklara | Regulatoriska krav<br>Riskkapital |

## ⚙️ Konfiguration

### Standardparametrar
```python
DEFAULT_CONFIG = {
    'confidence_level': 0.95,      # 95% VaR (standard)
    'time_horizon': 1,             # 1 dag
    'monte_carlo_sims': 10000,     # 10,000 simuleringar
    'lookback_periods': 252        # 1 år handelsdagar
}
```

### Anpassade Konfidensnivåer
```python
# Olika konfidensnivåer för olika användningsområden
configs = {
    'conservative': {'confidence_level': 0.99, 'time_horizon': 1},    # 99% VaR
    'standard': {'confidence_level': 0.95, 'time_horizon': 1},        # 95% VaR
    'aggressive': {'confidence_level': 0.90, 'time_horizon': 1},      # 90% VaR
    'stress_test': {'confidence_level': 0.999, 'time_horizon': 10}    # Extrem stress
}
```

## 🔍 Validering och Backtesting

### VaR Backtesting
```python
def backtest_var(returns: np.ndarray, var_values: np.ndarray, confidence_level: float = 0.95):
    """
    Backtestar VaR-modellens noggrannhet.

    Args:
        returns: Faktiska avkastningar
        var_values: Beräknade VaR-värden
        confidence_level: Förväntad konfidensnivå

    Returns:
        Backtesting-statistik
    """
    # Antal överskridanden (faktiska förluster större än VaR)
    violations = np.sum(returns < -var_values)
    expected_violations = (1 - confidence_level) * len(returns)

    # Kupiec's test för oberoende överskridanden
    violation_ratio = violations / expected_violations

    return {
        'total_violations': violations,
        'expected_violations': expected_violations,
        'violation_ratio': violation_ratio,
        'model_accuracy': 'good' if 0.8 <= violation_ratio <= 1.2 else 'poor'
    }
```

### Risk Model Validering

```python
def validate_risk_model(returns: np.ndarray, var_calculator: VaRCalculator):
    """Validerar riskmodellens prestanda."""
    n_periods = len(returns)
    var_values = []

    # Rullande VaR-beräkningar
    for i in range(252, n_periods):  # Starta efter 1 år
        historical_returns = returns[i-252:i]
        var = var_calculator.calculate_historical_var(historical_returns, 1.0)
        var_values.append(var)

    # Backtesta modellen
    backtest_results = backtest_var(
        returns[252:], np.array(var_values), var_calculator.confidence_level
    )

    return backtest_results
```

## 🚨 Riskvarningar och Tröskelvärden

### VaR Tröskelvärden
```python
VAR_THRESHOLDS = {
    'low_risk': 0.02,      # 2% VaR - Låg risk
    'medium_risk': 0.05,   # 5% VaR - Medium risk
    'high_risk': 0.10,     # 10% VaR - Hög risk
    'extreme_risk': 0.20   # 20% VaR - Extrem risk
}

def assess_var_risk_level(var_value: float, portfolio_value: float) -> str:
    """Bedömer risknivå baserat på VaR."""
    var_percentage = abs(var_value) / portfolio_value

    if var_percentage <= VAR_THRESHOLDS['low_risk']:
        return 'low'
    elif var_percentage <= VAR_THRESHOLDS['medium_risk']:
        return 'medium'
    elif var_percentage <= VAR_THRESHOLDS['high_risk']:
        return 'high'
    else:
        return 'extreme'
```

## 📈 Prestandaoptimering

### Cache-strategier
```python
from functools import lru_cache
import hashlib

class CachedVaRCalculator(VaRCalculator):
    @lru_cache(maxsize=128)
    def _cached_var_calculation(self, returns_hash: str, method: str) -> float:
        """Cache VaR-beräkningar för samma data."""
        # Implementera cache-logik här
        pass
```

### Parallellisering för Monte Carlo
```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

def parallel_monte_carlo_var(returns: np.ndarray,
                           portfolio_value: float,
                           simulations: int = 10000,
                           n_processes: int = 4) -> float:
    """
    Parallell Monte Carlo VaR-beräkning.
    """
    simulations_per_process = simulations // n_processes

    with ProcessPoolExecutor(max_workers=n_processes) as executor:
        futures = [
            executor.submit(
                monte_carlo_simulation,
                returns,
                portfolio_value,
                simulations_per_process
            )
            for _ in range(n_processes)
        ]

        results = [future.result() for future in futures]
        all_simulations = np.concatenate(results)

    return np.percentile(all_simulations, 5)  # 95% VaR
```

## 🔗 Integrationer

### Med Risk Handler
```python
# Integration med RiskHandler
risk_handler = RiskHandler()
assessment = await risk_handler.assess_portfolio_risk(portfolio, prices)

# VaR ingår automatiskt i riskbedömningen
print(f"Portfolio VaR: {assessment.var_95:.1%}")
```

### Med Portfolio Optimization
```python
# Integration med pyportfolioopt
from pypfopt import EfficientFrontier, risk_models

# Beräkna optimal portfölj med VaR-constraint
ef = EfficientFrontier(mu, S)
ef.add_constraint(lambda w: calculate_portfolio_var(returns, w) <= max_var)
weights = ef.max_sharpe()
```

## 🧪 Tester och Validering

### Unit Tests
```python
def test_var_calculations():
    """Testa VaR-beräkningsmetoder."""
    calculator = VaRCalculator()

    # Skapa testdata
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 1000)

    # Testa alla metoder
    historical = calculator.calculate_historical_var(returns, 100000)
    parametric = calculator.calculate_parametric_var(returns, 100000)
    monte_carlo = calculator.calculate_monte_carlo_var(returns, 100000)

    # Alla ska vara negativa (förluster)
    assert all(var < 0 for var in [historical, parametric, monte_carlo])

    # Expected Shortfall ska vara mer extrem än VaR
    es = calculator.calculate_expected_shortfall(returns, 100000)
    assert abs(es) >= abs(historical)
```

## 📚 Referenser

1. **RiskMetrics** - J.P. Morgan's risk measurement framework
2. **Value at Risk: The New Benchmark for Managing Financial Risk** - Philippe Jorion
3. **Modern Portfolio Theory** - Harry Markowitz
4. **Financial Risk Management** - Allan Malz

---

*VaR Calculator är kärnan i riskhanteringssystemet och tillhandahåller fundamentala riskmått för alla andra komponenter.*