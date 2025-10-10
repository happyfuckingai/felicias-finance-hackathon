# 📊 Portfolio Risk - Risk Analytics & Metrics

## Översikt

Portfolio Risk är den avancerade analytiska kärnan i Risk Management System. Modulen tillhandahåller omfattande riskmått, prestationsanalys och portföljoptimering baserat på moderna finansiella teorier och praktiska implementationer.

## 🎯 Funktioner

- **Sharpe & Sortino Ratios**: Riskjusterad avkastningsmått
- **Maximum Drawdown**: Största peak-to-trough decline
- **Beta & Alpha**: Marknadsexponering och överavkastning
- **Calmar Ratio**: Avkastning vs. Maximum Drawdown
- **Information Ratio**: Aktiv avkastning vs. tracking error
- **Efficient Frontier**: Optimal risk/avkastning kombinationer
- **Rolling Risk Metrics**: Tidsbaserade riskanalyser
- **Risk Attribution**: Bidrag till portföljrisk per tillgång

## 📈 Matematiska Grundformler

### Sharpe Ratio
```
Sharpe = (Rp - Rf) / σp
```
Där:
- `Rp` = Portföljens avkastning
- `Rf` = Riskfri ränta
- `σp` = Portföljens volatilitet (standardavvikelse)

**Annualiserad:** Multiplicera med `√(365/dagar per period)`

### Sortino Ratio
```
Sortino = (Rp - Rf) / σd
```
Där:
- `σd` = Downside deviation (endast negativa avkastningar)

### Maximum Drawdown
```
MDD = min((P_t - Peak) / Peak) för alla t
```
Där:
- `P_t` = Portföljvärde vid tidpunkt t
- `Peak` = Högsta värde hittills

### Beta
```
β = Cov(Rp, Rm) / Var(Rm)
```
Där:
- `Rp` = Portföljens avkastning
- `Rm` = Marknadens avkastning

### Alpha (Jensen's Alpha)
```
α = Rp - [Rf + β × (Rm - Rf)]
```
Där:
- `Rp` = Faktisk portföljavkastning
- `Rf + β × (Rm - Rf)` = Förväntad avkastning enligt CAPM

### Calmar Ratio
```
Calmar = Rp / |MDD|
```
Där:
- `Rp` = Årlig avkastning
- `MDD` = Maximum Drawdown (absolutvärde)

### Information Ratio
```
IR = (Rp - Rb) / σ(Rp - Rb)
```
Där:
- `Rb` = Benchmark avkastning
- `σ(Rp - Rb)` = Tracking error

## 💻 API Referens

### Klassdefinition

```python
class PortfolioRisk:
    """Avancerade portfölj-riskmått och prestationsanalys."""
```

#### Konstruktor
```python
__init__(self, risk_free_rate: float = 0.02, periods_per_year: int = 365)
```

**Parametrar:**
- `risk_free_rate` (float): Riskfri ränta som decimal (default: 0.02 för 2%)
- `periods_per_year` (int): Perioder per år för annualisering (default: 365 för dagliga data)

#### Metoder

##### `calculate_sharpe_ratio()`
```python
def calculate_sharpe_ratio(self,
                          returns: Union[pd.Series, np.ndarray],
                          annualize: bool = True) -> float
```

**Beräknar Sharpe ratio för riskjusterad avkastning.**

**Parametrar:**
- `returns`: Portföljens historiska avkastningar
- `annualize`: Om ratio ska annualiseras

**Returnerar:** Sharpe ratio (högre värden = bättre riskjusterad avkastning)

---

##### `calculate_sortino_ratio()`
```python
def calculate_sortino_ratio(self,
                           returns: Union[pd.Series, np.ndarray],
                           annualize: bool = True) -> float
```

**Beräknar Sortino ratio med fokus på downside risk.**

**Parametrar:**
- `returns`: Portföljens historiska avkastningar
- `annualize`: Om ratio ska annualiseras

