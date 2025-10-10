# 📚 API Reference - Risk Management System

Komplett teknisk dokumentation för alla klasser, metoder och funktioner i Risk Management System.

## 📦 Core Components

### VaRCalculator

```python
class VaRCalculator:
    """Value-at-Risk beräkningsmotor med flera metoder."""
```

#### Konstruktor
```python
__init__(self, confidence_level: float = 0.95, time_horizon: int = 1)
```

**Parametrar:**
- `confidence_level` (float): Konfidensnivå för VaR (0-1), default 0.95
- `time_horizon` (int): Tidsperiod i dagar, default 1

#### Metoder

##### `calculate_historical_var()`
```python
def calculate_historical_var(self,
                            returns: Union[pd.Series, np.ndarray],
                            portfolio_value: float,
                            lookback_periods: Optional[int] = None) -> float
```

**Beräknar historisk VaR med empirisk fördelning.**

**Parametrar:**
- `returns`: Historiska avkastningar (dagliga)
- `portfolio_value`: Nuvarande portföljvärde
- `lookback_periods`: Antal perioder att använda (optional)

**Returnerar:** Historisk VaR-värde (negativt för förlust)

---

##### `calculate_parametric_var()`
```python
def calculate_parametric_var(self,
                            returns: Union[pd.Series, np.ndarray],
                            portfolio_value: float,
                            lookback_periods: Optional[int] = None) -> float
```

**Beräknar parametrisk VaR med normalfördelningsantagande.**

**Parametrar:**
- `returns`: Historiska avkastningar
- `portfolio_value`: Portföljvärde
- `lookback_periods`: Lookback-perioder (optional)

**Returnerar:** Parametrisk VaR-värde

---

##### `calculate_monte_carlo_var()`
```python
def calculate_monte_carlo_var(self,
                             returns: Union[pd.Series, np.ndarray],
                             portfolio_value: float,
                             simulations: int = 10000,
                             lookback_periods: Optional[int] = None) -> float
```

**Beräknar Monte Carlo VaR genom simulering.**

**Parametrar:**
- `returns`: Historiska avkastningar
- `portfolio_value`: Portföljvärde
- `simulations`: Antal simuleringar (default: 10,000)
- `lookback_periods`: Lookback-perioder (optional)

**Returnerar:** Monte Carlo VaR-värde

---

##### `calculate_expected_shortfall()`
```python
def calculate_expected_shortfall(self,
                                returns: Union[pd.Series, np.ndarray],
                                portfolio_value: float,
                                method: str = 'historical',
                                lookback_periods: Optional[int] = None) -> float
```

**Beräknar Expected Shortfall (CVaR).**

**Parametrar:**
- `returns`: Historiska avkastningar
- `portfolio_value`: Portföljvärde
- `method`: Beräkningsmetod ('historical', 'parametric', 'monte_carlo')
- `lookback_periods`: Lookback-perioder (optional)

**Returnerar:** Expected Shortfall-värde

---

##### `calculate_var_contribution()`
```python
def calculate_var_contribution(self,
                              asset_returns: pd.DataFrame,
                              weights: np.ndarray,
                              portfolio_value: float,
                              method: str = 'parametric') -> np.ndarray
```

**Beräknar individuella tillgångars bidrag till portfölj-VaR.**

**Parametrar:**
- `asset_returns`: DataFrame med tillgångsavkastningar
- `weights`: Portföljvikter
- `portfolio_value`: Portföljvärde
- `method`: VaR-metod ('parametric', 'historical')

**Returnerar:** Array med VaR-bidrag per tillgång

## 📏 Position Sizer

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
- `max_portfolio_risk`: Maximum risk per trade (default: 0.02)
- `max_single_position`: Maximum single position size (default: 0.10)
- `risk_free_rate`: Risk-free rate (default: 0.02)

#### Metoder

##### `kelly_criterion()`
```python
def kelly_criterion(self,
                   win_rate: float,
                   avg_win_return: float,
                   avg_loss_return: float,
                   current_portfolio: float) -> Dict[str, float]
```

**Beräknar Kelly Criterion optimal position size.**

**Parametrar:**
- `win_rate`: Sannolikhet för vinst (0-1)
- `avg_win_return`: Genomsnittlig vinstavkastning
- `avg_loss_return`: Genomsnittlig förlustavkastning
- `current_portfolio`: Nuvarande portföljvärde

