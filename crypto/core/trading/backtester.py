"""
Backtesting Framework för XGBoost Trading Modeller

Implementerar omfattande backtesting av ML-baserade trading strategier
med olika risk management tekniker och prestandamätningar.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from .trading.xgboost_trader import XGBoostTradingModel
from ..analytics.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class TradeType(Enum):
    """Typer av trades"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Trade:
    """Representerar en enskild trade"""
    timestamp: datetime
    trade_type: TradeType
    price: float
    quantity: float
    confidence: float
    reason: str = ""


@dataclass
class BacktestResult:
    """Resultat från backtest"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    max_win: float
    max_loss: float
    calmar_ratio: float
    sortino_ratio: float


class Backtester:
    """
    Omfattande backtesting framework för ML-baserade trading strategier

    Testar modellens prestanda på historiska data med realistiska
    handelsvillkor, slippage, och risk management.
    """

    def __init__(self,
                 model: XGBoostTradingModel,
                 initial_capital: float = 10000.0,
                 commission: float = 0.001,  # 0.1%
                 slippage: float = 0.0005,  # 0.05%
                 max_position_size: float = 0.1):  # Max 10% av kapital

        self.model = model
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.max_position_size = max_position_size

        # Trading state
        self.capital = initial_capital
        self.position = 0.0  # Antal tokens
        self.position_value = 0.0
        self.entry_price = 0.0
        self.trades: List[Trade] = []
        self.portfolio_values: List[Tuple[datetime, float]] = []
        self.current_timestamp: Optional[datetime] = None

        # Risk management
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.take_profit_pct = 0.10  # 10% take profit
        self.max_drawdown_limit = 0.20  # 20% max drawdown

    def run_backtest(self,
                    historical_data: pd.DataFrame,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    confidence_threshold: float = 0.6) -> BacktestResult:
        """
        Kör backtest på historiska data

        Args:
            historical_data: DataFrame med OHLCV data
            start_date: Startdatum för backtest (YYYY-MM-DD)
            end_date: Slutdatum för backtest (YYYY-MM-DD)
            confidence_threshold: Minsta confidence för trades

        Returns:
            BacktestResult med detaljerade metrics
        """
        try:
            # Förbered data
            if start_date:
                historical_data = historical_data[historical_data.index >= start_date]
            if end_date:
                historical_data = historical_data[historical_data.index <= end_date]

            if len(historical_data) < 100:
                raise ValueError("Otillräckligt med data för backtest")

            # Skapa features
            feature_engineer = FeatureEngineer()
            features = feature_engineer.create_trading_features(historical_data)

            # Rensa features från NaN
            features = features.dropna()

            # Initiera backtest
            self._reset_backtest()

            # Kör genom varje timestep
            for i, (timestamp, row) in enumerate(features.iterrows()):
                self.current_timestamp = timestamp
                current_price = historical_data.loc[timestamp, 'close']

                # Uppdatera portfolio värde
                self._update_portfolio_value(current_price, timestamp)

                # Generera signal
                signal_data = self.model.generate_trading_signal(
                    features.iloc[i:i+1],
                    confidence_threshold=confidence_threshold
                )

                # Utför trade baserat på signal
                self._execute_signal(signal_data, current_price, timestamp)

                # Risk management checks
                self._check_risk_limits(current_price)

            # Beräkna slutgiltiga metrics
            return self._calculate_metrics()

        except Exception as e:
            logger.error(f"Fel vid backtest: {str(e)}")
            raise

    def _execute_signal(self, signal_data: Dict[str, Any], price: float, timestamp: datetime):
        """Utför trade baserat på signal"""
        signal = signal_data['signal']
        confidence = signal_data['confidence']

        if signal == 'BUY' and self.position == 0:
            # Öppna long position
            position_size = self._calculate_position_size(price, confidence)
            if position_size > 0:
                actual_price = price * (1 + self.slippage)  # Köp till högre pris
                commission_cost = position_size * actual_price * self.commission

                if self.capital >= (position_size * actual_price + commission_cost):
                    self.position = position_size
                    self.entry_price = actual_price
                    self.capital -= (position_size * actual_price + commission_cost)
                    self.position_value = self.position * actual_price

                    self.trades.append(Trade(
                        timestamp=timestamp,
                        trade_type=TradeType.BUY,
                        price=actual_price,
                        quantity=position_size,
                        confidence=confidence,
                        reason=f"ML Signal: {confidence:.2f}"
                    ))

                    logger.debug(f"Opened long position: {position_size} @ {actual_price}")

        elif signal == 'SELL' and self.position > 0:
            # Stäng long position
            actual_price = price * (1 - self.slippage)  # Sälj till lägre pris
            commission_cost = self.position * actual_price * self.commission

            proceeds = self.position * actual_price - commission_cost
            self.capital += proceeds
            profit_loss = proceeds - (self.position * self.entry_price + self.position * self.entry_price * self.commission)

            self.trades.append(Trade(
                timestamp=timestamp,
                trade_type=TradeType.SELL,
                price=actual_price,
                quantity=self.position,
                confidence=confidence,
                reason=f"ML Signal: {confidence:.2f}, P&L: {profit_loss:.2f}"
            ))

            self.position = 0.0
            self.position_value = 0.0
            self.entry_price = 0.0

            logger.debug(f"Closed long position: P&L = {profit_loss:.2f}")

    def _calculate_position_size(self, price: float, confidence: float) -> float:
        """Beräkna position size baserat på confidence och risk limits"""
        # Bas position size på confidence
        base_size = self.capital * self.max_position_size * confidence

        # Risk-justera
        risk_adjusted_size = base_size * (1 - self._calculate_current_risk())

        # Säkerställ att vi inte överskrider kapital
        max_affordable = self.capital * 0.95 / price  # Lämna 5% buffert

        return min(risk_adjusted_size, max_affordable, base_size)

    def _calculate_current_risk(self) -> float:
        """Beräkna nuvarande risk nivå"""
        if len(self.portfolio_values) < 2:
            return 0.0

        # Beräkna drawdown
        current_value = self.capital + self.position_value
        peak_value = max([v for _, v in self.portfolio_values])

        if peak_value == 0:
            return 0.0

        drawdown = (peak_value - current_value) / peak_value
        return min(drawdown, 1.0)  # Cap at 100%

    def _check_risk_limits(self, current_price: float):
        """Kontrollera risk limits och stäng positioner om nödvändigt"""
        if self.position == 0:
            return

        # Stop loss check
        loss_pct = (self.entry_price - current_price) / self.entry_price
        if loss_pct >= self.stop_loss_pct:
            self._force_close_position(current_price, "Stop Loss")
            return

        # Take profit check
        profit_pct = (current_price - self.entry_price) / self.entry_price
        if profit_pct >= self.take_profit_pct:
            self._force_close_position(current_price, "Take Profit")
            return

    def _force_close_position(self, price: float, reason: str):
        """Tvingad stängning av position"""
        if self.position == 0:
            return

        actual_price = price * (1 - self.slippage)
        commission_cost = self.position * actual_price * self.commission

        proceeds = self.position * actual_price - commission_cost
        self.capital += proceeds

        self.trades.append(Trade(
            timestamp=self.current_timestamp,
            trade_type=TradeType.SELL,
            price=actual_price,
            quantity=self.position,
            confidence=0.0,
            reason=f"Forced close: {reason}"
        ))

        self.position = 0.0
        self.position_value = 0.0
        self.entry_price = 0.0

    def _update_portfolio_value(self, current_price: float, timestamp: datetime):
        """Uppdatera portfolio värde"""
        total_value = self.capital + (self.position * current_price)
        self.portfolio_values.append((timestamp, total_value))

    def _calculate_metrics(self) -> BacktestResult:
        """Beräkna detaljerade backtest metrics"""
        if not self.portfolio_values:
            return BacktestResult(
                total_return=0.0,
                annualized_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0.0,
                avg_loss=0.0,
                max_win=0.0,
                max_loss=0.0,
                calmar_ratio=0.0,
                sortino_ratio=0.0
            )

        # Beräkna returns
        portfolio_values = pd.Series([v for _, v in self.portfolio_values])
        returns = portfolio_values.pct_change().dropna()

        # Grundläggande metrics
        total_return = (portfolio_values.iloc[-1] - self.initial_capital) / self.initial_capital

        # Annualisering (antar daglig data)
        days = len(returns)
        if days > 0:
            annualized_return = (1 + total_return) ** (365 / days) - 1
        else:
            annualized_return = 0.0

        # Volatilitet och Sharpe ratio
        volatility = returns.std() * np.sqrt(365) if len(returns) > 0 else 0.0
        risk_free_rate = 0.02  # 2% riskfri ränta
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0.0

        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = drawdowns.min()

        # Trade metrics
        winning_trades = [t for t in self.trades if t.trade_type == TradeType.SELL and
                         hasattr(t, 'profit_loss') and getattr(t, 'profit_loss', 0) > 0]
        losing_trades = [t for t in self.trades if t.trade_type == TradeType.SELL and
                        hasattr(t, 'profit_loss') and getattr(t, 'profit_loss', 0) <= 0]

        total_trades = len([t for t in self.trades if t.trade_type == TradeType.SELL])
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0

        # Profit metrics
        if winning_trades:
            profits = [getattr(t, 'profit_loss', 0) for t in winning_trades if hasattr(t, 'profit_loss')]
            avg_win = np.mean(profits) if profits else 0.0
            max_win = max(profits) if profits else 0.0
        else:
            avg_win = 0.0
            max_win = 0.0

        if losing_trades:
            losses = [abs(getattr(t, 'profit_loss', 0)) for t in losing_trades if hasattr(t, 'profit_loss')]
            avg_loss = np.mean(losses) if losses else 0.0
            max_loss = max(losses) if losses else 0.0
        else:
            avg_loss = 0.0
            max_loss = 0.0

        # Profit factor
        total_profit = sum(getattr(t, 'profit_loss', 0) for t in winning_trades if hasattr(t, 'profit_loss'))
        total_loss = sum(abs(getattr(t, 'profit_loss', 0)) for t in losing_trades if hasattr(t, 'profit_loss'))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')

        # Calmar och Sortino ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

        # Sortino ratio (endast downside volatility)
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(365) if len(downside_returns) > 0 else 0.0
        sortino_ratio = (annualized_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0.0

        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_win=max_win,
            max_loss=max_loss,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio
        )

    def _reset_backtest(self):
        """Återställ backtest state"""
        self.capital = self.initial_capital
        self.position = 0.0
        self.position_value = 0.0
        self.entry_price = 0.0
        self.trades = []
        self.portfolio_values = []

    def get_trades_df(self) -> pd.DataFrame:
        """Returnera trades som DataFrame"""
        if not self.trades:
            return pd.DataFrame()

        trades_data = []
        for trade in self.trades:
            trade_dict = {
                'timestamp': trade.timestamp,
                'type': trade.trade_type.value,
                'price': trade.price,
                'quantity': trade.quantity,
                'value': trade.price * trade.quantity,
                'confidence': trade.confidence,
                'reason': trade.reason
            }
            trades_data.append(trade_dict)

        return pd.DataFrame(trades_data)

    def get_portfolio_history(self) -> pd.DataFrame:
        """Returnera portfolio värdehistorik"""
        if not self.portfolio_values:
            return pd.DataFrame()

        return pd.DataFrame(self.portfolio_values, columns=['timestamp', 'portfolio_value'])


def run_comprehensive_backtest(model: XGBoostTradingModel,
                              historical_data: pd.DataFrame,
                              confidence_thresholds: List[float] = None) -> Dict[str, Any]:
    """
    Kör omfattande backtest med olika parametrar

    Args:
        model: Tränad XGBoost modell
        historical_data: Historiska OHLCV data
        confidence_thresholds: Lista med confidence thresholds att testa

    Returns:
        Dict med backtest resultat för olika parametrar
    """
    if confidence_thresholds is None:
        confidence_thresholds = [0.5, 0.6, 0.7, 0.8]

    results = {}

    for threshold in confidence_thresholds:
        backtester = Backtester(model)
        result = backtester.run_backtest(
            historical_data=historical_data,
            confidence_threshold=threshold
        )

        results[f'confidence_{threshold}'] = {
            'metrics': result,
            'trades_df': backtester.get_trades_df(),
            'portfolio_history': backtester.get_portfolio_history()
        }

    return results