**Returnerar:** Sortino ratio

---

##### `calculate_max_drawdown()`
```python
def calculate_max_drawdown(self,
                          portfolio_values: Union[pd.Series, np.ndarray]) -> float
```

**Beräknar maximum drawdown.**

**Parametrar:**
- `portfolio_values`: Portföljvärden över tid

**Returnerar:** Maximum drawdown som decimal (t.ex. 0.15 för 15%)

---

##### `calculate_beta()`
```python
def calculate_beta(self,
                  portfolio_returns: Union[pd.Series, np.ndarray],
                  market_returns: Union[pd.Series, np.ndarray]) -> float
```

**Beräknar portföljens beta relativt marknaden.**

**Parametrar:**
- `portfolio_returns`: Portföljens avkastningar
- `market_returns`: Marknadens/benchmark avkastningar

**Returnerar:** Beta-värde (< 1 defensiv, = 1 neutral, > 1 offensiv)

---

##### `calculate_alpha()`
```python
def calculate_alpha(self,
                   portfolio_returns: Union[pd.Series, np.ndarray],
                   market_returns: Union[pd.Series, np.ndarray]) -> float
```

**Beräknar Jensen's alpha (överavkastning).**

**Parametrar:**
- `portfolio_returns`: Portföljens avkastningar
- `market_returns`: Marknadens/benchmark avkastningar

**Returnerar:** Alpha-värde (positivt = överavkastning)

---

##### `calculate_calmar_ratio()`
```python
def calculate_calmar_ratio(self,
                          returns: Union[pd.Series, np.ndarray],
                          portfolio_values: Union[pd.Series, np.ndarray],
                          annualize: bool = True) -> float
```

**Beräknar Calmar ratio (avkastning vs. drawdown).**

**Parametrar:**
- `returns`: Portföljens avkastningar
- `portfolio_values`: Portföljvärden över tid
- `annualize`: Om ratio ska annualiseras

**Returnerar:** Calmar ratio

---

##### `calculate_information_ratio()`
```python
def calculate_information_ratio(self,
                              portfolio_returns: Union[pd.Series, np.ndarray],
                              benchmark_returns: Union[pd.Series, np.ndarray]) -> float
```

**Beräknar Information ratio.**

**Parametrar:**
- `portfolio_returns`: Portföljens avkastningar
- `benchmark_returns`: Benchmark avkastningar

**Returnerar:** Information ratio (högre = bättre)

---

##### `calculate_correlation_matrix()`
```python
def calculate_correlation_matrix(self,
                                asset_returns: pd.DataFrame) -> pd.DataFrame
```

**Beräknar korrelationsmatris för tillgångar.**

**Parametrar:**
- `asset_returns`: DataFrame med tillgångsavkastningar

**Returnerar:** Korrelationsmatris

---

##### `calculate_covariance_matrix()`
```python
def calculate_covariance_matrix(self,
                               asset_returns: pd.DataFrame,
                               annualize: bool = True) -> pd.DataFrame
```

**Beräknar kovariansmatris.**

**Parametrar:**
- `asset_returns`: DataFrame med tillgångsavkastningar
- `annualize`: Om kovarians ska annualiseras

**Returnerar:** Kovariansmatris

---

##### `calculate_portfolio_volatility()`
```python
def calculate_portfolio_volatility(self,
                                  weights: np.ndarray,
                                  cov_matrix: pd.DataFrame) -> float
```

**Beräknar portföljvolatilitet från vikter och kovarians.**

**Parametrar:**
- `weights`: Portföljvikter som array
- `cov_matrix`: Kovariansmatris

**Returnerar:** Portföljvolatilitet

---

##### `calculate_risk_contributions()`
```python
def calculate_risk_contributions(self,
                                weights: np.ndarray,
                                cov_matrix: pd.DataFrame) -> np.ndarray
```

**Beräknar individuella tillgångars bidrag till portföljrisk.**