**Returnerar:** Dictionary med Kelly-resultat

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
- `portfolio_value`: Portföljvärde
- `risk_per_trade`: Risk per trade (optional)
- `volatility`: Asset volatility (optional)

**Returnerar:** Position size som fraction

---

##### `risk_parity_allocation()`
```python
def risk_parity_allocation(self,
                          asset_returns: pd.DataFrame,
                          target_volatility: Optional[float] = None) -> Dict[str, float]
```

**Beräknar Risk Parity allocation weights.**

**Parametrar:**
- `asset_returns`: Historiska tillgångsavkastningar
- `target_volatility`: Målord volatilitet (optional)

**Returnerar:** Dictionary med asset weights

## 🛡️ Risk Manager

```python
class RiskManager:
    """Risk management med stop-loss, take-profit och limit controls."""
```

#### Konstruktor
```python
__init__(self, risk_limits: Optional[RiskLimits] = None)
```

**Parametrar:**
- `risk_limits`: Risk limits configuration (optional)

#### Metoder

##### `add_position()`
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
- `token`: Asset token
- `entry_price`: Entry price
- `quantity`: Position quantity
- `stop_loss_percentage`: Stop loss som percentage
- `take_profit_percentage`: Take profit som percentage
- `trailing_stop`: Enable trailing stop
- `trailing_percentage`: Trailing stop percentage

**Returnerar:** True om position tillagd

---

##### `update_position_price()`
```python
def update_position_price(self, token: str, current_price: float) -> Dict[str, bool]
```

**Uppdaterar position med nya priser och checkar triggers.**

**Parametrar:**
- `token`: Asset token
- `current_price`: Current market price

**Returnerar:** Dictionary med aktiverade triggers

---

##### `check_daily_risk_limits()`
```python
def check_daily_risk_limits() -> bool
```

**Checkar om dagliga riskgränser överskridits.**

**Returnerar:** True om gränser överskridna

---

##### `emergency_stop()`
```python
def emergency_stop(self, reason: str = "Manual emergency stop")
```

**Triggerar emergency stop för alla positioner.**

**Parametrar:**
- `reason`: Anledning till emergency stop

## 📊 Portfolio Risk Analytics

```python
class PortfolioRisk:
    """Avancerade portfölj-riskmått och prestationsanalys."""
```

#### Konstruktor
```python
__init__(self, risk_free_rate: float = 0.02, periods_per_year: int = 365)
```

**Parametrar:**
- `risk_free_rate`: Risk-free rate (default: 0.02)
- `periods_per_year`: Perioder per år (default: 365)

#### Metoder

##### `calculate_sharpe_ratio()`
```python
def calculate_sharpe_ratio(self,
                          returns: Union[pd.Series, np.ndarray],
                          annualize: bool = True) -> float
```

**Beräknar Sharpe ratio.**

**Parametrar:**
- `returns`: Portfolio returns
- `annualize`: Whether to annualize ratio

**Returnerar:** Sharpe ratio

---

##### `calculate_sortino_ratio()`
```python
def calculate_sortino_ratio(self,
                           returns: Union[pd.Series, np.ndarray],
                           annualize: bool = True) -> float
```

**Beräknar Sortino ratio (downside risk).**

**Parametrar:**
- `returns`: Portfolio returns
- `annualize`: Whether to annualize ratio

**Returnerar:** Sortino ratio

---

##### `calculate_max_drawdown()`
```python
def calculate_max_drawdown(self,
                          portfolio_values: Union[pd.Series, np.ndarray]) -> float
```

**Beräknar maximum drawdown.**

**Parametrar:**
- `portfolio_values`: Portfolio values over time

**Returnerar:** Maximum drawdown (decimal)

---

##### `calculate_beta()`
```python
def calculate_beta(self,
                  portfolio_returns: Union[pd.Series, np.ndarray],
                  market_returns: Union[pd.Series, np.ndarray]) -> float
```

**Beräknar portfolio beta relativt market.**

**Parametrar:**
- `portfolio_returns`: Portfolio returns
- `market_returns`: Market/benchmark returns

**Returnerar:** Portfolio beta

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
- `portfolio_returns`: Portfolio returns series
- `portfolio_values`: Portfolio values over time
- `market_returns`: Market returns (optional)
- `confidence_level`: Confidence level for VaR

**Returnerar:** RiskMetrics dataclass

