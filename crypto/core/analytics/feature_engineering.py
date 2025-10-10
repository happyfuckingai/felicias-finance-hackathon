"""
Feature Engineering for XGBoost Trading Model

Skapar tekniska indikatorer och features från prisdata för ML-modellering.
Utökar befintliga tekniska indikatorer med ytterligare momentum och volatilitet features.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import talib as ta
from datetime import datetime, timedelta


class FeatureEngineer:
    """Skapar features från tekniska indikatorer för trading prediktioner"""

    def __init__(self):
        self.feature_columns = []

    def create_trading_features(self, price_data: pd.DataFrame,
                               include_volume: bool = True,
                               include_momentum: bool = True,
                               include_volatility: bool = True) -> pd.DataFrame:
        """
        Skapa omfattande feature set från pris- och volymdata

        Args:
            price_data: DataFrame med OHLCV data (open, high, low, close, volume)
            include_volume: Inkludera volymbaserade features
            include_momentum: Inkludera momentum indikatorer
            include_volatility: Inkludera volatilitet features

        Returns:
            DataFrame med alla tekniska indikatorer som features
        """
        features = pd.DataFrame(index=price_data.index)

        # Grundläggande prisbaserade features
        features['returns'] = price_data['close'].pct_change()
        features['log_returns'] = np.log(price_data['close'] / price_data['close'].shift(1))

        # Prisnivåer
        features['high_low_ratio'] = price_data['high'] / price_data['low']
        features['close_open_ratio'] = price_data['close'] / price_data['open']
        features['body_size'] = abs(price_data['close'] - price_data['open']) / price_data['open']

        # Volym features
        if include_volume and 'volume' in price_data.columns:
            features['volume_ratio'] = price_data['volume'] / price_data['volume'].rolling(20).mean()
            features['volume_ma_ratio'] = price_data['volume'] / price_data['volume'].rolling(20).mean()
            features['volume_std'] = price_data['volume'].rolling(20).std()
            features['dollar_volume'] = price_data['volume'] * price_data['close']

        # Tekniska indikatorer - Trend
        features['sma_20'] = ta.SMA(price_data['close'].values, timeperiod=20)
        features['sma_50'] = ta.SMA(price_data['close'].values, timeperiod=50)
        features['ema_12'] = ta.EMA(price_data['close'].values, timeperiod=12)
        features['ema_26'] = ta.EMA(price_data['close'].values, timeperiod=26)

        # RSI (Relative Strength Index)
        features['rsi_14'] = ta.RSI(price_data['close'].values, timeperiod=14)
        features['rsi_7'] = ta.RSI(price_data['close'].values, timeperiod=7)
        features['rsi_21'] = ta.RSI(price_data['close'].values, timeperiod=21)

        # MACD (Moving Average Convergence Divergence)
        macd, macdsignal, macdhist = ta.MACD(price_data['close'].values,
                                           fastperiod=12, slowperiod=26, signalperiod=9)
        features['macd'] = macd
        features['macd_signal'] = macdsignal
        features['macd_hist'] = macdhist

        # Bollinger Bands
        upper, middle, lower = ta.BBANDS(price_data['close'].values,
                                        timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        features['bb_upper'] = upper
        features['bb_middle'] = middle
        features['bb_lower'] = lower
        features['bb_width'] = (upper - lower) / middle
        features['bb_position'] = (price_data['close'] - lower) / (upper - lower)

        if include_momentum:
            # Stochastic Oscillator
            slowk, slowd = ta.STOCH(price_data['high'].values, price_data['low'].values,
                                   price_data['close'].values,
                                   fastk_period=14, slowk_period=3, slowd_period=3)
            features['stoch_k'] = slowk
            features['stoch_d'] = slowd

            # Williams %R
            features['williams_r'] = ta.WILLR(price_data['high'].values,
                                            price_data['low'].values,
                                            price_data['close'].values, timeperiod=14)

            # Momentum
            features['mom_10'] = ta.MOM(price_data['close'].values, timeperiod=10)
            features['mom_20'] = ta.MOM(price_data['close'].values, timeperiod=20)

            # Rate of Change (ROC)
            features['roc_10'] = ta.ROC(price_data['close'].values, timeperiod=10)
            features['roc_20'] = ta.ROC(price_data['close'].values, timeperiod=20)

        if include_volatility:
            # Average True Range (ATR)
            features['atr_14'] = ta.ATR(price_data['high'].values,
                                       price_data['low'].values,
                                       price_data['close'].values, timeperiod=14)

            # Normalized ATR
            features['natr'] = ta.NATR(price_data['high'].values,
                                      price_data['low'].values,
                                      price_data['close'].values, timeperiod=14)

            # Volatility Ratio
            features['volatility_ratio'] = features['atr_14'] / features['bb_width']

        # Laggade features (för att fånga momentum)
        for lag in [1, 3, 5, 10]:
            features[f'returns_lag_{lag}'] = features['returns'].shift(lag)
            features[f'rsi_lag_{lag}'] = features['rsi_14'].shift(lag)

        # Rolling statistik
        for window in [5, 10, 20]:
            features[f'returns_ma_{window}'] = features['returns'].rolling(window).mean()
            features[f'returns_std_{window}'] = features['returns'].rolling(window).std()
            features[f'volume_ma_{window}'] = (price_data['volume'].rolling(window).mean()
                                             if 'volume' in price_data.columns else np.nan)

        # Target för supervised learning (prisriktning nästa period)
        features['target'] = (price_data['close'].shift(-1) > price_data['close']).astype(int)

        # Rensa NaN värden från tekniska indikatorer
        features = features.fillna(method='bfill').fillna(method='ffill').fillna(0)

        self.feature_columns = [col for col in features.columns if col != 'target']

        return features

    def create_target_labels(self, price_data: pd.DataFrame,
                           horizon: int = 1,
                           threshold: float = 0.0) -> pd.Series:
        """
        Skapa target labels för prisriktning

        Args:
            price_data: DataFrame med prisdata
            horizon: Antal perioder framåt för prediktion
            threshold: Tröskelvärde för att klassificera som upp/ned (%)

        Returns:
            Series med binära labels (1 för upp, 0 för ner)
        """
        future_returns = price_data['close'].shift(-horizon) / price_data['close'] - 1
        return (future_returns > threshold).astype(int)

    def get_feature_importance_template(self) -> List[str]:
        """Returnerar lista med alla möjliga feature namn för importance analys"""
        return self.feature_columns

    def prepare_training_data(self, features: pd.DataFrame,
                            target: pd.Series,
                            split_ratio: float = 0.8) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Förbereder tränings- och testdata

        Args:
            features: Feature DataFrame
            target: Target Series
            split_ratio: Förhållande mellan träning och test

        Returns:
            Tuple med (X_train, X_test, y_train, y_test)
        """
        # Ta bort NaN från target
        valid_idx = target.dropna().index
        features_clean = features.loc[valid_idx]
        target_clean = target.loc[valid_idx]

        # Split data
        split_idx = int(len(features_clean) * split_ratio)

        X_train = features_clean.iloc[:split_idx]
        X_test = features_clean.iloc[split_idx:]
        y_train = target_clean.iloc[:split_idx]
        y_test = target_clean.iloc[split_idx:]

        return X_train, X_test, y_train, y_test


def create_advanced_features(price_data: pd.DataFrame) -> pd.DataFrame:
    """
    Utility funktion för att skapa avancerade features

    Args:
        price_data: OHLCV data

    Returns:
        DataFrame med avancerade tekniska features
    """
    engineer = FeatureEngineer()
    return engineer.create_trading_features(price_data)