**Parametrar:**
- `weights`: Portföljvikter
- `cov_matrix`: Kovariansmatris

**Returnerar:** Risk contributions per tillgång

---

##### `calculate_efficient_frontier()`
```python
def calculate_efficient_frontier(self,
                                asset_returns: pd.DataFrame,
                                target_returns: Optional[np.ndarray] = None,
                                num_portfolios: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]
```

**Beräknar efficient frontier portföljer.**

**Parametrar:**
- `asset_returns`: DataFrame med tillgångsavkastningar
- `target_returns`: Specifika målavkastningar (optional)
- `num_portfolios`: Antal portföljer att generera

**Returnerar:** Tuple av (avkastningar, volatiliteter, vikter)

---

##### `get_comprehensive_risk_metrics()`
```python
def get_comprehensive_risk_metrics(self,
                                  portfolio_returns: Union[pd.Series, np.ndarray],
                                  portfolio_values: Union[pd.Series, np.ndarray],
                                  market_returns: Optional[Union[pd.Series, np.ndarray]] = None,
                                  confidence_level: float = 0.95) -> RiskMetrics
```

**Beräknar omfattande risk metrics.**

**Parametrar:**
- `portfolio_returns`: Portföljens avkastningar
- `portfolio_values`: Portföljvärden över tid
- `market_returns`: Marknadsavkastningar (optional)
- `confidence_level`: Konfidensnivå för VaR

**Returnerar:** RiskMetrics dataclass med alla metrics

---

##### `get_portfolio_statistics()`
```python
def get_portfolio_statistics(self,
                            portfolio_returns: Union[pd.Series, np.ndarray]) -> PortfolioStats
```

**Beräknar omfattande portföljstatistik.**

**Parametrar:**
- `portfolio_returns`: Portföljens avkastningar

**Returnerar:** PortfolioStats dataclass

## 🧮 Beräkningsexempel

### 1. Sharpe Ratio Beräkning

```python
import numpy as np
from core.portfolio_risk import PortfolioRisk

# Skapa exempeldata
np.random.seed(42)
returns = np.random.normal(0.001, 0.02, 252)  # 1 år dagliga avkastningar

# Beräkna Sharpe ratio
analyzer = PortfolioRisk(risk_free_rate=0.02)
sharpe = analyzer.calculate_sharpe_ratio(returns)

print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Riskjusterad avkastning: {'Utmärkt' if sharpe > 2 else 'Bra' if sharpe > 1 else 'Acceptabel' if sharpe > 0.5 else 'Dålig'}")
```

### 2. Maximum Drawdown Analys

```python
import pandas as pd

# Skapa portföljvärden över tid
dates = pd.date_range('2023-01-01', periods=365, freq='D')
portfolio_values = 100000 * np.exp(np.cumsum(returns))
portfolio_series = pd.Series(portfolio_values, index=dates)

# Beräkna maximum drawdown
max_dd = analyzer.calculate_max_drawdown(portfolio_series)
print(f"Maximum Drawdown: {max_dd:.1%}")

# Analysera drawdown-perioder
peak = portfolio_series.expanding(min_periods=1).max()
drawdowns = (portfolio_series - peak) / peak

print(f"Längsta drawdown-period: {(drawdowns < 0).astype(int).groupby((drawdowns >= 0).cumsum()).sum().max()} dagar")
print(f"Genomsnittlig drawdown: {drawdowns[drawdowns < 0].mean():.1%}")
```

### 3. Beta och Alpha Beräkning

```python
# Skapa marknadsdata
market_returns = np.random.normal(0.0008, 0.015, 252)
market_series = pd.Series(market_returns, index=dates)

# Beräkna beta och alpha
beta = analyzer.calculate_beta(returns, market_returns)
alpha = analyzer.calculate_alpha(returns, market_returns)

print(f"Beta: {beta:.2f}")
print(f"Alpha: {alpha:.2f}")

# Interpret results
if beta > 1.2:
    print("Portföljen är aggressiv (högre volatilitet än marknaden)")
elif beta < 0.8:
    print("Portföljen är defensiv (lägre volatilitet än marknaden)")
else:
    print("Portföljen följer marknaden")

if alpha > 0.02:
    print("Portföljen överpresterar marknaden")
elif alpha < -0.02:
    print("Portföljen underpresterar marknaden")
else:
    print("Portföljen presterar i linje med marknaden")
```