## 🎛️ Risk Handler

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
- `risk_limits`: Risk limits configuration
- `confidence_level`: VaR confidence level
- `risk_free_rate`: Risk-free rate

#### Metoder

##### `assess_portfolio_risk()`
```python
async def assess_portfolio_risk(self,
                               portfolio: Dict[str, float],
                               current_prices: Dict[str, float],
                               historical_data: Optional[Dict[str, pd.DataFrame]] = None) -> RiskAssessment
```

**Genomför omfattande portfölj-riskbedömning.**

**Parametrar:**
- `portfolio`: Current portfolio positions
- `current_prices`: Current asset prices
- `historical_data`: Historical price data (optional)

**Returnerar:** RiskAssessment dataclass

---

##### `calculate_optimal_position_size()`
```python
async def calculate_optimal_position_size(self,
                                        token: str,
                                        entry_price: float,
                                        portfolio_value: float,
                                        risk_tolerance: float = 0.02,
                                        method: str = 'kelly',
                                        **kwargs) -> Dict[str, Any]
```

**Beräknar optimal position size.**

**Parametrar:**
- `token`: Asset token
- `entry_price`: Expected entry price
- `portfolio_value`: Current portfolio value
- `risk_tolerance`: Maximum risk per trade
- `method`: Sizing method ('kelly', 'fixed_fractional', 'risk_parity')
- `**kwargs`: Additional method-specific parameters

**Returnerar:** Dictionary med sizing results

---

##### `setup_risk_management()`
```python
async def setup_risk_management(self,
                               token: str,
                               entry_price: float,
                               quantity: float,
                               stop_loss_percentage: float = 0.05,
                               take_profit_percentage: float = 0.10,
                               trailing_stop: bool = False) -> bool
```

**Sätter upp risk management för position.**

**Parametrar:**
- `token`: Asset token
- `entry_price`: Entry price
- `quantity`: Position quantity
- `stop_loss_percentage`: Stop loss percentage
- `take_profit_percentage`: Take profit percentage
- `trailing_stop`: Enable trailing stop

**Returnerar:** True om setup lyckades

---

##### `update_position_prices()`
```python
async def update_position_prices(self,
                               price_updates: Dict[str, float]) -> Dict[str, Dict[str, bool]]
```

**Uppdaterar positioner med nya priser.**

**Parametrar:**
- `price_updates`: {token: current_price}

**Returnerar:** Dictionary med aktiverade triggers per position

---

##### `get_portfolio_risk_profile()`
```python
async def get_portfolio_risk_profile(self,
                                    portfolio: Dict[str, float],
                                    historical_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]
```

**Hämtar detaljerad portfölj-riskprofil.**

**Parametrar:**
- `portfolio`: Current portfolio positions
- `historical_data`: Historical price data (optional)

**Returnerar:** Dictionary med risk profile

---

##### `start_risk_monitoring()`
```python
async def start_risk_monitoring(self)
```

**Startar kontinuerlig risk monitoring.**

---

##### `stop_risk_monitoring()`
```python
async def stop_risk_monitoring()
```

**Stoppar risk monitoring.**

## 📋 Data Structures

### RiskLimits
```python
@dataclass
class RiskLimits:
    max_daily_loss: float = 0.05        # 5% max daily loss
    max_single_position: float = 0.10   # 10% max single position
    max_portfolio_var: float = 0.15     # 15% max portfolio VaR
    max_correlation: float = 0.8        # Max correlation threshold
    max_concentration: float = 0.25     # 25% max concentration
```

### RiskAssessment
```python
@dataclass
class RiskAssessment:
    overall_risk_level: str              # 'low', 'medium', 'high', 'critical'
    var_95: float                        # 95% VaR value
    expected_shortfall: float            # Expected shortfall
    sharpe_ratio: float                  # Sharpe ratio
    max_drawdown: float                  # Maximum drawdown
    concentration_risk: float           # Concentration risk score
    correlation_risk: float             # Correlation risk score
    position_limit_breached: bool       # Position limit status
    daily_loss_limit_breached: bool     # Daily loss limit status
    recommendations: List[str]          # Risk management recommendations
    alerts: List[Dict[str, Any]]        # Active risk alerts
```

### RiskMetrics
```python
@dataclass
class RiskMetrics:
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    beta: float
    alpha: float
    calmar_ratio: float
    information_ratio: float
    value_at_risk: float
    expected_shortfall: float
```