### 4. Korrelationsanalys

```python
# Skapa multi-asset data
assets = ['BTC', 'ETH', 'ADA', 'DOT']
np.random.seed(42)

asset_data = {}
for asset in assets:
    # Skapa korrelerade avkastningar
    base_returns = np.random.normal(0.001, 0.02, 252)
    noise = np.random.normal(0, 0.01, 252)
    asset_data[asset] = base_returns + noise * {'BTC': 1.0, 'ETH': 0.8, 'ADA': 0.6, 'DOT': 0.4}[asset]

asset_returns = pd.DataFrame(asset_data, index=dates)

# Beräkna korrelationsmatris
correlation_matrix = analyzer.calculate_correlation_matrix(asset_returns)
print("Korrelationsmatris:")
print(correlation_matrix.round(2))

# Identifiera högst korrelerade par
correlations = correlation_matrix.unstack()
correlations = correlations[correlations < 1.0]  # Ta bort diagonal
max_corr = correlations.max()
max_corr_pair = correlations.idxmax()

print(f"\nHögst korrelation: {max_corr:.2f} mellan {max_corr_pair[0]} och {max_corr_pair[1]}")
```

### 5. Efficient Frontier

```python
# Beräkna efficient frontier
returns_array, volatility_array, weights_array = analyzer.calculate_efficient_frontier(
    asset_returns, num_portfolios=50
)

# Visa några optimala portföljer
print("Efficient Frontier - Optimala Portföljer:")
for i in range(0, len(returns_array), 10):  # Visa var 10:e portfölj
    ret = returns_array[i] * 365  # Annualiserad
    vol = volatility_array[i] * np.sqrt(365)  # Annualiserad
    sharpe = (ret - analyzer.risk_free_rate) / vol if vol > 0 else 0

    print(f"Portfölj {i+1}: Avkastning={ret:.1%}, Volatilitet={vol:.1%}, Sharpe={sharpe:.2f}")

# Hitta maximal Sharpe portfölj
best_idx = np.argmax((returns_array * 365 - analyzer.risk_free_rate) /
                    (volatility_array * np.sqrt(365)))
best_weights = weights_array[best_idx]

print(f"\nBästa portfölj (Max Sharpe):")
for asset, weight in zip(assets, best_weights):
    if weight > 0.01:  # Visa endast betydande vikter
        print(f"  {asset}: {weight:.1%}")
```

### 6. Omfattande Riskanalys

```python
# Hämta alla riskmått på en gång
comprehensive_metrics = analyzer.get_comprehensive_risk_metrics(
    returns, portfolio_series, market_returns, confidence_level=0.95
)

print("OMFATTANDE RISKANALYS")
print("=" * 50)
print(f"Sharpe Ratio: {comprehensive_metrics.sharpe_ratio:.2f}")
print(f"Sortino Ratio: {comprehensive_metrics.sortino_ratio:.2f}")
print(f"Maximum Drawdown: {comprehensive_metrics.max_drawdown:.1%}")
print(f"Volatilitet: {comprehensive_metrics.volatility:.1%}")
print(f"Beta: {comprehensive_metrics.beta:.2f}")
print(f"Alpha: {comprehensive_metrics.alpha:.2f}")
print(f"Calmar Ratio: {comprehensive_metrics.calmar_ratio:.2f}")
print(f"VaR (95%): ${comprehensive_metrics.value_at_risk:.2f}")
print(f"Expected Shortfall: ${comprehensive_metrics.expected_shortfall:.2f}")

# Riskbedömning
if comprehensive_metrics.sharpe_ratio > 1.5:
    risk_rating = "UTMÄRKT"
elif comprehensive_metrics.sharpe_ratio > 1.0:
    risk_rating = "BRA"
elif comprehensive_metrics.sharpe_ratio > 0.5:
    risk_rating = "ACCEPTABEL"
else:
    risk_rating = "DÅLIG"

print(f"\nRisk Rating: {risk_rating}")
```

## 📊 Risk Metrics Interpretation

### Sharpe Ratio Skala
- **> 3.0**: Utmärkt riskjusterad avkastning
- **2.0 - 3.0**: Mycket bra
- **1.5 - 2.0**: Bra
- **1.0 - 1.5**: Acceptabel
- **0.5 - 1.0**: Marginal
- **< 0.5**: Dålig

### Sortino Ratio Skala
- **> 2.0**: Utmärkt downside risk management
- **1.5 - 2.0**: Mycket bra
- **1.0 - 1.5**: Bra
- **0.5 - 1.0**: Acceptabel
- **< 0.5**: Dålig

### Maximum Drawdown
- **< 10%**: Mycket låg risk
- **10-20%**: Låg till medium risk
- **20-30%**: Medium till hög risk
- **> 30%**: Mycket hög risk

### Beta Interpretation
- **< 0.8**: Defensiv (lägre volatilitet än marknaden)
- **0.8 - 1.2**: Neutral
- **> 1.2**: Offensiv (högre volatilitet än marknaden)

## ⚙️ Konfiguration och Parametrar

### Standardinställningar
```python
DEFAULT_CONFIG = {
    'risk_free_rate': 0.02,          # 2% riskfri ränta
    'periods_per_year': 365,         # Dagliga data
    'confidence_level': 0.95,        # 95% konfidens för VaR
    'benchmark_return': 0.08,        # 8% benchmark avkastning
    'efficient_frontier_points': 100  # Punkter på efficient frontier
}
```

### Risknivå-konfigurationer
```python
RISK_LEVEL_CONFIGS = {
    'conservative': {
        'min_sharpe': 1.5,
        'max_drawdown': 0.10,
        'max_volatility': 0.15,
        'min_diversification': 0.7
    },
    'moderate': {
        'min_sharpe': 1.0,
        'max_drawdown': 0.20,
        'max_volatility': 0.25,
        'min_diversification': 0.5
    },
    'aggressive': {
        'min_sharpe': 0.5,
        'max_drawdown': 0.35,
        'max_volatility': 0.40,
        'min_diversification': 0.3
    }
}
```

## 🔍 Avancerade Analyser

### Rolling Risk Metrics
```python
def calculate_rolling_risk_metrics(returns: pd.Series,
                                  window: int = 252,
                                  risk_free_rate: float = 0.02) -> pd.DataFrame:
    """
    Beräkna rullande riskmått över tid.

    Args:
        returns: Avkastningsserie
        window: Rullande fönster i perioder
        risk_free_rate: Riskfri ränta

    Returns:
        DataFrame med rullande metrics
    """
    analyzer = PortfolioRisk(risk_free_rate=risk_free_rate)

    rolling_metrics = pd.DataFrame(index=returns.index)

    # Rullande volatilitet
    rolling_metrics['volatility'] = returns.rolling(window=window).std() * np.sqrt(365)

    # Rullande Sharpe ratio
    excess_returns = returns - risk_free_rate / 365
    rolling_metrics['sharpe'] = (
        excess_returns.rolling(window=window).mean() /
        excess_returns.rolling(window=window).std()
    ) * np.sqrt(365)

    # Rullande maximum drawdown
    cumulative = (1 + returns).cumprod()
    rolling_peak = cumulative.expanding(min_periods=1).max()
    rolling_dd = (cumulative - rolling_peak) / rolling_peak
    rolling_metrics['max_drawdown'] = rolling_dd.rolling(window=window).min().abs()

    return rolling_metrics

# Användning
rolling_risk = calculate_rolling_risk_metrics(returns, window=63)  # 3 månader
print("Rullande Riskmått (senaste 10 perioder):")
print(rolling_risk.tail(10).round(4))
```