### PositionRiskProfile
```python
@dataclass
class PositionRiskProfile:
    token: str
    position_size: float
    stop_loss_distance: float
    take_profit_distance: float
    unrealized_pnl: float
    risk_contribution: float
    correlation_to_portfolio: float
    volatility: float
```

## 🚀 Utility Functions

### `calculate_portfolio_var()`
```python
def calculate_portfolio_var(returns: pd.DataFrame,
                           weights: np.ndarray,
                           confidence_level: float = 0.95,
                           method: str = 'parametric') -> float
```

**Beräknar portfölj-VaR från komponenter.**

**Parametrar:**
- `returns`: Asset returns DataFrame
- `weights`: Portfolio weights
- `confidence_level`: Confidence level
- `method`: Calculation method

**Returnerar:** Portfolio VaR

### `optimize_portfolio_with_pyportfolioopt()`
```python
def optimize_portfolio_with_pyportfolioopt(asset_returns: pd.DataFrame,
                                          method: str = 'max_sharpe',
                                          bounds: Tuple[float, float] = (0, 0.2)) -> Dict[str, float]
```

**Optimerar portfölj med pyportfolioopt.**

**Parametrar:**
- `asset_returns`: Historical asset returns
- `method`: Optimization method
- `bounds`: Weight bounds per asset

**Returnerar:** Optimal weights dictionary

### `calculate_rolling_risk_metrics()`
```python
def calculate_rolling_risk_metrics(returns: pd.Series,
                                  window: int = 252,
                                  risk_free_rate: float = 0.02) -> pd.DataFrame
```

**Beräknar rullande riskmått.**

**Parametrar:**
- `returns`: Returns series
- `window`: Rolling window size
- `risk_free_rate`: Risk-free rate

**Returnerar:** DataFrame med rullande metrics

## 🔧 Exception Handling

### TradingError
```python
class TradingError(Exception):
    """Base exception för trading-relaterade fel."""
    pass
```

### RiskError
```python
class RiskError(TradingError):
    """Exception för risk management-relaterade fel."""
    pass
```

### ValidationError
```python
class ValidationError(RiskError):
    """Exception för valideringsfel."""
    pass
```

## 📊 Constants

### Standardvärden
```python
DEFAULT_CONFIDENCE_LEVEL = 0.95
DEFAULT_TIME_HORIZON = 1
DEFAULT_RISK_FREE_RATE = 0.02
DEFAULT_MAX_DAILY_LOSS = 0.05
DEFAULT_MAX_SINGLE_POSITION = 0.10
DEFAULT_MAX_PORTFOLIO_VAR = 0.15
```

### Risknivåer
```python
RISK_LEVELS = {
    'low': {'max_var': 0.05, 'max_drawdown': 0.10},
    'medium': {'max_var': 0.10, 'max_drawdown': 0.15},
    'high': {'max_var': 0.20, 'max_drawdown': 0.25},
    'critical': {'max_var': 0.30, 'max_drawdown': 0.35}
}
```

### Alert Severity
```python
ALERT_SEVERITY = {
    'info': 1,
    'warning': 2,
    'critical': 3,
    'emergency': 4
}
```

## 🔗 Dependencies

### Required Packages
- `numpy>=1.21.0`
- `pandas>=1.5.0`
- `scipy>=1.9.0`
- `pyportfolioopt>=1.5.0`

### Optional Packages
- `matplotlib>=3.5.0` (för visualisering)
- `plotly>=5.0.0` (för interaktiva diagram)
- `numba` (för prestandaoptimering)

## 📈 Performance Characteristics

### Time Complexity
- **VaR Calculation**: O(n) för historisk, O(1) för parametrisk
- **Monte Carlo**: O(simulations × time_horizon)
- **Portfolio Optimization**: O(n³) för standard metoder
- **Risk Assessment**: O(n²) för korrelationsanalys

### Space Complexity
- **VaR Calculator**: O(n) för historiska data
- **Position Sizer**: O(1) per beräkning
- **Risk Manager**: O(p) för p positioner
- **Portfolio Risk**: O(n × m) för n tillgångar, m perioder

### Memory Usage
- **Baseline**: ~50MB för typisk användning
- **Monte Carlo**: +100MB per 10k simuleringar
- **Historical Data**: +10MB per år historiska data

---

*Denna API-referens täcker alla publika metoder och klasser. För interna implementationer, se källkoden.*