### Risk Attribution Analysis
```python
def analyze_risk_attribution(asset_returns: pd.DataFrame,
                           weights: np.ndarray,
                           benchmark_returns: pd.Series) -> Dict[str, float]:
    """
    Analysera riskbidrag per tillgång.

    Args:
        asset_returns: Tillgångsavkastningar
        weights: Portföljvikter
        benchmark_returns: Benchmark avkastningar

    Returns:
        Risk attribution per tillgång
    """
    analyzer = PortfolioRisk()

    # Beräkna portföljavkastningar
    portfolio_returns = asset_returns.dot(weights)

    # Risk attribution
    attribution = {}

    for i, asset in enumerate(asset_returns.columns):
        # Beräkna asset-specifik riskbidrag
        asset_contribution = weights[i] * (
            asset_returns[asset].var() +
            2 * weights[i] * asset_returns[asset].cov(portfolio_returns - asset_returns[asset] * weights[i])
        )

        attribution[asset] = asset_contribution

    # Normalisera till procent
    total_risk = sum(attribution.values())
    for asset in attribution:
        attribution[asset] = attribution[asset] / total_risk

    return attribution

# Användning
weights = np.array([0.4, 0.3, 0.2, 0.1])  # BTC, ETH, ADA, DOT
benchmark = market_series

risk_attribution = analyze_risk_attribution(asset_returns, weights, benchmark)
print("Risk Attribution per Tillgång:")
for asset, contribution in risk_attribution.items():
    print(f"  {asset}: {contribution:.1%}")
```

## 🧪 Validering och Backtesting

### Risk Model Validering
```python
def validate_risk_model(actual_returns: np.ndarray,
                       predicted_volatility: np.ndarray,
                       confidence_level: float = 0.95) -> Dict[str, float]:
    """
    Validera riskmodellens noggrannhet.

    Args:
        actual_returns: Faktiska avkastningar
        predicted_volatility: Predicerad volatilitet
        confidence_level: Konfidensnivå

    Returns:
        Valideringsstatistik
    """
    # Beräkna förväntade vs. faktiska VaR överskridanden
    z_score = stats.norm.ppf(1 - confidence_level)
    expected_var = -predicted_volatility * z_score

    violations = np.sum(actual_returns < expected_var)
    expected_violations = (1 - confidence_level) * len(actual_returns)

    # Kupiec's test för oberoende överskridanden
    if violations == 0:
        p_value = 1.0
    else:
        likelihood_ratio = -2 * (
            expected_violations * np.log(expected_violations / violations) +
            (len(actual_returns) - expected_violations) * np.log(
                (len(actual_returns) - expected_violations) /
                (len(actual_returns) - violations)
            )
        )
        p_value = 1 - stats.chi2.cdf(likelihood_ratio, 1)

    return {
        'violations': violations,
        'expected_violations': expected_violations,
        'violation_rate': violations / len(actual_returns),
        'expected_rate': 1 - confidence_level,
        'kupiec_p_value': p_value,
        'model_adequate': p_value > 0.05  # 5% signifikansnivå
    }

# Användning
validation_results = validate_risk_model(returns, np.full_like(returns, 0.02))
print("Risk Model Validation:")
print(f"  Violations: {validation_results['violations']}")
print(f"  Expected: {validation_results['expected_violations']:.1f}")
print(f"  Model Adequate: {validation_results['model_adequate']}")
```

## 📈 Prestandaoptimering

### Vektoriserade Beräkningar
```python
def optimized_sharpe_calculation(returns: np.ndarray,
                               risk_free_rate: float = 0.02) -> float:
    """
    Optimerad Sharpe ratio beräkning med numpy-vektorisering.
    """
    # Beräkna alla metrics på en gång
    excess_returns = returns - risk_free_rate / 365

    # Använd numpy's built-in funktioner för bättre prestanda
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    return (mean_excess / std_excess) * np.sqrt(365)
```

### Cache-strategier
```python
from functools import lru_cache
import hashlib

class CachedPortfolioRisk(PortfolioRisk):
    @lru_cache(maxsize=128)
    def _cached_covariance_calculation(self, returns_hash: str, annualize: bool) -> pd.DataFrame:
        """Cache kovariansberäkningar."""
        # Implementation för cache
        pass

    def calculate_covariance_matrix(self, asset_returns: pd.DataFrame, annualize: bool = True):
        """Cached version."""
        returns_str = str(asset_returns.values.tobytes())
        cache_key = hashlib.md5(returns_str.encode()).hexdigest()

        return self._cached_covariance_calculation(cache_key, annualize)
```

## 🔗 Integrationer

### Med VaR Calculator
```python
# Integration för komplett riskanalys
def comprehensive_risk_analysis(returns: pd.Series,
                              portfolio_values: pd.Series,
                              market_returns: pd.Series) -> Dict[str, Any]:
    """
    Kombinera Portfolio Risk med VaR Calculator.
    """
    from core.var_calculator import VaRCalculator

    portfolio_analyzer = PortfolioRisk()
    var_calculator = VaRCalculator()

    # Grundläggande metrics
    sharpe = portfolio_analyzer.calculate_sharpe_ratio(returns)
    max_dd = portfolio_analyzer.calculate_max_drawdown(portfolio_values)
    beta = portfolio_analyzer.calculate_beta(returns, market_returns)

    # VaR calculations
    var_95 = var_calculator.calculate_historical_var(returns, portfolio_values.iloc[-1])
    es_95 = var_calculator.calculate_expected_shortfall(returns, portfolio_values.iloc[-1])

    return {
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'beta': beta,
        'var_95': var_95,
        'expected_shortfall': es_95,
        'risk_adjusted_score': sharpe / (1 + abs(max_dd))
    }
```

### Med Position Sizer
```python
# Integration för riskjusterade position sizes
def risk_adjusted_position_sizing(asset_returns: pd.DataFrame,
                                current_weights: np.ndarray,
                                target_volatility: float) -> np.ndarray:
    """
    Beräkna optimala vikter baserat på risk metrics.
    """
    from core.position_sizer import PositionSizer

    sizer = PositionSizer()
    analyzer = PortfolioRisk()

    # Beräkna nuvarande risk metrics
    portfolio_returns = asset_returns.dot(current_weights)
    current_volatility = analyzer.calculate_portfolio_volatility(
        current_weights, asset_returns.cov()
    )

    # Justera vikter för målvolatilitet
    if current_volatility > target_volatility:
        # Minska risk genom att minska vikter i volatila tillgångar
        volatilities = asset_returns.std()
        risk_adjustments = 1 - (volatilities / volatilities.max()) * 0.5
        new_weights = current_weights * risk_adjustments
        new_weights = new_weights / new_weights.sum()
    else:
        # Öka risk genom att öka vikter i mindre volatila tillgångar
        volatilities = asset_returns.std()
        risk_adjustments = 1 + (1 - volatilities / volatilities.max()) * 0.5
        new_weights = current_weights * risk_adjustments
        new_weights = new_weights / new_weights.sum()

    return new_weights
```

## 🧪 Tester och Validering

### Unit Tests
```python
def test_sharpe_ratio():
    """Test Sharpe ratio calculations."""
    analyzer = PortfolioRisk(risk_free_rate=0.02)

    # Test data
    returns = np.array([0.01, 0.02, -0.01, 0.015, -0.005])

    sharpe = analyzer.calculate_sharpe_ratio(returns, annualize=False)

    # Expected calculation
    excess_returns = returns - 0.02 / 365
    expected_sharpe = excess_returns.mean() / excess_returns.std()

    assert abs(sharpe - expected_sharpe) < 1e-6

def test_max_drawdown():
    """Test maximum drawdown calculations."""
    analyzer = PortfolioRisk()

    # Create portfolio values with known drawdown
    values = np.array([100, 110, 95, 105, 90, 100])  # 15% max drawdown

    max_dd = analyzer.calculate_max_drawdown(values)

    assert abs(max_dd - 0.15) < 1e-6  # Should be 15%

def test_beta_calculation():
    """Test beta calculations."""
    analyzer = PortfolioRisk()

    # Create correlated data
    market = np.array([0.01, 0.02, -0.01, 0.015])
    portfolio = np.array([0.012, 0.025, -0.008, 0.018])  # Beta ≈ 1.2

    beta = analyzer.calculate_beta(portfolio, market)

    assert 1.15 < beta < 1.25  # Should be approximately 1.2
```

### Integration Tests
```python
def test_comprehensive_metrics():
    """Test comprehensive risk metrics calculation."""
    analyzer = PortfolioRisk()

    # Generate test data
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 252)
    portfolio_values = 100000 * np.exp(np.cumsum(returns))
    market_returns = np.random.normal(0.0008, 0.015, 252)

    # Calculate comprehensive metrics
    metrics = analyzer.get_comprehensive_risk_metrics(
        returns, portfolio_values, market_returns
    )

    # Verify all metrics are calculated
    assert hasattr(metrics, 'sharpe_ratio')
    assert hasattr(metrics, 'sortino_ratio')
    assert hasattr(metrics, 'max_drawdown')
    assert hasattr(metrics, 'volatility')
    assert hasattr(metrics, 'beta')
    assert hasattr(metrics, 'alpha')
    assert hasattr(metrics, 'value_at_risk')
    assert hasattr(metrics, 'expected_shortfall')

    # Verify reasonable ranges
    assert -5 < metrics.sharpe_ratio < 5
    assert 0 <= metrics.max_drawdown <= 1
    assert -2 < metrics.beta < 2
    assert metrics.value_at_risk < 0  # Loss
    assert metrics.expected_shortfall < metrics.value_at_risk  # More extreme

def test_efficient_frontier():
    """Test efficient frontier calculations."""
    analyzer = PortfolioRisk()

    # Create test asset data
    np.random.seed(42)
    asset_returns = pd.DataFrame({
        'A': np.random.normal(0.001, 0.02, 252),
        'B': np.random.normal(0.001, 0.025, 252),
        'C': np.random.normal(0.001, 0.015, 252),
        'D': np.random.normal(0.001, 0.03, 252)
    })

    # Calculate efficient frontier
    returns_array, vol_array, weights_array = analyzer.calculate_efficient_frontier(
        asset_returns, num_portfolios=50
    )

    # Verify shapes
    assert len(returns_array) == 50
    assert len(vol_array) == 50
    assert weights_array.shape == (50, 4)  # 50 portfolios, 4 assets

    # Verify weights sum to 1
    for weights in weights_array:
        assert abs(np.sum(weights) - 1.0) < 1e-6

    # Verify non-negative weights
    assert np.all(weights_array >= -1e-6)  # Allow small numerical errors
```

## 📚 Referenser

1. **"Modern Portfolio Theory and Investment Analysis" - Edwin J. Elton** - Grundläggande portföljteori
2. **"Active Portfolio Management" - Richard C. Grinold & Ronald N. Kahn** - Avancerad portföljhantering
3. **"The Sharpe Ratio" - William F. Sharpe** - Ursprungliga Sharpe artikeln
4. **"Sortino: A 'Sharper' Ratio" - Frank A. Sortino** - Sortino ratio förklaring
5. **"Portfolio Selection" - Harry Markowitz** - Modern portföljteori

---

*Portfolio Risk är den analytiska kärnan som tillhandahåller alla nödvändiga riskmått för professionell portföljhantering och prestationsanalys.*